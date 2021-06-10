# -*- coding: utf-8 -*-
"""
Created on Tue Mar  2 15:03:10 2021

@author: jacobbumgarner
"""


from os import path, getcwd
import time
import numpy as np

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (QWidget, QDialogButtonBox, QPushButton,
                             QLabel, QHBoxLayout, QCheckBox,
                             QGroupBox, QLineEdit, QDoubleSpinBox,
                             QVBoxLayout, QProgressBar)

from Library import Image_Processing as improc
from Library import Volume_Processing as volproc
from Library import Graph_Processing as gproc
from Library import Volume_Visualization as volvis
from Library import Feature_Extraction as feats 
from Library.Radii_Corrections import load_corrections

resolution = 2.7
max_radius = 250


###############################
########## App Code ###########
###############################

class AnalysisThread(QThread):
    button_lock = pyqtSignal(int)
    selection_signal = pyqtSignal(int)
    analysis_stage = pyqtSignal(list)
    
    def __init__(self,  parent=None):
        QThread.__init__(self, parent)
        self.running = False    
    
    def load_ex(self, Page1):
        # Analysis options
        self.resolution = Page1.set_resolution.value()
        self.maximum_radius = Page1.max_radius.value()
        if Page1.filter_check.isChecked():
            self.segment_filter = Page1.filter_length.value() + 1 # +1 because of lt not le. Assumes 2 verts have 1 unit distance
        else:
            self.segment_filter = 2
        if Page1.prune_check.isChecked():
            self.prune_filter = Page1.prune_length.value()
        else:
            self.prune_filter = 0
            
        # Save options
        self.save_seg_results = Page1.seg_results.isChecked()
        self.save_graph_files = Page1.save_graphs.isChecked()
        self.files = Page1.files
        self.results_folder = Page1.results_path_location.text()
    
    def run(self):
        self.running = True
        self.button_lock.emit(1)
        
        main_results = []
        seg_results = []
        
        for i in range(len(self.files)):
            if self.running == False:
                self.analysis_stage.emit(["Cancelled.", i])
                continue
            t1 = time.perf_counter()
            self.selection_signal.emit(i)            
            self.analysis_stage.emit(["Loading File...", i])
            
            ### Analyze File ###
            filename = self.files[i]
            
            ## Image and volume processing.
            # Get array from the file image.
            # Continue through loop if file extension isn't compatable.
            volume = improc.getArray(filename)
            if volume is None:
                self.analysis_stage.emit(["Unable to Analyze.", i])
                continue

            
            # Skeletonize, then find radii of skeleton points
            self.analysis_stage.emit(["Skeletonizing...", i])
            skeleton, points = volproc.skeletonize(volume)
            self.analysis_stage.emit(["Calculating Radii...", i])
            LUT = load_corrections(resolution, self.maximum_radius)
            skeleton_radii = volproc.calculate_radii(volume, skeleton, points, LUT, self.resolution, max_radius)
            del(LUT)
            
            # Once radii have been calculated for 2D volumes, we can treat them 2D images as 3D arrays for compatability with the rest of our pipeline.
            if volume.ndim == 2:
                zeros = np.zeros(volume.shape)
                volume = np.dstack([volume, zeros])
                skeleton = np.dstack([skeleton, zeros])
                skeleton = np.dstack([zeros, skeleton])
                points = np.asarray(np.where(skeleton == 1))
                points = np.reshape(points, (-1), order = 'F')
                length = int(len(points) / 3)
                points = np.reshape(points, (length, 3))            
            
            ## Network creation and analysis.
            # Send information to graph network creation.
            self.analysis_stage.emit(["Building Network...", i])
            graph = gproc.create_graph(skeleton, skeleton_radii, points, self.resolution, self.prune_filter)
            
            # Take extracted centerlines and remove filtered segments from our volume dataset.
            volume = volproc.clean_volume(graph, volume, 
                                              self.segment_filter, self.resolution)
                            
            # Finally, extract relevant features from our graph.
            self.analysis_stage.emit(["Analyzing Network...", i])
            if not self.save_seg_results:
                single_result = feats.features(graph, volume, self.resolution, filename, self.save_seg_results)
                main_results.append(single_result)
            else:
                single_result, single_seg_results = feats.features(graph, volume, self.resolution, filename, self.save_seg_results)
                main_results.append(single_result)
                seg_results.append(single_seg_results)


            # Check to see if graph save was requested.
            self.analysis_stage.emit(["Saving Graph...", i])
            if self.save_graph_files:
                gproc.save_graph(graph, points, filename, self.results_folder)
            
            # Send completion announcement.
            seconds = '%.2f' % (time.perf_counter() - t1)
            concluding_remark = "Analyzed in " + seconds + " s."
            self.analysis_stage.emit([concluding_remark, i])
            
            # Just to keep things clean.
            del(graph)
            del(volume)
        
        if self.running:
            if not self.save_seg_results:
                feats.write_results(main_results, self.results_folder)
            else:
                feats.write_results(main_results, self.results_folder, seg_results)
            
        self.button_lock.emit(0)
        self.running = False
        # load_corrections(new_build=True) # Not sure if this is really a good idea...
        return 
    
    # Cancel option.
    def stop(self):
        self.running = False



  
class VisualizationThread(QThread):
    button_lock = pyqtSignal(int)
    progress_int = pyqtSignal(int)
    build_stage = pyqtSignal(str)
    
    def __init__(self):
        QThread.__init__(self)
        self.running = False
    
    def load_options(self, file, tubes, volume, resolution, filter_check, filter_length, prune_check, prune_length):
        # Vis options
        self.file = file
        self.tubes = tubes.isChecked()
        self.volume = volume.isChecked()
        self.meshes = [None]
    
        # Construction options
        self.resolution = resolution
        
        if filter_check:
            self.segment_filter = filter_length + 1 # +1 because of lt not le. Assumes 2 verts have 1 unit distance
        else:
            self.segment_filter = 2
        if prune_check:
            self.prune_filter = prune_length
        else:
            self.prune_filter = 0
        
    def run(self):
        # Start the build. Lock vis button and unlock cancel button.
        self.running = True 
        self.closed = False
        self.cancelled = False
        volume = None
        graph = None
        if self.running:   
            self.button_lock.emit(0)
            self.build_stage.emit("Loading File...")
        else:
            self.cancelled = True
            if not self.closed:
                self.build_stage.emit("Cancelled.")

        ### Analyze File ###
        filename = self.file
        
        ## Image and volume processing.
        # Get array from the file image.
        # Continue through loop if file extension isn't compatable.
        if self.running:
            volume = improc.getArray(filename)
        else:
            self.cancelled = True
            if not self.closed:
                self.build_stage.emit("Cancelled.")
        
        if volume is None:
            if self.running:
                self.build_stage.emit("Incompatible file...")
                return None
            else:
                self.cancelled = True
                if not self.closed:
                    self.build_stage.emit("Cancelled.")
                return None
        
        
        # Skeletonize, then find radii of skeleton points
        if self.running:
            self.progress_int.emit(10)
            self.build_stage.emit("Skeletonizing...")
            skeleton, points = volproc.skeletonize(volume)
            LUT = load_corrections(resolution, max_radius)
            skeleton_radii = volproc.calculate_radii(volume, skeleton, points, LUT, self.resolution, max_radius)
            del(LUT)
        else:
            self.cancelled = True
            if not self.closed:
                self.build_stage.emit("Cancelled.")
            
        # Once radii have been calculated for 2D volumes, treat them as 3D arrays for compatability with the rest of our pipeline.
        if volume.ndim == 2:
            zeros = np.zeros(volume.shape)
            volume = np.dstack([volume, zeros])
            skeleton = np.dstack([skeleton, zeros])
            skeleton = np.dstack([zeros, skeleton])
            points = np.asarray(np.where(skeleton == 1))
            points = np.reshape(points, (-1), order = 'F')
            length = int(len(points) / 3)
            points = np.reshape(points, (length, 3))
        
        ## Network creation and analysis.
        # Send information to graph network creation.
        if self.running:
            self.progress_int.emit(30)
            self.build_stage.emit("Building Network...")
            graph = gproc.create_graph(skeleton, skeleton_radii, points, 
                                       self.resolution, self.prune_filter)
        else:
            self.cancelled = True
            if not self.closed:
                self.build_stage.emit("Cancelled.")
        
        # Take extracted centerlines and remove filtered segments from our volume dataset.
        if self.running:
            self.progress_int.emit(50)
            self.build_stage.emit("Processing Network...")
            volume = volproc.clean_volume(graph, volume,
                                          self.segment_filter, self.resolution)
        else:
            self.cancelled = True
            if not self.closed:
                self.build_stage.emit("Cancelled.")
        
        # Finally, build the visualization components of our graph relevant features from our graph.
        if self.running:
            self.build_stage.emit("Building Mesh...")
            self.progress_int.emit(70)
            self.meshes = volvis.generate(graph, volume, self.resolution, 
                                          app=True, gen_tubes=self.tubes, 
                                          gen_volume=self.volume)
                        
        else:
            self.cancelled = True
            if not self.closed:  
                self.build_stage.emit("Cancelled.")
        
        # Finish up the process.
        if self.running:
            self.build_stage.emit("Mesh Construction Complete.")
            self.progress_int.emit(100)
            # Lock our cancel button.
            self.running = False
            self.button_lock.emit(1)
        else:
            self.cancelled = True
            
        
        # Just to keep things clean.
        if volume is not None:
            del(volume)
        if graph is not None:
            del(graph)
        return

    def load_meshes(self):
        if self.closed:
            return None
        if self.cancelled:
            return None
        return self.meshes
    
    def stop(self, closed=False):   
        self.closed = closed
        self.running = False

# This is for the init of the program. 
# Only purpose is to run a tiny dataset through to prime the JITs.
def process_file(file_path, Visualize=False, save_graph=False, verbose=False):
    if verbose:
        print ("Analyzing file:", file_path)

    tic = time.perf_counter()

    ## Image and volume processing.
    volume = improc.getArray(file_path)
    if volume is None:
        if verbose:
            print ("Couldn't analyze file.")
        return
        
    t1 = time.perf_counter()
    skeleton, points = volproc.skeletonize(volume)
    LUT = load_corrections(resolution, max_radius, verbose=verbose)
    skeleton_radii = volproc.calculate_radii(volume, skeleton, points, 
                                             LUT, resolution, max_radius)
    del(LUT) # Just for sanity
    if verbose:
        print (f"Radii identified in {time.perf_counter() - t1:0.2f} seconds.")
    
    if volume.ndim == 2:
        zeros = np.zeros(volume.shape)
        volume = np.dstack([volume, zeros])
        skeleton = np.dstack([skeleton, zeros])
        skeleton = np.dstack([zeros, skeleton])
        points = np.asarray(np.where(skeleton == 1))
        points = np.reshape(points, (-1), order = 'F')
        length = int(len(points) / 3)
        points = np.reshape(points, (length, 3))
        
    ## Network creation and analysis.
    t1 = time.perf_counter()
    graph = gproc.create_graph(skeleton, skeleton_radii, points, verbose, prune_length=0)
    
    volume = volproc.clean_volume(graph, volume)
    if verbose:
        print (f"Graph creation completed in {time.perf_counter() - t1:0.2f} seconds.")
    
    # Nothing past this point requires JITc.
 
    del(graph)
    del(volume)