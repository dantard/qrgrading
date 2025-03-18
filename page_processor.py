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