
"""
A helper file used to create, manage, and update PyQt5 widgets.
"""

__author__    = 'Jacob Bumgarner <jrbumgarner@mix.wvu.edu>'
__license__   = 'GPLv3 - GNU General Pulic License v3 (see LICENSE)'
__copyright__ = 'Copyright 2022 by Jacob Bumgarner'
__webpage__   = 'https://jacobbumgarner.github.io/VesselVio/'
__download__  = 'https://jacobbumgarner.github.io/VesselVio/Downloads'


from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import (QWidget, QPushButton, QSpinBox, QDoubleSpinBox, 
                             QHBoxLayout, QVBoxLayout, QToolButton, QLineEdit, 
                             QComboBox, QStyledItemDelegate, QCheckBox, 
                             QFormLayout, QFrame, QRadioButton, QButtonGroup, 
                             QScrollArea, QStackedWidget)

from library import helpers 

###############
### Widgets ###
###############

def new_radio(title, connect=None):
    radio = QRadioButton(title)
    if connect:
        radio.toggled.connect(connect)
    return radio

def new_checkbox(title, connect=None):
    checkbox = QCheckBox(title)
    if connect:
        checkbox.stateChanged.connect(connect)
    return checkbox

def new_spinbox(min=0, max=100, default=None, alignment='Left', step=None, decimals=None, suffix=None, width=None, connect=None):
    spinbox = QSpinBox()
    spinbox.setMinimum(min)
    spinbox.setMaximum(max)
    
    spinbox.setAlignment(find_alignment(alignment))
    
    if step:
        spinbox.setSingleStep(step)
    if default:
        spinbox.setValue(default)
    if suffix:
        spinbox.setSuffix(suffix)
    if width:
        spinbox.setFixedWidth(width)  
    if connect:
        spinbox.editingFinished.connect(connect)
    
    return spinbox


def new_doublespin(min, max, start=0, width=None, alignment='Left', suffix=None, decimals=1, connect=None, ):
    doublespin = QDoubleSpinBox()
    doublespin.setMinimum(min)
    doublespin.setMaximum(max)
    if start:
        doublespin.setValue(start)
        
    doublespin.setAlignment(find_alignment(alignment))
    
    if width:
        doublespin.setFixedWidth(width)
    if suffix:
        doublespin.setSuffix(suffix)
        
    if connect:
        doublespin.editingFinished.connect(connect)
        
    doublespin.setDecimals(decimals)
    
    
    return doublespin

def new_button(name, connect_to, width=None):
    button = QPushButton(name)
    
    if connect_to:
        button.clicked.connect(connect_to)
    
    if width:
        button.setFixedWidth(width)
    else:
        button.setFixedWidth(100)
    
    return button

def new_help_button(connection):
    button = QPushButton("?")
    button.clicked.connect(connection)
    button.setFixedWidth(35)
    # button.setStyleSheet("""QPushButton{
    #                         font-size: 15px;
    #                         font-weight: bold;
    #                         color: gray;
    #                         background-color: rgb(57,57,57);
    #                         border: 2px solid gray;
    #                         border-radius: 0.5em;
    #                         }
                            
    #                         QPushButton:pressed{
    #                         background-color: rgb(100,100,100);
    #                         }
    #                         """)
    return button

def button_defaulting(button, default):
    button.setDefault(default)
    button.setAutoDefault(default)
    return

def new_combo(items:list, size=None, alignment='Left', connect=None):
    combo = QComboBox()
    alignment = find_alignment(alignment)
    for item in items:
        combo.addItem(item)

    if not size:
        combo.setFixedWidth(100)
    else:
        combo.setFixedWidth(size)
        
    if connect:
        combo.currentIndexChanged.connect(connect)
    
    return combo

def new_widget(fixed_width=None, fixed_height=None, min_width=None, min_height=None, color=None):
    widget = QWidget()
    if fixed_width or fixed_height:
        if fixed_width:
            widget.setFixedWidth(fixed_width)
        if fixed_height:
            widget.setFixedHeight(fixed_height)
    
    elif min_height or min_width:
        if min_height:
            widget.setMinimumHeight(min_height)
        if min_width:
            widget.setMinimumWidth(min_width)
            
    if color:
        helpers.update_widget_color(widget, color)
            
    return widget

def new_line_edit(default_text=None, alignment=None, width=None, locked=False):
    line_edit = QLineEdit(default_text)
    line_edit.setAlignment(find_alignment(alignment))
    
    if width:
        line_edit.setFixedWidth(width)
    
    if locked:
        line_edit.setReadOnly(True)

    return line_edit

def new_line(orient='H', size=None):
    line = QFrame()
    if orient == 'H':
        shape = QFrame.HLine
    else:
        shape = QFrame.VLine
    if size:
        line.setFixedWidth(size)
    line.setFrameShape(shape)
    
    line.setFrameShadow(QFrame.Sunken)
    
    return line

"""Thanks to /u/eyllanesc on StackExchange for the original code base of this box.
https://stackoverflow.com/questions/52615115/how-to-create-collapsible-box-in-pyqt"""
class CollapsibleBox(QWidget):
    def __init__(self, title="", message="", parent=None):
        super(CollapsibleBox, self).__init__(parent)
        # self.toggle_header = QLabel(title)
        self.toggle_header = QPushButton(title)
        self.toggle_header.setToolTip(message)
        self.toggle_header.setStyleSheet("border:0px; font-weight:bold;")
        self.toggle_header.clicked.connect(self.button_press)
        
        self.toggle_button = QToolButton(checkable=True, checked=False)
        self.toggle_button.setStyleSheet("QToolButton { border: none;}")
        self.toggle_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toggle_button.setArrowType(Qt.RightArrow)
        self.toggle_button.setIconSize(QSize(5, 5))
        self.toggle_button.toggled.connect(self.on_pressed)

        self.content_area = QWidget()
        self.content_area.setVisible(False)

        dropdown = QWidget()
        dropdownlayout = QHBoxLayout(dropdown)
        dropdownlayout.setSpacing(0)
        dropdownlayout.setContentsMargins(0,0,0,0)
        dropdownlayout.addWidget(self.toggle_button, alignment=Qt.AlignLeft)
        dropdownlayout.addWidget(self.toggle_header, alignment=Qt.AlignLeft)
        dropdownlayout.addStretch(0)
        
        lay = QVBoxLayout(self)
        lay.setSpacing(2)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(dropdown)
        lay.addWidget(self.content_area)

    def on_pressed(self):
        checked = self.toggle_button.isChecked()
        self.toggle_button.setArrowType(Qt.DownArrow if not checked else Qt.RightArrow)
        self.content_area.setVisible(not checked)
        return
        
    def button_press(self):
        checked = self.toggle_button.isChecked()
        self.toggle_button.setChecked(not checked)
        return
        
    def lock(self, state):
        self.toggle_button.setDisabled(state)
        self.toggle_header.setDisabled(state)
        if state:
            self.toggle_button.setChecked(state)
            
    def setContentLayout(self, layout):
        self.content_area.setLayout(layout)

###############################
### Signals and Connections ###
###############################
def signal_block(block, items):
    for item in items:
        item.blockSignals(block)
    return

def button_grouping(buttons):
    group = QButtonGroup()
    for button in buttons:
        group.addButton(button)
        
    group.setExclusive(True)
    return group



###############
### Layouts ###
###############
def new_stacked(widgets):
    stacked = QStackedWidget()
    for widget in widgets:
        stacked.addWidget(widget)
    return stacked

def add_form_rows(form, rows:list):
    for row in rows:
        if type(row) == list:
            form.addRow(row[0], row[1])
        else:
            form.addRow(row)
    
def add_widgets(parent, widgets:list, alignment=None):
    alignment = find_alignment(alignment)
    for widget in widgets:
        if isinstance(widget, int):
            if widget == 0:
                parent.addStretch(0)
            else:
                parent.addSpacing(widget)
                
        elif isinstance(widget, list): # Deprecated
            if type(widget[1]) == str:
                alignment = find_alignment(widget[1])
                parent.addWidget(widget[0], alignment=alignment)
            else:
                parent.addWidget(widget[0], widget[1])
            
        elif type(widget) == QHBoxLayout or type(widget) == QVBoxLayout or type(widget) == QFormLayout:
            parent.addLayout(widget)
        else:
            parent.addWidget(widget, alignment=alignment)
    return

def new_form_layout(parent=None, alignment=None, hspacing=None, vspacing=None, wrap=False):
    formlayout = QFormLayout(parent)
    if alignment:
        formlayout.setFormAlignment(find_alignment(alignment))
        
    if vspacing is not None:
        formlayout.setVerticalSpacing(vspacing)
    if hspacing is not None:
        formlayout.setHorizontalSpacing(hspacing)
        
    if wrap:
        formlayout.setRowWrapPolicy(QFormLayout.WrapLongRows)
        
    return formlayout

def new_layout(parent=None, orient='H', no_spacing=False, spacing=None, margins=None):
    if orient == 'H':
        layout = QHBoxLayout(parent)
    elif orient == 'V':
        layout = QVBoxLayout(parent)
    
    if no_spacing:
        eliminate_spacing(layout)
    else:    
        if spacing is not None:
            set_spacing(layout, spacing)
        if margins is not None:
            if type(margins) == int:
                margins = [margins] * 4
            # Left, top, right, bottom
            set_margins(layout, margins)
        
    return layout

def new_scroll(parent, vertical=True, horizontal=False):
    scroll = QScrollArea()
    scroll.setWidget(parent)
    scroll.setWidgetResizable(True)
    scroll.setAlignment(Qt.AlignCenter)
    
    if not vertical:
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    if not horizontal:
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    
    return scroll

# Layout processing
def eliminate_spacing(layout):
    layout.setSpacing(0)
    layout.setContentsMargins(0,0,0,0)

def set_spacing(layout, spacing):
    layout.setSpacing(spacing)
    
def set_margins(layout, m):
    layout.setContentsMargins(m[0], m[1], m[2], m[3])

def find_alignment(alignment):
    if alignment == 'Right':
        alignment = Qt.AlignRight
    elif alignment == 'Left':
        alignment = Qt.AlignLeft
    elif alignment == 'Center':
        alignment = Qt.AlignCenter
    elif alignment == 'VCenter':
        alignment = Qt.AlignVCenter
    else:
        alignment = Qt.Alignment()

    return alignment

class AlignLeftDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super(AlignLeftDelegate, self).initStyleOption(option, index)
        option.displayAlignment = Qt.AlignLeft | Qt.AlignVCenter
        
class AlignCenterDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super(AlignCenterDelegate, self).initStyleOption(option, index)
        option.displayAlignment = Qt.AlignCenter | Qt.AlignVCenter
