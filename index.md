
## Vasculature Analysis and Visualization
VesselVio is an open-source application designed to allow researchers to analyze and visualize segmented and binarized vasculature datasets.
<div class="iframe-container">
  <iframe src='https://gfycat.com/ifr/NiftyGracefulAfricanrockpython?hd=1' frameborder='0' scrolling='no' allowfullscreen width="100%" height="100%"></iframe>
</div>&nbsp;

## Analysis
Analyzing the structure of vascular networks can improve our understanding of their roles in health and disease. By observing and quantifying discrete alterations in the features of these networks, we can potentially improve the identification and characterization of underlying pathological conditions. 

VesselVio is compatible with any binarized and segmented vasculature dataset. Analysis of loaded datasets provides convenient xlsx exports with whole-network and individual-segment quantitative features. The program has been tested on datasets acquired with light-sheet microscopy, micro-computed tomography, and magnetic resonance angiography. Examples of dataset analyses can be found in our recent [pre-print publication](https://www.researchsquare.com/article/rs-608609/v1). 

<p align="center">
 <img style="width: 50%; min-width: 300px;" alt="Analysis Page" src="https://i.imgur.com/szFAVii.png">
</p>

Numerous advancements in preclinical imaging technologies have lead to the generation of large-scale and micron-resolution vasculature datasets. These datasets include whole-brain, lymph node, and tumor vascualture. VesselVio bridges the gap between modern imaging and segmentation technologies and open-source analysis programs.

## Visualization
VesselVio provides built-in visualization features to observe and inspect vasculature datasets for feature identifications and accuracy confirmations.

Vascular datasets can be viewed in simple-network or scaled-network form (as shown below). They can also be visualized alongside original voxel/pixel meshes and smoothed surface meshes to inform the modification of segment prune settings prior to analysis.
<p align="center">
 <img align="center" style="width: 70%; min-width: 280px;" alt="Visualization Page" src="https://i.imgur.com/wnxSylE.png">
</p>

Thanks to the open-source python PyVista package, meshes can be visualized interactively and modified on the fly for rapid color and feature changes.

## Download
Currently, VesselVio is available for download as a standalone application for computers running MacOS 10.15.17+ and Windows 10. If you would rather run the VesselVio from the command-line, instructions for python virtual environment builds on MacOS and Windows are found on the left side-bar.


This application is entirely open-source and free to download under [GNU GPLv3](https://github.com/JacobBumgarner/VesselVio/blob/main/LICENSE). Reseachers hoping to modify or use individual components of the application's software can find the sourcecode on the [GitHub VesselVio page](https://github.com/JacobBumgarner/VesselVio).

