import os

import pandas
from PyQt5.QtCore import Qt, QObject, pyqtSignal
from PyQt5.QtGui import QPen
from PyQt5.QtWidgets import QMainWindow, QHBoxLayout, QWidget, QTreeWidget, QTreeWidgetItem, QSplitter, QGraphicsRectItem, QTabWidget
from swikv4.widgets.swik_basic_widget import SwikBasicWidget
import sys
from PyQt5.QtWidgets import QApplication

from code import Code
from code_set import CodeSet
from common import check_workspace, get_workspace_paths, Questions
from draggable_list import DraggableList


class Mark(QGraphicsRectItem):
    class Signal(QObject):
        double_click = pyqtSignal(object)

    def __init__(self, code):
        super().__init__()
        self.signal = Mark.Signal()
        self.code = code
        self.setRect(code.x, code.y, code.w, code.h)
        if code.marked:
            self.setPen(QPen(Qt.red, 2))
        else:
            self.setPen(QPen(Qt.transparent, 2))

    def mouseDoubleClickEvent(self, event):
        self.signal.double_click.emit(self.code)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.current_exam = None
        self.detected = CodeSet()
        self.rubrics = []
        self.questions = None

        (self.dir_workspace,
         self.dir_data,
         self.dir_scanned, _,
         self.dir_xls,
         self.dir_publish) = get_workspace_paths(os.getcwd())

        self.central_widget = QWidget()
        self.main_layout = QHBoxLayout()
        self.central_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.central_widget)
        self.pdf_tree = QTreeWidget()
        self.pdf_tree.setColumnCount(4)
        self.swik = SwikBasicWidget()
        self.splitter = QSplitter()
        self.main_layout.addWidget(self.splitter)

        self.rubrics_tabs = QTabWidget()

        self.splitter.addWidget(self.pdf_tree)
        self.splitter.addWidget(self.swik)
        self.splitter.addWidget(self.rubrics_tabs)

        self.setWindowTitle("QR Grader")

        self.load_detected()
        self.load_questions()
        self.load_schemas()

        self.populate_pdf_tree()

        self.pdf_tree.currentItemChanged.connect(self.pdf_tree_selection_changed)
        self.show()

    def load_detected(self):
        self.detected.load(self.dir_data + "detected.csv")


    def load_questions(self):
        self.questions = Questions(self.dir_xls)
        if not self.questions.load():
            print("ERROR: questions file nos present")
            sys.exit(1)


    def load_schemas(self):
        r1 = DraggableList(0, "rubric1.scm")
        r1.score_changed.connect(self.rubric_score_changed)
        r2 = DraggableList(0, "rubric2.scm")
        r2.score_changed.connect(self.rubric_score_changed)
        self.rubrics_tabs.addTab(r1, "Rubric 1")
        self.rubrics_tabs.addTab(r2, "Rubric 2")
        self.rubrics.extend([r1, r2])

    def rubric_score_changed(self, rubric, exam_id):
        rubric.compute_score(exam_id)


    def pdf_tree_selection_changed(self, current, previous):
        self.current_exam = int(current.text(0))
        filename = self.dir_publish + current.text(0) + ".pdf"
        self.swik.open(filename)
        self.process_exam()

        current = int(current.text(0)) if current is not None else None
        previous = int(previous.text(0)) if previous is not None else None

        for rubric in self.rubrics:
            rubric.exam_changed(current, previous)

    def populate_pdf_tree(self):
        files = os.listdir(self.dir_publish)
        files = sorted([f.replace(".pdf","") for f in files if f.endswith(".pdf") and f.replace(".pdf","").isdigit()])

        for f in files:
            exam_id = int(f)%1000
            score = self.get_quiz_score(exam_id)
            item = QTreeWidgetItem([f, str(score)])
            self.pdf_tree.addTopLevelItem(item)

    def process_exam(self):
        marks = [x for x in self.swik.view.items() if isinstance(x, Mark)]

        while len(marks) > 0:
            mark = marks.pop()
            self.swik.view.scene().removeItem(mark)

        marks = {}
        for index in range(self.swik.renderer.get_document_length()):
            exam_id = self.current_exam % 1000
            page_codes = self.detected.select(exam=exam_id, pdf_page=index+1)
            type_a = page_codes.select(type=Code.TYPE_A)
            for code in type_a:
                r = Mark(code)
                r.signal.double_click.connect(self.code_clicked)
                r.setParentItem(self.swik.view.get_page(index))
                marks[code] = r
                if code.marked:
                    if self.questions.get_value(code.question, code.answer)>0:
                        r.setPen(QPen(Qt.green, 2))
                    else:
                        r.setPen(QPen(Qt.red, 2))

            type_n = page_codes.select(type=Code.TYPE_N)
            for code in type_n:
                r = Mark(code)
                r.signal.double_click.connect(self.code_clicked)
                r.setParentItem(self.swik.view.get_page(index))
                if code.marked:
                    r.setPen(QPen(Qt.blue, 2))

        yellow = self.get_multiple_marks(exam_id)
        for answer in yellow:
            marks[answer].setPen(QPen(Qt.yellow, 2))

    def update_all_quiz_scores(self):
        for index in range(self.pdf_tree.topLevelItemCount()):
            item = self.pdf_tree.topLevelItem(index)
            exam_id = int(item.text(0)) % 1000
            score = self.get_quiz_score(exam_id)
            item.setText(1, str(score))

    def get_quiz_score(self, exam_id):
        score = 0
        exam_codes = self.detected.select(exam=exam_id, type=Code.TYPE_A)
        for code in exam_codes:
            if code.marked:
                score += self.questions.get_value(code.question, code.answer)
        return score

    def get_multiple_marks(self, exam_id):
        yellow = []
        for index in range(self.swik.renderer.get_document_length()):
            type_a = self.detected.select(exam=exam_id, pdf_page=index+1, type=Code.TYPE_A)
            for question in type_a.get_questions():
                answers = type_a.select(question=question)
                marked = sum([1 for x in answers if x.marked])
                if marked > 1:
                    for answer in answers:
                        if answer.marked:
                            yellow.append(answer)
        return yellow

    def code_clicked(self, code):
        code.marked = not code.marked
        self.process_exam()
        self.update_all_quiz_scores()


if __name__ == "__main__":

    app = QApplication(sys.argv)

    if not check_workspace():
        print("ERROR: qrgrader must be run from the workspace root")
        sys.exit(1)

    main = MainWindow()
    sys.exit(app.exec_())