import sys, platform
import datetime
from os import path, environ, getcwd, mkdir

from PyQt5.QtGui import QFont, QPalette
from PyQt5.QtCore import Qt, QSize, pyqtSlot
from PyQt5.QtWidgets import (QApplication,
                            QWidget, QLabel, QSpacerItem, QPushButton, QMessageBox, QScrollArea, QButtonGroup,
                            QCheckBox, QDoubleSpinBox, QGroupBox, QFrame, QComboBox, QSpinBox, QRadioButton,
                            QListWidget, QListWidgetItem, QStackedWidget, QSlider,
                            QInputDialog, QLineEdit, QFileDialog,
                            QDialog, QColorDialog, QSplitter,
                            QGridLayout, QHBoxLayout, QVBoxLayout,
                            QMainWindow, QProgressBar)


from Library.helpers import eliminate_spacing, get_dir, get_cwd

from Library.UI.stylesheets import buttonstyle, MenuSheet, FilesSheet, StatusSheet

class LeftMenu(QFrame):
    def __init__(self):
        super().__init__()

        self.setFixedWidth(96)
        self.setStyleSheet("background: rgb(32, 34, 37)")
        self.leftmenulayout = QVBoxLayout(self)
        self.leftmenulayout.setSpacing(0)
        self.leftmenulayout.setContentsMargins(0,0,0,0)
        self.qList = QListWidget()
        self.leftmenulayout.addWidget(self.qList)
        self.leftmenulayout.addSpacing(10)
        # self.leftmenulayout.addStretch(0)
        
        # Add our info tag to the bottom.
        self.initinfo(self.leftmenulayout)

        self.leftmenulayout.addSpacing(20)       
                
        # Format house-keeping.
        self.qList.setStyleSheet(MenuSheet)
        self.qList.setFrameShape(QListWidget.NoFrame)
        self.qList.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.qList.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.qList.setWordWrap(True)
        
        # Add menu items to our list.
        menu_items = ['Analyze', 'Visualize', 'Sequence Converter']
        for item in menu_items:
            item = QListWidgetItem(
                str(item), self.qList)
            item.setSizeHint(QSize(1, 70))
            item.setTextAlignment(Qt.AlignCenter)
                
        # self.maingrid.addWidget(self.leftmenu)
        
    def initinfo(self, layout):
        tab = QWidget()
        infoTab = QHBoxLayout(tab)
        eliminate_spacing(infoTab)
        tab.setStyleSheet("background: rgb(32, 34, 37)")
        infoTab.setContentsMargins(0,0,0,0)
        infoTab.addSpacing(10)
        infoTabLabel = QLabel(cc)
        infoTabLabel.setStyleSheet("color: white; font-weight: bold;")
        infoTab.addWidget(infoTabLabel)
        infoTab.addSpacing(10)
        
        infoTabQ = QPushButton("?")
        infoTabQ.clicked.connect(self.infoclick)
        infoTab.addWidget(infoTabQ)
        infoTabQ.setStyleSheet("""  
                                QPushButton{
                                font-size: 15px;
                                font-weight: bold;
                                color: white;
                                border: 2px solid white;
                                border-radius: 0.5em;
                                }
                                
                                QPushButton:pressed{
                                background-color: rgb(100,100,100);
                                }
                                """)
        infoTab.addSpacing(10)
        
        layout.addWidget(tab)
        
    def infoclick(self):
        message = """<center><b><u>About VesselVio:</b></u></center><br>
                    This program is compatible with 2D and 3D datasets that have been pre-binarized and segmented.<br><br> 
                    VesselVio was developed by Jacob Bumgarner in Randy Nelson's lab at West Virginia University.<br><br>
                    This software is <a href='https://github.com/JacobBumgarner/VesselVio'>open-source</a> under GNU GPLv3.<br><br>
                    Please contact Jacob with any suggestions or questions:<br>
                    <center> <a href='mailto:jrbumgarner@mix.wvu.edu'>jrbumgarner@mix.wvu.edu</a>"""
        msgBox = QMessageBox()

        msgBox.setText(message)
        msgBox.exec_()
        
        
now = datetime.datetime.now()
year = str(now.year)

cc = "©" + " " + year