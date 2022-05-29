import json
import os
import sys

sys.path.insert(1, "/Users/jacobbumgarner/Documents/GitHub/VesselVio")
import pytest

from library.annotation import tree_processing


THIS_PATH = os.path.realpath(__file__)
FIXTURE_DIR = os.path.join(os.path.dirname(THIS_PATH), "test_files")
ANNOTATION_DIR = os.path.join(FIXTURE_DIR, "annotation_data")


@pytest.fixture
def expected_data():
    ids = [
        3,
        11,
        18,
        25,
        34,
        43,
        49,
        57,
        65,
        624,
        1024,
        1032,
        1040,
        1055,
        1063,
        1071,
        1078,
        1087,
        1095,
        1103,
        1112,
        1119,
    ]
    colors = ["AAAAAA"]
    return {"ids": ids, "colors": colors}


def test_JSON_Options():
    default_options = tree_processing.JSON_Options()
    assert default_options.name == "name"
    assert default_options.children == "children"
    assert default_options.id == "id"
    assert default_options.color == "color_hex_triplet"


@pytest.mark.datafiles(ANNOTATION_DIR)
def test_load_annotation_file(datafiles):
    annotation_dict = tree_processing.load_annotation_file(
        os.path.join(datafiles, "Cortex Unique.json")
    )
    regions = [
        "Frontal pole, cerebral cortex",
        "Somatomotor areas",
        "Somatosensory areas",
        "Gustatory areas",
        "Visceral area",
        "Auditory areas",
    ]
    assert list(annotation_dict.keys()) == regions


@pytest.mark.datafiles(ANNOTATION_DIR)
def test_find_children(datafiles, expected_data):
    tree_file = os.path.join(datafiles, "p56 Mouse Brain.json")
    with open(tree_file, "r") as f:
        tree_data = json.load(f)
        tree = tree_data["children"]

    sub_tree = [key["children"] for key in tree if key["name"] == "grooves"][0]
    ids, colors = tree_processing.find_children(
        sub_tree, [], [], tree_processing.JSON_Options()
    )
    # add the parent id
    ids.append(1024)

    # compare to the expected results
    assert sorted(ids) == expected_data["ids"]
    assert list(set(colors)) == expected_data["colors"]


@pytest.mark.datafiles(ANNOTATION_DIR)
def test_find_family(datafiles, expected_data):
    tree_file = os.path.join(datafiles, "p56 Mouse Brain.json")
    with open(tree_file, "r") as f:
        tree_data = json.load(f)
        tree = tree_data["children"]

    family = tree_processing.find_family(
        tree, "grooves", tree_processing.JSON_Options()
    )

    assert family["colors"] == expected_data["colors"]
    assert sorted(family["ids"]) == expected_data["ids"]


def test_convert_annotation_data(expected_data):
    annotation_info = tree_processing.convert_annotation_data(["grooves"])

    assert list(annotation_info.keys()) == ["grooves"]
    assert sorted(annotation_info["grooves"]["ids"]) == expected_data["ids"]
    assert annotation_info["grooves"]["colors"] == expected_data["colors"]


@pytest.mark.datafiles(ANNOTATION_DIR)
def test_RGB_duplicates_check(datafiles):
    unique_annotation_data = tree_processing.load_annotation_file(
        os.path.join(datafiles, "Cortex Unique.json")
    )
    assert tree_processing.RGB_duplicates_check(unique_annotation_data) is False

    duplicate_annotation_data = tree_processing.load_annotation_file(
        os.path.join(datafiles, "HPF Duplicates.json")
    )
    assert tree_processing.RGB_duplicates_check(duplicate_annotation_data) is True
    return
