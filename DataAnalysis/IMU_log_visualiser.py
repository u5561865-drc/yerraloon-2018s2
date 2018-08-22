# TODO
# change all usage of quaternions to the quaternion object
# implement single data point visualisation
# implement control for multi data point playback

import csv
import math
import sys
import datetime
from pyquaternion import Quaternion
from vpython import *

# each quaternion is stored in the form (w,    x,    y,    z)
#                                       q[0], q[1], q[2], q[3]

# Method for converting from quaternions to Euler angles, taken from:
# https://en.wikipedia.org/wiki/Conversion_between_quaternions_and_Euler_angles
def quaternionToEulerAngle(w, x, y, z):
    ysqr = y * y
    
    t0 = +2.0 * (w * x + y * z)
    t1 = +1.0 - 2.0 * (x * x + ysqr)
    X = math.degrees(math.atan2(t0, t1))
    
    t2 = +2.0 * (w * y - z * x)
    t2 = +1.0 if t2 > +1.0 else t2
    t2 = -1.0 if t2 < -1.0 else t2
    Y = math.degrees(math.asin(t2))
    
    t3 = +2.0 * (w * z + x * y)
    t4 = +1.0 - 2.0 * (ysqr + z * z)
    Z = math.degrees(math.atan2(t3, t4))
    
    return X, Y, Z

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

def calculateEulerAngles(quaternions):
    euler_angles = []
    
    for q in quaternions:
        eul_temp = quaternionToEulerAngle(q)
        euler_angles.append((eul_temp[0], eul_temp[1], eul_temp[2]))
    
    return euler_angles

def calculateAxisAngles(quaternions):
    axis_angles = []
    for q in quaternions:
        eq_part = math.sqrt(1 - (q[3] * q[3]))
        angle = 2 * math.acos(q[3])
        # need to handle potential divide by zero here
        # axis may need to be normalised
        if eq_part < 0.001:
            axis_angles.append((angle,\
                               q[0],\
                               q[1],\
                               q[2]))
        else:
            axis_angles.append((angle,\
                               q[0] / eq_part,\
                               q[1] / eq_part,\
                               q[2] / eq_part))
    return axis_angles

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

def buildQuaternionObjects(quaternions):
    quat_OBJs = []
    for q in quaternions:
        quat_OBJs.append(Quaternion(q))
    return quat_OBJs

def build3DVisualisation(balloon_train_length):
    main_scene = canvas(title="IMU 3D Orientation", height = 900, width = 900)
    main_scene.range = balloon_train_length + 3
    main_scene.forward=vector(0.5, -0.5, 1)

    objects = []
    payload = box(pos = vector(0, -(balloon_train_length / 2), 0),\
                  size = vector(2,1,1))
    objects.append(payload)
    balloon_train = arrow(
                        pos = vector(0, (balloon_train_length / 2) + 0.5, 0),\
                        axis = vector(0, -balloon_train_length, 0),\
                        shaftwidth = 0.2)
    objects.append(balloon_train)
    balloon = sphere(pos = vector(0, (balloon_train_length / 2) + 1.5, 0),\
                     radius = 1)
    objects.append(balloon)
    return (main_scene, objects)

def updateVisualisationObjects(quaternion, objects, balloon_train_length):
    # payload - objects[0]
    # all motion is currently being carried out in 1 dimension - this needs to 
    # be fixed. Position is also currently not being updated
    objects[0].rotate()
    # objects[0].pos = 
    return objects

def playback(indices, time_deltas, quaternion_OBJs,\
             objects, balloon_train_length):
    for index in indices:
        time.sleep(time_deltas[index].total_seconds())
        updateVisualisationObjects(quaternion_OBJs[index], objects,\
                                   balloon_train_length)

# To read a csv
# 1. discard first line
# Each following line is of format: 
# Tstamp, gyro_x, y, z, acc_x, y, z, quat_x, y, z, w, temp
# 2. For each line: 
    # put Tstamp into list
    # put gyro x y z into triplet into list
    # put acc x y z into triplet into list
    # put quat x y z w into quadruplet into list
    # put temp into list
def main(argv):
    file = open(argv[0])
    balloon_train_length = int(argv[1])
    
    (total_lines, indices, timestamps, gyro_data,\
     acc_data, quaternions, temperatures)          = parseFile(file)

    # euler_angles = calculateEulerAngles(quaternions)
    axis_angles = calculateAxisAngles(quaternions)
    
    (reference_time, average_time_delta,\
     time_deltas, cumulative_elapsed_times) = calculateTimeDeltas(timestamps)

    quaternion_OBJs = buildQuaternionObjects(quaternions)

    # need to calculate position and then rotate representation at this point, around the normal vevtor to the horizontal plane
    (main_scene, objects) = build3DVisualisation(balloon_train_length)
    
    playback(indices, time_deltas, quaternion_OBJs,\
             objects, balloon_train_length)
    
    print("finished playback")

if __name__ == "__main__":
    main(sys.argv[1:])