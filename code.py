class Code:
    TYPE_A = 0
    TYPE_P = 1
    TYPE_Q = 2
    TYPE_N = 3

    def __init__(self, data, x, y, w, h, page=None):
        self.data = data
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.exam = None
        self.page = page
        if self.data[0] == "P":
            self.date = int(self.data[1:7])
            self.exam = int(self.data[7:10])
            self.page = int(self.data[10:12])
            self.type = self.TYPE_P
        elif self.data[0] == "Q":
            self.date = int(self.data[1:7])
            self.exam = int(self.data[7:10])
            self.page = int(self.data[10:12])
            self.type = self.TYPE_Q
        elif self.data[0] == "N":
            self.date = int(self.data[1:7])
            self.exam = int(self.data[7:10])
            self.number = int(self.data[10:12])
            self.type = self.TYPE_N
        else:
            self.date = int(self.data[0:6])
            self.exam = int(self.data[6:9])
            self.question = int(self.data[9:11])
            self.answer = int(self.data[11])
            self.type = self.TYPE_A

    def set_page(self, page):
        self.page = page

    def get_exam_id(self):
        return self.exam

    def get_date(self):
        return self.date

    def get_page(self):
        return self.page

    def get_type(self):
        return self.type

    def get_data(self):
        return self.data

    def get_pos(self):
        return self.x, self.y


    def __repr__(self):
        if self.type == self.TYPE_A:
            return f"({self.data}, {self.exam}, {self.x}, {self.y}, {self.w}, {self.h}, Q:{self.question}, A:{self.answer})"
        elif self.type in [self.TYPE_P, self.TYPE_Q]:
            return f"({self.data}, {self.exam}, {self.x}, {self.y}, {self.w}, {self.h}, PAG:{self.page})"
        elif self.type == self.TYPE_N:
            return f"({self.data}, {self.exam}, {self.x}, {self.y}, {self.w}, {self.h}, NUM:{self.number})"