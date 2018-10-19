To make the global raster of oceanic and tectonic environments:

The values will be:

oceanic_global.grd
Oceanic = 1, non-oceanic = 0

and 

tectonic_global.grd
Stable = 1
Active = 2
Volcanic = 3
Subduction = 4

$ gdal_rasterize -at -burn 1 -init 0 -l ocean -te -180 -90 180 90 -tr 0.008333333333 0.008333333333 -ot Byte ocean.geojson oceanic_global.tif

$ gdal_rasterize -at -burn 1 -init 0 -l stable -te -180 -90 180 90 -tr 0.008333333333 0.008333333333 -ot Byte stable.geojson tectonic_global.tif
$ gdal_rasterize -at -burn 2 -l active_no_vol_sub_extra active.geojson tectonic_global.tif
$ gdal_rasterize -at -burn 3 -l volcanic volcanic.geojson tectonic_global.tif
$ gdal_rasterize -at -burn 4 -l stable_with_extra subduction.geojson tectonic_global.tif
$ gmt grdconvert oceanic_global.tif oceanic_global.grd=nb
$ gmt grdconvert tectonic_global.tif tectonic_global.grd=nb

