import sys, platform
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

import numpy as np
import matplotlib as mpl
import vtk
import pyvista as pv
from pyvistaqt import QtInteractor, BackgroundPlotter

from Library import Backend_Processing as bep
from Library.helpers import remove_legend, prep_scalars_update, get_rgb, eliminate_spacing, get_dir, get_cwd, load_results_dir

# Import our UIs
from Library.UI import LeftMenu as lm
from Library.UI import Page1 as p1
from Library.UI import Page2 as p2


# Get our working directory
wd = get_cwd()

# Build site for our application.
class mainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        ## Setup the main window.        
        # Name & Color.
        self.setWindowTitle('VesselVio')
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)        

        # Size and layout
        self.resize(750, 500)
        self.setMinimumWidth(750)
        self.maingrid = QHBoxLayout()
        self.maingrid.setSpacing(0)
        self.maingrid.setContentsMargins(0,0,0,0)
        self.centralWidget.setLayout(self.maingrid)
        
        # Setup the individual pages of the application.
        self.qStack = QStackedWidget()

        left_menu = lm.LeftMenu()
        self.page1 = p1.Page1()
        self.page2 = p2.Page2()
        
        self.maingrid.addWidget(left_menu)
        self.qStack.addWidget(self.page1)
        self.qStack.addWidget(self.page2)
        page3 = self.initPage3()
        self.maingrid.addWidget(self.qStack)
        
        # Connect our left menu to our pages.
        left_menu.qList.currentRowChanged.connect(
            self.qStack.setCurrentIndex)
        left_menu.qList.currentRowChanged.connect(self.update_dirs)
        left_menu.qList.setCurrentRow(0)        
        
        
        # Run our tiny file to prep our numba jit compilers.
        # bep.process_file('./Library/tiny.nii')
        
        # Present File
        self.show()
      
    def update_dirs(self):
        results_dir = load_results_dir()
        self.page1.results_path_location.setText(results_dir)
        
        
    # Page 3 Construction
    def initPage3(self):
        page3 = QWidget()
        page3layout = QHBoxLayout(page3)
        page3layout.setSpacing(0)
        page3layout.setContentsMargins(20,0,0,0)
        label = QLabel("Coming in future update.")
        page3layout.addWidget(label, alignment=Qt.AlignCenter)
        self.qStack.addWidget(page3)
     
    # Close all associated widgets if the main thread is ended.
    def closeEvent(self, event):
        self.page1.a_thread.stop()
        try:
            self.page2.v_thread.close()
        except:
            pass
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = mainWindow()
    sys.exit(app.exec_())