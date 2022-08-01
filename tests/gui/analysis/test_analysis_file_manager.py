# import os
# from pathlib import Path

# import pytest

# from library.objects.analysis_file_manager import AnalysisFileHandler


# THIS_PATH = Path(__file__).parent.absolute()
# FIXTURE_DIR = Path(*THIS_PATH.parts[: list(THIS_PATH.parts).index("tests") + 1])
# ANNOTATION_DIR = os.path.join(FIXTURE_DIR, "test_files", "annotation_data")


# def test_main_file_func():
#     files = AnalysisFileHandler()

#     test = ["1", "2", "3"]
#     files.add_main_files(test)
#     files.add_associated_files(test)

#     assert files.main_files == test
#     assert files.associated_files == test

#     files.associated_files.pop(0)
#     assert files.paired_files_check() is False

#     return


# annotation_check_test_data = [
#     ("p56 Mouse Brain.json", False),
#     ("Cortex Unique.json", True),
# ]


# @pytest.mark.parametrize("input_file, compatible", annotation_check_test_data)
# def test_JSON_loading(input_file, compatible):
#     files = AnalysisFileHandler()
#     data_file = os.path.join(ANNOTATION_DIR, input_file)
#     compatibility = files.add_annotation_JSON(data_file)
#     assert compatibility == compatible


# def test_file_removal():
#     files = AnalysisFileHandler()
#     test = ["1", "2", "3"]
#     files.add_main_files(test)
#     files.add_associated_files(test)

#     files.remove_main_files(1)
#     assert len(files.main_files) == 2
#     files.remove_main_files([0, 1])
#     assert len(files.main_files) == 0

#     files.remove_associated_files(1)
#     assert len(files.associated_files) == 2
#     files.remove_associated_files([0, 1])
#     assert len(files.associated_files) == 0


# def test_file_clearance():
#     files = AnalysisFileHandler()
#     test = ["1", "2", "3"]
#     files.add_main_files(test)
#     files.add_associated_files(test)
#     files.clear_all_files()

#     assert len(files.main_files) == 0
#     assert len(files.associated_files) == 0
#     assert files.annotation_data is None
#     return
