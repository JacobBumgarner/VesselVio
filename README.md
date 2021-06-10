# VesselVio
VesselVio is an open-source application and software package developed for the analysis and visualization of vasculature datasets. 

The program is compatabile with both 2D and 3D datasets of any imaging origin, with the caveat that the vasculature has been pre-segmented prior to analysis.

## Analysis
Various whole-network and individual segment features are extracted from datasets and exported into convenient xlsx files for subsequent analyses. Through the adoption of Numba just-in-time compilation and parrellization of array processing, our back-end python source-code provides rapid options for dataset analyis s


<img align="center" height="200" alt="Untitled" src="https://user-images.githubusercontent.com/70919881/121594866-a369c100-ca0b-11eb-9e17-f59a55763a98.png">
<img align="center" height="300" alt="Data2" src="https://user-images.githubusercontent.com/70919881/121596339-4ff87280-ca0d-11eb-94e9-818d6928f070.png">


## Visualization
VesselVio was constructed to allow users to interactively visualize their of vascular datasets. This can be great for the generation of figure images or result inspections.

<img width="300" alt="Brain" src="https://user-images.githubusercontent.com/70919881/121595124-f5124b80-ca0b-11eb-83b4-1d2820a8e367.png">
