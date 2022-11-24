#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A command line utility to automate the process of compiling a LaTex project to a PDF complaint with the PDF/A standard

## Credits and other resources
- [Peter Selinger: Creating high-quality PDF/A documents using LaTeX](https://www.mathstat.dal.ca/~selinger/pdfa/)
- [latex-pdfa-howto](https://github.com/op3/latex-pdfa-howto)


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

import argparse
import os
import re
import shutil
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from rich.panel import Panel
from rich.prompt import Confirm
from utils import open_file, run_process, executable_exists, console, logger
import importlib.metadata

__author__ = "Abdeladim S."
__github__ = ""
__copyright__ = "Copyright 2022"
__license__ = "GPLv3"
__version__ = importlib.metadata.version("latex2pdfa")
__file__ = 'latex2pdfa'

# intro
__header__ = f"""
[yellow]

888           88888888888                 .d8888b.  8888888b.  8888888b.  8888888888     d88P  d8888 
888               888                    d88P  Y88b 888   Y88b 888  "Y88b 888           d88P  d88888 
888               888                           888 888    888 888    888 888          d88P  d88P888 
888       8888b.  888   .d88b.  888  888      .d88P 888   d88P 888    888 8888888     d88P  d88P 888 
888          "88b 888  d8P  Y8b `Y8bd8P'  .od888P"  8888888P"  888    888 888        d88P  d88P  888 
888      .d888888 888  88888888   X88K   d88P"      888        888    888 888       d88P  d88P   888 
888      888  888 888  Y8b.     .d8""8b. 888"       888        888  .d88P 888      d88P  d8888888888 
88888888 "Y888888 888   "Y8888  888  888 888888888  888        8888888P"  888     d88P  d88P     888 
                                                                                                     
[/]
[italic black on yellow]An automated process to compile a [green]LaTex[/] project to a pdf file compliant with the [green]PDF/A[/] standard[/] 

version:  [blue underline]{__version__}[/]                                                                                                                                                                                          
"""

# Global vars
comment_start = "%" * 30 + __file__ + "%" * 30 + '\n'
comment_end = "%" * len(comment_start) + '\n'


class Latex2pdfa:

    def __init__(self, main_tex_file: str,
                 conformance_level: str = 'b',
                 conformance_level_version: str = '1',
                 output_dir: str = None,
                 output_filename: str = None,
                 ignore_metadata: bool = False,
                 verbose: bool = False,
                 verify: bool = False,
                 pdflatex_path: str = None,
                 pdflatex_extra_cmds: str = None,
                 bibtex_path: str = None,
                 gs_path: str = None,
                 exiftool_path: str = None,
                 qpdf_path: str = None,
                 verapdf_path: str = None,
                 clean: bool = True):
        """
        :param main_tex_file: the main LaTex file of the project
        :param conformance_level: The PDF/A standard conformance level:  `a`, `b`, or `u`.
                For archiving purposes, most universities require `b`, so the script is only compatible with the `b` level
                for now.
                Unfortunately, there is noway to generate a fully compatible `PDF/A-a` from LaTex at the moment of
                writing the script (2022) because of the problem of "pdf tagging".
        :param conformance_level_version: The version  of the standard: `1`, `2` or `3`.
                more info:  https://www.pdfa.org/resource/iso-19005-pdfa/
        :param output_dir: Output directory
        :param output_filename: The generated PDF filename
        :param ignore_metadata: Ignore adding the metadata file to the project folder in case it is already done manually
        :param verbose: Show all under the hood commands and their output
        :param clean: Remove the temporary files generated from the compilation
        :param verify: Verify the generated PDF using veraPDF
        :param pdflatex_path: pdflatex executable
        :param bibtex_path: bibtex executable
        :param gs_path: ghostscript executable
        :param exiftool_path: exiftool executable
        :param qpdf: qpdf executable
        """
        self.script_name = __file__  # the name of the script
        d = os.path.dirname(sys.modules[self.script_name].__file__)
        self.resources = (Path(d) / 'resources').absolute()
        self.binaries = (Path(d) / 'binaries').absolute()

        self.main_tex_file = Path(main_tex_file)
        assert conformance_level in ['a', 'b', 'u']
        self.conformance_level = conformance_level
        assert conformance_level_version in [1, 2, 3]
        self.conformance_level_version = conformance_level_version
        self.xmpdata_sample = self.resources / 'sample.xmpdata'
        self.verbose = verbose
        self.ignore_metadata = ignore_metadata
        self.verify = verify
        self.clean = clean
        self.pdflatex_extra_cmds = pdflatex_extra_cmds
        self.log = logger
        self.console_spinner = "bouncingBall"
        self.cmds_before_documentclass = [
            "\\pdfobjcompresslevel=0",
            "\\pdfminorversion=7",
            "\\pdfinclusioncopyfonts=1"
        ]

        self.preambule_cmds = [
            "\\usepackage[a-{}{}]{{pdfx}}".format(self.conformance_level_version, self.conformance_level),
            # "\\usepackage[pdfa]{hyperref}"
        ]

        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = self.main_tex_file.parent
        # creating output dir if it does not exist
        os.makedirs(self.output_dir, exist_ok=True)

        if output_filename:
            self.output_filename = output_filename
        else:
            self.output_filename = str(
                self.main_tex_file.stem) + f'-PDFA-{conformance_level_version}{conformance_level}.pdf'

        self.compiled_pdf_filename = str(self.main_tex_file.stem) + '.pdf'

        if pdflatex_path:
            self.pdflatex_cmd = Path(pdflatex_path)
        else:
            self.pdflatex_cmd = 'pdflatex'

        if bibtex_path:
            self.bibtex_cmd = Path(bibtex_path)
        else:
            self.bibtex_cmd = 'bibtex'

        if gs_path:
            self.gs_cmd = gs_path
        else:
            self.gs_cmd = self.binaries / 'ghostscript' / 'gs-923-linux-x86_64'

        if exiftool_path:
            self.exiftool_cmd = exiftool_path
        else:
            self.exiftool_cmd = 'exiftool'

        if qpdf_path:
            self.qpdf_cmd = qpdf_path
        else:
            self.qpdf_cmd = 'qpdf'

        if self.verify:
            if verapdf_path is not None:
                self.verapdf_cmd = verapdf_path
            else:
                self.log.error(
                    f"[red]Verification flag is used but no veraPDF path was provided",
                    extra={'markup': True})
                sys.exit(1)
        # else:
        #     self.verapdf_cmd = self.binaries / 'verapdf' / 'verapdf'

    def setup(self):
        """
        General setup requirements before running the script
        :return: None
        """
        console.rule(f"Checking requirements")
        with console.status("Checking LaTex file ...\n", spinner=self.console_spinner):
            self.check_tex_file()
        with console.status("Checking Executables ...\n", spinner=self.console_spinner):
            self.check_executables()

        # check if output filename has .pdf extension, otherwise add it
        if not self.output_filename.endswith('.pdf'):
            self.output_filename = self.output_filename + '.pdf'
        console.rule("***")

    def check_tex_file(self):
        """
        Checks if the tex file exists or not.
        :return: None
        """
        if not self.main_tex_file.is_file():
            self.log.error(f"[red]{self.main_tex_file} is not a file or does not exist!", extra={'markup': True})
            sys.exit(1)
        else:
            self.log.info(
                f"[green]:white_heavy_check_mark-text:LaTex file at: [blue underline]{self.main_tex_file.absolute()}[/] [OK][/]",
                extra={"markup": True})

    def add_metadata(self):
        """
        adds the `.xmpdata to the project directory
        :return: None
        """
        # return if `.xmpdata already exists on folder
        xmpdata_filename = self.main_tex_file.stem + ".xmpdata"
        xmpdata_file = self.main_tex_file.parent / xmpdata_filename
        modify_xmpdata = False
        if xmpdata_file.is_file():
            self.log.warning(
                f"[bold yellow]:warning-text: A file with extension [green italic].xmpdata[/] ([blue underline]{xmpdata_filename}[/]) already exists in your project folder.\n"
                f"  Do you want to modify it ?[/]", extra={"markup": True})
            modify_xmpdata = Confirm.ask()
            if not modify_xmpdata:
                return
        # if not, copy file from resources to project folder
        try:
            if not modify_xmpdata:  # don't overwrite the existing file, just modification
                shutil.copy(self.xmpdata_sample, xmpdata_file)
                self.log.info(
                    f"[green]:white_heavy_check_mark-text:The metadata file [blue underline]{xmpdata_filename}[/] has been added successfully to your project folder [/]",
                    extra={"markup": True})
            # open file in text editor for modification

            self.log.info(
                f"Do you want me to open the file [blue underline]{xmpdata_filename}[/] on your default text editor "
                f"to make the necessary modifications ?\n[thin](you can answer no to make the changes manually using "
                f"your favorite text editor)[/]",
                extra={"markup": True})
            confirm_open = Confirm.ask(" ")
            self.log.info(
                f"[magenta]Once you finish the modification (please pay attention to the syntax), save the file, "
                f"and press Enter to continue[/]",
                extra={"markup": True})
            time.sleep(3)
            if confirm_open:
                open_file(xmpdata_file.absolute())

            pause = input()
        except IOError as e:
            self.log.warning(
                f"[bold red blink]Cannot copy file to project folder, ensure that you have the necessary "
                f"permissions!\n Please add a file named {xmpdata_filename} manually and rerun the program[/] or run it with --ignore_metadata to skup this step",
                extra={"markup": True})
            sys.exit(0)

    def patch_latex(self):
        # checking if latex2pdfa has already changed the file
        with open(self.main_tex_file) as file:
            content = file.read()
            if self.script_name in content:
                self.log.info(
                    f"[green]:warning-text: It looks like the LaTex file has already been patched [/]",
                    extra={"markup": True})
                # Maybe the pdfx arguments should be updated any ways,
                # It is ok if the script is aborted in this phase, a backup file was created in the first pass

                path = Path(self.main_tex_file)
                text = path.read_text()
                text = re.sub('usepackage.*{pdfx}', self.preambule_cmds[0][1:], text)
                path.write_text(text)
                return
        # backing up the original file (in case something unusual happens, who knows!!)
        shutil.move(self.main_tex_file.absolute(), str(self.main_tex_file.absolute()) + ".backup")

        with open(self.main_tex_file, 'w') as file:
            with open(str(self.main_tex_file.absolute()) + '.backup', 'r') as orig_file:
                lines = orig_file.readlines()
            file.truncate()  # clear all file content
            # add cmds before documentclass
            file.write(comment_start)
            for cmd in self.cmds_before_documentclass:
                file.write(cmd + '\n')
            file.write(comment_end)
            for line in lines:
                file.write(line)
                if 'documentclass' in line:
                    # write cmds after documetclass
                    file.write(comment_start)
                    for cmd in self.preambule_cmds:
                        file.write(cmd + '\n')
                    file.write(comment_end)
        self.log.info(
            f"[green]:white_heavy_check_mark-text:LaTex file has been patched successfully[/]",
            extra={"markup": True})

    def generate_pdf(self):
        """
        Genrates the pdf file using pdflatex.
        Interestingly enough, the pdf generated from the first pass does not contain any references,
        the solution is to compile it in this order: pdflatex -> bibtex -> pdflatex -> pdflatex
        :return: None
        """
        pdflatex_cmd = " ".join(
            [self.pdflatex_cmd, '-no-shell-escape', '-interaction=nonstopmode',
             str(self.main_tex_file.absolute()),
             self.pdflatex_extra_cmds if self.pdflatex_extra_cmds is not None else ''])
        bibtex_cmd = " ".join([self.bibtex_cmd, self.main_tex_file.stem])
        run_process(pdflatex_cmd, self.main_tex_file.parent.absolute(), verbose=self.verbose)
        run_process(bibtex_cmd, self.main_tex_file.parent.absolute(), verbose=self.verbose)
        run_process(pdflatex_cmd, self.main_tex_file.parent.absolute(), verbose=self.verbose)
        run_process(pdflatex_cmd, self.main_tex_file.parent.absolute(), verbose=self.verbose)

        self.log.info(f"[green]:white_heavy_check_mark-text:Project compiled successfully[/]",
                      extra={"markup": True})

    def gs(self):
        """
        Unfortunately, the pdfx package does not generate a pdf that complies with the standard (or at
        least veraPDF says so).
        One of the issues is that it cannot fix transparency of the included graphics.
        This method runs ghost script to hopefully fix the remaining errors
        more info: https://www.ghostscript.com/doc/current/Use.htm#Help_command
        :return: None
        """
        compiled_pdf = self.main_tex_file.parent / self.compiled_pdf_filename
        output_document = self.output_dir / self.output_filename

        gs_cmd = " ".join(
            [str(self.gs_cmd),
             f"-dPDFA={self.conformance_level_version}", "-dBATCH", "-dNOPAUSE",
             "-sProcessColorModel=DeviceRGB", "-dOverprint=/disable",
             "-sColorConversionStrategy=RGB", "-sDEVICE=pdfwrite", "-dPDFACompatibilityPolicy=1",
             f"-sOutputFile={output_document.absolute()}", f"{self.resources.absolute() / 'lib_PDFA_def.ps'}",
             str(compiled_pdf.absolute())])
        run_process(gs_cmd, verbose=self.verbose, cwd='.')

        self.log.info(f"[green]:white_heavy_check_mark-text:The new pdf file has been generated successfully[/]",
                      extra={"markup": True})

    def fix_metadata(self):
        """
        Runs exiftool to copy metadata to the generated ghostscript file
        The problem with ghostscript again is that it does not care about metadata, and it wipes everything,
        so we need to fix this as well.
        credits: https://github.com/op3/latex-pdfa-howto
        :return: None
        """
        compiled_pdf = self.main_tex_file.parent / self.compiled_pdf_filename
        output_document = self.output_dir / self.output_filename

        exiftool_cmd = " ".join(
            [str(self.exiftool_cmd), "-TagsFromFile", f"{compiled_pdf}",
             '"-all:all>all:all"', '"-xmp-dc:all>xmp-dc:all"', '"-pdf:subject>pdf:subject"', '-overwrite_original',
             f"{output_document}"])
        run_process(exiftool_cmd, verbose=self.verbose, cwd='.')

        self.log.info(f"[green]:white_heavy_check_mark-text:Metadata fixed successfully[/]",
                      extra={"markup": True})

    def linearize_pdf(self):
        """
        runs qpdf to linearize the pdf.
        You can read more on the github link bellow.
        credits: https://github.com/op3/latex-pdfa-howto
        :return: None
        """
        output_document = self.output_dir / self.output_filename
        qpdf_cmd = " ".join(
            [str(self.qpdf_cmd), '--linearize', '--newline-before-endstream', '--replace-input', f"{output_document}"])

        run_process(qpdf_cmd, verbose=self.verbose, cwd='.')

        self.log.info(f"[green]:white_heavy_check_mark-text:PDF linearized successfully[/]",
                      extra={"markup": True})

    def check_executable(self, executable, name=None):
        """
        Check if the executable command exists before running the script
        :param executable: executable command or path
        :return: None
        """
        if isinstance(executable, Path):
            if not executable.is_file():
                self.log.error(
                    f"[red]{name} (path: [underline]{executable}[/]) does not exist! Please provide a valid {name} path",
                    extra={'markup': True})
                sys.exit(1)
        elif not executable_exists(executable):
            self.log.error(
                f"[red]`{executable}` does not exist in PATH, please ensure that {name} exists on your variable PATH or "
                f"run the script with [underline]--help[/] to get more details[/]", extra={'markup': True})
            sys.exit(1)
        else:
            # console.print(f"[green]:white_heavy_check_mark-text:{executable} [OK][/]")
            pass

    def check_executables(self):
        """
        It will go through the commands and check them one by one before running the program
        :return: None
        """
        # pdflatex command
        self.check_executable(self.pdflatex_cmd, name='pdflatex')
        # bibtex
        self.check_executable(self.bibtex_cmd, name='bibtex')
        # latexmk
        # if self.clean:
        #     self.check_executable(self.latexmk_cmd, name='latexmk')
        # Ghostscript
        self.check_executable(self.gs_cmd, name='ghostscript')
        # exiftool
        self.check_executable(self.exiftool_cmd, name='exiftool')
        # qpdf
        self.check_executable(self.qpdf_cmd, name='qpdf')
        # veraPDF
        if self.verify:
            self.check_executable(self.verapdf_cmd, name='veraPDF')

        self.log.info(f"[green]:white_heavy_check_mark-text:Requirements [OK][/]", extra={'markup': True})

    def verify_compliance(self, document=None):
        """
        runs verapdf to verify the compliance status of the pdf
        more info: https://verapdf.org/
        :return: boolean
        """
        if document:
            output_document = Path(document)
        else:
            output_document = self.output_dir / self.output_filename

        verapdf_cmd = " ".join(
            [str(self.verapdf_cmd.absolute()), f"{output_document.absolute()}",
             f"-f {self.conformance_level_version}{self.conformance_level}"])
        report = run_process(verapdf_cmd, verbose=False, cwd='.')
        tree = ET.ElementTree(ET.fromstring(report))
        summary = tree.find('.//validationReport')
        isCompliant = summary.get('isCompliant')
        statement = summary.get('statement')
        profile_name = summary.get('profileName')
        details = summary.find('.//details')
        failedChecks = details.get('failedChecks')
        passed_checks = details.get('passedChecks')

        result = f"[cian]veraPDF verification results:\n[yellow]Profile: {profile_name}[/][/]" \
                 f"\n\t[green]Number of Passed checks: {passed_checks}[/]" \
                 f"\n\t[red]Number of Failed checks: {failedChecks}[/]"

        if isCompliant == 'true':
            result += f"\n[green on white underline]:white_heavy_check_mark-text:{statement} ({profile_name})[/]"
        else:
            result += f"\n[red on white underline]:x-text:{statement} ({profile_name})[/]"

        self.log.info(result, extra={"markup": True})

        return isCompliant == 'true'

    def clean_files(self):
        """
        clean pdflatex output files
        :return: None
        """
        try:
            aux_files_ext = ['.aux', '.bbl', '.blg', '.toc', '.out', '.log']
            directory = self.main_tex_file.parent
            for file in directory.iterdir():
                if file.suffix in aux_files_ext:
                    os.remove(file.absolute())
            compiled_document = directory / self.compiled_pdf_filename
            os.remove(compiled_document.absolute())
            self.log.info(f"[green]:white_heavy_check_mark-text:Temporary files removed successfully[/]",
                          extra={"markup": True})
        except Exception as e:
            self.log.error(f"[red]Cleaning temporary files fails with error {str(e)}\nYou can always remove them "
                           f"manually[/]", extra={"markup": True})

    def run(self):
        """
        A simple method to run the process in order
        :return: None
        """
        # intro banner
        console.print(Panel(__header__))

        # checking requirements before starting the execution
        self.setup()

        if not self.ignore_metadata:
            self.add_metadata()
        with console.status("Patching the LaTex file ... [Please do not abort the script]\n",
                            spinner=self.console_spinner):
            self.patch_latex()

        with console.status("Compiling the Latex project ...\n", spinner=self.console_spinner):
            self.generate_pdf()

        with console.status("Fixing remaining compliance errors using GhostScript...\n",
                            spinner=self.console_spinner):
            self.gs()

        with console.status("Fixing metadata  ...\n", spinner=self.console_spinner):
            self.fix_metadata()

        with console.status("Linearizing the PDF file  ...\n", spinner=self.console_spinner):
            self.linearize_pdf()

        if self.clean:
            with console.status("Cleaning temporary files ...\n", spinner=self.console_spinner):
                self.clean_files()

        if self.verify:
            with console.status("Verifying the PDF file  ...\n", spinner=self.console_spinner):
                self.verify_compliance()

        console.rule('*** Notes ***')
        self.log.info(
            f"The generated PDF file is at: [blue underline]{(self.output_dir / self.output_filename).absolute()}",
            extra={'markup': True})
        self.log.info(f"Verify that the PDF is working fine, including the outlines and the references",
                      extra={'markup': True})
        self.log.info(
            f"If something went wrong to your LaTex main file, a backup is made on the project "
            f"folder with extension `.backup`",
            extra={'markup': True})
        self.log.info(
            f"Verify that the metadata are correct (You can check them inside the `properties` tab "
            f"of your favorite PDF reader)",
            extra={'markup': True})
        self.log.info(
            f"[yellow]The script did its best to generate a PDF/A complaint file. "
            f"Please use veraPDF-GUI to re-verify or to get more information if the generated PDF is still "
            f"containing some failed checks",
            extra={'markup': True})


def main():
    parser = argparse.ArgumentParser(description="", allow_abbrev=True)
    # Positional args
    parser.add_argument('tex_file', type=str, help="The main tex file of your LaTex project")

    # Optional args
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    parser.add_argument('-cl', '--conformance-level', default='b',
                        help="The PDF/A standard conformance level (`a`, `b`, or `u`), default to `b`")
    parser.add_argument('-clv', '--conformance-level-version', type=int, default=1,
                        help="The PDF/A standard conformance level version (`1`, `2`, or `3`), default to `1`")
    parser.add_argument('-o', '--output-dir', default=None,
                        help='The directory where the generated PDF will be stored, default to the project directory')
    parser.add_argument('-of', '--output-filename', default=None,
                        help='The filename of the generated PDF, default to the main LaTex filename with the suffix '
                             'PDFA-`cl`clv` (for ex: thesis-PDFA-1b.pdf')
    parser.add_argument('-i', '--ignore-metadata', action='store_true',
                        help='Ignore adding the metadata file to the project folder in case it is already done '
                             'manually, default to false')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help="show all under the hood commands and their output")
    parser.add_argument('-nc', '--no-clean', action='store_true',
                        help="Keep the temporary files generated from the compilation")
    parser.add_argument('-ve', '--verify', action='store_true',
                        help='Verify the generated PDF using veraPDF (veraPDF path must be provided in this case)')
    parser.add_argument('--pdflatex-path', default=None,
                        help='pdflatex executable path, if it is not specified, '
                             'the script will search on your environment variable PATH')
    parser.add_argument('--pdflatex_extra_cmds', default=None,
                        help='Add any extra commands to pdflatex (use quotation marks)')
    parser.add_argument('--bibtex-path', default=None,
                        help='bibtex executable path, if it is not specified, '
                             'the script will search on your environment variable PATH')
    # parser.add_argument('--latexmk-path', default=None,
    #                     help='latexmk executable path, if it is not specified, '
    #                          'the script will search on your environment variable PATH')
    parser.add_argument('--gs-path', default=None,
                        help='ghostscript executable path, if it is not specified, '
                             'the script will consider the one inside the binaries folder')
    parser.add_argument('--verapdf-path', default=None,
                        help='veraPDF executable path, if it is not specified, '
                             'the script will consider the one inside the binaries folder')

    args = parser.parse_args()

    latex2pdfa = Latex2pdfa(main_tex_file=args.tex_file,
                               conformance_level=args.conformance_level,
                               conformance_level_version=args.conformance_level_version,
                               output_dir=args.output_dir,
                               output_filename=args.output_filename,
                               ignore_metadata=args.ignore_metadata,
                               verbose=args.verbose,
                               clean=not args.no_clean,
                               verify=args.verify,
                               pdflatex_path=args.pdflatex_path,
                               bibtex_path=args.bibtex_path,
                               gs_path=args.gs_path,
                               verapdf_path=args.verapdf_path
                               )
    latex2pdfa.run()


if __name__ == '__main__':
    main()
