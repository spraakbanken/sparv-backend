import smtplib

from builtins import str
from queue import Queue
from threading import Thread
from xml.sax.saxutils import escape, unescape
from werkzeug.utils import secure_filename
from flask import Response, request, json
import logging

from build import Build
from enums import Status, Message, finished
from schema_utils import validate_json
from schema_generator import make_schema
from utils import pretty_epoch_time, ERROR_MSG, make_trace
try:
    from config import Config
except ImportError:
    from config_default import Config

log = logging.getLogger('pipeline.' + __name__)


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
        except Exception as error:
            log.error("Error while getting result: %s" % str(error))
            return "<error>%s\n</error>\n</result>\n" % ERROR_MSG["no_result"]

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
        for filename, textlist in filedict.items():
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


def upload_procedure(builds, settings, files, email):
    """The file upload procedure. Called by wrapper 'upload()'."""

    if not files:
        log.exception(ERROR_MSG["no_files"])
        yield '<result>\n<error>' + ERROR_MSG["no_files"] + '</error>\n</result>\n'
        raise StopIteration

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


def get_settings(lang, mode):
    """Get the makefile settings."""
    schema_json = make_schema(lang, mode)
    error = None

    try:
        settings = json.loads(request.values.get('settings', '{}'))
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
        res = '<result>\n<error>' + error + '</error>\n</result>\n'
        return Response(res, mimetype='application/xml')

    else:
        incremental = request.values.get('incremental', '')
        incremental = incremental.lower() == 'true'
        return settings, incremental


def check_secret_key(secret_key):
    if Config.secret_key and secret_key == Config.secret_key:
        log.info("Secret key was confirmed.")
        return True
    else:
        log.error("Secret key was not supplied or incorrect.")
        return False
