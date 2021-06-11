# VesselVio
VesselVio is an open-source application and software package developed for the analysis and visualization of vasculature datasets. 

The program is compatabile with both 2D and 3D datasets of any imaging origin, with the caveat that the vasculature has been pre-segmented prior to analysis.

## Analysis
Various whole-network and individual segment features are extracted from datasets and exported into convenient xlsx files for subsequent analyses. Through the adoption of Numba just-in-time compilation and parallelization of array processing, our back-end python source-code provides rapid options for various feature extractions. Users can prune segments at pre-defined lengths and can export graphml files for custom network analyses.

<p align="center">
  <img align="center" height="200" alt="Untitled" src="https://user-images.githubusercontent.com/70919881/121594866-a369c100-ca0b-11eb-9e17-f59a55763a98.png" /><img align="center" height="300" alt="Data2" src="https://user-images.githubusercontent.com/70919881/121596339-4ff87280-ca0d-11eb-94e9-818d6928f070.png" />
  
<img align="center" width="50%" alt="Untitled" src="https://i.imgur.com/szFAVii.png" />
</p>

Briefly, binarized vascular datasets are skeletonized, and undirected graphs are created from the skeleton centerlines. Centerlines are smoothed, spurious branch points are filtered, and end-point and isolated segments of defined lengths are filtered from the datasets. Following this, various results are extracted from the undirected graph.


## Visualization
VesselVio was constructed using [PyVista](https://github.com/pyvista/pyvista), a high-level VTK package, to allow users to interactively visualize their of vascular datasets. This can be great for the generation of figure images or result inspections.

<p align="center">
  <img width="40%" alt="Gif" src="https://user-images.githubusercontent.com/70919881/121599185-b337d400-ca10-11eb-8d66-1b1bb1e0040c.mp4" /> <img width="40%" alt="Brain" src="https://user-images.githubusercontent.com/70919881/121599523-28a3a480-ca11-11eb-8340-c29350998f02.mp4">
  
  <img align="center" width="70%" alt="Untitled" src="https://i.imgur.com/wnxSylE.png" />
  
</p>


Any suggestions, improvements, or comments should be directed to Jacob Bumgarner.

If you use VesselVio in your research, please cite our [pre-print publication](https://www.researchsquare.com/article/rs-608609/v1).

https://www.researchsquare.com/article/rs-608609/v1


