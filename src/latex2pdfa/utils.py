#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utility functions

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.
This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with
this program. If not, see <http://www.gnu.org/licenses/>.
"""
import logging
import os
import platform
import re
import signal
import subprocess
from shutil import which
from subprocess import Popen, PIPE

from rich.console import Console
from rich.logging import RichHandler

console = Console(style="bold")

FORMAT = "%(message)s"
logging.basicConfig(
    level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler(show_path=False, console=console)]
)
logger = logging.getLogger("rich")


class CalledProcessError(subprocess.CalledProcessError):
    """Raised when run() is called with check=True and the process
       returns a non-zero exit status.

       Attributes:
         cmd, returncode, stdout, stderr, output
       """

    def __init__(self, returncode, cmd, output=None, stderr=None):
        self.returncode = returncode
        self.cmd = cmd
        self.output = output
        self.stderr = stderr

    def __str__(self):
        if self.returncode and self.returncode < 0:
            try:
                return "Command '%s' died with %r. %s" % (
                    self.cmd, signal.Signals(-self.returncod), self.stderr if self.stderr else "")
            except ValueError:
                return "Command '%s' died with unknown signal %d.  \n %s" % (
                    self.cmd, -self.returncode,  self.stderr if self.stderr else "")
        else:
            return "Command '%s' returned non-zero exit status %d.  \n %s" % (
                self.cmd, self.returncode,  self.stderr if str(self.stderr) else "")

    @property
    def stdout(self):
        """Alias for output attribute, to match stderr"""
        return self.output

    @stdout.setter
    def stdout(self, value):
        # There's no obvious reason to set this, but allow it anyway so
        # .stdout is a transparent alias for .output
        self.output = value


def run(*popenargs,
        input=None, capture_output=False, capture_error=False, timeout=None, check=False, **kwargs):
    """Run command with arguments and return a CompletedProcess instance.

    The returned instance will have attributes args, returncode, stdout and
    stderr. By default, stdout and stderr are not captured, and those attributes
    will be None. Pass stdout=PIPE and/or stderr=PIPE in order to capture them.

    If check is True and the exit code was non-zero, it raises a
    CalledProcessError. The CalledProcessError object will have the return code
    in the returncode attribute, and output & stderr attributes if those streams
    were captured.

    If timeout is given, and the process takes too long, a TimeoutExpired
    exception will be raised.

    There is an optional argument "input", allowing you to
    pass bytes or a string to the subprocess's stdin.  If you use this argument
    you may not also use the Popen constructor's "stdin" argument, as
    it will be used internally.

    By default, all communication is in bytes, and therefore any "input" should
    be bytes, and the stdout and stderr will be bytes. If in text mode, any
    "input" should be a string, and stdout and stderr will be strings decoded
    according to locale encoding, or by "encoding" if set. Text mode is
    triggered by setting any of text, encoding, errors or universal_newlines.

    The other arguments are the same as for the Popen constructor.
    """
    if input is not None:
        if kwargs.get('stdin') is not None:
            raise ValueError('stdin and input arguments may not both be used.')
        kwargs['stdin'] = PIPE

    if capture_output:
        if kwargs.get('stdout') is not None:
            raise ValueError('stdout argument may not be used '
                             'with capture_output.')
        kwargs['stdout'] = PIPE
    if capture_error:
        if kwargs.get('stderr') is not None:
            raise ValueError('stderr arguments may not be used '
                             'with capture_error.')
        kwargs['stderr'] = PIPE

    with Popen(*popenargs, **kwargs) as process:
        try:
            stdout, stderr = process.communicate(input, timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            process.kill()
            if subprocess._mswindows:
                # Windows accumulates the output in a single blocking
                # read() call run on child threads, with the timeout
                # being done in a join() on those threads.  communicate()
                # _after_ kill() is required to collect that and add it
                # to the exception.
                exc.stdout, exc.stderr = process.communicate()
            else:
                # POSIX _communicate already populated the output so
                # far into the TimeoutExpired exception.
                process.wait()
            raise
        except:  # Including KeyboardInterrupt, communicate handled that.
            process.kill()
            # We don't call process.wait() as .__exit__ does that for us.
            raise
        retcode = process.poll()
        if check and retcode:
            raise CalledProcessError(retcode, process.args,
                                     output=stdout, stderr=stderr)
    return subprocess.CompletedProcess(process.args, retcode, stdout, stderr)


def executable_exists(executable_cmd: str):
    """Check whether `exec` is on PATH and marked as executable."""
    return which(executable_cmd) is not None


def open_file(file):
    """
    cross-platform function to open a file with OS default app
    credits: https://stackoverflow.com/a/435669
    :param file: path of the file
    :return: None
    """
    if platform.system() == 'Darwin':  # macOS
        subprocess.call(('open', file))
    elif platform.system() == 'Windows':  # Windows
        os.startfile(file)
    else:  # linux variants
        subprocess.call(('xdg-open', file))


def run_process(cmd, cwd=None, verbose=False, ignore_errors=False):
    """
    runs the cmd as a subprocess
    :param cmd: command
    :param cwd: current working directory
    :param verbose: write the output to stduout in realtime
    :param ignore_errors: if true, the function will not raise exception if the cmd failed
    :return: None if verbose, cmd output otherwise
    """
    if verbose:
        console.rule()
        logger.info(f"[black on white]Running command: {cmd}[/]", extra={'markup': True})
        result = run(cmd, shell=True, stdout=console.file, check=not ignore_errors, cwd=cwd)
    else:
        result = run(cmd, shell=True, capture_output=True, capture_error=True, cwd=cwd)
        if result.stdout:
            # hack: catching pdflatex error msg
            match = re.search(r'Fatal error[\S\n ]+', result.stdout.decode('utf-8'))
            if match:
                error = "pdflatex compilation error: " + match.group()
                raise CalledProcessError(
                    returncode=result.returncode,
                    cmd=result.args,
                    stderr=error
                )
            return result.stdout.decode('utf-8')
        if result.stderr and not ignore_errors:
            raise CalledProcessError(
                returncode=result.returncode,
                cmd=result.args,
                stderr=result.stderr
            )

    return result
