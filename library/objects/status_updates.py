"""An object class that carries status updates"""


class StatusUpdate:
    """A simple object used to carry the file analysis status to the main thread.

    Parameters:
    analysis_status : str
        The text update of the analysis progress. E.g., "Skeletonizing..."

    analysis_progress : float, optional
        The percentage completion of the analysis. Ranges between 0-100. Default ``0``.

    file_row : str, optional
        The row of the current file being analyzed. Default ``0``.

    annotation_progress : str, optional
        A str containing the number of analyzed annotation regions. Default ``None``.
    """

    def __init__(
        self,
        analysis_status: str,
        analysis_progress: float = 0,
        file_row: int = 0,
        annotation_progress: str = None,
    ):
        """Create the status."""
        self.file_status = analysis_status
        self.analysis_progress = analysis_progress
        self.file_row = file_row
        self.annotation_progress = annotation_progress
