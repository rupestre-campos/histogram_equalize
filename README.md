# Equalize satellite image histogram

it is used as follows:

```histogram_equalize.py img_path out_img_type in_nodata out_nodata```

img_path: provide a valid path to a satellite image file. Out file will be created at same path with same extension with '_hist' sufix.

out_img_type: provide a value from 32, 16 or 8. Use 32 for a result in range 0-1. Use 16 for range 0-65535 and 8 for range 0-255.

in_nodata: supply a valid nodata

out_nodata: supply a valid outdata

## Simple usage
install GDAL suite and python (via qgis or OSGeo4W standalone)

on command line type:

```python histogram_equalize.py path/to/image.tif 8 0 0```

Modify as you want.
Not any garantee that it will work, still under development showing good results. Any suggestions are appreciated.
