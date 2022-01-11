
"""
The main entry point to build the GUI of the application.
Copyright © 2021, Jacob Bumgarner
"""

__author__    = 'Jacob Bumgarner <jrbumgarner@mix.wvu.edu>'
__license__   = 'GPLv3 - GNU General Pulic License v3 (see LICENSE)'
__copyright__ = 'Copyright © 2021 by Jacob Bumgarner'
__webpage__   = 'https://jacobbumgarner.github.io/VesselVio/'
__download__  = 'https://jacobbumgarner.github.io/VesselVio/Downloads'


import sys

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (QApplication, QStackedWidget,
                            QMainWindow, QStatusBar, QMessageBox)
from multiprocessing import freeze_support

from pyvistaqt import QtInteractor
import pyvista as pv

# Import UIs
from Library.UI import QtObjects as QtO
from Library.UI import LeftMenu as lm
from Library.UI import Analysis_Page as p1
from Library.UI import Visualization_Page as p2
from Library.UI import Annotation_Page as p3
from Library.UI import UpdateAlert
from Library import QtThreading as QtTh
from Library import Image_Processing as ImProc


######
version = "V 1.1.0"
######
     

# Main window for the application.
class mainWindow(QMainWindow):
    def __init__(self):
        super().__init__()        
        ## Setup the main window.
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.setVisible(False)
                
        self.plotter = QtInteractor()
        light = pv.Light(light_type='headlight', intensity=0.1)
        self.plotter.add_light(light)
        
        # Name & Color.
        self.setWindowTitle('VesselVio')
        self.centralWidget = QtO.new_widget()
        self.setCentralWidget(self.centralWidget)        
        self.centralLayout = QtO.new_layout(self.centralWidget, no_spacing=True)
        
        # Setup the individual pages of the application.
        self.qStack = QStackedWidget()

        self.leftMenu = lm.LeftMenu(version)
        
        self.page1 = p1.AnalysisPage()
        self.page2 = p2.VisualizationPage(self.statusBar, self.plotter, self)
        self.page3 = p3.AnnotationPage()
        
        self.pageStack = QtO.new_stacked([self.page1,
                                          self.page2, self.page3])
        
        # Connect sour left menu to our pages.
        self.leftMenu.pageTabs.currentRowChanged.connect(
            self.pageStack.setCurrentIndex)
        self.leftMenu.pageTabs.setCurrentRow(0)        
        
        # Add pages to the app
        QtO.add_widgets(self.centralLayout, [self.leftMenu, self.pageStack])
        
        # Make sure we delete the labeled_cache_volume if it exists
        ImProc.clear_labeled_cache()
        
        # Run our tiny file to prep our numba jit compilers.
        QtTh.prepare_compilers()
        
        # Check for updates
        UpdateAlert.local_version = version[2:]
        QTimer.singleShot(500, UpdateAlert.version_check)
        return
    
    # Close all associated widgets if the main thread is ended.s
    def closeEvent(self, event):
        try:
            self.page1.a_thread.stop()
            self.page2.v_thread.close()
        except:
            pass
        event.accept()

     
if __name__ == '__main__':
    freeze_support()
    app = QApplication(sys.argv)  
    main_app = mainWindow()
    main_app.show()
    sys.exit(app.exec_()) 
