"""An object class that carries status updates"""

from dataclasses import dataclass


@dataclass
class StatusUpdate:
    """A simple object used to carry the file analysis status to the main thread.

    Parameters
    ----------
    analysis_status : str
        The update of the analysis progress passed as a string. E.g., "Skeletonizing..."
    analysis_progress : float, optional
        The percentage completion of the analysis. Ranges between 0-100. Default is 0.
    file_row : str, optional
        The row of the current file being analyzed. Default is 0.
    annotation_progress : str, optional
        A str containing the number of analyzed annotation regions. Default is None.
    """

    file_status: str
    analysis_progress: str = 0
    file_row: int = 0
    annotation_progress: str = None
