import os
import sys
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
        self.resize = kwargs.get("resize", 1.0)
        self.filename = filename
        self.index = index
        self.codes_detected = codes_detected
        self.detected = detected
        self.dpi = kwargs.get("dpi", 400)
        self.ppm = self.dpi / 25.4
        self.thresholds = kwargs.get("thresholds", [50, 55, 60, 65, 70, 75, 80])
        self.matrix = pymupdf.Matrix(self.dpi / 72, self.dpi / 72)
        self.show_patches = kwargs.get("show_patches", False)
        self.generated = generated

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
            h, w = image.shape[0], image.shape[1]

            nw = image[0:500, 0:500]
            ne = image[0:500, w - 500:w]
            sw = image[h - 500:h, 0:500]
            se = image[h - 500:h, w - 500:w]

            nw = threshold(nw, th)
            ne = threshold(ne, th)
            sw = threshold(sw, th)
            se = threshold(se, th)

            cv2.imwrite("nw.png", nw)
            cv2.imwrite("sw.png", sw)
            cv2.imwrite("ne.png", ne)
            cv2.imwrite("se.png", se)


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

        # Get the page if we got it
        page = codes.get_page()
        exam = codes.get_exam_id()

        # Clear the codes because the
        # page may have been rotated
        codes.clear()

        for th in self.thresholds:
            th_image = threshold(image, th)
            patches = get_patches(th_image, self.ppm, 8)

            for x, y, w, h in patches:
                patch = image[y:y + h, x:x + w]

                if self.show_patches:
                    cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 1)

                for text, cx, cy, cw, ch in get_codes(patch):
                    codes.append(Code(text, x + cx, y + cy, cw, ch, page))

        generated_page_codeset = PageCodeSet(self.generated.filter(page=page, exam=exam))
        if codes.get_p() is not None and codes.get_q() is not None:
            p11 = codes.get_p().get_pos()
            p12 = codes.get_q().get_pos()
            p21 = generated_page_codeset.get_p().get_pos()
            p22 = generated_page_codeset.get_q().get_pos()
            _, _, T = compute_similarity_transform(p11, p12, p21, p22)
        elif codes.get_p() is not None:
            x1, y1 = codes.get_p().get_pos()
            x2, y2 = generated_page_codeset.get_p().get_pos()
            T = (x2 - x1, y2 - y1)
        elif codes.get_q() is not None:
            x1, y1 = codes.get_q().get_pos()
            x2, y2 = generated_page_codeset.get_q().get_pos()
            T = (x2 - x1, y2 - y1)
        else:
            T = (0, 0)


        for code in codes.codes:
            x, y = code.get_pos()
            w, h = 120, 120
            print(x, y, w, h)
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 5)

        for code in generated_page_codeset.codes:
            x, y = code.get_pos()
            w, h = 120, 120
            x = x- int(T[0])
            y = y- int(T[1])

            cv2.rectangle(image, (x, y), (x + w, y + h), (255, 0, 0), 5)

        if self.resize != 1.0:
            image = cv2.resize(image, (int(image.shape[1] * self.resize), int(image.shape[0] * self.resize)),
                              interpolation=cv2.INTER_AREA)

        if codes.get_page() is not None:
            cv2.imwrite("page-{}-{}-{:03d}.jpg".format(codes.get_date(), codes.get_exam_id(), codes.get_page()), image)
        elif codes.get_exam_id():
            cv2.imwrite("unknown_page-{}-{}-{:03d}.jpg".format(codes.get_date(), codes.get_exam_id(), 0), image)

        for code in codes.codes:
            self.detected.append(code)

        #print("Page", self.index, "processed.")

        return codes

if __name__ == '__main__':
    ppm = 400 / 25.4
    all_codes = CodeSet()
    with open("generated.txt", "rb") as f:
        lines = f.readlines()
        for line in lines:
            data, x, y, w, h, pag, pdf_pag = line.decode().strip().split(",")
            x = int(int(x) / 65535 * 0.351459804 * ppm)
            y = int(297 * ppm - int(int(y) / 65535 * 0.351459804 * ppm))  # 297???
            code = Code(data, int(x), int(y), 50, 50)
            code.set_page(int(pag))
            all_codes.append(code)

    pool = Pool(processes=4)

    with Manager() as manager:
        detected = manager.list()

        document = pymupdf.open("test.pdf")

        processes = []
        for i in range(len(document)):
            process = PageProcessor("test.pdf", i, all_codes, detected)
            processes.append(process)
            process.start()
            print("Started process", i)
            while len([p for p in processes if p.is_alive()]) >= 4:
                time.sleep(1)

        for process in processes:
            process.join()

        print(detected)
