# VesselVio
[![](https://img.shields.io/badge/Article-10.1016%2Fj.crmeth.2022.100189-blueviolet)](https://doi.org/10.1016/j.crmeth.2022.100189) [![Zenodo](https://img.shields.io/badge/Zenodo-10.5281%2Fzenodo.6147198-blue)](https://zenodo.org/badge/latestdoi/365252628) [![](https://img.shields.io/badge/Slack-Join%20us%20on%20Slack!-orange?logo=slack)](https://communityinviter.com/apps/vesselvio/join-vesselvio-on-slack)


VesselVio is an open-source application designed for the analysis and visualization of segmented vasculature datasets. 

There are several ways to use VesselVio:

- [Download the app](https://jacobbumgarner.github.io/VesselVio/Downloads.html) for Windows and MacOS.
- Run the app from your terminal by using the VesselVio.py file (single-line executable)
  - Follow the Windows & MacOS build instructions [here](https://jacobbumgarner.github.io/VesselVio/Build.html)
- Modify the analysis pipeline and add custom analyses using the VVTerminal.py file

<img align="center" width="50%" alt="Untitled" src="https://user-images.githubusercontent.com/70919881/149036341-2b1515ba-94f4-4c89-b774-10e70e5e65c1.png" /><img align="center" width="50%" alt="Untitled" src="https://user-images.githubusercontent.com/70919881/149036342-f8aecef3-84fe-4fe7-8e2e-4eac6d543795.png" />

VesselVio is compatible with several different types of segmented vasculature datasets, including:
- Segmented vascular volumes from any imaging source (e.g., LSFM, µCT)
- Annotated volumes, including:
  - Whole-brain vasculature datasets with Allen Brain Institute ID-based annotations
  - Manually labelled datasets with a program such as [ITK-Snap](http://www.itksnap.org/pmwiki/pmwiki.php)
  - RGB-based annotations, such as those created with [QuickNII](https://www.nitrc.org/projects/quicknii)
- Pre-constructed graphs (both edge- and vertex- based graphs)
- 2D and 3D datasets
- Isotropic and Anisotropic datasets


## Analysis
VesselVio reconstructs vascular networks to extract whole-network and individual segment features. Several examples of feature outputs can be seen below.

<p align="center">
  <img align="center" width="50%" alt="Untitled" src="https://user-images.githubusercontent.com/70919881/149639453-71c22b0a-7a0c-4c3f-8af5-f38aaf4027df.png" />
</p>

## Visualization
Visualization with VesselVio is made possible with [PyVista](https://github.com/pyvista/pyvista), an intuitive and high-level VTK package. Thanks to PyVista, users can easily visualize and examine their vasculature datasets with numerous options to create for accompanying figure images.


Inferior Colliculus | Human Brain 
:--: | :--:
<video src="https://user-images.githubusercontent.com/70919881/121599185-b337d400-ca10-11eb-8d66-1b1bb1e0040c.mp4" /> | <video src="https://user-images.githubusercontent.com/70919881/121599523-28a3a480-ca11-11eb-8340-c29350998f02.mp4" />

## Segmentation Tips
If you are looking for help with segmenting your vasculature, there are numerous packages available for this process<sup>[1](https://github.com/ChristophKirst/ClearMap2)[2](https://github.com/vessap/vessap)[3](https://github.com/giesekow/deepvesselnet)</sup>.

## Other
Any suggestions, improvements, or comments should be directed to [Jacob Bumgarner](mailto:jrbumgarner@mix.wvu.edu).

Feel free to join us on [Slack](https://communityinviter.com/apps/vesselvio/join-vesselvio-on-slack) for general communication or troubleshooting purposes!

<b>If you use VesselVio in your research, please cite our publication in <i>[Cell Reports Methods](https://www.cell.com/cell-reports-methods/fulltext/S2667-2375(22)00044-3)</i>.
