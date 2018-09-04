# -*- coding: utf-8 -*-
# The Build class that contains the information about an initalised, running,
# or finished build.

from future import standard_library
standard_library.install_aliases()
from builtins import str, object
from xml.sax.saxutils import escape

import time
import os
import logging
import zipfile
import io
import re

try:
    from config import Config
except ImportError:
    from config_default import Config
from enums import Status, Message, finished
from make_makefile import makefile
from utils import make_hash, make, mkdir, rmdir, ERROR_MSG, make_trace, UTF8
from subprocess import call

log = logging.getLogger('pipeline.' + __name__)


class Build(object):
    """
    The Build class.

    Register yourself with a queue to the queues list to get messages
    about status changes and incremental messages.
    """

    def __init__(self, text, settings, files=None, init_from_hash=None, resuming=False):
        """
        Create the necessary directories and the makefile for this
        text and the JSON settings.
        """
        self.status = None
        self.queues = []
        self.files = files

        if init_from_hash:
            self.build_hash = init_from_hash
            # File upload:
            if init_from_hash.endswith(Config.fileupload_ext):
                original_dir = os.path.join(os.path.join(Config.builds_dir, self.build_hash), 'original')
                filelist = []
                for root, dirs, files in os.walk(original_dir):
                    for infile in files:
                        with open(os.path.join(root, infile), "r") as f:
                            text = f.read()
                        fname = infile[:infile.rfind(".")]
                        filelist.append((fname, text))
                self.files = filelist
            else:
                self.text = text
                self.filename = 'text'

        else:
            self.makefile_contents = makefile(settings)
            self.settings = settings
            # File upload
            if files:
                self.text = "\n".join(text for _fn, text in files)
                filenames = " ".join(fn for fn, _text in files)
                self.build_hash = make_hash(self.text, self.makefile_contents, filenames) + Config.fileupload_ext
            else:
                self.text = text
                self.filename = 'text'
                self.build_hash = make_hash(self.text, self.makefile_contents)

        # Directories
        self.directory = os.path.join(Config.builds_dir, self.build_hash)

        self.original_dir = os.path.join(self.directory, 'original')
        self.annotations_dir = os.path.join(self.directory, 'annotations')
        self.export_dir = os.path.join(self.directory, 'export.original')

        # Files
        self.makefile = os.path.join(self.directory, 'Makefile')
        self.warnings_log_file = os.path.join(self.directory, 'warnings.log')
        self.accessed_file = os.path.join(self.directory, 'accessed')
        self.settings_file = os.path.join(self.directory, 'settings.json')
        self.zipfpath = os.path.join(self.directory, "export.zip")
        self.zipfile = "export.zip"
        if not files:
            self.text_file = os.path.join(self.original_dir, self.filename + '.xml')
            self.result_file_path = os.path.join(self.export_dir, self.filename + '.xml')
            self.result_file = self.filename + '.xml'

        # Deem this build as accessed now, unless resuming an old build
        self.access(resuming)

        # Output from make, line by line
        self.make_out = []

        # Set increments to dummy values
        self.command = ""
        self.steps = 0
        self.step = 0

    def access(self, resuming=False):
        """
        Update the access time of this build.
        If resuming=True just get the time stamp of the build.
        """
        if not resuming:
            call(['touch', self.accessed_file])
            self.accessed_time = time.time()
        else:
            if os.path.exists(self.accessed_file):
                self.accessed_time = os.path.getmtime(self.accessed_file)
            else:
                self.accessed_time = time.time()

    def increment_msg(self):
        """The current increment message"""
        return '<increment command="%s" step="%s" steps="%s"/>\n' % (self.command, self.step, self.steps)

    def send_to_all(self, msg):
        """Send a message to all listeners."""
        for q in self.queues:
            q.put(msg)

    def change_status(self, status):
        """Change the status and notify all listeners."""
        self.status = status
        self.status_change_time = time.time()
        self.send_to_all((Message.StatusChange, self.status))
        log.info("%s: Status changed to %s", self.build_hash, Status.lookup[self.status])

    def change_step(self, new_cmd=None, new_step=None, new_steps=None):
        """
        Change the current step, and notify all listeners that the increment
        has been changed.
        """
        if new_step is not None:
            self.step = new_step
        if new_cmd is not None:
            self.command = new_cmd
        if new_steps is not None:
            self.steps = new_steps
        self.send_to_all((Message.Increment, self.increment_msg()))

    def get_settings(self):
        # Open settings file
        try:
            with open(self.settings_file, 'r') as f:
                settings = f.read()
        except:
            log.exception("Could not get settings for build")
            settings = "{}"
        return settings

    def get_original(self):
        # for file upload
        if self.files:
            original = []
            for filename, _text in self.files:
                original.append(filename + ".xml")
            original = "files='%s'" % ", ".join(original)
        else:
            try:
                # Open original file
                with open(self.text_file, 'r') as f:
                    original = f.read()
            except:
                log.exception("Could not get original for build")
                original = ""
        return original

    def make_files(self):
        """
        Make the files for building this corpus:
        directories, the original corpus and the makefile
        """
        self.change_status(Status.Init)
        self.access()

        # Make directories
        # map(mkdir, [self.directory, self.original_dir, self.annotations_dir, self.export_dir])
        for i in [self.directory, self.original_dir, self.annotations_dir, self.export_dir]:
            mkdir(i)

        # Make makefile
        with open(self.makefile, 'w') as f:
            f.write(makefile(self.settings))

        # Write settings file
        with open(self.settings_file, 'w') as f:
            import json
            f.write(json.dumps(self.settings, indent=2))

        # for file upload
        if self.files:
            for filename, text in self.files:
                infile = os.path.join(self.original_dir, filename + ".xml")
                with open(infile, 'w') as f:
                    f.write(text)

        else:
            if os.path.isfile(self.text_file):
                # This file has probably been built by a previous incarnation of the pipeline
                # (index.wsgi script has been restarted)
                log.info("File exists and is not rewritten: %s" % self.build_hash)
            else:
                with open(self.text_file, 'w') as f:
                    f.write(self.text)

    def remove_files(self):
        """Remove the files associated with this build."""
        self.change_status(Status.Deleted)
        log.info("Removing files")
        rmdir(self.directory)

    def _run(self, fmt):
        """
        Run make, sending increments, and eventually change status to done.
        """
        def send_warnings():
            try:
                with open(self.warnings_log_file, "r") as f:
                    self.warnings = self.fix_warnings(f.read().rstrip())

            except IOError:
                self.warnings = None

        make_settings = ['-C', self.directory,
                         'dir_chmod=777',
                         '-j', str(Config.processes),
                         "python=%s" % Config.python_interpreter]

        # First set up some environment variables
        os.environ['SPARV_MODELS'] = Config.sparv_models
        os.environ['SPARV_MAKEFILES'] = Config.sparv_makefiles

        # For initial parsing
        make_init = ['@TEXT'] + make_settings

        # For file upload
        if self.files:
            make_settings = ['export'] + make_settings
            self.out_files = []
            self.textfiles = []
            for filename, _text in self.files:
                self.out_files.append(os.path.join(self.export_dir, filename + '.xml'))
                self.textfiles.append(os.path.join(self.annotations_dir, filename + '.@TEXT'))

            # Try to parse files first
            stdout, stderr = make(make_init).communicate("")
            self.change_status(Status.Parsing)
            # Send warnings
            for out_file in self.textfiles:
                if not os.path.exists(out_file):
                    send_warnings()
                    self.change_status(Status.ParseError)
                    log.error(ERROR_MSG["parsing_error"])
                    return

        else:
            # Try to parse file first
            self.textfile = os.path.join(self.annotations_dir, self.filename + '.@TEXT')
            stdout, stderr = make(make_init).communicate("")
            self.change_status(Status.Parsing)
            if stderr:
                send_warnings()
                self.change_status(Status.Error)
                self.stderr = stderr.rstrip().decode("UTF-8")
                log.error(ERROR_MSG["make_error"])
                return
            # Send warnings
            if not os.path.exists(self.textfile):
                send_warnings()
                self.change_status(Status.ParseError)
                log.error(ERROR_MSG["parsing_error"])
                return

            if fmt == 'vrt' or fmt == 'cwb':
                make_settings = [fmt] + make_settings
                self.out_file = os.path.join(self.annotations_dir, self.filename + '.vrt')
            else:
                make_settings = ['export'] + make_settings
                self.out_file = os.path.join(self.export_dir, self.filename + '.xml')

        # Do a dry run to get the number of invocations that will be made
        stdout, stderr = make(make_settings + ['--dry-run']).communicate("")
        self.stderr = stderr.decode(UTF8)
        assert(self.stderr == "")
        steps = stdout.decode(UTF8).count(Config.python_interpreter)

        # No remote installations allowed
        os.environ['remote_cwb_datadir'] = "null"
        os.environ['remote_cwb_registry'] = "null"
        os.environ['remote_host'] = "null"

        # Now, make!
        self.make_process = make(make_settings)
        self.change_status(Status.Running)

        # Process the output from make
        self.change_step(new_cmd="", new_step=0, new_steps=steps + 1)
        step = 0
        for line in iter(self.make_process.stdout.readline, b''):
            line = line.decode(UTF8)
            self.make_out.append(line)
            if Config.python_interpreter in line:
                step += 1
                argstring = line.split(Config.python_interpreter)[1]
                arguments = argstring.lstrip().split()
                command = " ".join(arguments[1:3]) if "--" in arguments[3] else arguments[1]
                self.change_step(new_step=step, new_cmd=command)
        self.change_step(new_cmd="", new_step=step + 1)

        send_warnings()

        # The corpus should now be in self.out_file
        # Its contents are not stored because of memory reasons
        # assert os.path.isfile(self.out_file)

        self.make_process.stdout.close()
        self.make_process.stderr.close()
        self.make_process.wait()

        self.change_status(Status.Done)

    def run(self, fmt):
        """Run make, catching errors."""
        self.make_process = None
        self.trace, self.stdout, self.stderr = ("", "", "")

        try:
            self._run(fmt)
        except:
            self.trace = make_trace()
            log.exception(ERROR_MSG["make_error"])
            self.stdout = "".join(self.make_out)
            if self.make_process:
                self.stderr = self.make_process.stderr.read().rstrip()
                self.make_process.stdout.close()
                self.make_process.stderr.close()
                self.make_process.wait()
            self.change_status(Status.Error)

    def fix_warnings(self, warnings_str):
        """Remove confusing stuff from warnings log."""
        lines = []
        for line in warnings_str.split("\n"):
            l = re.sub(r"^\d+\W\|\W", "", line)
            # Only include lines with warnings and errors
            if "warning :" in l or "-ERROR-" in l:
                if escape(l) not in lines:
                    lines.append(escape(l))
        return "\n".join(lines)

    def zip_result(self):
        """Create a zip archive of all the result files in the export.original folder."""
        log.info("Creating zip file...")
        assert(finished(self.status))
        if self.status == Status.Done:
            if os.listdir(self.export_dir):
                zipf = zipfile.ZipFile(self.zipfpath, 'w', compression=zipfile.ZIP_DEFLATED)
                filelike = io.BytesIO()
                with zipfile.ZipFile(filelike, 'w', compression=zipfile.ZIP_DEFLATED) as zipflike:
                    for root, _dirs, files in os.walk(self.export_dir):
                        for xmlfile in files:
                            newfilename = xmlfile[:-4] + "_annotated.xml"
                            zipflike.write(os.path.join(root, xmlfile), arcname="korpus/" + newfilename)
                            zipf.write(os.path.join(root, xmlfile), arcname="korpus/" + newfilename)
                return filelike
            else:
                # används inte just nu
                out = ['<trace>' + escape(self.trace) + '</trace>',
                       '<stderr>' + escape(self.stderr) + '</stderr>',
                       '<stdout>' + escape(self.stdout) + '</stdout>']
                return "\n".join(out) + "\n"
        else:
            # används inte just nu
            out = ['<trace>' + escape(self.trace) + '</trace>',
                   '<stderr>' + escape(self.stderr) + '</stderr>',
                   '<stdout>' + escape(self.stdout) + '</stdout>']
            return "\n".join(out) + "\n"

    def result(self):
        """
        Return the result: either a built corpus with possible warning messages,
        or the error messages for an unsuccessful build.
        """
        assert(finished(self.status))
        out = []

        # Result when Parse Error
        if self.status == Status.ParseError:
            if self.warnings:
                out.append('<warning>' + escape(self.warnings) + '</warning>')
                out.append("<error>%s</error>" % ERROR_MSG["parsing_error"])
                log.error(ERROR_MSG["parsing_error"])
                return "\n".join(out)

        # Result when Done
        elif self.status == Status.Done:
            download_link = "%s/download?hash=%s" % (Config.backend, self.build_hash)

            if self.warnings:
                out.append('<warning>' + escape(self.warnings) + '</warning>')

            if hasattr(self, 'out_files'):
                for out_file in self.out_files:
                    if not os.path.exists(out_file):
                        self.change_status(Status.Error)
                        out.append("<error>%s</error>" % ERROR_MSG["missing_file"])
                        log.error(ERROR_MSG["missing_file"])
                        return "\n".join(out)

                result = "<corpus link='%s'/>\n" % download_link
                return result

            else:
                # Check for empty input (e.g. "<text></text>")
                try:
                    wordfile = os.path.join(self.annotations_dir, self.filename + '.token.word')
                    with open(wordfile, "r") as f:
                        word_contents = f.read()
                        if not word_contents:
                            raise ValueError('empty token.word file')
                except:
                    self.change_status(Status.Error)
                    log.exception(ERROR_MSG["empty_input"])
                    return "<error>%s</error>" % ERROR_MSG["empty_input"]

                # Check if result file is not empty
                try:
                    with open(self.out_file, "r") as f:
                        result_contents = f.read()
                        if not result_contents.strip("<corpus>\n").rstrip("</corpus>\n\n"):
                            raise ValueError('empty result file')
                        else:
                            result_contents = result_contents.replace("<corpus", "<corpus link='%s'" % download_link)
                            out.append(result_contents)
                            return "\n".join(out)
                except:
                    self.change_status(Status.Error)
                    log.exception(ERROR_MSG["no_result"])
                    return "<error>%s</error>" % ERROR_MSG["no_result"]

        else:
            out = ['<trace>' + escape(self.trace) + '</trace>',
                   '<stderr>' + escape(self.stderr) + '</stderr>',
                   '<stdout>' + escape(self.stdout) + '</stdout>',
                   '<error>' + ERROR_MSG["no_result"] + '</error>']
            return "\n".join(out) + "\n"
