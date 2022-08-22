## VesselVio Annotation Processing
The modules in this directory contain all of the annotation processing functions in VesselVio.

#### `tree_processing.py`
Handles annotation tree loading, VesselVio annotation file i/o, and VesselVio annotation file processing.

#### 'segmentation_prep.py'
Contains all of the functions used to prepare the segmentation and labeling processes.

### `labeling.py`
Contains all of the functions to label vasculature volumes with corresponding ID or RGB based annotation volumes. The labeling functions  handle the isolation of the selected regions during labeling. The functions also take advantage of `numba` for JIT and parallel processing.

VesselVio takes a region-first approach to ROI analysis. This approach speeds up dataset processing times and dramatically reduces memory requirements, but it comes with the tradeoff that endpoint counts can be inflated if analyzing side-by-side regions. You can read a more technical explanation of this tradeoff in the *Limitations* section of our manuscript.

*Explanation of region-first analysis:*
Often users load annotation volumes that contain dozens or hundreds of annotations. For example, the Allen Institute `p56 mouse brain` atlas contains _hundreds_ of regions. However, users might not want to analyze all of the annotated regions. For example, in our lab we typically only run hippocampal vasculature analyses.

Because of this, VesselVio analyzes ROIs one-by-one. This means that instead of multiplying the labeled volume by the vasculature volume for a whole-dataset analysis, each ROI is segmented and analyzed separately. Re: above for pros/cons.

### `segmentation.py`
These functions serve to segment the region of interest from the labeled volume and bound the segmented volume for faster array processing. Once the regions of interest have been labeled and are being analyzed, there's no need to analyze the entire input volume. 

### `annotation trees`
This directory contains the default annotation trees that are loaded with VesselVio.
