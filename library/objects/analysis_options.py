"""
Input classes used to carry options for the analysis of datasets.
"""

from dataclasses import dataclass


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
        The file format of the input graph. Default ``GraphML``.

    graph_type : str
        The type of the input graph. Indicates what the edges represent. Must be either
        ``"Branches"`` or ``"Centerlines"``. Default ``"Branches"``.

    filter_cliques : bool
        Default ``False``.

    smooth_centerlines : bool
        Default ``False``.

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
