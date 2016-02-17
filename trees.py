#!/usr/bin/env python

import osgeo.gdal
from osgeo.gdalconst import *
import numpy
#import pylab
import shpUtils
import sqlite3 as sqlite
from math import sqrt
print "all libs imported"


display_it=False

# input files
point_file = 'sample/crown_1meter_point_Clip.shp'
raster_file = 'sample/for_ndsm/hdr.adf'

# output file
output_raster_file = 'output.tiff'
output_format = 'GTiff'

# search parameters
radius = 10
threshold = .75

def read_points(shape_file):
    shpRecords = shpUtils.loadShapefile(shape_file)
    
    points = []
    for record in shpRecords:
        points.append(( record['dbf_data']['POINTID'], record['shp_data'], 
                        record['dbf_data']['GRID_CODE'] ))
    return points


def read_raster(dataset):
    
    geotransform = dataset.GetGeoTransform()
    if not geotransform is None:
        (x,y) = (geotransform[0], geotransform[3])
        #print 'Pixel Size = (',geotransform[1], ',',geotransform[5],')'
        
        band = dataset.GetRasterBand(1)
        #print 'Band Type=%s' % osgeo.gdal.GetDataTypeName(band.DataType)
        
        min = band.GetMinimum()
        max = band.GetMaximum()
        a = dataset.ReadAsArray()
    return (a, x, y, min, max)
        
def display_raster(array, min, max): 
    pylab.imshow (array, vmin=min, vmax=max, interpolation='nearest')
    pylab.colorbar()
    
    pylab.show()


def init_db(points):
    connection = sqlite.connect('points.db')
    cursor = connection.cursor()
    cursor.execute(""" CREATE TABLE IF NOT EXISTS points 
                        (id INTEGER PRIMARY KEY, 
                        x REAL, 
                        y REAL, 
                        grid_value REAL) """)
    cursor.execute('DELETE FROM points')
    for (point_id, coords, grid_value) in points:
        cursor.execute('INSERT INTO points VALUES (?, ?, ?, ?)', 
                            (int(point_id), float(coords['x']), 
                            float(coords['y']), float(grid_value)))
    connection.commit()
    return cursor


def pinwheel(grid_y, grid_x, crown_height, point_id):
    # in the cell of the crown:
    if input_array[grid_y][grid_x] > crown_height:
        print "crown_id: %s %s input grid value is higher than crown" % (point_id, (grid_y,grid_x))
        if output_array[grid_y][grid_x] < 1:
            output_array[grid_y][grid_x] = point_id
    # working out way outward
    for m in range(-radius,radius):
        for n in range(-radius,radius):
            try:
               
                
                # are we within our search radius?
                if sqrt(m*m + n*n) < radius:
                    # calculate score
                    score = input_array[grid_y + m][grid_x + n] / crown_height 
                
                    #print "n = %s, m = %s" %(n,m)
                    # compare against upslope value
                    if (m == 0 and n == 0):
                        #we are in the crown cell, no need to evaluate
                        break
                    elif (m == 0):
                        if n > 0:
                            upslope_value = input_array[grid_y + m][grid_y + n - 1]
                            #print "we are on the m axis, n is positive"
                        if n < 0:
                            #print "we are on the m axis, n is negative"
                            upslope_value = input_array[grid_y + m][grid_y + n + 1]
                    elif (n == 0):
                        if m > 0:
                            #print "we are on the n axis, m is positive"
                            upslope_value = input_array[grid_y + m - 1][grid_y + n]
                        if m < 0:
                            #print "we are on the n axis, m is negative"
                            upslope_value = input_array[grid_y + m + 1][grid_y + n]
                    elif (m > 0 and n > 0):
                        #print "we are in quadrant I"
                        upslope_value = input_array[grid_y + m - 1][grid_y + n - 1]
                    elif (m > 0 and n < 0):
                        #print "we are in quadrant II"
                        upslope_value = input_array[grid_y + m - 1][grid_y + n + 1]
                    elif (m < 0 and n < 0):
                        #print "we are in quadrant III"
                        upslope_value = input_array[grid_y + m + 1][grid_y + n + 1]
                    elif (m < 0 and n > 0):
                        #print "we are in quadrant IV"
                        upslope_value = input_array[grid_y + m + 1][grid_y + n - 1]
					# end of upslope value determination
					
					# start classification
					# score < 1 means that grid_value is higher than crown height                     
                    if score > threshold and score < 1:
                        #we are above our threshold and below the crown height (score=1) 
                        print "crown_id: %s %s is above threshold and below crown height (%s) " % (point_id, (grid_x+n, grid_y+m), score)
                        
                        # make sure that the upslope value is higher than the grid_value
                        if upslope_value > input_array[grid_y + m][grid_x + n]:
                            # check to make sure that cell is not already classified
                            if output_array[grid_y + m][grid_x + n] < 1:
                                output_array[grid_y + m][grid_x + n] = point_id
                            else:
                                print "crown_id: %s %s is already classified (%s) " % (point_id, (grid_x+n, grid_y+m), score)
                        else:
                            print "crown_id: %s %s is below threshold or higher than canopy (%s) " % (point_id, (grid_y+n, grid_y+m), score)
            except:
		        # cell is off of the grid
                print "crown_id: %s %s probably out of bounds, near edge" % (point_id, (grid_y, grid_x) ) 



if __name__ == "__main__":
  
    # open input raster
    input_dataset = osgeo.gdal.Open(raster_file, GA_ReadOnly)
    
    # open output raster
    driver = osgeo.gdal.GetDriverByName( output_format )
    output_dataset = driver.CreateCopy( output_raster_file, input_dataset, 0 )
    
    # read input raster
    (input_array, origin_x, origin_y, min, max) = read_raster(input_dataset)
 
    # read points and create database
    c = init_db(read_points(point_file))
    c.execute( """ SELECT id, x, y, grid_value 
                        FROM points order by grid_value ASC""" )
    
    # create an empty output array
    output_array = numpy.zeros( input_array.shape )    
    
    # process input
    for row in c:
        (point_id, x, y, input_crown_height) = (row[0], row[1], row[2], row[3])
        print "db_id: %s crown: %s (%s)" % (point_id, input_crown_height, (x,y))
        # project from utm coordinates into grid coordinates
        grid_x = int(x - origin_x)
        grid_y = int(origin_y - y)
        pinwheel(grid_y, grid_x, input_crown_height, point_id)

    # write the output dataset
    output_dataset.GetRasterBand(1).WriteArray( output_array )

    
    # close the datasets
    input_dataset = None
    ouput_dataset = None
    
