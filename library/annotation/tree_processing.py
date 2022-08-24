"""Annotation file io and processing."""

__author__ = "Jacob Bumgarner <jrbumgarner@mix.wvu.edu>"
__license__ = "GPLv3 - GNU General Pulic License v3 (see LICENSE)"
__copyright__ = "Copyright 2022 by Jacob Bumgarner"
__webpage__ = "https://jacobbumgarner.github.io/VesselVio/"
__download__ = "https://jacobbumgarner.github.io/VesselVio/Downloads"


import json
import os
from typing import Tuple

from library import helpers


class JSON_Options:
    """Options class carrying keys for loading JSON annotation trees.

    Parameters
    ----------
    name_key : str
        The key used in the JSON to point to the name of regions.
    children_key : str
        The key that points to the name of individual regions' children.
    color_key : str
        The key used to point to the color that is represented by each region.
    id_key : str
        The key used to point to the int or float ID that represents each region.
    """

    def __init__(
        self,
        name: str = "name",
        children: str = "children",
        color: str = "color_hex_triplet",
        id: str = "id",
    ):
        """Build the options class."""
        self.name = name
        self.children = children
        self.id = id
        self.color = color


def check_annotation_data_origin(filepath: str) -> bool:
    """Return whether the selected file is a VesselVio annotation data file.

    Parameters
    ----------
    filepath : str
        The filepath to the annotation data file. Should be a JSON, False returned if
        not.

    Returns
    -------
    bool
        Whether the file is a VesselVio annotation data file.
    """
    if not os.path.splitext(filepath)[0].lower() == ".json":
        return False

    with open(filepath) as f:
        annotation_data = json.load(f)
    return "VesselVio Annotations" in annotation_data.keys()


def load_vesselvio_annotation_file(file: str) -> dict:
    """Load a vesselvio annotation data file.

    Parameters
    ----------
    file : str
        The path pointing to the VesselVio annotation data file.

    Returns
    -------
    annotation_data : dict
        The annotation data file. Example return may be:
        ``{"Eye": {"colors": ["#190000"], "ids": [1]}}``
    """
    with open(file) as f:
        annotation_data = json.load(f)["VesselVio Annotations"]
    return annotation_data


def find_children(
    sub_tree: list, ids: list, colors: list, tree_keys: JSON_Options
) -> Tuple[list, list]:
    """Recursively identify the hex colors and ids of the children of a parent region.

    Recursively indexes through the children of the parent region and their
    children to find all of the hex colors and ids associated with the parent
    region.

    Parameters
    ----------
    sub_tree : list
        An list of all of the children of the parent ROI. Each of these elements will
        be a dictionary.
    colors : list
        An list of all of the children IDs of the parent ROI. The list may be empty.
    ids : list
        An list of all of the children colors of the parent ROI. The list may be empty.
    tree_keys : JSON_Options
        A JSON_Options class that carries the key information that points to the IDs,
        colors for the dict elements in the ``sub_tree` list.

    Returns
    -------
    ids : list
        An updated list of all of the children IDs of the parent ROI.
    colors : list
        An updated list of all of the children colors of the parent ROI.
    """
    for child in sub_tree:
        ids.append(child[tree_keys.id])
        colors.append(child[tree_keys.color])
        if child[tree_keys.children]:
            ids, colors = find_children(
                child[tree_keys.children], ids, colors, tree_keys
            )
    return ids, colors


def find_family(tree: list, region_name: str, tree_keys: JSON_Options) -> dict:
    """Return the family information of an input annotation region.

    Parameters
    ----------
    annotation_tree : list
        A list of dicts, where each dict is a region with the associated
        information. This dict typically comes from a tree annotation file, such as
        the Allen Intitute mouse brain tree.
    region_name : str
        The name of the region whose family will be found.
    tree_keys : JSON_Options
        A JSON_Options class that carries the key information that points to the IDs,
        colors for the dict elements in family.

    Returns
    -------
    family : dict
        A dict with two keys: [``"colors"``, ``"ids"``]. The items of the keys
        represent all of ids and colors of the family, including the parent's.

    """
    # iterate through the list of the children until the region_name is found
    for child in tree:
        if child[tree_keys.name] == region_name:
            # Get the id and colors of the parent
            ids = [child[tree_keys.id]]
            colors = [child[tree_keys.color]]
            ids, colors = find_children(
                child[tree_keys.children], ids, colors, tree_keys
            )
            colors = list(set(colors))  # Get set of unique colors
            return {"colors": colors, "ids": ids}
        elif child[tree_keys.children]:
            family = find_family(child[tree_keys.children], region_name, tree_keys)
            if family:
                return family
    return None


def convert_annotation_data(
    regions: list, annotation_file: str = None, tree_keys=None
) -> list:
    """Convert a list of names into a VesselVio annotation dictionary.

    Given an annotation tree and a list of region names, identify the ids and
    colors associated with each of the regions.

    Parameters
    ----------
    regions : list
        The regions to be extracted from the tree.
    annotation_file : str, optional
        The filepath to the annotation tree. The tree must contain a
        'root' parent. The default file is from the the Allen Institute, defaults to
        ``"p56 Mouse Brain.json"``.
    tree_keys : JSON_Options, optional
        The keys to find the id, name, color, and children of each region in the
        annotation file, defaults to ``JSON_Options()``

    Returns
    -------
    annotation_info : dict
        A dict where each key is the region name, and the time is a second
        dict containing the all of the family ids and colors of the parent
        region.
    """
    # Load the default file if there isn't one
    if not annotation_file:
        wd = helpers.get_cwd()
        annotation_file = helpers.std_path(
            os.path.join(
                wd, "library", "annotation", "annotation_trees", "p56 Mouse Brain.json"
            )
        )

    # Set up the JSON_Options object to know how to read the JSON file
    if not tree_keys:
        tree_keys = JSON_Options()

    # Load the annotation tree
    with open(annotation_file) as f:
        tree_data = json.load(f)
        tree = tree_data[tree_keys.children]  # Load all children of the root

    # Populate the annotation_info dict with the id/color information for each child
    # Assumes that tree has
    annotation_info = {}
    for region in regions:
        annotation_info[region] = find_family(tree, region, tree_keys)

    return annotation_info


###########
### RGB ###
###########
def RGB_duplicates_check(annotation_data: dict) -> bool:
    """Determine whether duplicate colors exist among annotation regions.

    For RGB processing, it is important to determine whether individual regions
    share the same color coded values. For example, in the hippocampal formation
    of mice, the Allen Brain Atlas color coding scheme uses both ``"7ED04B"``
    and ``"66A83D"`` for the Ammon's Horn and Dentate Gyrus regions. If both
    regions were selected for separate analyses, the results would include
    vessels from both regions.

    Parameters
    ----------
    annotation_data : dict
        A dictionary output of the `Annotation Processing` export that has been
        preprocessed using `prep_RGB_annotation`.

    Returns
    -------
    duplicates_present : bool
        True if duplicates present, False otherwise
    """
    nested_hexes = [annotation_data[key]["colors"] for key in annotation_data.keys()]
    hexes = [color for nested_colors in nested_hexes for color in nested_colors]

    duplicates_present = len(hexes) != len(set(hexes))
    return duplicates_present
