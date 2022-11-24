# latex2pdfa
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

A command line utility to automate the process of compiling a LaTex project to a PDF complaint with the PDF/A standard.


## Setup 
_Assuming you are using a **Debian/Ubuntu** machine_:

+ Python3
  + Usually pre-installed
+ [TeX Live](https://www.tug.org/texlive/)
  ```bash 
    sudo apt install texlive-latex-base texlive-fonts-recommended texlive-latex-extra texlive-bibtex-extra
    ```
+ [ExifTool](https://exiftool.org/)
  ```bash
  sudo apt install exiftool
  ```
- [QPDF](https://qpdf.sourceforge.io/)
    ```bash
      sudo apt-get install qpdf
   ```
- [veraPDF](https://verapdf.org/) [Optional] (For validation)

## Installation
```bash

```
## Usage
Run the following in your terminal and follow the instructions:
```bash 
latex2pdfa path/to/your/main_tex_file.tex 
```
By default, the generated PDF will comply with the `1b` standard which most universities require.

You can specify an output filename with `--output-filename`, otherwise the generated PDF will have the same name of your
`main_tex_file` followed by `-PDFA-1b`. 

-----
You can get the exhaustive list of arguments by running:

```bash
latex2pdfa --help
```
```
usage: latex2pdfa.py [-h] [--version] [-cl CONFORMANCE_LEVEL] [-clv CONFORMANCE_LEVEL_VERSION] [-o OUTPUT_DIR] [-of OUTPUT_FILENAME] [-i]
                     [-v] [-nc] [-ve] [--pdflatex-path PDFLATEX_PATH] [--pdflatex_extra_cmds PDFLATEX_EXTRA_CMDS] [--bibtex-path BIBTEX_PATH]
                     [--gs-path GS_PATH] [--verapdf-path VERAPDF_PATH]
                     tex_file

positional arguments:
  tex_file              The main tex file of your LaTex project

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  -cl CONFORMANCE_LEVEL, --conformance-level CONFORMANCE_LEVEL
                        The PDF/A standard conformance level (`a`, `b`, or `u`), default to `b`
  -clv CONFORMANCE_LEVEL_VERSION, --conformance-level-version CONFORMANCE_LEVEL_VERSION
                        The PDF/A standard conformance level version (`1`, `2`, or `3`), default to `1`
  -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                        The directory where the generated PDF will be stored, default to the project directory
  -of OUTPUT_FILENAME, --output-filename OUTPUT_FILENAME
                        The filename of the generated PDF, default to the main LaTex filename with the suffix PDFA-`cl`clv` (for ex: thesis-
                        PDFA-1b.pdf
  -i, --ignore-metadata
                        Ignore adding the metadata file to the project folder in case it is already done manually, default to false
  -v, --verbose         show all under the hood commands and their output
  -nc, --no-clean       Keep the temporary files generated from the compilation
  -ve, --verify         Verify the generated PDF using veraPDF (veraPDF path must be provided in this case)
  --pdflatex-path PDFLATEX_PATH
                        pdflatex executable path, if it is not specified, the script will search on your environment variable PATH
  --pdflatex_extra_cmds PDFLATEX_EXTRA_CMDS
                        Add any extra commands to pdflatex (use quotation marks)
  --bibtex-path BIBTEX_PATH
                        bibtex executable path, if it is not specified, the script will search on your environment variable PATH
  --gs-path GS_PATH     ghostscript executable path, if it is not specified, the script will consider the one inside the binaries folder
  --verapdf-path VERAPDF_PATH
                        veraPDF executable path, if it is not specified, the script will consider the one inside the binaries folder

```

## Motivation
This is quoted from the [pdf2archive](https://github.com/matteosecli/pdf2archive) repository. 

_(I can't say it better 😂)_

<blockquote>
This script was born as a necessity, when I had to convert the LaTeX-produced PDF of my MSc Thesis into a PDF/A-1B.

Once upon a time, the delivery of the Thesis had to be done manually, by burning a CD-ROM with the Thesis PDF on it. I don't need to say that it was extremely old-fasioned and inefficient, as you had to deliver the CD-ROM to the secretariat in person. Finally, in 2015, my university decided to activate the online submission of the PDF: you just had to upload your PDF and you were done, completely hassle-free.

Then one year ago, some _enlightened mind_ in whoever knows what administrative office, decided that a regular PDF was not easy enough; so, the university began to require the much more _satanic_ PDF/A-1B. Of course, they had to provide a set of instructions for us mere mortal, so that we could produce valid PDF/A-1B files; and indeed they did, by uploading a [_fantastic document_](http://www.biblioteca.unitn.it/282/tesi-di-laurea). If you took the (click)bait and read the PDF (not PDF/A-1B, eh!) instructions at the previous linked page, you might have noticed the _absolute completeness_ of the information contained in it: there are instructions to transform a PDF into a PDF/A-1B by either using a Windows-only free program (yeah, I know) or an obsolete OpenOffice plugin that doesn't work anymore or _paid_, commercial programs that work at most only on Windows and MacOS. No free, cross-platform alternative because hey, _everyone_ loves Windows! Naturally, you can directly produce a PDF/A-1B version of your Thesis. The document lists some easy instructions to perform a direct export into a PDF/A-1B from either Microsoft Word (or Excel, because there are people who of course write their thesis in Excel) or OpenOffice. Because _everyone_ on Earth, especially people who do Physics or Maths, write their thesis in Microsoft Word... they look _sooo beautiful_, in particular when you have to put footnotes, citations, table of contents, when Word spreads the text in a page in a zebra-style, and when you write those amazing equations in Comic Sans that get rendered as 10 DPI jpeg's. "And people who use LaTeX"? "Latex? What latex? I don't do that kind of dirty sex stuff"! - would say the guy who wrote that document. 

So you could imagine me and my friends, on the last available day for the Thesis delivery, still struggling trying to figure out how to convert. There is a [nice site](https://docupub.com/pdfconvert/) that converts PDF's into PDF/A-1B files, but there are some points:
+ your Thesis gets filled with metadata from that site, which is not nice for an official document
+ the file size limit is 10 Mb, so if you do a more experimental Thesis which is full of images you're out
+ this solution depends on someone else resources; if the site goes down tomorrow, you're in deep s***
+ it only works online, no offline alternative if you're on the move
+ you have to send personal data to an unknown site
+ you don't know what operations are being performed on your file and your data on the other side of the line

By digging around on Google, you can find people saying that you can perform the conversion via Ghostscript by just turning on a couple of switches; unfortunately, this doesn't work (the online system, Esse3, keeps saying that the file is not valid) and the matter is slightly more complicated and poorly documented. The failure in producing a valid PDF/A-1B is connected to the complex set of requirements needed, especially font embedding, metadata and color space. This script is just a collection of all the things one should to in order to obtain (in most of the cases) a valid PDF/A-1B document [...]. 

</blockquote>

## Discussion
 
- The use of the `pdfx` package alone still produce validation errors!!
- The use of `Ghostscript` alone to convert the PDF to PDF/A is not always successful. Sometimes the old versions does not work. Sometimes, the recent versions does not have the same arguments because it is always evolving, and even if it works, you may find that the links are not working, or the table of contents does not exist, etc.
After a lot (I mean a lot) of trial and error, I found that the version `9.23` is giving the best results, I decided to include it with the project files.
- The script uses both to produce a high quality PDF/A directly from the LaTex source files.
- The script is only compatible with the `b` conformance level.
Unfortunately, there is noway to generate a fully compatible `PDF/A-a` from LaTex until now (as of my knowledge).
- More interesting information are available in the [FAQs](https://github.com/matteosecli/pdf2archive#faqs) section of [pdf2archive](https://github.com/matteosecli/pdf2archive).


## License

GPLv3 © [latex2pdfa](https://github.com/abdeladim-s/latex2pdfa). For more information see `LICENSE.md`.

