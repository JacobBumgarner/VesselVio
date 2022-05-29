import os

import numpy as np

import pytest

from library import image_processing as ImProc
from library.annotation import labeling, segmentation_prep
from skimage.io import imread


THIS_PATH = os.path.realpath(__file__)
FIXTURE_DIR = os.path.join(os.path.dirname(THIS_PATH), "test_files")
ANNOTATION_DIR = os.path.join(FIXTURE_DIR, "annotation_data")


labeled_volume = imread(os.path.join(ANNOTATION_DIR, "test_labeled.nii"))
VOLUME = (labeled_volume > 0).astype(np.uint8)


# ROI array specific to the labeled_test.nii volume
@pytest.fixture
def prepped_data():
    id_roi_array = np.array([[1, 0], [2, 0]])
    rgb_roi_array = np.array([[255, 0], [65280, 0]])
    id_roi_dict, id_roi_keys = segmentation_prep.prep_roi_array(id_roi_array)
    rgb_roi_dict, rgb_roi_keys = segmentation_prep.prep_roi_array(rgb_roi_array)
    roi_volumes, volume_updates = segmentation_prep.prep_volume_arrays(id_roi_array)
    minima = [(1, 3, 0), (2, 0, 0)]
    maxima = [(3, 4, 2), (4, 1, 4)]
    expected_volumes = [18, 30]
    expected_unique_values = [0, 1, 2]
    prepped = {
        "id_roi_array": id_roi_array,
        "rgb_roi_array": rgb_roi_array,
        "id_roi_dict": id_roi_dict,
        "id_roi_keys": id_roi_keys,
        "rgb_roi_dict": rgb_roi_dict,
        "rgb_roi_keys": rgb_roi_keys,
        "roi_volumes": roi_volumes,
        "volume_updates": volume_updates,
        "expected_minima": minima,
        "expected_maxima": maxima,
        "expected_volumes": expected_volumes,
        "expected_unique_values": expected_unique_values,
    }
    return prepped


def test_update_bounds():
    # don't parameterize, we want to keep the minima/maxima values
    minima = np.full((5, 3), 10)
    maxima = np.zeros((5, 3))

    points = [(1, 1, 1), (5, 5, 5)]
    checks = [[(1, 1, 1), (0, 0, 0)], [(1, 1, 1), (5, 5, 5)]]

    for i in range(2):
        labeling.update_bounds.py_func(minima, maxima, *points[i], 1)
        assert np.all(minima[1] == checks[i][0])
        assert np.all(maxima[1] == checks[i][1])


def test_label_slice(prepped_data):
    volume = VOLUME.copy()

    minima, maxima = segmentation_prep.build_minima_maxima_arrays(
        volume, prepped_data["id_roi_array"]
    )

    slice_volumes = prepped_data["roi_volumes"].copy()
    for z in range(5):
        volume, slice_volumes, minima, maxima = labeling.label_slice.py_func(
            volume,
            labeled_volume[z],
            slice_volumes,
            prepped_data["volume_updates"],
            prepped_data["id_roi_dict"],
            np.asarray(list(prepped_data["id_roi_keys"])),
            minima,
            maxima,
            z,
        )
        prepped_data["roi_volumes"] += slice_volumes
        slice_volumes *= 0

    assert np.all(prepped_data["roi_volumes"] == prepped_data["expected_volumes"])
    assert np.all(minima == prepped_data["expected_minima"])
    assert np.all(maxima == prepped_data["expected_maxima"])
    return


bgr_test_data = [
    (np.array([[255, 255, 255], [0, 0, 0]]), [16777215, 0], (2,)),
    (np.array([[[100, 100, 200]], [[0, 0, 1]]]), [[13132900], [65536]], (2, 1)),
]


@pytest.mark.parametrize("rgb_array, int_check, shape_check", bgr_test_data)
def test_convert_bgr_to_int(rgb_array, int_check, shape_check):
    int_array = labeling.convert_bgr_to_int.py_func(rgb_array)
    assert np.all(int_array == int_check)
    assert int_array.shape == shape_check
    return


@pytest.mark.datafiles(ANNOTATION_DIR)
def test_RGB_labeling_input(datafiles, prepped_data):
    volume = VOLUME.copy()

    rgb_folder = os.path.join(datafiles, "test_rgb_labeled")

    volume, roi_volumes, minima, maxima = labeling.RGB_labeling_input(
        volume, rgb_folder, prepped_data["rgb_roi_array"]
    )
    print(volume)
    assert np.all(np.unique(volume) == prepped_data["expected_unique_values"])
    assert volume.shape == (5, 5, 5)
    assert np.all(roi_volumes == prepped_data["expected_volumes"])
    assert np.all(minima == prepped_data["expected_minima"])
    assert np.all(maxima == prepped_data["expected_maxima"])
    return


@pytest.mark.datafiles(ANNOTATION_DIR)
def test_nn_id_labeling(datafiles, prepped_data):
    labeled_volume = ImProc.load_nii_volume(
        os.path.join(datafiles, "test_labeled_f4.nii")
    )
    volume = VOLUME.copy()

    volume, roi_volumes, minima, maxima = labeling.nn_id_labeling(
        volume, labeled_volume, prepped_data["id_roi_array"]
    )
    assert np.all(np.unique(volume) == prepped_data["expected_unique_values"])
    assert volume.shape == (5, 5, 5)
    assert np.all(roi_volumes == prepped_data["expected_volumes"])
    assert np.all(minima == prepped_data["expected_minima"])
    assert np.all(maxima == prepped_data["expected_maxima"])
    return


def test_numba_id_labeling(prepped_data):
    volume = VOLUME.copy()

    volume, roi_volumes, minima, maxima = labeling.numba_id_labeling.py_func(
        volume, labeled_volume, prepped_data["id_roi_array"]
    )
    assert np.all(np.unique(volume) == prepped_data["expected_unique_values"])
    assert volume.shape == (5, 5, 5)
    assert np.all(roi_volumes == prepped_data["expected_volumes"])
    assert np.all(minima == prepped_data["expected_minima"])
    assert np.all(maxima == prepped_data["expected_maxima"])
    return


id_annotation_test_files = [
    ("test_labeled.nii", False),
    ("test_labeled_f4.nii", False),
    ("test_labeled_wrong_size.nii", True),
]


@pytest.mark.parametrize(
    "annotation_file, empty_result_expected", id_annotation_test_files
)
def test_id_labeling_input(annotation_file, empty_result_expected, prepped_data):
    annotation_file = os.path.join(ANNOTATION_DIR, annotation_file)
    volume = VOLUME.copy()

    volume, roi_volumes, minima, maxima = labeling.id_labeling_input(
        volume, annotation_file, prepped_data["id_roi_array"]
    )

    if empty_result_expected:
        assert all(x is None for x in (volume, roi_volumes, minima, maxima))
    else:
        assert np.all(np.unique(volume) == prepped_data["expected_unique_values"])
        assert volume.shape == (5, 5, 5)
        assert np.all(roi_volumes == prepped_data["expected_volumes"])
        assert np.all(minima == prepped_data["expected_minima"])
        assert np.all(maxima == prepped_data["expected_maxima"])

    return


input_annotation_test_files = [
    ("test_labeled.nii", "ID", "id_roi_array"),
    ("test_rgb_labeled", "RGB", "rgb_roi_array"),
]


@pytest.mark.parametrize(
    "annotation_file, annotation_type, roi_array_key", input_annotation_test_files
)
def test_volume_labeling_input(
    tmpdir, prepped_data, annotation_file, annotation_type, roi_array_key
):
    volume = VOLUME.copy()

    annotation_file = os.path.join(ANNOTATION_DIR, annotation_file)
    roi_volumes, minima, maxima = labeling.volume_labeling_input(
        volume,
        annotation_file,
        prepped_data[roi_array_key],
        annotation_type,
        tmpdir,
    )

    # check output
    assert np.all(roi_volumes == prepped_data["expected_volumes"])
    assert np.all(minima == prepped_data["expected_minima"])
    assert np.all(maxima == prepped_data["expected_maxima"])

    # check cached volume
    cache_path = os.path.join(tmpdir, "labeled_volume.npy")
    assert os.path.exists(cache_path)
    labeled_volume = np.load(cache_path)
    assert labeled_volume.shape == (5, 5, 5)
    assert all(np.unique(labeled_volume) == prepped_data["expected_unique_values"])
    return
