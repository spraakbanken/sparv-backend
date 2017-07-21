# -*- coding: UTF-8 -*-

from Queue import Queue
from threading import Thread
from xml.sax.saxutils import escape, unescape
from werkzeug.utils import secure_filename

import logging
import json
import time
import cgi
import smtplib
import os
import signal
import sys

from build import Build
from config import Config
from enums import Status, Message, finished
from make_makefile import makefile
from make_trace import make_trace
from schema_utils import validate_json
from schema_generator import make_schema
from utils import pretty_epoch_time, query, get_build_directories, rmdir, ERROR_MSG

log = logging.getLogger('pipeline.' + __name__)


def handlers(builds, environ):
    """Return the handlers with a builds dictionary, and wsgi environment"""
    return {
        '': lambda: handle(builds, environ),
        '/join': lambda: handle(builds, environ, 'join'),
        '/makefile': lambda: handle(builds, environ, 'makefile'),
        '/upload': lambda: handle(builds, environ, 'upload'),
        '/download': lambda: download(builds, environ),
        '/api': api,
        '/schema': lambda: schema(environ),
        '/ping': ping,
        '/status': lambda: status(builds),
        '/cleanup': lambda: cleanup(builds),
        '/cleanup/errors': lambda: cleanup(builds, remove_errors=True),
        '/cleanup/forceall': lambda: cleanup_all(builds, environ),
        '/cleanup/kill': lambda: kill_zombies(environ)
    }


def handler_content_type(path):
    """Return the content type for a handler."""
    if path == "/schema" or path == "/api":
        return "application/json; charset=utf-8"
    elif path == "/makefile":
        return "text/plain; charset=utf-8"
    elif path == "/download":
        return "application/zip; charset=utf-8"
    elif path == "/upload":
        return "application/xml; charset=utf-8"
    else:
        return "application/xml; charset=utf-8"


def schema(environ):
    """The /schema handler"""
    qs = cgi.parse_qs(environ['QUERY_STRING'])
    lang = qs.get('language', [''])[0]
    mode = qs.get('mode', [''])[0]

    return_json = make_schema(lang, mode)
    yield json.dumps(return_json, indent=2)


def status(builds):
    """
    The /status handler.
    Return the status of existing builds.
    """
    res = "<status>\n"
    for h, b in builds.iteritems():
        if b.status is not None:
            res += ("<build hash='%s' status='%s' since='%s' accessed='%s' accessed-secs-ago='%s'/>\n" %
                    (h, Status.lookup[b.status],
                     pretty_epoch_time(b.status_change_time),
                     pretty_epoch_time(b.accessed_time),
                     round(time.time() - b.accessed_time, 1)))

    res += "</status>\n"
    return [res]


def cleanup(builds, timeout=604800, remove_errors=False):
    """
    The /cleanup handler.
    Remove builds that are finished and haven't been accessed within the timeout,
    which is by default 7 days.
    With remove_errors, removes the builds with status Error.
    """
    to_remove = []
    for h, b in builds.iteritems():
        if (finished(b.status) and time.time() - b.accessed_time > timeout or
                b.status == Status.Error and remove_errors):
            log.info("Removing %s" % h)
            b.remove_files()
            to_remove.append(h)
    res = ""
    for h in to_remove:
        del builds[h]
        res += "<removed hash='%s'/>\n" % h
    if not res:
        res = "<message>No hashes to be removed.</message>"
    return [res]


def cleanup_all(builds, environ):
    """Remove all the existing builds. Requires secret_key parameter in query."""
    to_remove = []
    secret_key = query(environ, 'secret_key', '')

    if Config.secret_key and secret_key == Config.secret_key:
        log.info("Secret key was confirmed. All builds will be removed.")
        build_dirs = get_build_directories(Config.builds_dir)
        for hashnumber in build_dirs:
            b = builds.get(hashnumber, None)
            log.info("Removing %s" % hashnumber)
            if b:
                to_remove.append(hashnumber)
                b.remove_files()
            else:
                rmdir(os.path.join(Config.builds_dir, hashnumber))
        res = ""
        for h in to_remove:
            del builds[h]
            res += "<removed hash='%s'/>\n" % h
        if not res:
            res = "<message>No hashes to be removed.</message>"
        return [res]
    else:
        log.error("Secret key was not supplied or incorrect. No builds removed.")
        return ["<error>Failed to remove all builds: secret key could not be confirmed.</error>\n"]


def kill_zombies(environ):
    """
    Find zombie processes and kill them.
    Requires secret_key and user parameter in query.
    """
    user = query(environ, 'user', '')
    if not user:
        log.error("No user supplied.")
        return ["<error>No user supplied.</error>\n"]
    secret_key = query(environ, 'secret_key', '')
    if not Config.secret_key or secret_key != Config.secret_key:
        log.error("Secret key could not be confirmed.")
        return ["<error>Secret key could not be confirmed.</error>\n"]

    zombies = []
    for line in os.popen("ps -u %s a" % user):
        fields = line.split(None, 4)
        status = fields[2]
        pid = fields[0]
        if status == "Z":
            zombies.append(pid)

    if zombies:
        for n, pid in enumerate(zombies, start=1):
            os.kill(int(pid), signal.SIGHUP)
        log.info("%s zombies killed" % n)
        return ["<message>%s zombies were killed.</message>" % n]
    else:
        log.info("No zombies found")
        return ["<message>No zombies found.</message>"]


def ping():
    """
    The /ping handler.
    Ping this script, respond with the status of the catapult.
    """
    ping_error_msg = "<error>\n<catapult time='%s'>\n<stdout>%s</stdout>\n<stderr>%s</stderr>\n</catapult>\n</error>"
    try:
        t0 = time.time()
        from subprocess import Popen, PIPE
        cmd = [Config.catalaunch_binary, Config.socket_file, "PING"]
        stdout, stderr = Popen(cmd, stdout=PIPE, stderr=PIPE).communicate()
        t1 = time.time()
    except BaseException as e:
        return ["<error>Failed to ping catapult: %s</error>\n" % e]
    else:
        t = round(t1 - t0, 4)
        if not stderr and stdout == "PONG":
            return ["<catapult time='%s'>%s</catapult>\n" % (t, stdout)]
        else:
            return [ping_error_msg % (t, stdout, stderr)]


def download(builds, environ):
    """The /download handler."""
    hashnumber = query(environ, 'hash', '')
    build = builds[hashnumber]

    # Serve zip file or xml
    if build.files:
        filepath = build.zipfpath
    else:
        filepath = build.result_file

    filelike = open(filepath, "rb")
    for byte in iter(lambda: filelike.read(4096), ''):
        yield byte


def upload(builds, environ, settings, post, email):
    """The /upload handler. Called by wrapper 'handle()'."""
    # start new build with file upload
    files = get_files(post["files[]"])

    yield "<result>\n"
    log.info("Starting a new build with file upload procedure")
    for node, current_build in build(builds, "", settings, True, "xml", files=files):
        yield node

    # create downloadable zip file
    current_build.zip_result()

    # something went wrong...
    if current_build.status == Status.Error or current_build.status == Status.ParseError:
        if email:
            if current_build.warnings:
                warnings = current_build.warnings
            else:
                warnings = ""
            send_crash_mail(email, current_build.build_hash, warnings)

    # send mail with download link
    else:
        if email:
            link = "%s/download?hash=%s" % (Config.backend, current_build.build_hash)
            send_result_mail(email, link)


def build(builds, original_text, settings, incremental, fmt, files=None):
    """
    Start a build for this corpus. If it is already running,
    join it. Messages from the build are received on a queue.
    """
    if not files:
        build = Build(original_text, settings)
    else:
        build = Build(original_text, settings, files=files)

    # Start build or listen to existing build
    if build.build_hash not in builds:
        builds[build.build_hash] = build
        build.make_files()
        t = Thread(target=Build.run, args=[build, fmt])
        t.start()
    # elif builds[build.build_hash].status == (Status.Error or Status.ParseError):
    #     log.info("Errorneous build found! Retrying...")
    #     t = Thread(target=Build.run, args=[build, fmt])
    #     t.start()
    else:
        build = builds[build.build_hash]
        log.info("Joining existing build (%s) which started at %s" %
                 (build.build_hash, pretty_epoch_time(build.status_change_time)))

    if files:
        return join_build(build, incremental, fileupload=True)
    else:
        return join_build(build, incremental)


def join_from_hash(builds, hashnumber, incremental):
    """Join a build with a given hash number if it exists."""
    build = builds.get(hashnumber, None)
    if build is not None:
        if hashnumber.endswith(Config.fileupload_ext):
            yield ("<settings>%s</settings>\n<original %s/>\n"
                   % (build.get_settings(), escape(build.get_original())))
            for node, _b in join_build(build, True, fileupload=True):
                yield node
        else:
            yield ("<settings>%s</settings>\n<original>%s</original>\n"
                   % (build.get_settings(), escape(build.get_original())))
            for node in join_build(build, incremental):
                yield node
    else:
        yield "<error>No such build!</error>\n</result>\n"


def join_build(build, incremental, fileupload=False):
    """
    Join an existing build, and send increment messages
    until it is completed. Then send the build's result or
    the link to the downloadable zip file.
    """
    # Make a new queue which receives messages from the builder process
    queue = Queue()
    build.queues.append(queue)

    def get_result():
        assert(finished(build.status))
        build.access()
        try:
            return build.result() + '</result>\n'
        except:
            error = sys.exc_info()[0]
            log.error("Error while getting result: " + error)
            return "<result>\n<error>%s\n\n%s</error>\n</result>\n" % (ERROR_MSG["no_result"], error)

    # Send this build's hash
    if fileupload:
        yield "<build hash='%s' type='files'/>\n" % build.build_hash, build
    else:
        yield "<build hash='%s'/>\n" % build.build_hash

    # Result already exists
    if finished(build.status):
        log.info("Result already exists since %s" %
                 pretty_epoch_time(build.status_change_time))
        if fileupload:
            yield get_result(), build
        else:
            yield get_result()

    # Listen for completion
    else:
        if incremental and build.status == Status.Running:
            log.info("Already running, sending increment message")
            if fileupload:
                yield build.increment_msg(), build
            else:
                yield build.increment_msg()

        while True:
            msg_type, msg = queue.get()
            if msg_type == Message.StatusChange:
                log.info("Message %s" % Status.lookup[msg])
            # Has status changed to finished?
            if msg_type == Message.StatusChange:
                if finished(msg):
                    break
            # Increment message
            elif incremental and msg_type == Message.Increment:
                if fileupload:
                    yield msg, build
                else:
                    yield msg

        log.info("Getting result...")
        if fileupload:
            yield get_result(), build
        else:
            yield get_result()


def get_files(infiles):
    """Extract text and file name from input file."""
    filedict = {}
    if type(infiles) != list:
        infiles = [infiles]
    for infile in infiles:

        # get file name (strip file extension)
        if "." not in infile.filename:
            filename = infile.filename
            fileext = ".txt"
        else:
            filename = infile.filename[:infile.filename.rfind(".")]
            fileext = infile.filename[infile.filename.rfind("."):]

        # Ensure ASCII filename without white spaces etc.
        filename = secure_filename(filename)
        original_text = infile.file.read()

        # Convert to xml
        if fileext != ".xml":
            original_text = escape(original_text)
            original_text = "<text>\n" + original_text + "\n</text>"

        filedict.setdefault(filename, []).append(original_text)

        files = []
        for filename, textlist in filedict.iteritems():
            if len(textlist) > 1:
                for n, txt in enumerate(textlist, start=1):
                    newfilename = "%s_#%s" % (filename, str(n))
                    if newfilename not in filedict:
                        files.append((newfilename, txt))
                    else:
                        newfilename = "%s_##%s" % (filename, str(n))
            else:
                files.append((filename, textlist[0]))

    return sorted(files)


def send_result_mail(adress, link):
    """Create and send a mail with the download link to adress."""
    # parse adress
    if "," in adress:
        splitchar = ","
    elif ";" in adress:
        splitchar = ";"
    else:
        splitchar = " "
    toadress = adress.split(splitchar)
    toadress = [i.strip() for i in toadress]

    server = "localhost"
    fromadress = "sb-sparv@svenska.gu.se"
    subject = "Your corpus is done!"
    txt = "Dear Sparv User,\n\n"
    txt += "You can download the annotated corpus by clicking on the following link:\n\n" + link
    txt += "\n\nPlease note that the corpus will be removed after seven days."
    txt += "\n\nYours,\nSparv\nhttp://spraakbanken.gu.se/sparv\nsb-sparv@svenska.gu.se"

    # Prepare actual message
    message = "\From: %s\nTo: %s\nSubject: %s\n\n%s" % (fromadress, ", ".join(toadress), subject, txt)

    # Send the mail
    server = smtplib.SMTP(server)
    server.sendmail(fromadress, toadress, message)
    server.quit()


def send_crash_mail(adress, hashnumber, warnings):
    """Create and send a mail with the crash report."""
    from email.header import Header
    from email.mime.text import MIMEText

    # parse adress
    if "," in adress:
        splitchar = ","
    elif ";" in adress:
        splitchar = ";"
    else:
        splitchar = " "
    toadress = adress.split(splitchar)
    toadress = [i.strip() for i in toadress]

    server = "localhost"
    fromadress = "sb-sparv@svenska.gu.se"

    subject = "The analysis of your corpus crashed"
    txt = []
    txt.append(u"Dear Sparv User,\n")
    txt.append(u"Unfortunately, something went wrong with the analysis of your corpus (hashnumber: %s)." % hashnumber)
    txt.append(u"When you upload files, please make sure that they are either text files or that they contain valid XML.")
    txt.append(u"If you don't know what went wrong and you would like Språkbanken to help you with this problem, please forward this email to sb-sparv@svenska.gu.se")
    txt.append(u"\nYours,\nSparv\nhttp://spraakbanken.gu.se/sparv\nsb-sparv@svenska.gu.se")

    if warnings:
        txt.append("\n\nCrash report:\n")
        txt.append(unescape(warnings))

    # Prepare actual message
    msg = MIMEText("\n".join(txt).encode("utf-8"), 'plain', 'UTF-8')
    msg['Subject'] = "%s" % Header(subject, 'utf-8')
    msg['From'] = fromadress
    msg['To'] = ", ".join(toadress)

    # Send the mail
    server = smtplib.SMTP(server)
    server.sendmail(fromadress, toadress, msg.as_string())
    server.quit()


def handle(builds, environ, cmd=None):
    """Remaining handlers: /makefile, /join, / and wrapper for /upload"""
    email = query(environ, 'email', '')
    lang = (query(environ, 'language', 'sv'))
    mode = (query(environ, 'mode', 'plain'))

    schema_json = make_schema(lang, mode)
    error = None

    try:
        settings = json.loads(query(environ, 'settings', '{}'))
    except:
        log.exception("Error in json parsing the settings variable")
        error = escape(make_trace())
        settings = {}
    settings_validator = validate_json(schema_json)
    for e in sorted(settings_validator.iter_errors(settings)):
        if error is None:
            error = ""
        error += str(e) + "\n"

    if error is not None:
        log.error("Errors from schema: " + error)
        yield '<result>\n<error>' + error + '</error>\n</result>\n'
    else:
        incremental = query(environ, 'incremental', '')
        incremental = incremental.lower() == 'true'

        post_env = environ.copy()
        post = cgi.FieldStorage(
            fp=environ['wsgi.input'],
            environ=post_env,
            keep_blank_values=True)

        try:
            if cmd == "makefile":
                log.info("Returning makefile")
                yield makefile(settings)

            elif cmd == "join":
                log.info("Joining existing build")
                yield "<result>\n"
                hashnumber = query(environ, 'hash', '')
                for node in join_from_hash(builds, hashnumber, incremental):
                    yield node

            elif cmd == "upload":
                for node in upload(builds, environ, settings, post, email):
                    yield node

            else:
                log.info("Starting a new build with text input procedure")
                yield "<result>\n"
                txt = post["text"].value
                # Escape plain text and give it a root element
                if mode == "plain":
                    txt = escape(txt)
                    txt = "<text>" + txt + "</text>"
                # Check for empty input
                if not txt:
                    log.exception(ERROR_MSG["empty_input"])
                    yield "<error>%s</error>\n</result>" % ERROR_MSG["empty_input"]
                else:
                    for node in build(builds, txt, settings, incremental, "xml"):
                        yield node
        except:
            trace = make_trace()
            log.exception("Error in handle")
            yield '<trace>' + escape(trace) + '</trace>\n'
            yield '</result>\n'


def api():
    with open(Config.api_json, "r") as f:
        api = f.read()
    return [api]
