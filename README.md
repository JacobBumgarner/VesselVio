# VesselVio
VesselVio is an open-source application designed for the analysis and visualization of segmented vasculature datasets. 

There several options for using VesselVio:

- [Download the app](https://jacobbumgarner.github.io/VesselVio/Downloads.html) for Windows and MacOS (most convenient option).
- Build the app in your own IDE by executing or freezing the VesselVio.py file (fastest option)
- Modify the analysis pipeline and add custom analyses using the VVTerminal.py file

<img align="center" width="50%" alt="Untitled" src="https://user-images.githubusercontent.com/70919881/149036341-2b1515ba-94f4-4c89-b774-10e70e5e65c1.png" /><img align="center" width="50%" alt="Untitled" src="https://user-images.githubusercontent.com/70919881/149036342-f8aecef3-84fe-4fe7-8e2e-4eac6d543795.png" />

VesselVio is compatible with several different types of segmented vasculature datasets, including:
- Non-annotated volumes of any imaging source
- Annotated volumes, including:
  - Whole-brain vasculature datasets with Allen Brain Institute ID-based annotations
  - Manually labelled datasets with a program such as [ITK-Snap](http://www.itksnap.org/pmwiki/pmwiki.php)
  - RGB-based annotations, such as those created with [QuickNII](https://www.nitrc.org/projects/quicknii)
- Pre-constructed graphs (both edge- and vertex- based graphs)
- 2D and 3D datasets
- Isotropic and Anisotropic datasets


## Analysis
Various reconstructs vascular networks to extract whole-network and individual segment features. Several examples of feature outputs can be seen below.

<p align="center">
  <img align="center" width="50%" alt="Untitled" src="https://user-images.githubusercontent.com/70919881/149639453-71c22b0a-7a0c-4c3f-8af5-f38aaf4027df.png" />
</p>

## Visualization
Visualization with VesselVio is made possible with [PyVista](https://github.com/pyvista/pyvista), an intuitive and high-level VTK package. Thanks to PyVista, users can easily visualize and examine their vasculature datasets with numerous options intended for accompanying figure images.

<p align="center">
  <img width="48%" alt="Inferior Colliculus" src="https://user-images.githubusercontent.com/70919881/121599185-b337d400-ca10-11eb-8d66-1b1bb1e0040c.mp4" /> <img width="48%" alt="Brain" src="https://user-images.githubusercontent.com/70919881/121599523-28a3a480-ca11-11eb-8340-c29350998f02.mp4">
</p>

![Fig3](https://user-images.githubusercontent.com/70919881/121599523-28a3a480-ca11-11eb-8340-c29350998f02.mp4)

## App Design

The application's front-end was designed using [PyQt5](https://github.com/PyQt5/PyQt).


##
Any suggestions, improvements, or comments should be directed to [Jacob Bumgarner](jrbumgarner@mix.wvu.edu).

<b>If you use VesselVio in your research, please cite our [pre-print publication](https://www.researchsquare.com/article/rs-608609/v1).


If you are looking for help with segmenting your vasculature, there are numerous packages available for this process<sup>[1](https://github.com/ChristophKirst/ClearMap2)[2](https://github.com/vessap/vessap)[3](https://github.com/giesekow/deepvesselnet)</sup>. The program is also capable of analyzing and visualizing  vasculature graphs that have been pre-constructed using other programs.
