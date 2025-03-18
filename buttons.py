from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QCursor, QGuiApplication
from PyQt5.QtWidgets import QWidget, QPushButton, QHBoxLayout, QSpinBox, QLabel

class Button(QWidget):
    pass

class StepButton(Button):

    score_modified = pyqtSignal()

    def __init__(self, name, **kwargs):
        super(QWidget, self).__init__()

        self.config = {"weight": 1, "value": 1,
                       "steps": 0, "color": None,
                       "comment": "", "start_with": 100,
                       "click_next": False}

        self.config.update(kwargs)

        self.weight = self.config.get('weight', 1)
        self.value = self.config.get('value', 1)
        self.n_steps = self.config.get('steps', 0)
        color = self.config.get("color", None)

        self.name = name
        self.comment = None
        self.step = int(100 / self.n_steps) if self.n_steps > 0 else 100

        layout = QHBoxLayout()
        layout.setContentsMargins(15, 5, 15, 5)

        self.button = QPushButton(name)
        self.button.setMinimumWidth(10)
        self.button.setCheckable(True)
        if color is not None:
            self.button.setStyleSheet('background-color: {}'.format(color))
        self.button.clicked.connect(self.clicked)

        self.spinner = QSpinBox()
        self.spinner.setEnabled(False)
        self.spinner.lineEdit().setReadOnly(True)
        self.spinner.setMinimum(0)
        self.spinner.setSingleStep(self.step)
        self.spinner.setMaximum(100)
        self.spinner.setMaximumWidth(50)
        self.spinner.valueChanged.connect(self.score_modified.emit) # type: ignore

        layout.addWidget(self.button)
        self.comment_lbl = QLabel(self.button)
        self.comment_lbl.setGeometry(5, 5, 15, 15)
        self.comment_lbl.setText("*")
        self.comment_lbl.setStyleSheet('background-color: #00FFFF00;')
        self.comment_lbl.setMaximumWidth(10)
        self.comment_lbl.setVisible(False)

        self.set_comment(kwargs.get('comment', ""))
        self.start_with = kwargs.get('start_with', 100)

        if self.n_steps > 0:
            layout.addWidget(self.spinner)

        self.setLayout(layout)

    def get_config(self):
        return self.config

    def toggle_show_points(self):
        self.points_lb.setVisible(not self.points_lb.isVisible())

    def is_checked(self):
        return self.button.isChecked()

    def get_state(self):
        if self.is_checked():
            if self.n_steps == 0:
                value = 100
            else:
                value = self.spinner.value()
        else:
            value = -1

        return  {"value": value, "comment": self.comment}

    def get_xls_value(self):
        state = self.get_state()
        value = state.get("value")
        if value == -1:
            return " "
        else:
            return value/100

    def get_value(self):
        if self.is_checked():
            if self.n_steps == 0:
                return self.get_full_value()
            else:
                return float(self.spinner.value()/100.0)*self.get_full_value()
        else:
            return None

    def get_name(self):
        return self.name

    def clicked(self):
        self.spinner.blockSignals(True)
        if QGuiApplication.queryKeyboardModifiers() == Qt.ControlModifier:
            self.spinner.setValue(0)
        else:
            self.spinner.setValue(self.start_with if self.button.isChecked() else 0)
        self.spinner.setEnabled(self.button.isChecked())
        self.spinner.blockSignals(False)

        font = self.button.font()
        font.setBold(self.button.isChecked())
        self.button.setFont(font)

        self.score_modified.emit() # type: ignore

    def set_state(self, state):
        self.set_comment(state.get("comment", ""))
        value = state.get("value", 0)

        self.button.blockSignals(True)
        self.button.setChecked(value >= 0 if self.n_steps > 0 else value > 0)
        self.button.blockSignals(False)

        self.spinner.blockSignals(True)
        self.spinner.setMinimum(0)
        self.spinner.setValue(value if value > 0 else 0)
        self.spinner.setEnabled(self.button.isChecked())
        self.spinner.blockSignals(False)

        font = self.button.font()
        font.setBold(self.button.isChecked())
        self.button.setFont(font)

        self.score_modified.emit() # type: ignore

    def set_comment(self, text):
        self.comment_lbl.setVisible(text != "")
        self.setToolTip(text)
        self.comment = text

    def get_comment(self):
        return self.comment

    def clear_comment(self):
        self.set_comment("")

    def get_full_value(self):
        return self.value

    def click(self):
        self.button.click()

    def get_click_next(self):
        return self.click_next and self.button.isChecked()
