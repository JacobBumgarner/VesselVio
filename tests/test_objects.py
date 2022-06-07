import sys

sys.path.insert(1, "/Users/jacobbumgarner/Documents/GitHub/VesselVio")

# import pytest
from library.objects.analysis_files import AnalysisFiles


def test_analysis_files():
    files = AnalysisFiles()
    test = ["1", "2", "3"]
    files.add_main_files(test)
    return
