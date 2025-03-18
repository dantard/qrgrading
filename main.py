import argparse
import os
import time
from multiprocessing import Manager, Pool, Process

import cv2
import pymupdf

from code import Code
from code_set import CodeSet, PageCodeSet
from page_processor import PageProcessor
from utils import pix2np, get_patches, threshold, get_codes, compute_similarity_transform





if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Patching and detection')

    parser.add_argument('-B', '--begin', type=int, help='First page to process', default=0)
    parser.add_argument('-E', '--end', type=int, help='Last page to process', default=None)
    parser.add_argument('-R', '--ratio', type=int, help='Resize image to save space', default=0.25)
    parser.add_argument('-p', '--process', type=int, help='Process pages in scanned folder')
    args = vars(parser.parse_args())

    dir_workspace = "workspace" + os.sep + os.sep
    dir_pool = "pool/" + os.sep
    dir_images = dir_pool + os.sep + "images" + os.sep
    dir_data = dir_workspace + os.sep + "data" + os.sep
    dir_scanned = dir_workspace + os.sep + "scanned" + os.sep
    dir_xls = dir_workspace + os.sep + "results" + os.sep + "xls" + os.sep
    dir_publish = dir_workspace + os.sep + "results" + os.sep + "pdf" + os.sep

    directories = [dir_workspace, dir_pool, dir_images, dir_data, dir_scanned, dir_xls, dir_publish]

    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    ppm = 400 / 25.4
    all_codes = CodeSet()
    with open(dir_data + "generated.txt", "rb") as f:
        lines = f.readlines()
        for line in lines:
            data, x, y, w, h, pag, pdf_pag = line.decode().strip().split(",")
            x = int(int(x) / 65535 * 0.351459804 * ppm)
            y = int(297 * ppm - int(int(y) / 65535 * 0.351459804 * ppm))  # 297???
            code = Code(data, int(x), int(y), 50, 50, pag, pdf_pag)
            code.set_page(int(pag))
            all_codes.append(code)

    pool = Pool(processes=4)

    if args.get("process", True) or True:

        with Manager() as manager:
            detected = manager.list()

            document = pymupdf.open(dir_scanned + "test.pdf")
            npages = len(document)
            document.close()

            last_page = args["end"] if args["end"] is not None else npages

            processes = []
            for i in range(args.get("begin"), last_page):

                # We send the filename and open the document in the process for three reasons:
                # 1. Sending the page object is not possible because it is not pickable
                # 2. Rendering the page image in parellel make the whole process much faster
                # 3. For some reason sending the image to the process creates memory overflow

                process = PageProcessor(dir_scanned + "test.pdf", i, all_codes, detected, dir_images=dir_images, resize=args.get("ratio"))
                processes.append(process)
                process.start()
                print("Started process", i)
                while len([p for p in processes if p.is_alive()]) >= 4:
                    time.sleep(0.25)

            for process in processes:
                process.join()

            codes = CodeSet()
            codes.extend(detected)
            codes.save(dir_data + "detected.txt")

    codes = CodeSet()
    codes.load(dir_data + "detected.txt")

    exams = codes.get_exams()
    date = codes.get_date()

    print("Create NIA xls file")
    with open(dir_xls + "nia.txt", "w") as f:
        f.write("Exam\tNIA\n")
        for exam in exams:
            nia = {0: 'Y', 1: 'Y', 2: 'Y', 3: 'Y', 4: 'Y', 5: 'Y'}
            for row in range(6):
                for number in range(10):
                    result = codes.select(exam=exam, type=Code.TYPE_N, number=row*10 + number)
                    if result.empty():
                        nia[row] = number if nia[row] == 'Y' else 'X'
            nia = "".join([str(x) for x in nia.values()])

            f.write("{}\t{}\n".format(date*1000 + exam, nia))

    print("Create exam xls file", exam)
    with open(dir_xls + "raw.txt", "w") as f:
        for exam in exams:
            line = f"{date},{exam}"
            for question in codes.get_questions():
                for answer in codes.get_answers():
                    result = codes.select(exam=exam, type=Code.TYPE_A, question=question, answer=answer)
                    line += ",1" if result.empty() else ",0"

            f.write(line + "\n")

    print("Reconstruct the exam")

    images = os.listdir(dir_images)
    for exam in exams:
        filename = dir_publish + "{}{:03d}.pdf".format(date, exam)
        pdf_file = pymupdf.open()
        exam_images = sorted([x for x in images if x.startswith("page-{}-{}-".format(date, exam))])
        for image in exam_images:
            page = pdf_file.new_page()
            page.insert_image(pymupdf.Rect(0, 0, 595.28, 842), filename=dir_images + os.sep + image)

        pdf_file.save(filename)


    print("Annotate exam")

    for exam in exams:
        filename = dir_publish + "{}{:03d}.pdf".format(date, exam)
        pdf_file = pymupdf.open(filename)
        for page in pdf_file:
            this_page = PageCodeSet(codes.select(exam=exam, page=page.number + 1))
            generated_page_codeset = PageCodeSet(all_codes.select(exam=exam, page=page.number + 1))

            # Compute the transformation
            if this_page.get_p() is not None and this_page.get_q() is not None:
                p11 = this_page.get_p().get_pos()
                p12 = this_page.get_q().get_pos()
                p21 = generated_page_codeset.get_p().get_pos()
                p22 = generated_page_codeset.get_q().get_pos()
                _, _, delta = compute_similarity_transform(p11, p12, p21, p22)
            elif this_page.get_p() is not None:
                x1, y1 = this_page.get_p().get_pos()
                x2, y2 = generated_page_codeset.get_p().get_pos()
                delta = (x2 - x1, y2 - y1)
            elif this_page.get_q() is not None:
                x1, y1 = this_page.get_q().get_pos()
                x2, y2 = generated_page_codeset.get_q().get_pos()
                delta = (x2 - x1, y2 - y1)
            else:
                delta = (0, 0)

            this_page = this_page.select(type=Code.TYPE_A)
            generated_page_codeset = generated_page_codeset.select(type=Code.TYPE_A)

            for code in generated_page_codeset:
                if codes.get(code) is None or args.get("annotate") == "all":
                    x, y = code.get_pos()
                    x = x - int(delta[0])
                    y = y - int(delta[1])
                    w, h = 120,120
                    x,y,w,h = x/5.55, y/5.55, w/5.55, h/5.55
                    r = pymupdf.Rect(x, y, x+w, y+h)
                    annot = page.add_rect_annot(r)
                    annot.set_border(width=2)
                    if code.answer == 1:
                        annot.set_colors(stroke=(0,1,0))
                    else:
                        annot.set_colors(stroke=(1,0,0))
                    annot.update()
        pdf_file.save(filename.replace(".pdf", "-annotated.pdf"))


















