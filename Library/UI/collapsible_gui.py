"""


Thanks to /u/eyllanesc on StackExchange for the original code base of this box.
https://stackoverflow.com/questions/52615115/how-to-create-collapsible-box-in-pyqt
"""


from PyQt5.QtCore import Qt, pyqtSlot, QSize
from PyQt5.QtWidgets import QToolButton, QScrollArea, QVBoxLayout, QWidget, QLabel, QHBoxLayout

class CollapsibleBox(QWidget):
    def __init__(self, title="", message="", parent=None):
        super(CollapsibleBox, self).__init__(parent)
        self.toggle_header = QLabel(title)
        self.toggle_header.setToolTip(message)
        self.toggle_button = QToolButton(
             checkable=True, checked=False
        )
        self.toggle_button.setStyleSheet("QToolButton { border: none;}")
        self.toggle_button.setToolButtonStyle(
            Qt.ToolButtonTextBesideIcon
        )
        self.toggle_button.setArrowType(Qt.RightArrow)
        self.toggle_button.setIconSize(QSize(5, 5))
        self.toggle_button.toggled.connect(self.on_pressed)

        self.content_area = QWidget()
        self.content_area.setVisible(False)

        dropdown = QWidget()
        dropdownlayout = QHBoxLayout(dropdown)
        dropdownlayout.setSpacing(0)
        dropdownlayout.setContentsMargins(0,0,0,0)
        dropdownlayout.addWidget(self.toggle_button, alignment=Qt.AlignCenter)
        dropdownlayout.addWidget(self.toggle_header, alignment=Qt.AlignCenter)
        dropdownlayout.addStretch(0)
        
        lay = QVBoxLayout(self)
        lay.setSpacing(2)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(dropdown)
        lay.addWidget(self.content_area)


    @pyqtSlot()
    def on_pressed(self):
        checked = self.toggle_button.isChecked()
        self.toggle_button.setArrowType(
            Qt.DownArrow if not checked else Qt.RightArrow
        )
        self.content_area.setVisible(not checked)

    def setContentLayout(self, layout):
        self.content_area.setLayout(layout)
        
    def lock(self, state):
        self.toggle_button.setDisabled(state)
