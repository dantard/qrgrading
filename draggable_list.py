#!/usr/bin/env python
import csv
import os

import yaml
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDrag, QPixmap, QPainter
from PyQt5.QtWidgets import (QListWidget,
                             QAbstractItemView, QListWidgetItem, QMenu, QMessageBox,
                             QInputDialog, QColorDialog)

from button_edit_dialog import ButtonEditDialog
from buttons import StepButton


class DraggableList(QListWidget):
    score_changed = pyqtSignal(object)
    goto_next = pyqtSignal()

    def __init__(self, exam_date, schema_filename):
        super().__init__()

        self.config = {}
        self.scores = {}
        self.schema_dictionary = {}
        self.schema_filename = schema_filename
        name = self.schema_filename.split(".")[0]
        self.scores_filename = name + ".yaml"
        self.table_name = str(exam_date) + "_" + name
        self.current_exam_id = None
        self.modified = False

        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setMinimumWidth(115)

        #self.schemaChanged.connect(self.save_schema) # type: ignore
        self.customContextMenuRequested.connect(self.button_list_right_click)
        self.populate()
        self.load_scores()

    def load_scores(self):
        if os.path.exists(self.scores_filename):
            with open(self.scores_filename) as file:
                self.scores = yaml.safe_load(file)

    def exam_changed(self, exam_id, prev_exam_id):
        if prev_exam_id is not None:
            self.store(prev_exam_id)
        self.save_scores()

        self.retrieve(exam_id)


    def get_page(self):
        return self.config.get("page", 1) - 1

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Down:
            self.goto_next.emit()
            print("Key Down")
        else:
            super().keyPressEvent(e)

    def populate(self):
        if os.path.exists(self.schema_filename):
            # Load schema
            with open(self.schema_filename, newline='') as csvfile:
                content = yaml.full_load(csvfile)

                self.config = content.get("config", {})
                self.schema_dictionary = content.get("buttons", {})

                # Create lateral panel and buttons
                for button_name in self.schema_dictionary:
                    button_config = self.schema_dictionary[button_name]

                    if button_config.get("type") == 'button':
                        button = StepButton(button_name, **button_config)
                    else:
                        button = None

                    if button is not None:
                        # Create Item in ListWidget
                        item = QListWidgetItem()
                        self.addItem(item)
                        self.setItemWidget(item, button)
                        item.setSizeHint(button.sizeHint())

    def save_schema(self):
        buttons =  {}
        for b in self.filter_buttons(StepButton):  # type: Score
            buttons[b.get_name()] = b.get_config()

        with open(self.schema_filename, "w") as f:
            schema = {"buttons": buttons, "config": self.config}
            yaml.dump(schema, f, sort_keys=False)

    def add_button(self):

        button = self.get_dialog()

        if button is None:
            return

        # Create Item in ListWidget
        item = QListWidgetItem()
        self.addItem(item)

        self.setItemWidget(item, button)
        item.setSizeHint(button.sizeHint())
        self.save_schema()

    def get_dialog(self, button=None):

        dialog = ButtonEditDialog(self, button)

        if not dialog.exec():
            return None

        name, kind, config = dialog.get()

        self.schema_dictionary[name] = config

        if kind == 'button':
            button = StepButton(name, **config)
        else:
            button = None

        return button

    def edit_button(self, position):
        item = self.item(position)
        widget = self.itemWidget(item)
        prev_name = widget.get_name()

        button = self.get_dialog(widget)

        if button is None:
            return

        self.setItemWidget(item, button)

        # Rename the key in the dictionary
        if prev_name is not None:
            for exam_id in self.scores:
                if prev_name in self.scores[exam_id].keys():
                    self.scores[exam_id][button.get_name()] = self.scores[exam_id].pop(prev_name)

        self.save_schema()

    def button_list_right_click(self, pos):
        menu = QMenu()
        item = self.item(self.currentRow())
        widget = self.itemWidget(item)

        if isinstance(widget, StepButton):
            menu.addAction("Edit", lambda: self.edit_button(self.currentRow()))
            menu.addAction("Duplicate", lambda: self.duplicate_button(self.currentRow()))
            menu.addAction("Remove", lambda: self.delete_button(self.currentRow()))
            menu.addAction("Add Comment", lambda: self.add_comment(self.currentRow()))
            menu.addSeparator()
        # elif isinstance(widget, Shortcut):
        #     menu.addAction("Remove", lambda: self.remove_shortcut(self.currentRow()))
        #     menu.addAction("Change Color", lambda: self.set_shortcut_color(self.currentRow()))
        #     menu.addSeparator()
        #menu.addAction("Edit Config", self.edit_rubric_config)
        menu.addAction("Add Button", self.add_button)
        #menu.addAction("Add Shortcut", self.add_shortcut)

        menu.exec(self.mapToGlobal(pos))
        self.clearSelection()
        self.clearFocus()

    def save_scores(self):
        with open(self.scores_filename, 'w') as file:
            yaml.dump(self.scores, file)

    # def get_exam_score(self, exam_id):
    #     points, total, multiplier = 0, 0, 1
    #     this_exam_data = self.rubric_grades_data.get(int(exam_id), {})
    #     for b in self.buttons(Score):  # type: Score
    #         this_button_data = this_exam_data.get(b.get_name(), {})
    #         value = max(this_button_data.get("value", 0), 0)
    #         points = points + value / 100 * b.get_full_value()
    #         total = total + (b.get_full_value() * b.get_weight())
    #
    #     if total == 0:
    #         return 0
    #
    #     multiplier = 1
    #     for b in self.buttons(Multiplier):  # type: Multiplier
    #         this_button_data = this_exam_data.get(b.get_name(), {})
    #         value = this_button_data.get("value", -1)/100.0
    #         if value >= 0:
    #             multiplier = multiplier * value * b.get_full_value()
    #
    #     percent = min(points / total, 1)
    #     percent = percent * multiplier
    #
    #     for b in self.buttons(ScoreCutter):  # type: ScoreCutter
    #         this_button_data = this_exam_data.get(b.get_name(), {})
    #         cut = this_button_data.get("value", -1)/100.0
    #         if cut >= 0:
    #             cut = cut * b.get_full_value()
    #             percent = cut if percent > cut else percent
    #
    #     return percent * self.config.get("weight", 10)
    #
    #
    # def flush(self, xls_path):
    #     if self.modified:
    #         self.save_rubric_data_yaml()
    #         self.generate_rubric_data_csv(xls_path)
    #
    # def get_buttons_name(self):
    #     names = []
    #     for b in self.buttons(StepButton):
    #         names.append(b.get_name())
    #     return names
    #
    # def get_button_state(self, exam_id, name):
    #     element = self.rubric_grades_data.get(int(exam_id))
    #
    #     if element is not None:
    #         return element.get(name)
    #

    #
    #     # Load rubric data
    #     try:
    #         with open(self.rubric_grades_filename) as file:
    #             self.rubric_grades_data = yaml.full_load(file)
    #     except:
    #         print("No rubric data found")
    #
    # def shortcut_activated(self, buttons):
    #     for b in self.buttons(StepButton):  # type: StepButton
    #         b.button.setChecked(b.get_name() in buttons)
    #         b.clicked()
    #
    # def add_shortcut(self):
    #     text, ok = QInputDialog.getText(self, "Shortcut", "Name:")
    #     if ok:
    #
    #         buttons = []
    #         for b in self.buttons(StepButton):  # type: StepButton
    #             if b.button.isChecked():
    #                 buttons.append(b.get_name())
    #
    #         b2 = Shortcut(text, {"buttons": buttons, "color": "#FF0000", "type":"shortcut"})
    #         b2.shortcut_activated.connect(self.shortcut_activated) # type: ignore
    #         item = QListWidgetItem()
    #         self.addItem(item)
    #         self.setItemWidget(item, b2)
    #         item.setSizeHint(b2.sizeHint())
    #         item.setFlags(item.flags() & ~Qt.ItemIsDragEnabled)
    #         self.save_schema()
    #
    #
    #


        # if isinstance(button, StepButton):
        #     self.buttons_callback()

    #     self.save_schema()
    #
    # def set_current_exam_id(self, exam_id):
    #     self.current_exam_id = exam_id
    #
    # def get_current_exam_score(self):
    #     points, total = 0, 0
    #     print("----\n")
    #     for b in self.buttons(Score):  # type: Score
    #         print("Button: ", b.get_name(), b.get_value(), b.get_full_value(), b.get_weight())
    #         points = points + (b.get_value() if b.is_checked() else 0)
    #         total = total + (b.get_full_value() * b.get_weight())
    #
    #     print("total", total)
    #
    #     if total == 0:
    #         return 0
    #
    #     multiplier = 1
    #     for b in self.buttons(Multiplier):  # type: Multiplier
    #         multiplier = multiplier * (b.get_value() if b.is_checked() else 1)
    #
    #     percent = min(points / total, 1)
    #     percent = percent * multiplier
    #
    #     for b in self.buttons(ScoreCutter):  # type: ScoreCutter
    #         cut = b.get_value() if b.is_checked() else 1
    #         percent = cut if percent > cut else percent
    #
    #     return percent * self.config.get("weight", 10)
    #
    # def text_callback(self):
    #     self.modified = True
    #
    # def buttons_callback(self):
    #     self.modified = True
    #     # DISABLED 4 EXAM TODO: self.store(self.current_exam_id)
    #     self.score_changed.emit(self) # type: ignore
    #

    #
    # def delete_button(self, position):
    #     qm = QMessageBox()
    #     ret = qm.question(self, '', "Are you sure?", qm.Yes | qm.No)
    #
    #     if ret == qm.Yes:
    #         item = self.takeItem(position)
    #         del item
    #         self.save_schema()
    #
    # def add_comment(self, position):
    #     # help me get text comment with dialog
    #     item = self.item(position)
    #     widget = self.itemWidget(item)
    #     text, ok = QInputDialog.getText(self, 'Add Comment', 'Comment:', text=widget.get_comment())
    #     if ok:
    #         item = self.item(position)
    #         widget = self.itemWidget(item)
    #         widget.setToolTip(text)
    #         widget.set_comment(text)
    #
    # def duplicate_button(self, position):
    #     item = self.item(position)
    #     widget = self.itemWidget(item)
    #     name, ok = QInputDialog.getText(self, 'Duplicate', 'Name:', text=widget.get_name() + "_copy")
    #     if ok:
    #         b2 = widget.__class__(name, widget.get_schema(), percent=self.config.get("percent", 100))
    #
    #         item = QListWidgetItem()
    #         self.addItem(item)
    #         self.setItemWidget(item, b2)
    #         item.setSizeHint(b2.sizeHint())
    #         self.save_schema()
    #

    #
    #
    # def edit_rubric_config(self):
    #     dialog = RubricEditDialog(self.config)
    #     if dialog.exec():
    #         self.save_schema()
    #

    #
    # def set_shortcut_color(self, position):
    #     item = self.item(position)
    #     widget = self.itemWidget(item)
    #     color = QColorDialog.getColor()
    #     if color.isValid():
    #         widget.set_color(color.name())
    #         self.save_schema()
    #
    #
    # def remove_shortcut(self, position):
    #     self.takeItem(position)
    #     self.save_schema()
    #
    # def is_done(self, exam_id):
    #     done = False
    #     grades_for_this_exam = self.rubric_grades_data.get(exam_id)
    #     if grades_for_this_exam is None:
    #         return False
    #
    #     for b in self.buttons(StepButton):  # type: Score
    #         this_button = grades_for_this_exam.get(b.get_name(), {})
    #         value = this_button.get("value", -1)
    #         done = done or value != -1
    #     for b in self.buttons(Text):
    #         this_button = grades_for_this_exam.get(b.get_name(), {})
    #         value = this_button.get("text", "")
    #         done = done or value != ""
    #
    #     return done
    #
    def store(self, exam_id):
        if self.scores.get(exam_id) is None:
            self.scores[exam_id] = {}

        for b in self.filter_buttons():  # type: Score
            self.scores[exam_id][b.get_name()] = b.get_state()
            #b.clear_comment()


    def retrieve(self, exam_id):
        self.current_exam_id = exam_id
        rubric_data = self.scores.get(exam_id, {})
        if  rubric_data is not None:
            for b in self.filter_buttons():  # type: Score
                b.blockSignals(True)
                b.set_state(rubric_data.get(b.get_name(), {}))
                b.blockSignals(False)
    #
    #     self.modified = False
    #
    #
    # def save_rubric_data_yaml(self):
    #     with open(self.rubric_grades_filename, 'w') as file:
    #         yaml.dump(self.rubric_grades_data, file)
    #
    # def generate_rubric_data_csv(self, xls_path):
    #     with open(xls_path + self.table_name + ".csv", 'w') as file:
    #         writer = csv.writer(file)
    #         header = ["Exam #"]
    #         header.extend([b.get_name() + "'" for b in self.buttons()])
    #         writer.writerow(header)
    #
    #         scores = ["0"]
    #         for b in self.buttons():
    #             scores.append(b.get_full_value() if isinstance(b, StepButton) else "0")
    #         writer.writerow(scores)
    #
    #         # For each exam
    #         for exam_id in self.rubric_grades_data:
    #             # Prepare row to append data
    #             row = [exam_id]
    #
    #             # For each button
    #             for i in range(self.count()):
    #                 button_widget = self.itemWidget(self.item(i))
    #                 state_for_this_button_for_this_exam = self.rubric_grades_data[exam_id].get(button_widget.get_name(), {})
    #                 value = button_widget.get_xls_value(state_for_this_button_for_this_exam)
    #                 row.append(value)
    #             writer.writerow(row)

    def startDrag(self, ev):
        selected = self.selectedIndexes()[0].row()
        item = self.item(selected)
        widget = self.itemWidget(item)
        qd = QDrag(self)
        qd.setMimeData(self.model().mimeData(self.selectedIndexes()))
        pm = QPixmap(400, 20)
        pm.fill(Qt.transparent)
        qp = QPainter(pm)
        qp.drawText(10, 15, widget.get_name())
        qd.setPixmap(pm)
        qd.exec(ev, Qt.MoveAction)
        del qp

    schemaChanged = pyqtSignal()

    def dropEvent(self, event):
        super().dropEvent(event)
        self.schemaChanged.emit() # type: ignore

    def filter_buttons(self, kind=StepButton):
        buttons = []
        for i in range(self.count()):
            item = self.item(i)
            widget = self.itemWidget(item)
            if isinstance(widget, kind):
                buttons.append(widget)
        return buttons