from PyQt5 import QtWidgets
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (QLineEdit, QPushButton, QSpinBox, QDialog, QDialogButtonBox, QComboBox, QDoubleSpinBox)

from widget_utils import WidgetsRow, VBox


class ButtonEditDialog(QDialog):
    def __init__(self, draggable_list, button=None):
        super().__init__()

        schema = button.get_config() if button is not None else {}

        self.draggable_list = draggable_list
        self.setWindowTitle("Edit")

        dialog_ok_cancel_btn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(dialog_ok_cancel_btn)
        self.buttonBox.accepted.connect(self.accept) # type: ignore
        self.buttonBox.rejected.connect(self.reject) # type: ignore
        self.buttonBox.buttons()[0].setEnabled(False)

        self.layout = VBox()
        self.setLayout(self.layout)

        self.combo = QComboBox()
        self.combo.addItems(['button', 'multiplier', 'cutter', 'text', 'separator'])
        self.combo.setCurrentText(schema.get('type', 'button'))
        self.layout.addWidget(WidgetsRow("Type", self.combo))

        self.le = QLineEdit()
        self.le.textChanged.connect(lambda: self.buttonBox.buttons()[0].setEnabled(self.le.text() != "")) # type: ignore
        self.le.setText(button.get_name() if button is not None else "")
        self.layout.addWidget(WidgetsRow("Name", self.le))

        #self.value = QComboBox()
        self.value = QDoubleSpinBox()
        self.value.setDecimals(1)
        self.value.setMinimum(-20)
        self.value.setMaximum(20)
        self.value.setValue(float(schema.get('value', 1)))
        self.value.setSingleStep(0.5)

        #self.fill_cb(schema.get("type", 'button'), schema.get('value', 1))
        self.layout.addWidget(WidgetsRow("Value", self.value))

        self.steps = QSpinBox()
        self.steps.setMinimum(0)
        self.steps.setMaximum(10)
        self.steps.setValue(int(schema.get('steps', 0)))
        self.layout.addWidget(WidgetsRow("Steps", self.steps))
        #
        self.weight = QDoubleSpinBox()
        self.weight.setDecimals(1)
        self.weight.setMinimum(-20)
        self.weight.setMaximum(20)
        self.weight.setValue(float(schema.get('weight', 1)))
        self.weight.setSingleStep(0.5)
        self.layout.addWidget(WidgetsRow("Weight", self.weight))

        # Show the current color and a color picker button
        self.color = QColor(schema.get('color', "#D4D4D4"))
        self.colorButton = QPushButton('Choose color')
        self.colorButton.clicked.connect(self.pick_color) # type: ignore
        self.layout.addWidget(WidgetsRow('Color', self.colorButton))
        self.colorButton.setStyleSheet(f'background-color: {schema.get("color", "#D4D4D4")}')

        self.layout.addWidget(self.buttonBox)
        self.combo.currentTextChanged.connect(self.cb_changed)  # type: ignore

        self.enable_widgets()


    def cb_changed(self, text):
#        self.fill_cb(self.combo.currentText(), 1)
        self.enable_widgets()

    def enable_widgets(self):
        b = self.combo.currentText() in ['button']
        bm =  self.combo.currentText() in ['button', 'multiplier']
        bmc = self.combo.currentText() in ['button', 'multiplier', 'cutter']

        self.layout.widgets['Value'].setVisible(bmc)
        self.layout.widgets['Steps'].setVisible(bm)
        self.layout.widgets['Weight'].setVisible(b)
        self.layout.widgets['Color'].setVisible(bmc)

        self.adjustSize()


    def pick_color(self, button):
        color = QtWidgets.QColorDialog.getColor()
        if color.isValid():
            self.color = color
            self.colorButton.setStyleSheet(f'background-color: {color.name()}')

    def get_stylesheet(self):
        return f'background-color: {self.color.name()}'

    def get(self):
        res = {'type': self.combo.currentText()}
        if self.combo.currentText() in ['button', 'multiplier', 'cutter']:
            res['color'] = self.color.name()
        if self.combo.currentText() in ['multiplier', 'cutter']:
            res['value'] = float(self.value.value())
        if self.combo.currentText() in ['button', 'multiplier']:
            res['steps'] = self.steps.value()
        if self.combo.currentText() in ['button']:
            res['weight'] = float(self.weight.value())
            res['value'] = float(self.value.value())
            res['start_with'] = 77

        return self.le.text(), self.combo.currentText(), res