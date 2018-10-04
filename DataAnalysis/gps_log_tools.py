import csv
import datetime

def parseLog(file):
    reader = csv.reader(file, delimiter=',')

    # GPS log files are of the format:
    # Sys_tstamp, gps_tstamp, latitude, longitude, altitude

    total_lines = 0
    indices = []
    sys_tstamps = []
    gps_tstamps = []
    latitudes = []
    longitudes = []
    altitudes = []

    row_index = 0
    for row in reader:
        if row_index == 0:
            # this is the header, ignore it
            header = row
        else:
            indices.append(row_index - 1)
            col_index = 0

            for col in row:
                col = "".join(col.split())
                if col_index == 0:
                    sys_tstamps.append(col)
                if col_index == 1:
                    gps_tstamps.append(col)
                if col_index == 2:
                    latitudes.append(col)
                if col_index == 3:
                    longitudes.append(col)
                if col_index == 4:
                    altitudes.append(col)

                col_index += 1
        row_index += 1
    total_lines = row_index - 1

    return (total_lines, indices, sys_tstamps, gps_tstamps, 
            latitudes, longitudes, altitudes)

def calculateTimeDeltas(sys_tstamps, gps_tstamps):
    # find first timestamp from gps, calculate time offset between system time
    # and gps time - return this as we may want it to convert times to UTC 
    # later

    

    # return 