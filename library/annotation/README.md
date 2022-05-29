## VessselVio Annotation Processing

These functions handle everything related to annotation processing in VesselVio.

#### `tree_processing.py`
Handles tree loading, VesselVio annotation file i/o, and VesselVio annotation file processing

#### 'segmentation_prep.py'
Contains all of the functions used to prepare the segmentation and labeling processes.

### `labeling.py`
Contains all of the functions to label vasculature volumes with corresponding ID or RGB based annotation volumes.

You might be wondering why we don't just label the input volume with the annotation volume by multiplying the arrays.

Well, often users load annotation volumes that contain dozens or hundreds of annotations. But they might not be interested in analyzing every annotated region.

For example, the Allen Insitute `p56 mouse brain` atlas contains _hundreds_ of regions, but users might only want to analyze the hippocampus.

These labeling functions handle the isolation of the selected regions during labeling. They also take advantage of `numba` for JIT and parallel processing.

### `segmentation.py`
Once the regions of interest have been labeled and are being analyed, there's no need to analyze the entire input volume. 

These functions serve to segment the region of interest from the labeled volume and bound the segmented volume for faster array processing.

### `annotation trees`
These are the default annotation trees that are loaded with VesselVio.
