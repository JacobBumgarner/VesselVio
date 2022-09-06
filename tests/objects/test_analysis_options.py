import sys
from pathlib import Path

VESSELVIO_DIR = Path.cwd()
sys.path.insert(1, str(VESSELVIO_DIR))

import pytest

from library.objects import AnalysisOptions


def test_analysis_options_init():
    with pytest.raises(TypeError):
        options = AnalysisOptions()

    options = AnalysisOptions("results_path", 1)

    assert options.results_folder == "results_path"
    assert options.resolution == 1
    assert options.prune_length == 5
    assert options.filter_length == 10
    assert options.image_dimensionality == 3
    assert options.save_segment_results is False
    assert options.save_graph_file is False
