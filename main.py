import argparse
import os
import time
from multiprocessing import Manager, Pool, Process

import cv2
import pymupdf

from code import Code
from code_set import CodeSet, PageCodeSet
from utils import pix2np, get_patches, threshold, get_codes, compute_similarity_transform


class PageProcessor(Process):

    def __init__(self, filename, index, generated, codes_detected, **kwargs):
        super().__init__()
        self.filename = filename
        self.index = index
        self.generated = generated
        self.detected = codes_detected

        self.dpi = kwargs.get("dpi", 400)
        self.thresholds = kwargs.get("thresholds", [50, 55, 60, 65, 70, 75, 80])
        self.matrix = pymupdf.Matrix(self.dpi / 72, self.dpi / 72)
        self.show_patches = kwargs.get("show_patches", False)
        self.resize = kwargs.get("resize", 1.0)
        self.dir_images = kwargs.get("dir_images", ".")

        self.ppm = self.dpi / 25.4

    def run(self):

        # Render the image
        doc = pymupdf.open(self.filename)
        page = doc[self.index]
        image = pix2np(page.get_pixmap(matrix=self.matrix))  # noqa
        doc.close()

        # Find page, orientation and rotate page
        rotation = None
        codes = PageCodeSet()

        for th in self.thresholds:
            ph, pw = image.shape[0], image.shape[1]

            nw = image[0:500, 0:500]
            ne = image[0:500, pw - 500:pw]
            sw = image[ph - 500:ph, 0:500]
            se = image[ph - 500:ph, pw - 500:pw]

            nw = threshold(nw, th)
            ne = threshold(ne, th)
            sw = threshold(sw, th)
            se = threshold(se, th)

            # cv2.imwrite("nw.png", nw)
            # cv2.imwrite("sw.png", sw)
            # cv2.imwrite("ne.png", ne)
            # cv2.imwrite("se.png", se)

            for text, cx, cy, cw, ch in get_codes(ne):
                if text.startswith("P"):
                    rotation = None
                elif text.startswith("Q"):
                    rotation = cv2.ROTATE_90_CLOCKWISE
                codes.append(Code(text, cx, cy, cw, ch))

            for text, cx, cy, cw, ch in get_codes(nw):
                if text.startswith("P"):
                    rotation = cv2.ROTATE_90_CLOCKWISE
                elif text.startswith("Q"):
                    rotation = cv2.ROTATE_90_COUNTERCLOCKWISE
                codes.append(Code(text, cx, cy, cw, ch))

            for text, cx, cy, cw, ch in get_codes(sw):
                if text.startswith("P"):
                    rotation = cv2.ROTATE_90_COUNTERCLOCKWISE
                elif text.startswith("Q"):
                    rotation = None
                codes.append(Code(text, cx, cy, cw, ch))

            for text, cx, cy, cw, ch in get_codes(se):
                if text.startswith("P"):
                    rotation = cv2.ROTATE_180
                elif text.startswith("Q"):
                    rotation = cv2.ROTATE_90_COUNTERCLOCKWISE
                codes.append(Code(text, cx, cy, cw, ch))

        if rotation is not None:
            image = cv2.rotate(image, rotation)

        # Get the page number if we got it
        page = codes.get_page() if codes.get_page() is not None else 0

        # Clear the codes because the
        # page may have been rotated
        codes.clear()

        # Process the page and extract the codes
        for th in self.thresholds:
            th_image = threshold(image, th)
            patches = get_patches(th_image, self.ppm, 8)

            for px, py, pw, ph in patches:
                patch = image[py:py + ph, px:px + pw]

                if self.show_patches:
                    cv2.rectangle(image, (px, py), (px + pw, py + ph), (0, 0, 255), 1)

                for text, cx, cy, cw, ch in get_codes(patch):
                    codes.append(Code(text, px + cx, py + cy, cw, ch, page, self.index))

        # Check if we already have the page number otherwise
        # try to get it from the generated codes
        # if page is None:
        #     page = 0
        #     for code in codes:
        #         if self.generated.get(code) is not None:
        #             page = self.generated.get(code).get_page()
        #             break
        #     for code in codes:
        #         code.set_page(page)

        if self.resize != 1.0:
            image = cv2.resize(image, (int(image.shape[1] * self.resize), int(image.shape[0] * self.resize)),
                               interpolation=cv2.INTER_AREA)

        if codes.get_page() is not None:
            cv2.imwrite(self.dir_images + os.sep + "page-{}-{}-{:03d}.jpg".format(codes.get_date(), codes.get_exam_id(), codes.get_page()), image)
        elif codes.get_exam_id():
            cv2.imwrite(self.dir_images + os.sep + "page-{}-{}-{:03d}.jpg".format(codes.get_date(), codes.get_exam_id(), 0), image)
        else:
            cv2.imwrite(self.dir_images + os.sep + "{}-{:03d}.jpg".format(self.filename, self.index), image)

        for c in codes.codes.values():
            self.detected.append(c)

        return codes


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
                process = PageProcessor(dir_scanned + "test.pdf", i, all_codes, detected, dir_images=dir_images, resize=args.get("ratio"))
                processes.append(process)
                process.start()
                print("Started process", i)
                while len([p for p in processes if p.is_alive()]) >= 4:
                    time.sleep(1)

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


















