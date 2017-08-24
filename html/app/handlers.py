# -*- coding: UTF-8 -*-

from future import standard_library
standard_library.install_aliases()
from flask import Flask, Response, request, json, render_template
from flask_cors import CORS
from xml.sax.saxutils import escape
import logging
import time
import os

from config import Config
from make_makefile import makefile
from schema_generator import make_schema
from utils import pretty_epoch_time, get_build_directories, rmdir, ERROR_MSG, make_trace
from handler_utils import build, upload_procedure, get_settings, join_from_hash, check_secret_key
from enums import Status, finished

app = Flask(__name__)
CORS(app)  # enables CORS support on all routes
log = logging.getLogger('pipeline.' + __name__)


@app.before_request
def my_method():
    app.config["N_REQUESTS"] += 1
    try:
        path = request.url_rule.rule
    except:
        path = "/"
    log.info("Handling %s (request %s)" % (path, int(app.config["N_REQUESTS"])))


@app.route('/hello')
def hello_world():
    log.info("hello!")
    return Response("<response>Hello!</response>\n", mimetype='application/xml')


@app.route('/api')
def api():
    """Return description of API."""
    return render_template("api.html")


@app.route('/status')
def status():
    """
    The /status handler.
    Return the status of existing builds.
    """
    builds = app.config["BUILDS"]
    res = "<status>\n"
    for h, b in builds.items():
        if b.status is not None:
            res += ("<build hash='%s' status='%s' since='%s' accessed='%s' accessed-secs-ago='%s'/>\n" %
                    (h, Status.lookup[b.status],
                     pretty_epoch_time(b.status_change_time),
                     pretty_epoch_time(b.accessed_time),
                     round(time.time() - b.accessed_time, 1)))

    res += "</status>\n"
    return Response(res, mimetype='application/xml', content_type='application/xml; charset=utf-8')


@app.route('/ping')
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
        xml = "<error>Failed to ping catapult: %s</error>\n" % e
        return Response(xml, mimetype='application/xml')
    else:
        t = round(t1 - t0, 4)
        if not stderr and stdout == "PONG":
            xml = "<catapult time='%s'>%s</catapult>\n" % (t, stdout)
        else:
            xml = ping_error_msg % (t, stdout, stderr)
        return Response(xml, mimetype='application/xml')


@app.route('/schema')
def schema():
    """The /schema handler"""
    lang = request.values.get('language', 'sv')
    mode = request.values.get('mode', 'plain')
    return_json = make_schema(lang, mode)
    return Response(json.dumps(return_json, indent=2, ensure_ascii=False),
                    mimetype="application/json",
                    content_type='application/json; charset=utf-8')


@app.route('/cleanup')
def cleanup(timeout=604800, remove_errors=False):
    """
    The /cleanup handler.
    Remove builds that are finished and haven't been accessed within the timeout,
    which is by default 7 days.
    With remove_errors, removes the builds with status Error.
    Requires secret_key parameter in query.
    """
    secret_key = request.values.get('secret_key', '')
    if check_secret_key(secret_key):
        builds = app.config["BUILDS"]
        to_remove = []
        for h, b in builds.items():
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
            res = "<message>No hashes to be removed.</message>\n"
    else:
        res = "<error>Failed to run cleanup: secret key could not be confirmed.</error>\n"

    return Response(res, mimetype='application/xml')


@app.route('/cleanup/errors')
def cleanup_errors():
    return cleanup(remove_errors=True)


@app.route('/cleanup/forceall')
def cleanup_all():
    """Remove all the existing builds. Requires secret_key parameter in query."""
    builds = app.config["BUILDS"]
    to_remove = []
    secret_key = request.values.get('secret_key', '')

    if check_secret_key(secret_key):
        log.info("All builds will be removed.")
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
            res = "<message>No hashes to be removed.</message>\n"
    else:
        log.error("No builds will be removed.")
        res = "<error>Failed to remove all builds: secret key could not be confirmed.</error>\n"

    return Response(res, mimetype='application/xml')


@app.route('/makefile', methods=['GET', 'POST'])
def get_makefile():
    """Handler for returning the makefile."""
    try:
        lang = request.values.get('language', 'sv')
        mode = request.values.get('mode', 'plain')
        settings, incremental = get_settings(lang, mode)
        log.info("Returning makefile")
        return Response(makefile(settings), mimetype='text/plain')
    except:
        trace = make_trace()
        log.exception("Error in /makefile")
        res = '<result>\n<trace>' + escape(trace) + '</trace>\n</result>\n'
        return Response(res, mimetype='application/xml')


@app.route('/', methods=['GET', 'POST'])
def text_input():
    # On empty input return api description
    if not request.values:
        return api()

    try:
        log.info("Starting a new build with text input procedure")
        lang = request.values.get('language', 'sv')
        mode = request.values.get('mode', 'plain')
        txt = request.values.get('text', '')

        builds = app.config["BUILDS"]
        settings, incremental = get_settings(lang, mode)

        def generate(mode, builds, txt, settings, incremental):
            yield "<result>\n".encode("UTF-8")
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

        return Response(generate(mode, builds, txt, settings, incremental), mimetype='application/xml')
    except:
        trace = make_trace()
        log.exception("Error in text input procedure")
        res = '<result>\n<trace>' + escape(trace) + '</trace>\n</result>\n'
        return Response(res, mimetype='application/xml')


@app.route('/join', methods=['GET', 'POST'])
def join():
    """Handler for joining an existing build."""
    try:
        log.info("Joining existing build")
        lang = request.values.get('language', 'sv')
        mode = request.values.get('mode', 'plain')
        builds = app.config["BUILDS"]
        _settings, incremental = get_settings(lang, mode)
        hashnumber = request.values.get('hash', '')

        def generate(builds, hashnumber, incremental):
            yield "<result>\n"
            for node in join_from_hash(builds, hashnumber, incremental):
                yield node

        return Response(generate(builds, hashnumber, incremental), mimetype='text/plain')
    except:
        trace = make_trace()
        log.exception("Error in /join")
        res = '<result>\n<trace>' + escape(trace) + '</trace>\n</result>\n'
        return Response(res, mimetype='application/xml')


@app.route('/upload', methods=['GET', 'POST'])
def file_upload():
    """Handler for file upload procedure."""
    try:
        lang = request.values.get('language', 'sv')
        mode = request.values.get('mode', 'plain')
        email = request.values.get('email', '')
        builds = app.config['BUILDS']
        settings, _incremental = get_settings(lang, mode)
        files = request.files.getlist("file[]")

        def generate(builds, settings, files, email):
            for node in upload_procedure(builds, settings, files, email):
                yield node

        return Response(generate(builds, settings, files, email), mimetype='application/xml')
    except:
        trace = make_trace()
        log.exception("Error in /upload")
        res = '<result>\n<trace>' + escape(trace) + '</trace>\n</result>\n'
        return Response(res, mimetype='application/xml')


@app.route('/download')
def download():
    """The /download handler."""
    hashnumber = request.values.get('hash', '')
    builds = app.config["BUILDS"]
    build = builds[hashnumber]

    # Serve zip file or xml
    if build.files:
        filepath = build.zipfpath
        header = ('Content-Disposition', 'attachment; filename="korpus.zip"')
        mimetype = 'application/zip'
    else:
        filepath = build.result_file
        header = ('Content-Disposition', 'attachment; filename="korpus.xml"')
        mimetype = 'application/xml'

    filelike = open(filepath, "rb")

    def generate(filelike):
        for byte in iter(lambda: filelike.read(4096), ''):
            yield byte

    res = Response(generate(filelike), mimetype=mimetype)
    res.headers.set(header)
    return res
