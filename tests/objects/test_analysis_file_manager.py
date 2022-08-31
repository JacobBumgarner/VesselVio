import sys
from pathlib import Path

VESSELVIO_DIR = Path.cwd()
sys.path.insert(1, str(VESSELVIO_DIR))

import os

import pytest

from library.objects import AnalysisFileManager


THIS_PATH = Path(__file__).parent.absolute()
FIXTURE_DIR = Path(*THIS_PATH.parts[: list(THIS_PATH.parts).index("tests") + 1])
ANNOTATION_DIR = os.path.join(FIXTURE_DIR, "test_files", "annotation_data")


@pytest.fixture
def file_manager():
    manager = AnalysisFileManager()
    return manager


def test_analysis_file_manager_init(file_manager):
    assert len(file_manager.main_files) == 0
    assert len(file_manager.associated_files) == 0
    assert file_manager.annotation_data is None
    assert file_manager.analyzed is False

    return


def test_main_files(file_manager):
    files = ["a.csv", "b.csv", "c.csv"]
    file_manager.add_main_files(files)

    assert len(file_manager.main_files) == 3
    assert file_manager.main_files == files

    file_manager.remove_main_files(0)
    assert file_manager.main_files == files[1:]

    return


def test_associated_files(file_manager):
    files = ["a.csv", "b.csv", "c.csv"]
    file_manager.add_associated_files(files)

    assert len(file_manager.associated_files) == 3
    assert file_manager.associated_files == files

    file_manager.remove_associated_files(0)
    assert file_manager.associated_files == files[1:]

    return


@pytest.mark.datafiles(ANNOTATION_DIR)
def test_annotation(datafiles, file_manager):
    compatible = os.path.join(datafiles, "Cortex Unique.json")
    incompatible = os.path.join(datafiles, "p56 Mouse Brain.json")

    added = file_manager.add_annotation_JSON(incompatible)
    assert added is False
    assert file_manager.annotation_data is None

    added = file_manager.add_annotation_JSON(compatible)
    assert added is True
    assert isinstance(file_manager.annotation_data, dict)

    file_manager.clear_annotation_data()
    assert file_manager.annotation_data is None


def test_clear_files(file_manager):
    main_files = ["a.csv", "b.csv"]
    associated_files = ["c.csv", "d.csv"]

    file_manager.add_main_files(main_files)
    file_manager.add_associated_files(associated_files)

    # Make sure the files were loaded
    assert file_manager.main_files
    assert file_manager.associated_files

    # Clear them
    file_manager.clear_analysis_files()
    assert len(file_manager.main_files) == 0
    assert len(file_manager.associated_files) == 0

    # Clear all
    file_manager.add_main_files(main_files)
    file_manager.annotation_data = {"test": "data"}

    file_manager.clear_all_files()
    assert len(file_manager.main_files) == 0
    assert len(file_manager.associated_files) == 0
    assert file_manager.annotation_data is None
