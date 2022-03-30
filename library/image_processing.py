
"""
Image loading and processing.
"""


__author__    = 'Jacob Bumgarner <jrbumgarner@mix.wvu.edu>'
__license__   = 'GPLv3 - GNU General Pulic License v3 (see LICENSE)'
__copyright__ = 'Copyright 2022 by Jacob Bumgarner'
__webpage__   = 'https://jacobbumgarner.github.io/VesselVio/'
__download__  = 'https://jacobbumgarner.github.io/VesselVio/Downloads'


import sys, os
import numpy as np
from numba import njit, prange
from time import perf_counter as pf

# Image processing
from pathlib import Path
from SimpleITK import ReadImage, GetArrayFromImage, GetImageFromArray, WriteImage
from skimage.io import imread
import cv2
import nibabel

# Result Export
from pyexcelerate import Workbook

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
    
    if volume is None or volume.ndim not in [2,3]:
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
        image = ReadImage(file)
        volume = GetArrayFromImage(image)
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
   
   
# Get the sum of an ROI volume and correct it with the resolution.   
def get_ROI_volume(file, resolution):
    try:
        image = ReadImage(file)
    except:
        return None
    data = GetArrayFromImage(image)
    
    binary = data > 0
    dataset = binary * np.prod(resolution)
    result = np.sum(dataset)
    return result
    
    
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
        
        
def load_numba_compatible(volume):
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

# Get file name
def get_filename(file_path):
    filename = os.path.splitext(os.path.basename(file_path))[0]
    return filename

    
# Loads image series and combines them into a stack.
def stack_construction(file_dir, output_dir, sub_dir, old_ext='.bmp', new_ext='.nii'):
    # Save filename as the basename of the directory.
    filename = os.path.basename(file_dir)  
        
    # Get Path of dir/subfolder so we can use glob for the image names.
    if sub_dir:
        file_dir = Path(file_dir, sub_dir)
    else:
        file_dir = Path(file_dir)

    # Iterate through our folder to find files with our desired .ext
    files = dir_files(file_dir, old_ext)
    if not files:
        return
    
    # Open each image in the series and load it into the volume
    shape = list(GetArrayFromImage(ReadImage(files[0])).shape)
    shape.insert(0, len(files))
    volume = np.zeros(shape, dtype=np.uint8)
    for i, file in enumerate(files):
        image = GetArrayFromImage(ReadImage(file))
        volume[i] = image
         
    binary = volume > 0
    dataset = binary.astype(np.uint8)
    
    # Create the path for our new filename.
    filename = filename + new_ext
    filepath = os.path.join(output_dir, filename)
    
    # Write our image
    if dataset is not None:
        image = GetImageFromArray(dataset)
        WriteImage(image, filepath)
        return True
    else:
        return False
    
    
###########################
### __main__ Processing ### 
###########################
## Iterate through the directory input and send the subfolder off to be processed.
def sequencer_input(dir_path, output_dir, sub_dir=None, old_ext='.bmp', new_ext='.nii', verbose=False):
    start = pf()
    if os.path.exists(dir_path) == False:
        os.mkdir(dir_path)
    if os.path.exists(output_dir) == False:
        os.mkdir(output_dir)
    for folder in os.listdir(dir_path):
        folder_path = os.path.join(dir_path, folder)
        if os.path.isdir(folder_path):
            if verbose:
                print ("Processing:", folder_path)
                t1 = pf()
            result = stack_construction(folder_path, output_dir, sub_dir, old_ext, new_ext)
            if result:
                if verbose:
                    print (f"   Image series created in {pf() - t1:0.2f} seconds.")
            else:
                if verbose:
                    print ("No image series found in this folder.")
    if verbose:
        print (f"Series construction complete in {pf() - start:0.2f} seconds.")
    return    


## Calculate the volume of the ROIs for analysis corrections.
def ROIV_input(directory, results_dir, ext, resolution, verbose=False):
    results = []
    if type(resolution) != np.ndarray:
        resolution = np.array([resolution, resolution, resolution])
    # Iterate through the directory input and send the files off for volume calculation.
    for file in os.listdir(directory):
        if file.endswith(ext):
            filename = os.path.splitext(file)[0]
            file_path = os.path.join(directory, file)
            if verbose:
                print (f"Analyzing {filename}...")
            volume = get_ROI_volume(file_path, resolution)
            result = [filename, volume]
            results.append(result)
            if verbose:
                print (file, "analysis complete.")
    
    if os.path.exists(results_dir) == False:
        os.mkdir(results_dir)
    
    file_path = os.path.join(results_dir, os.path.basename(directory)+'.xlsx')
    print (file_path)
    
    wb = Workbook()
    ws = wb.new_sheet("Volumes", data=results)
    wb.save(file_path)
    
    return
    

######################
### Terminal Input ###
######################
if __name__ == "__main__":
    directory = ''
    results_directory = ''
    sub_directory = None
    old_ext = '.jpg'
    new_ext = '.nii'
    ext = '.nii'
    resolution = 2.7 # Either a float or an np.array
    output_dimensions = [1554, 1037] # [X,Y] dimensions
    
    # sequencer_input(directory, results_directory, sub_directory, old_ext, new_ext, verbose=True)
    ROIV_input(directory, results_directory, ext, resolution, verbose=True)
    # image_resizing(directory, output_dimensions, ext)
