import argparse
import os
import sys
import time
from multiprocessing import Manager, Pool, Process

import cv2
import pymupdf
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QGraphicsRectItem

from code import Code
from code_set import CodeSet, PageCodeSet
from common import check_workspace, get_workspace_paths, get_temp_paths
from page_processor import PageProcessor
from utils import Questions, Generated

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Patching and detection')

    parser.add_argument('-B', '--begin', type=int, help='First page to process', default=0)
    parser.add_argument('-E', '--end', type=int, help='Last page to process', default=None)
    parser.add_argument('-R', '--ratio', type=int, help='Resize image to save space', default=0.25)
    parser.add_argument('-p', '--process', help='Process pages in scanned folder', action="store_true")
    parser.add_argument('-d', '--dpi', help='Dot per inch', type=int, default=400)


    args = vars(parser.parse_args())

    if not check_workspace():
        print("ERROR: qrscanner must be run from a workspace directory")
        sys.exit(1)

    dir_workspace, dir_data, dir_scanned, _, dir_xls, dir_publish = get_workspace_paths(os.getcwd())
    dir_pool, dir_images = get_temp_paths(os.getcwd())

    if args.get("process", False):

        os.makedirs(dir_images, exist_ok=True)

        ppm = args.get("dpi") / 25.4

        generated = Generated(ppm)
        if not generated.load(dir_data + "generated.csv"):
            print("ERROR: generated.csv not found")
            sys.exit(1)

        with Manager() as manager:


            processes = []
            detected = manager.list()

            files = [x for x in os.listdir(dir_scanned) if x.endswith(".pdf")]
            for filename in files:

                document = pymupdf.open(dir_scanned + filename)
                last_page = args.get("end") if args.get("end") is not None else len(document)
                document.close()

                for i in range(args.get("begin"), last_page):

                    # We send the filename and open the document in the process for three reasons:
                    # 1. Sending the page object is not possible because it is not pickable
                    # 2. Rendering the page image in parallel make the whole process much faster
                    # 3. For some reason sending the image to the process creates memory overflow

                    process = PageProcessor(dir_scanned + filename, i, generated, detected, dir_images=dir_images, resize=args.get("ratio"))
                    processes.append(process)
                    process.start()

                    while len([p for p in processes if p.is_alive()]) >= 4:
                        time.sleep(0.25)

            for process in processes:
                process.join()

            codes = CodeSet()
            codes.extend(detected)
            codes.save(dir_data + "detected.csv")



    codes = CodeSet()
    if not codes.load(dir_data + "detected.csv"):
        print("ERROR: detected.csv not found")
        sys.exit(1)

    exams = codes.get_exams()
    date = codes.get_date()

    print("Creating NIA xls file")
    with open(dir_xls + "nia.csv", "w") as f:
        f.write("Exam\tNIA\n")
        for exam in exams:
            nia = {0: 'Y', 1: 'Y', 2: 'Y', 3: 'Y', 4: 'Y', 5: 'Y'}
            for row in range(6):
                for number in range(10):
                    result = codes.first(exam=exam, type=Code.TYPE_N, number=row*10 + number)
                    if result is None or result.marked:
                        nia[row] = number if nia[row] == 'Y' else 'X'
            nia = "".join([str(x) for x in nia.values()])

            f.write("{}\t{}\n".format(date*1000 + exam, nia))

    print("Creating RAW xls file")
    with open(dir_xls + "raw.csv", "w") as f:
        for exam in exams:
            line = f"{date},{exam}"
            for question in codes.get_questions():
                for answer in codes.get_answers():
                    result = codes.first(exam=exam, type=Code.TYPE_A, question=question, answer=answer)
                    line += ",1" if result is None or result.marked else ",0"

            f.write(line + "\n")

    print("Reconstructing exams")

    images = os.listdir(dir_images)
    for exam in exams:
        filename = dir_publish + "{}{:03d}.pdf".format(date, exam)
        pdf_file = pymupdf.open()
        exam_images = sorted([x for x in images if x.startswith("page-{}-{}-".format(date, exam))])
        for image in exam_images:
            page = pdf_file.new_page() # noqa
            page.insert_image(pymupdf.Rect(0, 0, 595.28, 842), filename=dir_images + os.sep + image)

        pdf_file.save(filename)

    print("Annotating exams")

    questions = Questions(dir_xls)
    if not questions.load():
        print("ERROR: questions.csv not found")
        sys.exit(1)

    for exam in exams:
        filename = dir_publish + "{}{:03d}.pdf".format(date, exam)
        pdf_file = pymupdf.open(filename)
        for page in pdf_file:

            this_page = codes.select(type=Code.TYPE_A, exam=exam, page=page.number+1)
            for code in this_page:
                if code.marked:
                    x, y = code.get_pos()
                    w, h = code.get_size()
                    r = pymupdf.Rect(x, y, x+w, y+h)
                    annot = page.add_rect_annot(r)
                    annot.set_border(width=2)
                    if questions.get_value(code.question, code.answer) > 0:
                        annot.set_colors(stroke=(0,1,0))
                    else:
                        annot.set_colors(stroke=(1,0,0))
                    annot.update()
        pdf_file.save(filename.replace(".pdf", "-annotated.pdf"))

    print("All done :)")
















