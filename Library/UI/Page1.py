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

from Library import Backend_Processing as bep
from Library.helpers import eliminate_spacing, get_dir, get_cwd, load_results_dir, set_results_dir

from Library.UI.stylesheets import buttonstyle, MenuSheet, FilesSheet, StatusSheet

wd = get_cwd()


class Page1(QWidget):
    def __init__(self):
        super().__init__()
        # Setup variables.
        self.files = []
        self.analysis_complete = False       
        
        # Connecting our analysis thread.
        self.a_thread = bep.AnalysisThread()
        
        page1layout = QHBoxLayout(self)
        page1layout.setSpacing(0)
        page1layout.setContentsMargins(0,20,20,20)
        
        p1left = QWidget()
        p1leftlayout = QVBoxLayout(p1left)
        eliminate_spacing(p1leftlayout)
        
        p1right = QWidget()
        p1rightlayout = QVBoxLayout(p1right)
        eliminate_spacing(p1rightlayout)
        
        p1righttop = QWidget()
        p1righttoplayout = QHBoxLayout(p1righttop)
        eliminate_spacing(p1righttoplayout)
        
        p1rightbottom = QWidget()
        p1rightbottomlayout = QHBoxLayout(p1rightbottom)
        p1rightbottomlayout.setContentsMargins(0,0,0,0)
        
        p1rightbottomleft = QWidget()
        p1rbllayout = QVBoxLayout(p1rightbottomleft)
        
        p1rightbottomright = QWidget()
        p1rbrlayout = QVBoxLayout(p1rightbottomright)
        
        p1rightrow1 = QWidget()
        p1rightrow1layout = QHBoxLayout(p1rightrow1)
        eliminate_spacing(p1rightrow1layout)
        
        p1rightrow2 = QWidget()
        p1rightrow2layout = QHBoxLayout(p1rightrow2)
        eliminate_spacing(p1rightrow2layout)

        p1rightrow3 = QWidget()
        p1rightrow3layout = QHBoxLayout(p1rightrow3)
        p1rightrow3layout.setContentsMargins(0,0,0,0)
                
        ## Left
        # Files button
        self.add_files = QPushButton("Add Files")
        self.add_files.setFixedWidth(100)
        self.add_files.clicked.connect(self.loadfiles)
        
        # Delete file button
        self.delete_file = QPushButton("Remove File")
        self.delete_file.setFixedWidth(100)
        self.delete_file.clicked.connect(self.delete_selected)

        # Delete files button
        self.delete_all = QPushButton("Clear Files")
        self.delete_all.setFixedWidth(100)
        self.delete_all.clicked.connect(self.clear_files)
        
        # Add buttons to layout.
        buttons = QWidget()
        button_layout = QVBoxLayout(buttons)
        button_layout.addSpacing(20)
        button_layout.addWidget(self.add_files, alignment=Qt.AlignCenter)
        button_layout.addWidget(self.delete_file, alignment=Qt.AlignCenter)
        button_layout.addWidget(self.delete_all, alignment=Qt.AlignCenter)
        buttons.setFixedWidth(140)
        
        # Add buttons layout to left layout.
        p1leftlayout.addWidget(buttons)
        p1leftlayout.addStretch(1)
                                    
        ## Right        
        # Added files lists
        file_box = QVBoxLayout()
        fileslayout = QHBoxLayout()
        files_header = QLabel("Loaded Files")
        fileslayout.addSpacing(5)
        fileslayout.addWidget(files_header)
        self.analyze_files = QListWidget()
        self.analyze_files.setStyleSheet(FilesSheet)
        self.analyze_files.setMinimumWidth(200)
        self.analyze_files.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        file_box.addLayout(fileslayout)
        file_box.addSpacing(2)
        file_box.addWidget(self.analyze_files)
        
        # Setup an identical list with full paths of files for analysis.
        self.analyze_paths = QListWidget()
        
        # Add status list
        status_box = QVBoxLayout()
        statuslayout = QHBoxLayout()
        status_header = QLabel("Status")
        statuslayout.addSpacing(5)
        statuslayout.addWidget(status_header)
        self.files_status = QListWidget()
        self.files_status.setStyleSheet(StatusSheet)
        self.files_status.setFixedWidth(160)
        self.files_status.setStyleSheet(StatusSheet)
        
        # Connect these to one another.
        self.files_status.currentRowChanged.connect(self.analyze_files.setCurrentRow)
        self.analyze_files.currentRowChanged.connect(self.files_status.setCurrentRow)
        self.analyze_files.verticalScrollBar().valueChanged.connect(self.files_status.verticalScrollBar().setValue)
        self.files_status.verticalScrollBar().valueChanged.connect(self.analyze_files.verticalScrollBar().setValue)
        
        status_box.addLayout(statuslayout)
        status_box.addSpacing(2)
        status_box.addWidget(self.files_status)

        # Add these items to top right.
        p1righttoplayout.addLayout(file_box)
        p1righttoplayout.addLayout(status_box)
                        
        ### Right Bottom
        ## Left        
        # Results Header
        results_info = QLabel("Results Folder:  ")
        
        # Load our results location 
        results_dir = load_results_dir()
        
        self.results_path_location = QLineEdit(results_dir)
        self.results_path_location.setReadOnly(True)
        self.results_path_location.setMinimumWidth(100)
                
        # Set Location of our results. Add to bottom 
        self.set_location = QPushButton("Set Location")
        self.set_location.setFixedWidth(100)
        self.set_location.clicked.connect(self.new_results_dir)
                        
        # Add widgets to middle1 widget.
        p1rightrow1layout.addWidget(results_info)
        p1rightrow1layout.addWidget(self.results_path_location)
        p1rightrow1layout.addSpacing(10)
        p1rightrow1layout.addWidget(self.set_location)
        
        ## Next Row        
        # Set Resolution
        resolution_header = QLabel("Image Resolution:")
        self.set_resolution = QDoubleSpinBox()
        self.set_resolution.setSuffix(" µm\u00B3/voxel")
        self.set_resolution.setAlignment(Qt.AlignCenter)
        self.set_resolution.setValue(1.0)
        self.set_resolution.setMinimum(0.01)
        self.set_resolution.setFixedWidth(130)
        
        # Change units
        unit_label = QLabel("Unit: ")
        self.unit = QComboBox()
        self.unit.addItem("µm\u00B3")
        self.unit.addItem("µm\u00B2")
        self.unit.addItem("mm\u00B3")
        self.unit.addItem("mm\u00B2")
        self.unit.currentIndexChanged.connect(self.update_units)
        
        # Analyze button
        self.analyze = QPushButton("Analyze")
        self.analyze.setFixedWidth(100)
        self.analyze.clicked.connect(self.run_analysis)
        
        # Add options to options widget
        p1rightrow2layout.addWidget(resolution_header)
        p1rightrow2layout.addSpacing(5)
        p1rightrow2layout.addWidget(self.set_resolution)
        p1rightrow2layout.addSpacing(10)
        p1rightrow2layout.addWidget(unit_label)
        p1rightrow2layout.addWidget(self.unit)
        p1rightrow2layout.addStretch(0)
        p1rightrow2layout.addWidget(self.analyze)
        
        # Radius row
        # Maximum Radius
        radius_label = QLabel("Maximum Radius: ")
        self.max_radius = QSpinBox()
        self.max_radius.setMinimum(20)
        self.max_radius.setMaximum(300)
        self.max_radius.setValue(150)
        self.max_radius.setSingleStep(10)
        self.max_radius.setSuffix(" µm")
        self.max_radius.setAlignment(Qt.AlignCenter)
        self.max_radius.setFixedWidth(80)
        
        # Cancel Button
        self.cancel_analysis = QPushButton("Cancel")
        self.cancel_analysis.setFixedWidth(100)
        self.cancel_analysis.setDisabled(True)
        self.cancel_analysis.clicked.connect(self.stop_thread)        
                                
        radius_row = QWidget()
        radius_rowlayout = QHBoxLayout(radius_row)
        eliminate_spacing(radius_rowlayout)
        radius_rowlayout.addWidget(radius_label)
        radius_rowlayout.addSpacing(3)
        radius_rowlayout.addWidget(self.max_radius)
        radius_rowlayout.addStretch(0)
        radius_rowlayout.addWidget(self.cancel_analysis)
        
        
        ## Filter segments
        filter_row = QWidget()
        filter_rowlayout = QHBoxLayout(filter_row)
        eliminate_spacing(filter_rowlayout)
        
        # Eliminate isolated
        self.filter_check = QCheckBox("Filter isolated segments shorter than: ")
        self.filter_length = QDoubleSpinBox()
        self.filter_length.setDecimals(1)
        self.filter_length.setValue(5)
        self.filter_length.setMinimum(2)
        self.filter_length.setSuffix(" µm")
        self.filter_length.setAlignment(Qt.AlignCenter)
        self.filter_length.setFixedWidth(80)
        self.filter_check.toggled.connect(self.filter_length.setEnabled)
        self.filter_check.setChecked(True)
        
        filter_rowlayout.addWidget(self.filter_check)
        filter_rowlayout.addSpacing(17)
        filter_rowlayout.addWidget(self.filter_length)
        filter_rowlayout.addStretch(0)
        
        ## Prune endpoints
        prune_row = QWidget()
        prune_rowlayout = QHBoxLayout(prune_row)
        eliminate_spacing(prune_rowlayout)
        # Prune endpoint segments
        self.prune_check = QCheckBox("Prune endpoint segments shorter than: ")
        self.prune_check.setChecked(False)
        self.prune_length = QDoubleSpinBox()
        self.prune_length.setDecimals(1)
        self.prune_length.setValue(1)
        self.prune_length.setMinimum(1)
        self.prune_length.setSuffix(" µm")
        self.prune_length.setAlignment(Qt.AlignCenter)
        self.prune_length.setFixedWidth(80)
        self.prune_length.setDisabled(True)
        self.prune_check.toggled.connect(self.prune_length.setEnabled)
        
        prune_rowlayout.addWidget(self.prune_check)
        prune_rowlayout.addSpacing(5)
        prune_rowlayout.addWidget(self.prune_length)
        prune_rowlayout.addStretch(0)
        
        
        ## Next row
        # Save Segments Results
        self.seg_results = QCheckBox("Save Segment Results")
        self.seg_results.setToolTip("<b>If checked, an additional results tab will be created with details about segment length,  radius,  and tortuosity.")                                
    
        # Add widgets     
        p1rightrow3layout.addWidget(self.seg_results)
        p1rightrow3layout.setContentsMargins(0,5,0,8)
        p1rightrow3layout.addStretch(0)
    
        ## next row
        # Save Datsets
        graph_row = QWidget()
        graph_rowlayout = QHBoxLayout(graph_row)
        graph_rowlayout.setContentsMargins(0,5,0,8)
        self.save_graphs = QCheckBox("Save Graph Files")
        self.save_graphs.setToolTip("Saves igraph files for each dataset")   
        graph_rowlayout.addWidget(self.save_graphs)
        graph_rowlayout.addStretch(0)
        
    
        ## Add widgets to our right layout.
        p1rightlayout.addWidget(p1righttop)
        p1rightlayout.addSpacing(10)
        p1rightlayout.addWidget(p1rightrow1)
        p1rightlayout.addWidget(p1rightrow2)
        p1rightlayout.addSpacing(2)
        p1rightlayout.addWidget(radius_row)
        p1rightlayout.addWidget(filter_row)
        p1rightlayout.addWidget(prune_row)
        p1rightlayout.addWidget(p1rightrow3)
        p1rightlayout.addWidget(graph_row)

        ## Finalizing Page layout                
        page1layout.addWidget(p1left)
        page1layout.addWidget(p1right)
                           
                                
    ## UI management    
    def update_selection(self, row):
        self.analyze_files.setCurrentRow(row)
    
    def update_files_status(self, status):
        self.files_status.item(status[1]).setText(status[0])
    
    def update_units(self):
        a_unit = self.unit.currentText()
        if a_unit[0] == 'm':
            unit = ' mm'
        elif a_unit[0] == 'µ':
            unit = ' µm'
        if a_unit[-1] == '\u00B2':
            res_add = '/pixel'
        elif a_unit[-1] == '\u00B3':
            res_add = '/voxel'
        unit = " " + unit
        # Update filter
        self.max_radius.setSuffix(unit)
        self.filter_length.setSuffix(unit)
        self.prune_length.setSuffix(unit)
        
        # Update resolution
        res_unit = a_unit + res_add
        self.set_resolution.setSuffix(res_unit)
     
     
    ## File management
    def loadfiles(self):
        # Clear files if they have already been analyzed.
        queued = "In Queue"
        
        
        load_dir = get_dir('Desktop')
        # Open our file dialogue.         
        dialog_files = QFileDialog.getOpenFileNames(self, "Add files to analyze", load_dir)
        
        # Load files, but prevent loading repeats.
        if dialog_files:
            if self.analysis_complete == True:
                self.analyze.setEnabled(True)
                self.analyze_files.clear()
                self.analyze_paths.clear()
                self.files_status.clear()
                self.files = []
                
                # Mark that no analysis of these files has been completed.
                self.analysis_complete = False
            
            already_added = False                             
            dialog_files = dialog_files[0]
            
            # Get number of current files loaded.
            current_num = self.analyze_files.count()
            if current_num > 0:
                already_added = True
            
            for file_path in dialog_files:
                short_path = path.basename(file_path)
                
                # If files have been added already, make sure selected files aren't in the old list.
                if already_added:
                    current_files = []
                    for i in range(current_num):
                        current_files.append(self.analyze_files.item(i).text())
                    
                    if short_path not in current_files:                
                        QListWidgetItem(file_path, self.analyze_paths)
                        QListWidgetItem(short_path, self.analyze_files)
                        QListWidgetItem(queued, self.files_status)
                
                # If not, load without checking.
                else:
                    QListWidgetItem(file_path, self.analyze_paths)
                    QListWidgetItem(short_path, self.analyze_files)
                    QListWidgetItem(queued, self.files_status)

       

    # Internally manage results dir text.
    def new_results_dir(self):
        results_dir = set_results_dir(self)
        self.results_path_location.setText(results_dir)
        
    ## File management
    def delete_selected(self):
        row = self.analyze_files.currentRow()
        if row != -1:
            # Remove files from our display list and our storage list.
            self.analyze_files.takeItem(self.analyze_files.currentRow())
            self.analyze_paths.takeItem(self.analyze_files.currentRow())
            self.files_status.takeItem(self.analyze_files.currentRow())
            
    def clear_files(self):
        self.analyze_files.clear()
        self.analyze_paths.clear()
        self.files_status.clear()
    
    ## Analysis
    def run_analysis(self):
        if self.analysis_complete == True:
            return        
        # Make sure there's files loaded.
        current_num = self.analyze_files.count()
        if current_num > 0:
            # Load state of options into our analysis thread.
            self.a_thread.load_ex(self)
                        
            # Load files into our file variable.
            for i in range(current_num):
                self.files.append(self.analyze_paths.item(i).text())
                
            self.a_thread.button_lock.connect(self.lock_buttons)
            self.a_thread.selection_signal.connect(self.update_selection)
            self.a_thread.analysis_stage.connect(self.update_files_status)
            
            # Mark that an anlaysis has been completed.
            self.analysis_complete = True
            self.analyze.setDisabled(True)
                    
            self.a_thread.start()
    
    def lock_buttons(self,lock_status):
        self.add_files.setDisabled(lock_status)
        self.delete_file.setDisabled(lock_status)
        self.delete_all.setDisabled(lock_status)
        self.set_location.setDisabled(lock_status)
        
        if lock_status == 1:
            self.cancel_analysis.setDisabled(False)
        else:
            self.cancel_analysis.setDisabled(True)
            
    def stop_thread(self):
        # self.a_thread.stop() # Doesn't work... not sure why.
        self.cancel_analysis.setDisabled(True)
        self.a_thread.stop()
                          
    # Close all associated widgets if the main thread is ended.
    def closeEvent(self, event):
        self.a_thread.stop()
        try:
            self.v_thread.close()
        except:
            pass
        event.accept()

        

