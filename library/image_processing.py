"""
Image loading and processing.
"""

__author__    = 'Jacob Bumgarner <jrbumgarner@mix.wvu.edu>'
__license__   = 'GPLv3 - GNU General Pulic License v3 (see LICENSE)'
__copyright__ = 'Copyright 2022 by Jacob Bumgarner'
__webpage__   = 'https://jacobbumgarner.github.io/VesselVio/'
__download__  = 'https://jacobbumgarner.github.io/VesselVio/Downloads'


import os
import numpy as np
from time import perf_counter as pf

# Image processing
from pathlib import Path
from skimage.io import imread
import cv2
import nibabel


from library import helpers

## Global min_resolution variable
min_resolution = 1

########################
#### Volume Loading ####
########################
## Returns a true binary (0,1) array from an image file when given the file name and directory.
def load_volume(file, verbose=False):
    t1 = pf()
    
    # Only use .nii files for annotations, this is mainly due to loading speeds
    if helpers.get_ext(file) == '.nii':
        try:
            volume = load_nii_volume(file)
        except:
            volume = SITK_load(file)
    else:
        volume = SITK_load(file)
    
    if volume is None or volume.ndim not in (2,3):
        return None
    
    if verbose:
        print (f"Volume loaded in {pf() - t1:.2f} s.")
    
    return volume, volume.shape

# Load nifti files
def load_nii_volume(file):
    proxy = nibabel.load(file)
    data = proxy.dataobj.get_unscaled().transpose()
    # data = np.asarray(proxy.dataobj, dtype=np.float32).transpose()
    if data.ndim == 4:
        data = data[0]
    return data
 
# Load an image volume using SITK, return None upon read failure
def SITK_load(file):
    try:
        volume = imread(file).astype(np.uint8)
    except:
        volume = None
    return volume

# Reshape 2D array to make it compatible with analysis pipeline
def reshape_2D(points, volume, verbose=False):
    if verbose:
        print ('Re-constructing arrays...', end='\r')
    points = np.pad(points, ((0,0), (1,0)))
    zeros = np.zeros(volume.shape) # Pad zeros onto back of array 
    volume = np.stack([volume, zeros])
    image_shape = volume.shape
    return points, volume, image_shape   
   
# Confirm that the volume was either loaded or segmented properly
def volume_check(volume, loading=False, verbose=False):
    if volume is None:
        return False
        
    elif not loading and not np.any(volume):
        return False
    else:
        return True

# Returns file size in bytes
def check_file_size(file):
    size = os.path.getsize(file)
    return size
    
# Check to see if the dtype of a loaded proxy image is compatible with Numba.
def dtype_check(volume_prox):
    numba_compatible = True
    if (volume_prox.dtype == np.dtype('>f') or 
        volume_prox.dtype == np.dtype('>i')): # this is seems specific to ImageJ NIfTI export.
        numba_compatible = False
    elif not (np.issubdtype(volume_prox.dtype, np.floating) or
            np.issubdtype(volume_prox.dtype, np.integer)):
        numba_compatible = False
    return numba_compatible   
        
def prep_numba_compatability(volume):
    if not dtype_check(volume):
        volume = np.asarray(volume, dtype=np.uint8)
    return volume
    
    
####################################
### Annotation Volume Processing ###
####################################
# Get the annotation slice. Some 3D nifti files are saved in 4D rather than 3D (e.g., FIJI output)
def get_annotation_slice(a_prox, i):
    a_slice = a_prox[i].astype(np.float_)
    return a_slice
  
# Dimension check for ID annotated volumes, returns False if dimensions don't match.
def id_dim_check(proxy_an, vshape, verbose=False):
    ashape = proxy_an.shape
    if ashape != vshape:
        if verbose:
            print ("Annotation volume dimensions don't match dataset dimensions.")
        return False
    else:
        return True    
       
# Dimension check for RGB annotated volumes, returns True if dimensions don't match.
def RGB_dim_check(files, vshape, verbose=False):
    ex_im = cv2.imread(files[0])
    ex_shape = ex_im[..., 0].shape
    if len(files) != vshape[0] or ex_shape[0] != vshape[1] or ex_shape[1] != vshape[2]:
        if verbose:
            print ("Annotation volume dimensions don't match dataset dimensions.")
        return False
    else:
        return True  
  
def cache_labeled_volume(labeled_volume, verbose=False):
    if verbose:
        t = pf()
        print ("Saving cache of labeled volume...", end='\r')
        
    cache_path = helpers.get_volume_cache()
    np.save(cache_path, np.asarray(labeled_volume, dtype=np.uint8))
    # try:
    #     image = nibabel.Nifti1Image(np.ones([3,3,3]), affine=np.eye(4))
    #     nibabel.save(image, cache_path)
    #     image.uncache()
    # except:
    #     ??????????
    # WriteImage(GetImageFromArray(labeled_volume), cache_path)

    if verbose:
        print (f"Labeled volume caching complete in {pf() - t:0.2f} seconds.")
    return

def load_labeled_volume_cache():    
    labeled_cache = helpers.get_volume_cache()
    if os.path.exists(labeled_cache):
        labeled_volume = np.lib.format.open_memmap(labeled_cache, mode='r')
    else:
        labeled_volume = None
    return labeled_volume

def clear_labeled_cache():
    labeled_cache = helpers.get_volume_cache()
    if os.path.exists(labeled_cache):
        os.remove(labeled_cache)
    return


##########################
#### Image Processing ####
##########################
def prep_resolution(resolution):
    if type(resolution) != list:
        r = resolution
        resolution = np.array([r,r,r])
    else:
        resolution = np.flip(np.array(resolution))
    min_resolution = np.min(resolution)
    return resolution

# Get image files from a directory
# finds the first extension of the file in that dir
def dir_files(directory):
    extension = os.path.splitext(os.listdir(directory)[0])[1]
    files = sorted([str(file) for file in Path(directory).glob('*' + extension)])
    return files

def image_resizing(directory, output_size, ext):
    files = dir_files(directory, ext)
    
    for file in files:
        image = cv2.imread(file)
        image = cv2.resize(image, output_size, interpolation=cv2.INTER_NEAREST)
        cv2.imwrite(file, image)
    return

# Get file name
def get_filename(file_path):
    filename = os.path.splitext(os.path.basename(file_path))[0]
    return filename