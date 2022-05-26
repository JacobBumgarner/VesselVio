import os
import sys

import pytest

sys.path.insert(1, "/Users/jacobbumgarner/Documents/GitHub/VesselVio")

import numpy as np

from library import annotation_processing as AnnProc
from library.annotation import tree_processing

# from skimage.io import imread

THIS_PATH = os.path.realpath(__file__)
FIXTURE_DIR = os.path.join(os.path.dirname(THIS_PATH), "test_files")
ANNOTATION_DIR = os.path.join(FIXTURE_DIR, "annotation_data")


@pytest.mark.datafiles(ANNOTATION_DIR)
def test_convert_hex_to_int_tree(datafiles):
    annotation_dict = tree_processing.load_annotation_file(
        os.path.join(datafiles, "Cortex Unique.json")
    )
    hex_ROIs = [annotation_dict[key]["colors"] for key in annotation_dict.keys()]
    int_ROIs = AnnProc.convert_hex_list_to_int(hex_ROIs)
    assert len(int_ROIs) == 6
    assert len(int_ROIs[0]) == 1
    assert isinstance(int_ROIs[0][0], int)


@pytest.mark.datafiles(ANNOTATION_DIR)
def test_build_ROI_array(datafiles):
    annotation_dict = tree_processing.load_annotation_file(
        os.path.join(datafiles, "Cortex Unique.json")
    )

    # ID Check
    ROI_array = AnnProc.build_ROI_array(annotation_dict, annotation_type="ID")
    assert ROI_array.shape == (6, 78)
    assert np.issubdtype(ROI_array.dtype, np.uint32)

    # RGB Check
    ROI_array = AnnProc.build_ROI_array(annotation_dict, annotation_type="RGB")
    assert ROI_array.shape == (6, 2)
    assert np.issubdtype(ROI_array.dtype, np.uint32)
    print(ROI_array)
    return


def test_build_minima_maxima_arrays():
    volume = np.zeros((5, 10, 10))
    ROI_array = np.zeros((10, 5))

    minima, maxima = AnnProc.build_minima_maxima_arrays(volume, ROI_array)
    assert minima.shape == (ROI_array.shape[0], 3)
    assert maxima.shape == (ROI_array.shape[0], 3)

    assert np.all(minima[0] == volume.shape)
    assert np.all(maxima[0] == (0, 0, 0))

    return


@pytest.mark.datafiles(ANNOTATION_DIR)
def test_RGB_duplicates_check(datafiles):
    unique_annotation_data = tree_processing.load_annotation_file(
        os.path.join(datafiles, "Cortex Unique.json")
    )
    assert AnnProc.RGB_duplicates_check(unique_annotation_data) is False

    duplicate_annotation_data = tree_processing.load_annotation_file(
        os.path.join(datafiles, "HPF Duplicates.json")
    )
    assert AnnProc.RGB_duplicates_check(duplicate_annotation_data) is True
    return
