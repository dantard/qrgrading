# QRGRADER

QRGrader is a simple python script that allows you to grade
multiple choice questions using QR codes. The script will generate a QR code for each question and the correct answer.
Students can scan the QR code to check their answers. The script will also generate a summary of the results for each
question.

The exam must the prepared in a latex file using the style document provided.

## Prerequisites (Linux)

- Python 3 installed
- texlive-full installed

To install texlive-full on Ubuntu, run the following command:

```bash
sudo apt-get install texlive-full
```

## Usage

All the script command must be executed inside the so-called qr workspace which is
a directory tree called `qrgrading-NNNNNNN` with the following structure:

```
qrgrading-250212
├── data
├── source
├── generated
├── scanned
├── results
    ├── xls
    ├── pdf
```

### Creating a new workspace

To create a new workspace, run the following command:

```bash
qrworkspace -d 250312
Workspace 'qrgrading-250312' created successfully.
```

Generally, the number is the date of the exam. If the scripts is called
without the `-d` option, the current date will be used.

### Preparing the exam

The following is preparing the exam. The source files must be in the `source` directory.

The exam has the following structure:

```latex
\documentclass[oneside,spanish]{article}
\usepackage[aztec, draft]{qrgrader} 
\qrgraderpagestyle{Subject name or exam title}

\begin{document}

\IDMatrix{0.6cm}{\uniqueid}{Student ID figure}

\begin{exam}[shuffle=all, style=matrix, showcorrect=no, encode=yes]

\question[score=0.5, penalty=0.125, brief=first]{1}
{Stem 1}
{Key}
{Distractor 1}
{Distractor 2}
{Distractor 3}

%%

\question[score=0.5, penalty=0.125, brief=second, style=horizontal]{2}
{Stem 2}
{Key}
{Distractor 1}
{Distractor 2}
{Distractor 3}

%%

\question[score=0.5, penalty=0.125, brief=third, style=list]{3}
{Stem 3}
{Key}
{Distractor 1}
{Distractor 2}
{Distractor 3}
\end{exam}
\end{document} 
```

The main file must be called `main.tex`.

### Generating the exams

To generate the exams run the following command:
``

```bash
qrgenerator -n 10
``` 

Where `-n` is the number N of exams to generate.
This will generate 10 exams in the `generated` directory. Both the order of the questions and the answers
are different for each exam. The file name will have the format DDDDDDNNN.pdf where DDDDDD is the date of the exam
and NNN is the number of the exam from 001 to NNN, in thi case 010.

### Grading the exams

Once the students have answered the exam, the exams must be scanned at 400 dpi.
The scanned files must be put afterwards in the `scanned` directory.
The grading is carried out with the following command:

```bash
qrscanner -se
```

This command will process the and generate a set of files in the `results` directory.
Specifically, the `results/pdf` directory will contain the recontructed pdf files named in the same
way as the generated files.

On the other hand, the `results/xls` directory will contain the results in a set of
csv file as follows:

- `raw.csv`: A file in which each row contains the exam number, and a set of `1 and `0` and values organized in group of
  4 that resent wether or not the student has marked a specific question
- `nia.csv`: A file in which each row contains the exam number and the student ID
- `questions.csv`: A file in which each row contains a information about the questions

These files opened with a spreadsheet program will allow to grade the exams.

### Graphical user interface

Sometimes students mark an answer, and later they want to modify that answer.
Since it is impossible to erase the QR code, in these cases they are instructed to mark  
chosen answer as well and write "NO" beside the answer they want to erase.
It will result in an answer with two marks that can be easily identified.
To facilitate the grading of these cases, it exists a graphical user interface that allows to
unmark the answer that has been marked by mistake.
To use the graphical user interface, run the following command from within the workspace directory

```bash
qrgrader
```

### CSV files format details

The `raw.csv` file has the following format:

```
DDDDDD, NNN, Q1A, Q1B, Q1C, Q1D, Q2A, Q2B, Q2C, Q2D, Q3A, Q3B, Q3C, Q3D
```

as for example:

```
250319,   1,   0,   0,   1,   0,   1,   0,   0,   0,   1,   0,   0,   0
```

Where `DDDDDD` is the date of the exam, `NNN` is the number of the exam, and
`Q1A` is the `A` option, Q1B is the `B` option, and so on. If the student has marked the option, the value is `1`,
otherwise `0`.

-----
The `nia.csv` file has the following format:

```
DDDDDDNNN   NIA
```

as for example:

```
250319001   123456
```

Where `DDDDDD` is the date of the exam, `NNN` is the number of the exam, and `NIA` is
the student ID. Notice that in this case the
-----

The `questions.csv` file has the following format:

```
N TYPE   SA   SB   SC   SD BRIEF
```

as for example:

``` 
1    Q  0.5 -0.1 -0.1 -0.1 for_loop
2    Q  0.5 -0.1 -0.1 -0.1 error_handling
3    Q  0.5 -0.1 -0.1 -0.1 sintax_error
```

Where `N` is the question number, `TYPE` is the question type, `SA`, `SB`, `SC`, and `SD` are the scores for each
option, and `BRIEF` is a brief description of the question that are all recovered automatically from
the latex file.
