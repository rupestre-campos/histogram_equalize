from osgeo import gdal
from osgeo.gdalconst import *
from collections import Counter
import numpy as np
from subprocess import call
import sys
import time

def equalize_histogram(img,img_type,in_nodata,out_nodata):
    call('gdal_edit -a_nodata {} {}'.format(in_nodata,img),shell=True)
    if img_type == 8:
        scale = 255
    elif img_type == 16:
        scale = 65535
    elif img_type == 32:
        scale = 1
    inDs = gdal.Open(img)
    n_bands = inDs.RasterCount
    driver = inDs.GetDriver()
    rows = inDs.RasterYSize
    cols = inDs.RasterXSize
    
    out_path = '{}_hist{}'.format(img[:-4],img[-4:])
    if img_type != 32:
        if img_type == 16:
            outDs = driver.Create(out_path, cols, rows, n_bands, GDT_Int16)
        elif img_type == 8:
            outDs = driver.Create(out_path, cols, rows, n_bands, GDT_Byte)  
    else:
        outDs = driver.Create(out_path, cols, rows, n_bands, GDT_Float32)

    for b in range(n_bands):
        b+=1
        band = inDs.GetRasterBand(b)
        rasterArray = band.ReadAsArray(0,0,cols,rows)
        freq = Counter(rasterArray.flatten())
        value_list = sorted([i for i in freq])
        size = cols*rows - freq[in_nodata]
        value_list.remove(in_nodata)
        pdf = {}
        for val in value_list:
            pdf[val] = float(freq[val])/size
        cdf = {}
        summing = 0
        for val in value_list:
            summing += pdf[val]
            cdf[val] = summing*scale


        if img_type != 32:
            if img_type == 16:
                outData = np.zeros((rows,cols), np.uint16)
            elif img_type == 8:
                outData = np.zeros((rows,cols), np.uint8)            
        else:
            outData = np.zeros((rows,cols), np.float32)

        outBand = outDs.GetRasterBand(b)

        for i in range(0, rows):
            for j in range(0, cols):
                cell_value = rasterArray[i,j]
                if cell_value != in_nodata:
                    outData[i,j] = cdf[cell_value]
                        
        outBand.WriteArray(outData, 0, 0)
        # flush data to disk, set the NoData value and calculate stats
        outBand.SetNoDataValue(out_nodata)
        outBand.FlushCache()
        outBand = None
        del outData

    outDs.SetGeoTransform(inDs.GetGeoTransform())
    outDs.SetProjection(inDs.GetProjection())
    
    rasterArray = outDs = None
    return out_path

def time_exec(time1,time2):
    time = time2 - time1
    if time < 60:
        sys.stdout.write("\tTime: {:.2f} seconds\n".format(time))
    elif time < 3600:
        time = time/60
        sys.stdout.write("\tTime: {:.2f} minutes\n".format(time))
    elif time < 86400:
        time = (time/60)/60
        sys.stdout.write("\tTime: {:.2f} hours\n".format(time))
    else:
        time = ((time/60)/60)/24
        sys.stdout.write("Time: {} days\n".format(time))

def main():
    img = sys.argv[1]
    out_img_type = int(sys.argv[2])
    in_nodata = int(sys.argv[3])
    out_nodata = int(sys.argv[4])
    time1 = time.time()
    print("starting to equalize...")
    result = equalize_histogram(img,out_img_type,in_nodata,out_nodata)
    time2 = time.time()
    sys.stdout.write("image equalized:{} \n".format(result))
    time_exec(time1,time2)

if __name__ == "__main__":
    main()