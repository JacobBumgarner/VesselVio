# VesselVio
VesselVio is an open-source application designed for the analysis and visualization of segmented vasculature datasets. 

There several options for using VesselVio:

- [Download our app](https://jacobbumgarner.github.io/VesselVio/Downloads.html) for Windows and MacOS.
- Run the app in your own IDE by executing the VesselVio.py file
- Modify the analysis pipeline and add custom analyses using the VVTerminal.py file

The program is compatible with both 2D and 3D vasculature datasets that have been pre-segmented (binarized). 

Finally, VesselVio is compatible with annotated datasets. Annotations can be loaded with original volumes as .nii files or as .png RGB image series alongside custom or pre-loaded annotation trees from the Allen Brain Institute. Users can then select and process individual regions from these annotations as desired. If you're looking for help with annotating mouse brain datasets, check out [QuickNII](https://www.nitrc.org/projects/quicknii).


## Analysis
Various reconstructs vascular networks to extract whole-network and individual segment features. Several examples of feature outputs can be seen below.

<p align="center">
  <img align="center" height="200" alt="Untitled" src="https://user-images.githubusercontent.com/70919881/121594866-a369c100-ca0b-11eb-9e17-f59a55763a98.png" /><img align="center" height="300" alt="Data2" src="https://user-images.githubusercontent.com/70919881/121596339-4ff87280-ca0d-11eb-94e9-818d6928f070.png" />
  

</p>


## Visualization
Visualization with VesselVio is made possible with [PyVista](https://github.com/pyvista/pyvista), an intuitive and high-level VTK package. Thanks to PyVista, users can easily visualize and examine their vasculature datasets with numerous options intended for accompanying figure images.

<p align="center">
  <img width="48%" alt="Inferior Colliculus" src="https://user-images.githubusercontent.com/70919881/121599185-b337d400-ca10-11eb-8d66-1b1bb1e0040c.mp4" /> <img width="48%" alt="Brain" src="https://user-images.githubusercontent.com/70919881/121599523-28a3a480-ca11-11eb-8340-c29350998f02.mp4">
  
</p>

## App Design


The application's front-end was designed using [PyQt5](https://github.com/PyQt5/PyQt).

<img align="center" width="50%" alt="Untitled" src="https://i.imgur.com/szFAVii.png" /><img align="center" width="50%" alt="Untitled" src="https://i.imgur.com/wnxSylE.png" />

##
Any suggestions, improvements, or comments should be directed to [Jacob Bumgarner](jrbumgarner@mix.wvu.edu).

<b>If you use VesselVio in your research, please cite our [pre-print publication](https://www.researchsquare.com/article/rs-608609/v1).


