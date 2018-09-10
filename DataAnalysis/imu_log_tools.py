import csv
import datetime

# To read an IMU log file
# 1. discard first line
# Each following line is of format: 
# Tstamp, gyro_x, y, z, acc_x, y, z, quat_x, y, z, w, temp
# 2. For each line: 
    # put Tstamp into list
    # put gyro x y z into triplet into list
    # put acc x y z into triplet into list
    # put quat x y z w into quadruplet into list
    # put temp into list
def parseFile(file):
    reader = csv.reader(file, delimiter=',')

    total_lines = 0
    i = []
    tstamp = []
    gyro = []
    acc = []
    quat = []
    temp_c = []

    row_i = 0
    for row in reader:
        if row_i == 0:
            header = row
        else:
            i.append(row_i - 1)
            col_i = 0
            gyro_temp = []
            acc_temp = []
            quat_temp = []
            for col in row:
                col = "".join(col.split())
                if col_i == 0: # tstamp
                    tstamp.append(col)
                if col_i == 1 or col_i == 2: # gyro x and y
                    gyro_temp.append(col)
                if col_i == 3: # gyro z
                    gyro.append((float(gyro_temp[0]),\
                                 float(gyro_temp[1]),\
                                 float(col)))
                if col_i == 4 or col_i == 5: # acc x and y
                    acc_temp.append(col)
                if col_i == 6: # acc z
                    acc.append((float(acc_temp[0]),\
                                float(acc_temp[1]),\
                                float(col)))
                if col_i == 7 or col_i == 8 or col_i == 9: # quat x, y, z
                    quat_temp.append(col)
                if col_i == 10: # quat w
                    quat.append((float(col),\
                                 float(quat_temp[0]),\
                                 float(quat_temp[1]),\
                                 float(quat_temp[2])))
                if col_i == 11: # temperature
                    temp_c.append(float(col))
                col_i += 1
        row_i += 1

    total_lines = row_i - 1

    return (total_lines, i, tstamp, gyro, acc, quat, temp_c)

def calculateTimeDeltas(timestamps):
    time_fmt = '%H:%M:%S.%f'
    reference_time = datetime.datetime.strptime(timestamps[0], time_fmt)
    cumulative_elapsed_times = []
    average_time_delta = 0
    time_deltas = []
    index = 0
    previous_datetime = ''
    current_datetime = ''
    for t in timestamps:
        current_datetime = datetime.datetime.strptime(t, time_fmt)
        cumulative_elapsed_times.append((current_datetime -\
                                         reference_time).total_seconds())
        if index == 0:
            time_deltas.append(datetime.timedelta(0))
        else:
            time_delta = (current_datetime - previous_datetime)
            time_deltas.append(time_delta)
            average_time_delta += time_delta.total_seconds()

        previous_datetime = current_datetime
        index += 1

    average_time_delta = average_time_delta / index
    # convert to Hz
    # average_time_delta_Hz = (1000000 / average_time_delta)
    # average_data_rate_string = "Average IMU read rate: " +\
                               # str(round(average_time_delta_Hz, 3)) +\
                               # " (Hz)"

    return (reference_time, average_time_delta,\
            time_deltas, cumulative_elapsed_times)