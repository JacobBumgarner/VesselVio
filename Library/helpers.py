import sys, os
import platform
from os import path, environ, getcwd
import numpy as np


from pyvista.plotting.colors import hex_to_rgb
from matplotlib.cm import get_cmap
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QFileDialog
 
def eliminate_spacing(layout):
    layout.setContentsMargins(0,0,0,0)
    layout.setSpacing(0)

# Get our working directory.
def get_cwd():
    try:
        wd = sys._MEIPASS # Determines whether we're opening the file from a pyinstaller exec.
    except AttributeError:
        wd = getcwd()
    return wd

def get_dir(location):
    sys_os = platform.system()
    if sys_os == "Darwin":
        load_dir = path.join(path.expanduser('~'), location) 
    elif sys_os == "Windows":
        load_dir = path.join(path.join(environ['USERPROFILE']), location) 

    return load_dir 

# Results/Screenshot directory functions
results_cachefile = 'Library/results_cache.txt'
wd = get_cwd()    
results_cache = path.join(wd, results_cachefile)

def load_results_dir():
    # Define our results path
    cache_file = open(results_cache, "r")
    results_dir = cache_file.read()
    cache_file.close()
    
    # Checks to see if our results pathway is present or if our results cache is empty.
    set_default = False
    if path.isdir(results_dir) == False or len(results_dir) == 0:
        set_default = True
        
    if set_default:
        results_dir = get_dir('Desktop/VesselVio')
        
    return results_dir

def set_results_dir(self):
    results_dir = QFileDialog.getExistingDirectory(self, "Select Results Folder")
    # Update view of our dir widget.
    cache_file = open(results_cache, "w")
    cache_file.write(results_dir)
    cache_file.close()
    return results_dir

# Visualization Helpers 
def get_rgb(hex):
      return hex_to_rgb(hex) # Placed this in helps to avoid importing another thing into the main window.
   
def prep_opacity_update(p2):
    ids = [None] * 4
    
    return ids
    
def prep_scalars_update(p2):
    if p2.network_view.isChecked():
        ids = [2, 3]
        scalars_choice = p2.network_scalar.currentText()
        cmap_choice = p2.network_scalar_theme.currentText().lower()
    elif p2.scaled_view.isChecked():
        ids = [6, 7]
        scalars_choice = p2.scaled_scalar.currentText()
        cmap_choice = p2.scaled_scalar_theme.currentText().lower()
        
    cmap = get_cmap(cmap_choice)
    ctable = cmap(np.linspace(0, 1, 256))*255
    ctable = ctable.astype(np.uint8)
    return ids, scalars_choice, ctable, cmap_choice

# Stripped from pyvista==0.29.1. Was removed in the higher version for some reason
def remove_legend(plotter, actor, reset_camera=False, render=False):
    """Remove this actor's mapper from the given plotter's _scalar_bar_mappers."""
    try:
        mapper = actor.GetMapper()
    except AttributeError:
        return
    for name in list(plotter.scalar_bars._scalar_bar_mappers.keys()):
        try:
            plotter.scalar_bars._scalar_bar_mappers[name].remove(mapper)
        except ValueError:
            pass
        
        if len(plotter.scalar_bars._scalar_bar_mappers[name]) < 1:
            slot = plotter._scalar_bar_slot_lookup.pop(name, None)
            if slot is not None:
                plotter.scalar_bars._scalar_bar_mappers.pop(name)
                plotter.scalar_bars._scalar_bar_ranges.pop(name)
                plotter.remove_actor(plotter.scalar_bars._scalar_bar_actors.pop(name),
                                     reset_camera=reset_camera,
                                     render=render)
                plotter._scalar_bar_slots.add(slot)
    return