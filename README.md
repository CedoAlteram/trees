# trees 
Trees is a a project that aims to do a tree segmentation analysis on LiDAR data which in which the tree crowns have been identified using an inverse watershed segmentation method. This tool will need a few dependencies. They include the following:

osgeo.gdal
numpy
shpUtils
sqlite

once the shapefile has been uploaded into the correct directory, go <version of python (i.e. Python2.7)> trees.py
based on the size of the lidar DEM and the number of shapes in the shapefile, it could take a minute to complete. This is ok. Numpy is blindingly fast. 
Once done, check the appropriate directory and look for your raster file. 
