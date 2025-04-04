import os

import pandas
from qrgrading.common import Nia, get_workspace_paths, get_date, StudentsData, Questions


class Raw:
    def __init__(self, filename):
        self.filename = filename
        self.raw = None

    def load(self):
        if os.path.exists(self.filename):
            self.raw = pandas.read_csv(self.filename, sep='\t', header=None)
            return True
        return False

    def get_row(self, exam_id):
        if self.raw is None:
            return None
        by_exam = self.raw[self.raw[1] == exam_id]
        if by_exam.empty:
            return None
        return by_exam.iloc[0, :].tolist()

    def get_exams(self):
        if self.raw is None:
            return None
        return self.raw.iloc[:, 1].tolist()


def main():
    (dir_workspace,
     dir_data,
     dir_scanned, _,
     dir_xls,
     dir_publish, _) = get_workspace_paths(os.getcwd())

    date = get_date()

    nia = Nia(dir_xls + os.sep + str(date) + "_nia.csv")
    nia.load()

    students_data = StudentsData(dir_xls + os.sep + "DATA.csv")
    students_data.load()

    questions = Questions(dir_xls + os.sep + str(date) + "_questions.csv")
    questions.load()

    raw = Raw(dir_xls + os.sep + str(date) + "_raw.csv")
    raw.load()

    fields = ["EXAM", "ID"]

    fields = fields + ["NIA", "NAM", "CQ"]

    for f in fields:
        print(f"{f}\t", end="")

    column = chr(ord("A") + len(fields))

    for i in questions.get_questions():
        kind = questions.get_type(i)
        if kind == "Q":
            for j in range(4):
                if j == 0:
                    brief = questions.get_text(i)
                    print(f"{brief}\t", end="")
                elif j == 3:
                    begin_column = chr(ord(column) - 3)
                    print(f"=sum({begin_column}6:{column})/count({begin_column}6:{column})\t", end="")
                else:
                    print(f"  \t", end="")
                column = chr(ord(column) + 1)
        else:
            print(f"{i}\t")

    for f in fields:
        print(f"{f}\t", end="")

    for i in questions.get_questions():
        kind = questions.get_type(i)
        if kind == "Q":
            for j in range(4):
                print(f"{i}\t", end="")
        else:
            print(f"{i}\t")

    for f in fields:
        print(f"{f}\t", end="")

    for i in questions.get_questions():
        kind = questions.get_type(i)
        if kind == "Q":
            for j in range(4):
                print(f"{chr(65 + j)}\t", end="")
        else:
            print(f"O\t")
    for f in fields:
        print(f"{f}\t", end="")
    for i in questions.get_questions():
        kind = questions.get_type(i)
        if kind == "Q":
            for j in range(4):
                print(f"{questions.get_value(i, j + 1)}\t", end="")
        else:
            print(f"O\t")

    for f in fields:
        print(f"{f}\t", end="")

    column = chr(ord("A") + len(fields))

    for i in questions.get_questions():
        kind = questions.get_type(i)
        if kind == "Q":
            for j in range(4):
                print(f"=sum({column}6:{column})/count({column}6:{column})\t", end="")
                column = chr(ord(column) + 1)
        else:
            print(f"O\t")

    line = 4

    for i in raw.get_exams():
        row = raw.get_row(i)
        print(f"{row.pop(0)}\t{row.pop(0)}\t", end="")

        for f in fields[2:]:
            if f == "CQ":
                column = chr(ord("A") + len(fields))

                print(f"=sumproduct({column}4:4,{column}{line}:{line})\t", end="")
            else:

                print(f"   \t", end="")

        for elem in row:
            print(f"{elem}\t", end="")
        print()
        line += 1


if __name__ == "__main__":
    main()
