import os

import pandas

from code import Code
from code_set import CodeSet


def get_workspace_paths(base):
    dir_workspace = base + os.sep
    dir_data = dir_workspace + "data" + os.sep
    dir_scanned = dir_workspace  + "scanned" + os.sep
    dir_generated = dir_workspace + "generated" + os.sep
    dir_xls = dir_workspace + "results" + os.sep + "xls" + os.sep
    dir_publish = dir_workspace + "results" + os.sep + "pdf" + os.sep
    return dir_workspace, dir_data, dir_scanned, dir_generated, dir_xls, dir_publish


def get_temp_paths(base):
    dir_pool = base + os.sep + "pool" + os.sep
    dir_images = dir_pool + os.sep + "images" + os.sep
    return dir_pool, dir_images

def check_workspace():
    current_dir = os.getcwd()
    dir_name = os.path.basename(current_dir)
    name = dir_name.split("-")
    if len(name) != 2 or name[0] != "qrgrading" or len(name[1]) != 8 or not name[1].isdigit():
        return False
    return True

class Questions:
    def __init__(self, dir_xls):
        self.dir_xls = dir_xls
        self.questions = None

    def load(self):
        if os.path.exists(self.dir_xls + "questions.csv"):
            self.questions = pandas.read_csv(self.dir_xls + "questions.csv", sep='\t', header=0)
            return True
        return False


    def get_value(self, question, answer):
        return self.questions.loc[question-1, chr(answer+64)]

    def get_type(self, question):
        return self.questions.loc[question-1, "TYPE"]


class Generated(CodeSet):

    def __init__(self, ppm):
        super().__init__()
        self.ppm = ppm


    def load(self, filename):
        if not os.path.exists(filename):
            return False

        with open(filename, "rb") as f:
            for line in f.readlines():
                data, x, y, w, h, pag, pdf_pag = line.decode().strip().split(",")
                x = int(int(x) / 65535 * 0.351459804 * self.ppm)
                y = int(297 * self.ppm - int(int(y) / 65535 * 0.351459804 * self.ppm))  # 297???
                self.append(Code(data, int(x), int(y), 120, 120, int(pag), int(pdf_pag)))
        return True