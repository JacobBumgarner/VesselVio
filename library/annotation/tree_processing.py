"""Annotation file io and processing."""

__author__ = "Jacob Bumgarner <jrbumgarner@mix.wvu.edu>"
__license__ = "GPLv3 - GNU General Pulic License v3 (see LICENSE)"
__copyright__ = "Copyright 2022 by Jacob Bumgarner"
__webpage__ = "https://jacobbumgarner.github.io/VesselVio/"
__download__ = "https://jacobbumgarner.github.io/VesselVio/Downloads"


import json
import os
import typing

from library import helpers


class JSON_Options:
    """Options class carrying keys for loading JSON annotation trees.

    Parameters:
    name : str
        The key that points to the name of the region.
    children : str
        The key that points to the name of the region's children.
    color : str
        They key that points to the hex-based color of the region.
    id : str
        The key that points to the int-based id of the region.
    """

    def __init__(
        self, name="name", children="children", color="color_hex_triplet", id="id"
    ):
        """Build the options class."""
        self.name = name
        self.children = children
        self.id = id
        self.color = color


def load_annotation_file(file: str) -> dict:
    """Load a VesselVio Annotation file.

    Parameters:
    file : str

    Returns:
    dict : annotation_data
        A tree structure dict containing the name, color, id, and children of
        each region.
    """
    with open(file) as f:
        annotation_data = json.load(f)["VesselVio Annotations"]
    return annotation_data


def find_children(sub_tree, ids, colors, tree_keys) -> typing.Tuple[list, list]:
    """Identify the hex colors and ids of the input parent region.

    Recursively index through the children of the parent region and their
    children to find all of the hex colors and ids associated with the parent
    region.

    Parameters:
    sub_tree : list
        A list that contains the dict information of the children regions. The
        list may be empty.

    colors : list
        A single list containing all of the related colors.

    ids : list
        A single list containing all of the related ids.

    tree_keys : JSON_Options

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
    """Return the family of the input annotation region.

    Parameters:
    annotation_tree : list
        A list of dicts, where each dict is a region with the associated
        information.

    region_name : str
        The name of the region whose family will be found.

    tree_keys : JSON_Options

    Returns:
    dict
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
    """Convert a list of names into a VesselVio annotation list.

    Given an annotation tree and a list of region names, identify the ids and
    colors associated with each of the regions.

    Parameters:
    regions : list

    annotation_file : str, optional
        The filepath to the annotation tree. The tree must contain a
        'root' parent. Defaults to the ``"p56 Mouse Brain.json"`` file from
        the Allen Institute.

    tree_keys : JSON_Options, optional
        The keys to find the id, name, color, and children of each region in the
        annotation file. Default ``JSON_Options()``

    Returns:
    dict : annotation_info
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


################################################################################
def RGB_duplicates_check(annotation_data) -> bool:
    """Determine whether duplicate colors exist among annotation regions.

    For RGB processing, it is important to determine whether individual regions
    share the same color coded values. For example, in the hippocampal formation
    of mice, the Allen Brain Atlas color coding scheme uses both ``"7ED04B"``
    and ``"66A83D"`` for the Ammon's Horn and Dentate Gyrus regions. If both
    regions were selected for separate analyses, the results would include
    vessels from both regions.

    Parameters:
    annotation_data : dict
        A dict output of the `Annotation Processing` export that has been pre-
        processed using `prep_RGB_annotation`.

    Returns:
    bool : True if duplicates present, False otherwise
    """
    nested_hexes = [annotation_data[key]["colors"] for key in annotation_data.keys()]
    hexes = [color for nested_colors in nested_hexes for color in nested_colors]

    duplicates = len(hexes) != len(set(hexes))
    return duplicates
