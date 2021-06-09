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
from Library.UI.collapsible_gui import CollapsibleBox
from Library.helpers import remove_legend, prep_scalars_update, get_rgb, eliminate_spacing, get_dir, get_cwd, load_results_dir, set_results_dir


# Get our working directory
wd = get_cwd()

class Page2(QSplitter):
    def __init__(self):
        super().__init__()        
        # Make our plotter
        self.plotter = QtInteractor(multi_samples=8) 
                
        # page2 = QSplitter()
        page2layout = QHBoxLayout(self)
        eliminate_spacing(page2layout)
        
        # Create menu and pyqt objects.
        leftmenu = QFrame()
        leftscroll = QScrollArea()
        leftscroll.setWidget(leftmenu)
        leftscroll.setWidgetResizable(True)
        leftscroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        leftscroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        leftscroll.setFixedWidth(240)
        self.leftmenulayout = QVBoxLayout(leftmenu)
        self.leftmenulayout.setContentsMargins(0,20,0,20)
        

        ## Build left menu
        # Load file button
        load_file = QPushButton("Load File")
        load_file.setFixedWidth(100)
        load_file.clicked.connect(self.load_volume)
        
        # Line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        
        # Line Viewer
        file_loader = QWidget()
        load_layout = QVBoxLayout(file_loader)
        load_layout.setSpacing(5)
        load_layout.setContentsMargins(0,0,0,0)
        self.loaded_file_header = QLabel("Loaded File:")
        
        # Add our default file
        # A visualization
        self.visualized_file = path.join(wd, 'Library/tiny.nii')
        self.queued_file = self.visualized_file
        
        self.loaded_vis = QLineEdit("tiny.nii")
        self.loaded_vis.setFixedWidth(150)
        self.loaded_vis.setReadOnly(True)
        self.loaded_vis.setAlignment(Qt.AlignCenter)
        load_layout.addWidget(self.loaded_file_header, alignment=Qt.AlignCenter)
        load_layout.addWidget(self.loaded_vis)
        
        # # Visualize
        visualize_button = QPushButton("Visualize")
        visualize_button.setFixedWidth(100)
        visualize_button.clicked.connect(self.visualization_popup)
        
        # Visualization options below #
        vis_options = QGroupBox()
        vis_optionslayout = QVBoxLayout(vis_options)
        
        # Show axes
        self.axes_button = QCheckBox("Show Axes")
        self.axes_button.stateChanged.connect(self.axes_view)
        
        # Show Legends
        self.show_legend = QCheckBox("Show Legend") # Connected later on b
        self.show_legend.setChecked(True)
        
        ## Legend Options
        # Legend Unit
        unit_layout = QHBoxLayout()
        eliminate_spacing(unit_layout)
        legend_label = QLabel("Unit:")
        self.legend_unit = QComboBox()
        self.legend_unit.addItem("(µm)")
        self.legend_unit.addItem("(mm)")
        self.legend_unit.addItem("(px)")
        self.legend_unit.currentIndexChanged.connect(self.toggle_legend)
        # unit_widgetlayout.addStretch(0)
        unit_layout.addWidget(legend_label, alignment=Qt.AlignLeft)
        unit_layout.addSpacing(5)
        unit_layout.addWidget(self.legend_unit, alignment=Qt.AlignLeft)
        unit_layout.addStretch(0)
        
        # Legend limits
        limit_header = QLabel("Scalars Range:")
        limit_row = QHBoxLayout()
        eliminate_spacing(limit_row)
        self.legend_lowlim = QDoubleSpinBox()
        self.legend_lowlim.setDecimals(1)
        self.legend_lowlim.setAlignment(Qt.AlignCenter)
        self.legend_lowlim.setValue(0.0)
        self.legend_lowlim.setMaximum(1000)
        self.legend_lowlim.setFixedWidth(65)
        self.legend_lowlim.editingFinished.connect(self.update_clim)
        limit_between = QLabel(" to ")
        self.legend_uplim = QDoubleSpinBox()
        self.legend_uplim.setDecimals(1)
        self.legend_uplim.setAlignment(Qt.AlignCenter)
        self.legend_uplim.setValue(1.0)
        self.legend_uplim.setMaximum(1000)
        self.legend_uplim.setFixedWidth(65)
        self.legend_uplim.editingFinished.connect(self.update_clim)
        limit_row.addWidget(self.legend_lowlim)
        limit_row.addWidget(limit_between)
        limit_row.addWidget(self.legend_uplim)
        limit_row.addStretch(0)
        
        # Reset clim button
        self.mesh_clim = [0, 1]
        reset_climbutton = QPushButton("Reset Range")
        reset_climbutton.clicked.connect(self.reset_clim)
        
        # Legend options dropdown
        legend_help = "Select legend unit and scalars limits."
        self.legend_options = CollapsibleBox("Legend Options", legend_help)
        legend_optionslayout = QVBoxLayout()
        legend_optionslayout.addLayout(unit_layout)
        legend_optionslayout.addWidget(limit_header)
        legend_optionslayout.addLayout(limit_row)
        legend_optionslayout.addWidget(reset_climbutton, alignment=Qt.AlignCenter)
        self.legend_options.setContentLayout(legend_optionslayout)
        
        # Bounds box
        self.bounds_box = QCheckBox("Show Boundaries")
        self.bounds_box.toggled.connect(self.toggle_bounds)
        
        # Show Grid
        self.grid_coords = QCheckBox("Show Grid")
        self.grid_coords.toggled.connect(self.toggle_grid)
                
        # Background color
        background_button = QPushButton("Background Color")
        background_button.clicked.connect(self.background_dialog)
                                        
        # Capture Screenshot
        screen_cap = QPushButton("Take Screenshot")
        screen_cap.clicked.connect(self.screenshot)
        screen_cap.setToolTip("Saves screenshot of current view into results directory.")
        
        vis_optionslayout.addWidget(self.axes_button)
        vis_optionslayout.addWidget(self.show_legend)
        ## Collapsible here
        vis_optionslayout.addWidget(self.legend_options)
        vis_optionslayout.addWidget(self.bounds_box)
        vis_optionslayout.addWidget(self.grid_coords)
        vis_optionslayout.addWidget(background_button)
        vis_optionslayout.addWidget(screen_cap)
        
        ### Tube view groupbox ###
        group_font = QFont()
        group_font.setBold(True)
        option_font = QFont()
        option_font.setBold(False)
        self.tube_view = QGroupBox("Tube Meshes")
        self.tube_view.setFont(group_font)
        tube_viewlayout = QVBoxLayout(self.tube_view)
        self.tube_view.setDisabled(True)
        
        color_options0 = QLabel("<u><b>Color Options:")
        color_options1 = QLabel("<u><b>Color Options:")
        feature_themeheader0 = QLabel("Color Theme:")
        feature_themeheader1 = QLabel("Color Theme:")
        color_header = [None] * 8
        for i in range(8):
            color_header[i] = QLabel("Color:  ")
        
        ## Network tubes. Widgets added in order at bottom
        self.network_view = QCheckBox("Simple Network")
        self.network_view.stateChanged.connect(self.add_network)
        self.network_view.setFont(option_font)

        # Opacity
        net_opac = QWidget()
        net_opac_layout = QHBoxLayout(net_opac)
        net_opac_layout.setSpacing(0)
        net_opac_layout.setContentsMargins(0,0,0,0)
        opacity_label = QLabel("Opacity: ")
        self.network_opacity = QSpinBox()
        self.network_opacity.setFont(option_font)
        self.network_opacity.setAlignment(Qt.AlignRight)
        self.network_opacity.setSuffix(" %")
        self.network_opacity.setRange(0,100)
        self.network_opacity.setSingleStep(10)
        self.network_opacity.valueChanged.connect(self.update_opacity)
        net_opac_layout.addWidget(opacity_label)
        net_opac_layout.addWidget(self.network_opacity)
        net_opac_layout.addStretch(0)      
          
        # Show bifurcations # Stupid amount of f*n code for these few buttons.
        netbifs = QWidget()
        netbifslayout = QVBoxLayout(netbifs)
        netbifslayout.setContentsMargins(0,0,0,0)
        self.net_branches = QCheckBox("Show Branchpoints")
        self.net_branches.stateChanged.connect(self.network_bes)
        self.nbcolorcolumn = QWidget()
        nbcolorcolumnlayout = QVBoxLayout(self.nbcolorcolumn)
        nbcolorcolumnlayout.setContentsMargins(0,0,0,0)
        self.nb_color_button = QPushButton("Select Color")
        self.nb_color_button.clicked.connect(self.mesh_color)
        nbcolorbox = QHBoxLayout()
        nbcolorbox.setContentsMargins(0,0,0,0)
        self.netbcolor = QWidget()
        self.netbcolor.setFixedWidth(20)
        nbcolorbox.addStretch(0)
        nbcolorbox.addWidget(color_header[0])
        nbcolorbox.addWidget(self.netbcolor)
        nbcolorbox.addStretch(0)
        nbcolorcolumnlayout.addWidget(self.nb_color_button, alignment=Qt.AlignCenter)
        nbcolorcolumnlayout.addLayout(nbcolorbox)
        self.nbcolorcolumn.setVisible(False)
        
        netbifslayout.addWidget(self.nbcolorcolumn)
        
        # Show endpoints 
        netends = QWidget()
        netendslayout = QVBoxLayout(netends)
        netendslayout.setContentsMargins(0,0,0,0)
        self.net_ends = QCheckBox("Show Endpoints")
        self.net_ends.stateChanged.connect(self.network_bes)
        self.necolorcolumn = QWidget()
        necolorcolumnlayout = QVBoxLayout(self.necolorcolumn)
        necolorcolumnlayout.setContentsMargins(0,0,0,0)
        self.ne_color_button = QPushButton("Select Color")
        self.ne_color_button.clicked.connect(self.mesh_color)
        necolorbox = QHBoxLayout()
        necolorbox.setContentsMargins(0,0,0,0)
        self.netecolor = QWidget()
        self.netecolor.setFixedWidth(20)
        necolorbox.addStretch(0)
        necolorbox.addWidget(color_header[1])        
        necolorbox.addWidget(self.netecolor)
        necolorbox.addStretch(0)
        necolorcolumnlayout.addWidget(self.ne_color_button, alignment=Qt.AlignCenter)
        necolorcolumnlayout.addLayout(necolorbox)
        self.necolorcolumn.setVisible(False)
        
        netendslayout.addWidget(self.necolorcolumn)
        
        # Main Network Color Options #
        network_colors = QWidget()
        network_colorslayout = QVBoxLayout(network_colors)
        network_colorslayout.setContentsMargins(0,0,0,0)
        
        # Feature based color view
        self.network_scalar_colors = QRadioButton("Feature Based:")
        self.network_scalar_colors.setChecked(True)
        self.network_scalar_colors.toggled.connect(self.toggle_network_color)
        
        
        self.network_scalar = QComboBox()
        self.network_scalar.setFont(option_font)
        self.load_scalar_options(self.network_scalar)
        self.network_scalar.currentIndexChanged.connect(self.update_scalars)
        self.network_scalar_theme = QComboBox()
        self.network_scalar_theme.setFont(option_font)
        self.load_themes(self.network_scalar_theme)
        self.network_scalar_theme.currentIndexChanged.connect(self.update_cmap)
        
        self.nsb = QWidget()
        self.nsb_layout = QVBoxLayout(self.nsb)
        self.nsb_layout.setContentsMargins(0,0,0,0)
        self.nsb_layout.addWidget(self.network_scalar)
        self.nsb_layout.addWidget(feature_themeheader0)
        self.nsb_layout.addWidget(self.network_scalar_theme)
 
        # Single color
        self.network_single_colors = QRadioButton("Single Color")
        self.network_single_colors.setChecked(False)
        self.network_single_colors.toggled.connect(self.toggle_network_color)
        self.network_colorbutton = QPushButton("Select Color")
        self.network_colorbutton.clicked.connect(self.mesh_color)
        
        self.ncb = QWidget()
        ncblayout = QVBoxLayout(self.ncb)
        ncblayout.setContentsMargins(0,0,0,0)
        
        network_colorbox = QHBoxLayout()
        eliminate_spacing(network_colorbox)
        self.network_color = QWidget()
        self.network_color.setFixedWidth(20)
        network_colorbox.addStretch(0)
        network_colorbox.addWidget(color_header[2])
        network_colorbox.addWidget(self.network_color)
        network_colorbox.addStretch(0)
        
        ncblayout.addWidget(self.network_colorbutton)
        ncblayout.addLayout(network_colorbox)
        self.ncb.setVisible(False)
        
        # Add widgets to our single color layout
        network_colorslayout.addWidget(color_options0)
        network_colorslayout.addWidget(self.network_scalar_colors)
        network_colorslayout.addWidget(self.nsb)
        network_colorslayout.addSpacing(5)
        network_colorslayout.addWidget(self.network_single_colors)
        network_colorslayout.addSpacing(5)
        network_colorslayout.addWidget(self.ncb)
        
        # Create our dropdown box for the network options
        network_help = "Select view options and click 'Update' to enact update options."
        self.network_options = CollapsibleBox("Network Options", network_help)
        networklay = QVBoxLayout()
        networklay.addWidget(self.net_branches)
        networklay.addWidget(netbifs)
        networklay.addWidget(self.net_ends)
        networklay.addWidget(netends)
        networklay.addWidget(network_colors)
        networklay.addWidget(net_opac)
        self.network_options.setContentLayout(networklay)
        self.network_options.lock(True)
        
        
        ### Scaled View Groupbox ###
        self.scaled_view = QCheckBox("Scaled Network")
        self.scaled_view.stateChanged.connect(self.add_scaled)
        self.scaled_view.setFont(option_font)
        
        tube_group = QButtonGroup()
        tube_group.addButton(self.network_view)
        tube_group.addButton(self.scaled_view)
        tube_group.setExclusive(True)
        
        # Opacity
        scal_opac = QWidget()
        scal_opac_layout = QHBoxLayout(scal_opac)
        scal_opac_layout.setSpacing(0)
        scal_opac_layout.setContentsMargins(0,0,0,0)
        opacity_label1 = QLabel("Opacity: ")
        self.scaled_opacity = QSpinBox()
        self.scaled_opacity.setFont(option_font)
        self.scaled_opacity.setAlignment(Qt.AlignRight)
        self.scaled_opacity.setSuffix(" %")
        self.scaled_opacity.setRange(0,100)
        self.scaled_opacity.setSingleStep(10)
        self.scaled_opacity.valueChanged.connect(self.update_opacity)
        scal_opac_layout.addWidget(opacity_label1)
        scal_opac_layout.addWidget(self.scaled_opacity)
        scal_opac_layout.addStretch(0)      
          
        # Show bifurcations # Stupid amount of code for these few buttons.
        scalbifs = QWidget()
        scalbifslayout = QVBoxLayout(scalbifs)
        scalbifslayout.setContentsMargins(0,0,0,0)
        self.scal_branches = QCheckBox("Show Branchpoints")
        self.scal_branches.stateChanged.connect(self.scaled_bes)
        self.sbcolorcolumn = QWidget()
        sbcolorcolumnlayout = QVBoxLayout(self.sbcolorcolumn)
        sbcolorcolumnlayout.setContentsMargins(0,0,0,0)
        self.sb_color_button = QPushButton("Select Color")
        self.sb_color_button.clicked.connect(self.mesh_color)
        sbcolorbox = QHBoxLayout()
        sbcolorbox.setContentsMargins(0,0,0,0)
        self.sbcolor = QWidget()
        self.sbcolor.setFixedWidth(20)
        sbcolorbox.addStretch(0)
        sbcolorbox.addWidget(color_header[3])
        sbcolorbox.addWidget(self.sbcolor)
        sbcolorbox.addStretch(0)
        sbcolorcolumnlayout.addWidget(self.sb_color_button, alignment=Qt.AlignCenter)
        sbcolorcolumnlayout.addLayout(sbcolorbox)
        self.sbcolorcolumn.setVisible(False)
        
        scalbifslayout.addWidget(self.sbcolorcolumn)
        
        # Show endpoints 
        scalends = QWidget()
        scalendslayout = QVBoxLayout(scalends)
        scalendslayout.setContentsMargins(0,0,0,0)
        self.scal_ends = QCheckBox("Show Endpoints")
        self.scal_ends.stateChanged.connect(self.scaled_bes)
        self.secolorcolumn = QWidget()
        secolorcolumnlayout = QVBoxLayout(self.secolorcolumn)
        secolorcolumnlayout.setContentsMargins(0,0,0,0)
        self.se_color_button = QPushButton("Select Color")
        self.se_color_button.clicked.connect(self.mesh_color)
        secolorbox = QHBoxLayout()
        secolorbox.setContentsMargins(0,0,0,0)
        self.secolor = QWidget()
        self.secolor.setFixedWidth(20)
        secolorbox.addStretch(0)
        secolorbox.addWidget(color_header[4])        
        secolorbox.addWidget(self.secolor)
        secolorbox.addStretch(0)
        secolorcolumnlayout.addWidget(self.se_color_button, alignment=Qt.AlignCenter)
        secolorcolumnlayout.addLayout(secolorbox)
        self.secolorcolumn.setVisible(False)
        
        scalendslayout.addWidget(self.secolorcolumn)
        
        # Main Scaled Color Options #
        scal_colors = QWidget()
        scal_colorslayout = QVBoxLayout(scal_colors)
        scal_colorslayout.setContentsMargins(0,0,0,0)
        
        # Feature based color view
        self.scaled_scalar_colors = QRadioButton("Feature Based:")
        self.scaled_scalar_colors.setChecked(True)
        self.scaled_scalar_colors.toggled.connect(self.toggle_scaled_color)
        
        self.scaled_scalar = QComboBox()
        self.scaled_scalar.setFont(option_font)
        self.load_scalar_options(self.scaled_scalar)
        self.scaled_scalar.setCurrentIndex(1)
        self.scaled_scalar.currentIndexChanged.connect(self.update_scalars)
        self.scaled_scalar_theme = QComboBox()
        self.scaled_scalar_theme.setFont(option_font)
        self.load_themes(self.scaled_scalar_theme)
        self.scaled_scalar_theme.currentIndexChanged.connect(self.update_cmap)
        
        self.ssb = QWidget()
        self.ssb_layout = QVBoxLayout(self.ssb)
        self.ssb_layout.setContentsMargins(0,0,0,0)
        self.ssb_layout.addWidget(self.scaled_scalar)
        self.ssb_layout.addWidget(feature_themeheader1)
        self.ssb_layout.addWidget(self.scaled_scalar_theme)
 
        # Single color
        self.scaled_single_colors = QRadioButton("Single Color")
        self.scaled_single_colors.setChecked(False)
        self.scaled_single_colors.toggled.connect(self.toggle_scaled_color)
        self.scaled_colorbutton = QPushButton("Select Color")
        self.scaled_colorbutton.clicked.connect(self.mesh_color)
        
        self.scb = QWidget()
        scblayout = QVBoxLayout(self.scb)
        scblayout.setContentsMargins(0,0,0,0)
        
        scaled_colorbox = QHBoxLayout()
        eliminate_spacing(scaled_colorbox)
        self.scaled_color = QWidget()
        self.scaled_color.setFixedWidth(20)
        scaled_colorbox.addStretch(0)
        scaled_colorbox.addWidget(color_header[5])
        scaled_colorbox.addWidget(self.scaled_color)
        scaled_colorbox.addStretch(0)
        
        scblayout.addWidget(self.scaled_colorbutton)
        scblayout.addLayout(scaled_colorbox)
        self.scb.setVisible(False)
        
        # Add widgets to our single color layout
        scal_colorslayout.addWidget(color_options1)
        scal_colorslayout.addWidget(self.scaled_scalar_colors)
        scal_colorslayout.addWidget(self.ssb)
        scal_colorslayout.addSpacing(5)
        scal_colorslayout.addWidget(self.scaled_single_colors)
        scal_colorslayout.addSpacing(5)
        scal_colorslayout.addWidget(self.scb)
        
        # Create our dropdown box for the network options
        scaled_help = "Select view options and click 'Update' to enact options."
        self.scaled_options = CollapsibleBox("Scaled Options", scaled_help)
        scaledlay = QVBoxLayout()
        scaledlay.addWidget(self.scal_branches)
        scaledlay.addWidget(scalbifs)
        scaledlay.addWidget(self.scal_ends)
        scaledlay.addWidget(scalends)
        scaledlay.addWidget(scal_colors)
        scaledlay.addWidget(scal_opac)
        self.scaled_options.setContentLayout(scaledlay)  
        self.scaled_options.lock(True)
              
              
        # Connect our visualization button
        self.show_legend.toggled.connect(self.toggle_legend)
        
        ## Finally, we add these options to our left layout
        tube_viewlayout.addWidget(self.network_view)
        tube_viewlayout.addWidget(self.network_options)
        tube_viewlayout.addSpacing(5)
        tube_viewlayout.addWidget(self.scaled_view)
        tube_viewlayout.addWidget(self.scaled_options)
        
        ### Volume view groupbox ###
        self.volume_view = QGroupBox("Volume Meshes")
        self.volume_view.setFont(group_font)
        self.volume_view.setDisabled(True)
        volume_viewlayout = QVBoxLayout(self.volume_view)
        # volume_viewlayout.setContentsMargins(5,0,4,0)
        
        ## Smoothed volume
        self.smoothed_view = QCheckBox("Smoothed Volume")
        self.smoothed_view.stateChanged.connect(self.add_smoothed)
        self.smoothed_view.setFont(option_font)        
        
        # Smoothed Opacity
        smopacwidget = QWidget()
        sm_opaclayout = QHBoxLayout(smopacwidget)
        eliminate_spacing(sm_opaclayout)
        opacity_label3 = QLabel("Opacity: ")
        self.sm_opacity = QSpinBox()
        self.sm_opacity.setFont(option_font)
        self.sm_opacity.setAlignment(Qt.AlignRight)
        self.sm_opacity.setSuffix(" %")
        self.sm_opacity.setRange(0,100)
        self.sm_opacity.setSingleStep(10)
        sm_opaclayout.addWidget(opacity_label3)
        sm_opaclayout.addWidget(self.sm_opacity)
        sm_opaclayout.addStretch(0)
        self.sm_opacity.valueChanged.connect(self.update_opacity)
        
        # Smoothed colorbox
        self.smcb = QWidget()
        smcblayout = QVBoxLayout(self.smcb)
        smcblayout.setContentsMargins(0,0,0,0)
        
        self.smoothed_colorbutton = QPushButton("Select Color")
        self.smoothed_colorbutton.clicked.connect(self.mesh_color)
        
        sm_colorbox = QHBoxLayout()
        eliminate_spacing(sm_colorbox)
        self.smoothed_color = QWidget()
        self.smoothed_color.setFixedWidth(20)
        sm_colorbox.addStretch(0)
        sm_colorbox.addWidget(color_header[6])
        sm_colorbox.addWidget(self.smoothed_color)
        sm_colorbox.addStretch(0)
        
        smcblayout.addWidget(self.smoothed_colorbutton)
        smcblayout.addLayout(sm_colorbox)
        
        # Dropdown box for original options
        smoothed_help = "Select opacity and color options for the volume"
        self.smoothed_options = CollapsibleBox("Smoothed Options", smoothed_help)
        smoothedlay = QVBoxLayout()
        smoothedlay.addWidget(self.smcb)
        smoothedlay.addWidget(smopacwidget)
        self.smoothed_options.setContentLayout(smoothedlay)
        self.smoothed_options.lock(True)   
             
        ## Original Volume
        self.original_view = QCheckBox("Original Volume")
        self.original_view.stateChanged.connect(self.add_original)
        self.original_view.setFont(option_font)
        
        # Original Opacity
        oopacwidget = QWidget()
        o_opaclayout = QHBoxLayout(oopacwidget)
        eliminate_spacing(o_opaclayout)
        opacity_label2 = QLabel("Opacity: ")
        self.o_opacity = QSpinBox()
        self.o_opacity.setFont(option_font)
        self.o_opacity.setAlignment(Qt.AlignRight)
        self.o_opacity.setSuffix(" %")
        self.o_opacity.setRange(0,100)
        self.o_opacity.setSingleStep(10)
        o_opaclayout.addWidget(opacity_label2)
        o_opaclayout.addWidget(self.o_opacity)
        o_opaclayout.addStretch(0)
        self.o_opacity.valueChanged.connect(self.update_opacity)
        
        # Original colorbox
        self.ocb = QWidget()
        ocblayout = QVBoxLayout(self.ocb)
        ocblayout.setContentsMargins(0,0,0,0)
        
        self.original_colorbutton = QPushButton("Select Color")
        self.original_colorbutton.clicked.connect(self.mesh_color)
        
        o_colorbox = QHBoxLayout()
        eliminate_spacing(o_colorbox)
        self.original_color = QWidget()
        self.original_color.setFixedWidth(20)
        o_colorbox.addStretch(0)
        o_colorbox.addWidget(color_header[7])
        o_colorbox.addWidget(self.original_color)
        o_colorbox.addStretch(0)
        
        ocblayout.addWidget(self.original_colorbutton)
        ocblayout.addLayout(o_colorbox)
        
        # Dropdown box for original options
        original_help = "Select opacity and color options for the volume"
        self.original_options = CollapsibleBox("Original Options", original_help)
        originallay = QVBoxLayout()
        originallay.addWidget(self.ocb)
        originallay.addWidget(oopacwidget)
        self.original_options.setContentLayout(originallay)
        self.original_options.lock(True)
        
        
        # Add these views and their options to our 2nd volume groupbox.
        volume_viewlayout.addWidget(self.smoothed_view)
        volume_viewlayout.addWidget(self.smoothed_options)
        volume_viewlayout.addSpacing(5)
        volume_viewlayout.addWidget(self.original_view)
        volume_viewlayout.addWidget(self.original_options)
        
        
        # Add buttons to left menu
        self.leftmenulayout.addWidget(file_loader, alignment=Qt.AlignCenter)
        self.leftmenulayout.addWidget(load_file, alignment=Qt.AlignCenter)
        self.leftmenulayout.addWidget(visualize_button, alignment=Qt.AlignCenter)
        self.leftmenulayout.addWidget(line)
        self.leftmenulayout.addWidget(vis_options)
        self.leftmenulayout.addWidget(self.tube_view)
        self.leftmenulayout.addWidget(self.volume_view)
        self.leftmenulayout.addStretch(0)
        
        ## Right viewer
        pyvwindow = QWidget()
        pyvwindowlayout= QVBoxLayout(pyvwindow)
        pyvwindowlayout.setSpacing(0)
        pyvwindowlayout.setContentsMargins(0,0,0,0)
                
        # Add our established self.plotter to the menu.
        pyvwindowlayout.addWidget(self.plotter)
        self.meshes = [None] * 10
        self.actors = [None] * 10
        self.legend = None

        # Add colors to our boxes
        self.reset_options()
        
        # Add menu and pyvista window to our widget
        page2layout.addWidget(leftscroll)
        page2layout.addWidget(pyvwindow)
        
        # self.qStack.addWidget(page2)
    
    # Loading
    def load_volume(self):
        load_dir = get_dir('Desktop')
        # Open our file dialogue.         
        loaded_file = QFileDialog.getOpenFileName(self, "Add files to analyze", load_dir)

        if loaded_file[0]:
            # self.visualized_file = loaded_file[0]
            self.queued_file = loaded_file[0]
            self.loaded_file_header.setText("Loaded File:")
            self.loaded_vis.setText(path.basename(self.queued_file))
            
        # Build our popup box
        # self.visualization_popup()
        
    # Screenshot functions
    def check_imgname(self, results_dir, title, depth):
        filename = results_dir + '/' + title + '_%03d' % depth + '.png'
        if path.exists(filename):
            depth += 1
            filename = self.check_imgname(results_dir, title, depth)
        return filename
    
    def screenshot(self):
        results_dir = load_results_dir()
        if path.exists(results_dir) == False:
            results_dir = set_results_dir(self)
            
        results_dir = path.join(results_dir, 'Screenshots')
        if path.exists(results_dir) == False:
            mkdir(results_dir)
            
        title = path.splitext(path.basename(self.visualized_file))[0]
        filename = self.check_imgname(results_dir, title, 0)
        self.plotter.screenshot(filename)
              
    def axes_view(self):
        if self.axes_button.isChecked():
            self.plotter.show_axes() 
        else:
            self.plotter.hide_axes()
    
    def background_dialog(self):
        bg_color = QColorDialog.getColor()
        if bg_color.isValid():
            self.plotter.set_background(color=bg_color.name())
    
    def toggle_bounds(self):
        if self.bounds_box.isChecked():
            self.plotter.add_bounding_box()
        else:
            self.plotter.remove_bounding_box()
                        
    def toggle_grid(self):
        if self.grid_coords.isChecked():
            self.plotter.show_bounds()
        else:
            self.plotter.remove_bounds_axes()
                        
    def load_scalar_options(self, combo):
        options = ['Length', 'Radius', 'Tortuosity']
        combo.addItems(options)
        
    def load_themes(self, combo):
        themes = ['Viridis', 'HSV', 'Gist_Rainbow','Rainbow', 'Jet', 'Turbo', 'Hot', 'Plasma']
        combo.addItems(themes)
    
    def toggle_legend(self, add=None):
        scalar_view = False
        networkcheck = self.network_view.isChecked()
        scaledcheck = self.scaled_view.isChecked()
        if len(self.plotter.renderer._actors) > 0:
            if networkcheck or scaledcheck:
                # Check to see if the simple network is active
                if networkcheck and self.network_scalar_colors.isChecked():
                    actor = self.actors[2]
                    title = self.network_scalar.currentText()
                    scalar_view = True
                elif networkcheck:
                    actor = self.actors[2]
                
                #Check to see if the scaled is active
                if scaledcheck and self.scaled_scalar_colors.isChecked():
                    actor = self.actors[6]
                    title = self.scaled_scalar.currentText()
                    scalar_view = True
                elif scaledcheck:
                    actor = self.actors[6]
                
                # Add/remove legend conditionally.
                if self.show_legend.isChecked() and scalar_view:
                    if title !=  'Tortuosity':
                        title = title + " " + self.legend_unit.currentText()
                    remove_legend(self.plotter, actor)
                    self.plotter.scalar_bars.add_scalar_bar(title=title, mapper=actor.GetMapper(),
                                                            width=0.4, position_x=0.55, n_colors=256)
                else:
                    remove_legend(self.plotter, actor)
        else:
            return            
           
    @pyqtSlot()
    def update_clim(self):
        # Block signals so we don't wind up in endless recursion.
        self.legend_lowlim.blockSignals(True)
        self.legend_uplim.blockSignals(True)
        
        new_min = self.legend_lowlim.value()
        new_max = self.legend_uplim.value()
        if self.sender() == self.legend_lowlim:
            if self.legend_lowlim.value() > new_max:
                self.legend_uplim.setValue(new_min)
                new_max = new_min
        else:
            if self.legend_lowlim.value() > new_max:
                self.legend_lowlim.setValue(new_max)
                new_min = new_max
        
        # Find the active actors
        if self.network_view.isChecked():
            ids = [2, 3]
        elif self.scaled_view.isChecked():
            ids = [6, 7]
        else:
            ids = None    
            
        # Now get the mappers of our putative actors and adjust their         
        if ids:
            for id in ids:
                mapper = self.actors[id].GetMapper()
                mapper.scalar_range = [new_min, new_max]
            
        self.legend_lowlim.blockSignals(False)
        self.legend_uplim.blockSignals(False)
    
    def added_clim(self):
        if self.network_view.isChecked():
            ids = [2, 3]
        elif self.scaled_view.isChecked():
            ids = [6, 7] 
        new_min = None
        new_max = None
        for id in ids:
            if self.actors[id]:
                mapper = self.actors[id].GetMapper()
                clim = mapper.scalar_range
                if not new_min:
                    new_min = clim[0]
                if not new_max:
                    new_max = clim[1]
                if new_min > clim[0]:
                    new_min = clim[0]
                if new_max < clim[1]:
                    new_max = clim[1]
        if self.actors[ids[0]]:
            self.mesh_clim = [new_min, new_max]
            self.reset_clim()          
        return

    def reset_clim(self):
        self.legend_lowlim.setValue(self.mesh_clim[0])
        self.legend_uplim.setValue(self.mesh_clim[1])
        self.update_clim()
        
    # These functions handle the color and scalar mapping of added meshes.
    def toggle_network_color(self):
        checked = self.network_scalar_colors.isChecked()
        self.nsb.setVisible(checked)
        self.ncb.setVisible(not checked)
        ids = [self.actors[2], self.actors[3]]
        default = not checked
        color = get_rgb(self.network_color.palette().color(QPalette.Background).name())
        self.toggle_color_mode(ids, default, color)
    
    def toggle_scaled_color(self):
        checked = self.scaled_scalar_colors.isChecked()
        self.ssb.setVisible(checked)
        self.scb.setVisible(not checked)
        ids = [self.actors[6], self.actors[7]]
        default = not checked
        
        color = get_rgb(self.scaled_color.palette().color(QPalette.Background).name())
        self.toggle_color_mode(ids, default, color)          
     
    @pyqtSlot()
    def mesh_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            sender = self.sender()
            rgb = (color.red(), color.green(), color.blue())
            background = "background: rgb" + str(rgb)
            ## Tubes
            if sender is self.network_colorbutton:
                self.network_color.setStyleSheet(background)
                ids= [2, 3]
            elif sender  is self.nb_color_button:
                self.netbcolor.setStyleSheet(background)
                ids= [4]
            elif sender is self.ne_color_button:
                self.netecolor.setStyleSheet(background)
                ids= [5]
            elif sender is self.scaled_colorbutton:
                self.scaled_color.setStyleSheet(background)
                ids = [6, 7]
            elif sender is self.sb_color_button:
                self.sbcolor.setStyleSheet(background)
                ids = [8]
            elif sender is self.se_color_button:
                self.secolor.setStyleSheet(background)
                ids = [9]
                
            ## Volumes
            elif sender is self.smoothed_colorbutton:
                self.smoothed_color.setStyleSheet(background)
                ids = [1]
            elif sender is self.original_colorbutton:
                self.original_color.setStyleSheet(background)
                ids = [0]
                
            color = color.name()
            color = get_rgb(color)
            self.update_colors(ids, color)

    def update_scalars(self):
        ids, scalars_choice, cmap, cmap_choice = prep_scalars_update(self)
        for i in range(2):
            # Update our scalars
            if self.actors[ids[i]]:
                self.meshes[ids[i]].set_active_scalars(scalars_choice)
                mapper = self.actors[ids[i]].GetMapper()
                scalars = pv.utilities.get_array(self.meshes[ids[i]], scalars_choice)
                clim = [np.min(scalars), np.max(scalars)]
                mapper.scalar_range = clim        
        self.toggle_legend()
        self.added_clim()
    
    def update_cmap(self):
        ids, _, cmap, cmap_choice = prep_scalars_update(self)
        for i in range(2):
            # Update our cmaps
            if self.actors[ids[i]]:
                mapper = self.actors[ids[i]].GetMapper()
                mapper.cmap = cmap_choice
                table = mapper.GetLookupTable()
                table.SetTable(pv._vtk.numpy_to_vtk(cmap))
    
    def update_colors(self, ids, color):
        for id in ids:
            prop = self.actors[id].GetProperty()
            prop.SetColor(color)
        return
    
    def toggle_color_mode(self, ids, default, color):
        # Sent the ids and bool default. Update accordingly.
        for i in range(2): # Change the color mode accordingly
            mapper = ids[i].GetMapper()
            if default:     
                mapper.SetColorModeToDefault()
                ids[i].GetProperty().SetColor(color)
            else:
                mapper.SetColorModeToMapScalars()
            mapper.SetScalarVisibility(not default)
        self.toggle_legend()
        
    @pyqtSlot()
    def update_opacity(self):
        ref = self.sender()
        if ref == self.network_opacity:
            ids = [2, 3]
            opacity = self.network_opacity.value() / 100
        elif ref == self.scaled_opacity:
            ids = [6, 7]
            opacity = self.scaled_opacity.value() / 100
        elif ref == self.sm_opacity:
            ids = [1]
            opacity = self.sm_opacity.value() / 100
        elif ref == self.o_opacity:
            ids = [0]
            opacity = self.o_opacity.value() / 100        
        
        for id in ids:
            if self.actors[id]: # Needed for options reset
                prop = self.actors[id].GetProperty()
                prop.SetOpacity(opacity)

    

    # Functions below deal with loading/removing meshes.  
    def load_meshes(self):  
        # Clear the plotter of any actors if there are any.
        for i in range(len(self.actors)):
            if self.actors[i]:
                self.plotter.remove_actor(self.actors[i])
                remove_legend(self.plotter, self.actors[i], False)
                self.actors[i] = None
        
        self.reset_options()
        self.scaled_view.setChecked(False)
        self.original_view.setChecked(False)
        self.smoothed_view.setChecked(False)        
              
        self.bounds_box.setChecked(False)
        self.grid_coords.setChecked(False)
        self.original_view.setChecked(False)
        self.net_ends.setChecked(False)
        self.net_branches.setChecked(False)
        self.network_view.setChecked(False)
        self.scal_branches.setChecked(False)
        self.scal_ends.setChecked(False)
        self.scaled_view.setChecked(False)
        self.smoothed_view.setChecked(False)
                
        self.meshes = self.build_thread.load_meshes()
        self.build_thread.quit()
        if self.meshes is None:
            return

        if self.meshes[2] and self.meshes[1]:
            self.network_view.setChecked(True)
            self.tube_view.setEnabled(True)
            self.volume_view.setEnabled(True)
            
        elif self.meshes[2]:
            self.network_view.setChecked(True)
            self.tube_view.setEnabled(True)
            self.volume_view.setDisabled(True)
            
        elif self.meshes[1]:
            self.smoothed_view.setChecked(True)
            self.tube_view.setDisabled(True)
            self.volume_view.setEnabled(True)
            
        self.visualized_file = self.queued_file
        self.loaded_file_header.setText("Rendered File:")

    def reset_options(self):
        # Reset the colors of our buttons
        self.network_color.setStyleSheet("background: rgb(255, 205, 5)")
        self.netbcolor.setStyleSheet("background: rgb(255, 0, 0)")
        self.netecolor.setStyleSheet("background: rgb(0, 255, 0)")
        self.scaled_color.setStyleSheet("background: rgb(255, 205, 5)")
        self.sbcolor.setStyleSheet("background: rgb(255, 0, 0)")
        self.secolor.setStyleSheet("background: rgb(0, 255, 0)")
        self.smoothed_color.setStyleSheet("background: rgb(255,255,255)")
        self.original_color.setStyleSheet("background: rgb(255,255,255)")
        
        # Reset Opacity Options
        self.network_opacity.setValue(100)
        self.scaled_opacity.setValue(100)
        self.sm_opacity.setValue(100)
        self.o_opacity.setValue(100)
        
        # Reset scalar options
        self.network_scalar.setCurrentIndex(0)
        self.network_scalar_theme.setCurrentIndex(0)
        self.scaled_scalar.setCurrentIndex(1)
        self.scaled_scalar_theme.setCurrentIndex(0)
        
        return   
                 
    def add_network(self):
        checked = self.network_view.isChecked()
        self.network_options.lock(not checked)
        self.network_options.toggle_button.setChecked(True)
        if checked == True:
            scalars_choice = self.network_scalar.currentText() 
            if self.scaled_view.isChecked():
                self.scaled_view.setChecked(False)
            self.actors[2] = self.plotter.add_mesh(self.meshes[2], scalars=scalars_choice, 
                                                   show_scalar_bar=False, smooth_shading=True, pickable=False)   
            self.actors[3] = self.plotter.add_mesh(self.meshes[3], scalars=scalars_choice, 
                                                   show_scalar_bar=False, smooth_shading=True, pickable=False)
            self.toggle_legend()
            self.added_clim()
            
        else:
            if self.actors[2]:
                remove_legend(self.plotter, self.actors[2], False)
                self.plotter.remove_actor(self.actors[2])
                self.plotter.remove_actor(self.actors[3])
            if self.actors[4]:
                self.plotter.remove_actor(self.actors[4])
            if self.actors[5]:
                self.plotter.remove_actor(self.actors[5])

    def network_bes(self):
        b_checked = self.net_branches.isChecked()
        self.nbcolorcolumn.setVisible(b_checked)
    
        e_checked = self.net_ends.isChecked()
        self.necolorcolumn.setVisible(e_checked)
        
        if b_checked:
            color = self.netbcolor.palette().color(QPalette.Background)
            rgb = color.name()
            self.actors[4] = self.plotter.add_mesh(self.meshes[4], color=rgb, show_scalar_bar=False,
                                                   smooth_shading=True, pickable=False, reset_camera=False)
        else:
            self.plotter.remove_actor(self.actors[4])
        
        if e_checked:
            color = self.netecolor.palette().color(QPalette.Background)
            rgb = color.name()
            self.actors[5] = self.plotter.add_mesh(self.meshes[5], color=rgb, show_scalar_bar=False, 
                                                   smooth_shading=True, pickable=False, reset_camera=False)
        else:
            self.plotter.remove_actor(self.actors[5])
         
    def add_scaled(self):
        checked = self.scaled_view.isChecked()
        self.scaled_options.toggle_button.setChecked(True)
        self.scaled_options.lock(not checked)
        if checked == True:
            
            if self.network_view.isChecked():
                self.network_view.setChecked(False)        
            self.actors[6] = self.plotter.add_mesh(self.meshes[6], scalars="Radius", show_scalar_bar=False, 
                                                   smooth_shading=True, pickable=False)
            self.actors[7] = self.plotter.add_mesh(self.meshes[7], scalars="Radius", show_scalar_bar=False, 
                                                   smooth_shading=True, pickable=False)
            self.toggle_legend()
            self.added_clim()
            
        else:
            if self.actors[6]:
                remove_legend(self.plotter, self.actors[6], False)
                self.plotter.remove_actor(self.actors[6])
                self.plotter.remove_actor(self.actors[7])
            if self.actors[8]:
                self.plotter.remove_actor(self.actors[8])
            if self.actors[9]:
                self.plotter.remove_actor(self.actors[9])   
    
    def scaled_bes(self):
        b_checked = self.scal_branches.isChecked()
        self.sbcolorcolumn.setVisible(b_checked)
    
        e_checked = self.scal_ends.isChecked()
        self.secolorcolumn.setVisible(e_checked)
        
        if b_checked:
            color = self.sbcolor.palette().color(QPalette.Background)
            rgb = color.name()
            self.actors[8] = self.plotter.add_mesh(self.meshes[8], color=rgb, show_scalar_bar=False, 
                                                   smooth_shading=True, pickable=False, reset_camera=False)
        else:
            self.plotter.remove_actor(self.actors[8])
        
        if e_checked:
            color = self.secolor.palette().color(QPalette.Background)
            rgb = color.name()
            self.actors[9] = self.plotter.add_mesh(self.meshes[9], color=rgb, show_scalar_bar=False, 
                                                   smooth_shading=True, pickable=False, reset_camera=False)
        else:
            self.plotter.remove_actor(self.actors[9])     

    def add_original(self):
        checked = self.original_view.isChecked()
        self.original_options.toggle_button.setChecked(True)
        self.original_options.lock(not checked)
        if checked == True:
            self.actors[0] = self.plotter.add_mesh(self.meshes[0], ambient=0.1, specular=0, diffuse=1, 
                                                   color='white', show_scalar_bar=False, pickable=False)
        else:
            if self.actors[0]:
                self.plotter.remove_actor(self.actors[0])
        
    def add_smoothed(self):
        checked = self.smoothed_view.isChecked()
        self.smoothed_options.toggle_button.setChecked(True)
        self.smoothed_options.lock(not checked)
        if self.smoothed_view.isChecked() == True:
            self.actors[1] = self.plotter.add_mesh(self.meshes[1], show_scalar_bar=False, pickable=False)
        else:
            if self.actors[1]:
                self.plotter.remove_actor(self.actors[1])        
        
            
    def visualization_popup(self):        
        # Connect our thread
        self.build_thread = bep.VisualizationThread()
        
        popup = QDialog()
        popuplayout = QVBoxLayout(popup)
        popuplayout.setContentsMargins(10,0,10,10)
        popup.setFixedSize(400,300)
        popup.setWindowFlags(popup.windowFlags() | Qt.WindowCloseButtonHint)
        
        msgbox = QWidget()
        msgboxlayout = QVBoxLayout(msgbox)
        msgboxlayout.setSpacing(0)

        ### Add our widgets
        ## Top widgets
        top = QWidget()
        toplayout = QHBoxLayout(top)
        toplayout.setSpacing(0)
        toplayout.setContentsMargins(0,0,0,0)
        
        # Top Left
        topleft = QWidget()
        topleftlayout = QVBoxLayout(topleft)
        
        # Options Box
        self.vis_options = QGroupBox("Mesh Generation")
        optionslayout = QVBoxLayout(self.vis_options)
        
        self.tubes = QCheckBox("Tube Mesh")
        self.tubes.setChecked(True)
        self.volume = QCheckBox("Volume Mesh")
        
        # Resolution Widget
        resolution_header = QLabel("Image Resolution:")
        self.set_visresolution = QDoubleSpinBox()
        self.set_visresolution.setSuffix(" unit/voxel")
        self.set_visresolution.setAlignment(Qt.AlignCenter)
        self.set_visresolution.setValue(1.0)
        self.set_visresolution.setFixedWidth(150)
        
        optionslayout.addWidget(self.tubes)
        optionslayout.addWidget(self.volume)
        optionslayout.addSpacing(5)
        optionslayout.addWidget(resolution_header)
        optionslayout.addWidget(self.set_visresolution)
        optionslayout.addStretch(0)
        
        
        # Add widgets to top left
        topleftlayout.addStretch(0)
        topleftlayout.addSpacing(10)
        topleftlayout.addWidget(self.vis_options, alignment=Qt.AlignCenter)
        topleftlayout.addStretch(0)
                
        # Top Right
        topright = QWidget()
        toprightlayout = QVBoxLayout(topright)
        toprightlayout.setSpacing(5)
        self.name_label = QLabel("Loaded File:")
        self.basename = QLineEdit()
        self.basename.setText(path.basename(self.queued_file))
        self.basename.setReadOnly(True)
        self.basename.setAlignment(Qt.AlignCenter)
        
        # Visualize button
        self.visualize_button = QPushButton("Render")
        self.visualize_button.setFixedWidth(100)
        self.visualize_button.clicked.connect(self.start_vis_thread)
        
        # Cancel button
        self.vis_cancel = QPushButton("Cancel")
        self.vis_cancel.setFixedWidth(100)
        self.vis_cancel.setDisabled(True)
        self.vis_cancel.clicked.connect(self.cancel_vis)
        
        toprightlayout.addStretch(0)
        toprightlayout.addWidget(self.name_label, alignment=Qt.AlignCenter)
        toprightlayout.addWidget(self.basename, alignment=Qt.AlignCenter)
        toprightlayout.addSpacing(5)
        toprightlayout.addWidget(self.visualize_button, alignment=Qt.AlignCenter)
        toprightlayout.addSpacing(5)
        toprightlayout.addWidget(self.vis_cancel, alignment=Qt.AlignCenter)
        toprightlayout.addStretch(0)
        
        # Add widgets to top.
        toplayout.addWidget(topleft)
        toplayout.addWidget(topright)
        
        ## Middle row - filters
        middle = QFrame()
        middlelayout = QVBoxLayout(middle)
        eliminate_spacing(middlelayout)
        # Literally a copy/paste from Page1.
        # Didn't have time to setup classes for each of these. Oh well.
        filter_row = QWidget()
        filter_rowlayout = QHBoxLayout(filter_row)
        eliminate_spacing(filter_rowlayout)
        
        # Remove isolated segments
        self.filter_check = QCheckBox("Filter isolated segments shorter than: ")
        self.filter_check.setChecked(True)
        self.filter_length = QDoubleSpinBox()
        self.filter_length.setDecimals(1)
        self.filter_length.setValue(5)
        self.filter_length.setMinimum(2)
        self.filter_length.setSuffix(" µm")
        self.filter_length.setAlignment(Qt.AlignCenter)
        self.filter_length.setFixedWidth(80)
        self.filter_check.toggled.connect(self.filter_length.setEnabled)
        
        filter_rowlayout.addWidget(self.filter_check)
        filter_rowlayout.addSpacing(17)
        filter_rowlayout.addWidget(self.filter_length)
        filter_rowlayout.addStretch(0)
        
        # Prune endpoint segments
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
        
        middlelayout.addWidget(filter_row)
        middlelayout.addWidget(prune_row)              
        
        ## Bottom widget
        bottom = QWidget()
        bottomlayout = QVBoxLayout(bottom)
        bottomlayout.setSpacing(5)
        bottomlayout.setContentsMargins(0,0,0,10)
        self.progressbar = QProgressBar()
        self.progressbar_label = QLabel("Please select visualization options.")
        
        bottomlayout.addWidget(self.progressbar)
        bottomlayout.addWidget(self.progressbar_label, alignment=Qt.AlignCenter)
        
        
        msgboxlayout.addWidget(top)
        msgboxlayout.addWidget(middle)
        msgboxlayout.addWidget(bottom)
        
        # Add buttons to our messagebox      
        popuplayout.addWidget(msgbox)  
        popup.finished.connect(self.dialogue_closed)
        popup.exec()
        
    def dialogue_closed(self):
        self.cancel_vis(closed=True)
    
    def vis_update_progress(self, update):
        self.progressbar_label.setText(update)
        
    def vis_update_progressbar(self, number):
        self.progressbar.setValue(number)
                
    def vis_button_lock(self, state):
        if state == 0:
            self.visualize_button.setDisabled(True)    
            self.vis_cancel.setEnabled(True)
            self.vis_options.setDisabled(True)
        if state == 1:
            self.vis_cancel.setDisabled(True)
        
    def start_vis_thread(self):
        
        if self.tubes.isChecked() or self.volume.isChecked():            
            # Load file into our thread.
            # Because I build the popup after init, I just load the options in here manually.
            self.build_thread.load_options(self.queued_file, self.tubes, self.volume, 
                                           self.set_visresolution.value(), 
                                           self.filter_check.isChecked(), self.filter_length.value(), 
                                           self.prune_check.isChecked(), self.prune_length.value())
            
            # Connect our thread to our progress info.
            self.build_thread.button_lock.connect(self.vis_button_lock)
            self.build_thread.progress_int.connect(self.vis_update_progressbar)
            self.build_thread.build_stage.connect(self.vis_update_progress)
            self.build_thread.finished.connect(self.load_meshes)
            
            self.build_thread.start()

        else:
            message = "<b> At least one mesh must be generated</b>"
            self.update_progress(message)        
    
    def cancel_vis(self, closed=False):
        # self.vis_cancel.setDisabled(True)
        self.build_thread.stop(closed)
     