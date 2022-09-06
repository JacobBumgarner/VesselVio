"""
Input classes used to carry options for the analysis of datasets.
"""

from dataclasses import dataclass
from typing import Union

import numpy as np


@dataclass
class AnalysisOptions:
    """The dataclass that carries the options for a volume-based vasculature analysis.

    Parameters
    ----------
    results_folder : str
        The path to the export for the results folder.
    resolution : float, list, tuple, np.ndarray
        The resolution of the input dataset. The resolution can be a single value for
        isotropic datasets, or an (3,) shaped list, tuple, or np.ndarray of the XYZ
        dimensions for anisotropic volumes.
    prune_length : float, optional
        The length of endpoint vessels that will be pruned from the vascular network.
        Vessels less than or equal to the prune length are removed from the analysis.
        Default is 5.
    filter_length : float, optional
        The length of isolated vessels that will be filtered from the dataset.
        Vessels less than or equal to the filter length are removed prior to analysis.
        Default is 10.
    image_dimensionality : int, optional
        The dimensionality of the dataset that will be analyzed. Should be either 3 or
        2. Default is 3.
    save_segment_results : bool, optional
        Whether to save the features about individual segments as a extra CSV file for
        each input dataset. Default is False.
    save_graph_file : bool, optional
        Whether to save a GraphML file of the reconstructed vascular network. Default
        is False.
    """

    results_folder: str
    resolution: Union[float, list, tuple, np.ndarray]
    prune_length: float = 5
    filter_length: float = 10
    image_dimensionality: int = 3
    save_segment_results: bool = False
    save_graph_file: bool = False


@dataclass
class GraphAttributeKey:
    """The class containing the keys used to identify attributes of an input graph."""

    vertex_x_pos: str
    vertex_y_pos: str
    vertex_z_pos: str
    vertex_radius: str
    edge_radius: str
    edge_length: str
    edge_volume: str
    edge_surface_area: str
    edge_tortuosity: str
    edge_source: str
    edge_target: str
    edge_hex_color: str = None


@dataclass
class GraphAnalysisOptions:
    """The class containing options used to analyze an input graph.

    Parameters:
    file_format : str
        The file format of the input graph. Default "GraphML".

    graph_type : str
        The type of the input graph. Indicates what the edges represent. Must be either
        "Branches" or "Centerlines". Default "Branches".

    filter_cliques : bool
        Default False.

    smooth_centerlines : bool
        Default False.

    attribute_key : GraphAttributeKey

    csv_delimiter : str
        Default ``None``.
    """

    file_format: str = "GraphML"
    graph_type: str = "Branches"
    filter_cliques: bool = False
    smooth_centerlines: bool = False
    attribute_key: "GraphAttributeKey" = None
    csv_delimiter: str = None
