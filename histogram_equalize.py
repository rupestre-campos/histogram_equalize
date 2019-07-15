from osgeo import gdal
from osgeo.gdalconst import *
from collections import Counter
import numpy as np
from subprocess import call
import sys
import time
from collections import defaultdict

def dsum(*dicts):
    ret = defaultdict(int)
    for d in dicts:
        for k, v in d.items():
            ret[k] += v
    return dict(ret)

def read_histograms(n_bands,in_ds,cols,rows):
    freq_tot = {}
    for b in range(n_bands):
        b+=1
        band = in_ds.GetRasterBand(b)
        rasterArray = band.ReadAsArray(0,0,cols,rows)
        unique, counts = np.unique(rasterArray.flatten(), return_counts=True)
        freq = dict(zip(unique,counts))
        #freq = Counter(rasterArray.flatten())
        freq_tot = dsum(freq_tot,freq)
    return freq_tot

def equalize_histogram(img,img_type,in_nodata,out_nodata):
    call('gdal_edit -a_nodata {} {}'.format(in_nodata,img),shell=True)
    if img_type == 8:
        scale = 255
    elif img_type == 16:
        scale = 65535
    elif img_type == 32:
        scale = 1
    in_ds = gdal.Open(img)
    n_bands = in_ds.RasterCount
    driver = in_ds.GetDriver()
    rows = in_ds.RasterYSize
    cols = in_ds.RasterXSize
    out_path = '{}_hist{}'.format(img[:-4],img[-4:])
    if img_type != 32:
        if img_type == 16:
            out_ds = driver.Create(out_path, cols, rows, n_bands, GDT_Int16)
        elif img_type == 8:
            out_ds = driver.Create(out_path, cols, rows, n_bands, GDT_Byte)  
    else:
        out_ds = driver.Create(out_path, cols, rows, n_bands, GDT_Float32)
    pdf = defaultdict(int)
    print("computing pdf...")
    freq_tot = read_histograms(n_bands,in_ds,cols,rows)

    size = cols*rows*n_bands - freq_tot[in_nodata]
    for val in freq_tot:
        pdf[val] += float(freq_tot[val])/size
    print("computing cdf...")    
    value_list = sorted([i for i in pdf])
    value_list.remove(in_nodata)
    cdf = {}
    summing = 0
    for val in value_list:
        summing += pdf[val]
        new_val = summing*scale
        if new_val == 0:
            new_val = 1
        cdf[val] = new_val
    print("converting band histograms...")
    for b in range(n_bands):
        b+=1
        band = in_ds.GetRasterBand(b)
        raster_array = band.ReadAsArray(0,0,cols,rows)
        if img_type != 32:
            if img_type == 16:
                out_data = np.zeros((rows,cols), np.uint16)
            elif img_type == 8:
                out_data = np.zeros((rows,cols), np.uint8)            
        else:
            out_data = np.zeros((rows,cols), np.float32)
        out_data = write_data(raster_array,out_data,cdf,in_nodata,rows,cols)
        out_band = out_ds.GetRasterBand(b)
        out_band.WriteArray(out_data, 0, 0)
        out_band.SetNoDataValue(out_nodata)
        out_band.FlushCache()
        out_band = out_data = None
    out_ds.SetGeoTransform(in_ds.GetGeoTransform())
    out_ds.SetProjection(in_ds.GetProjection())
    raster_array = out_ds = in_ds = None
    return out_path

def write_data(raster_array,out_data,cdf,in_nodata,rows,cols):
    for i in range(0, rows):
        for j in range(0, cols):
            cell_value = raster_array[i,j]
            if cell_value != in_nodata:
                out_data[i,j] = cdf[cell_value]
    return out_data

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