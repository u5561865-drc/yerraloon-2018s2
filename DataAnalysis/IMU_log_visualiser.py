import csv
import math
import sys
import datetime
from pyquaternion import Quaternion
from vpython import *

# determines if the payload should be treated as an individual object,
# or as a pendulum. set via arguments
pendulum_mode = False

# each quaternion is stored in the form (w,    x,    y,    z)
#                                       q[0], q[1], q[2], q[3]

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

def calculateEulerAngles(quaternions):
    euler_angles = []
    for q in quaternions:
        euler_angles.append(quaternionToEulerAngle(q[0], q[1], q[2], q[3]))
    return euler_angles

def quaternionToAxisAngle(quaternion):
    equation_part = math.sqrt(1 - (quaternion[0] * quaternion[0]))
    angle = 2 * math.acos(quaternion[0])
    # need to handle potential divide by zero here
    if eq_part < 0.001:
        return (angle, quaternion[1], quaternion[2], quaternion[3])
    else:
        return (angle, quaternion[1] / equation_part, 
                       quaternion[2] / equation_part, 
                       quaternion[3] / equation_part)

def calculateAxisAngles(quaternions):
    axis_angles = []
    for q in quaternions:
        axis_angles.append(quaternionToAxisAngle(q))
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
        # swap y and z axes for visualisation purposes
        quat_OBJ = Quaternion((q[0], q[1], q[3], q[2]))
        quat_OBJs.append(quat_OBJ)
    return quat_OBJs

def build3DVisualisation(balloon_train_length):
    scene_3d = canvas(title="IMU 3D Orientation", height = 700, width = 700)
    scene_3d.range = balloon_train_length / 2 + 2
    scene_3d.forward = vec(1, -1, -1)

    objects_3d = []
    payload = box(pos = vec(0, 0, 0),\
                  size = vec(1.2, 1.4, 0.9))
    objects_3d.append(payload)
    
    if pendulum_mode:
        balloon_train = arrow(pos = vec(0, balloon_train_length, 0),
                              axis = vec(0, -balloon_train_length, 0),
                              shaftwidth = 0.02)
        objects_3d.append(balloon_train)
        
        balloon = sphere(pos = vec(0, balloon_train_length + 1, 0), radius = 1)
        objects_3d.append(balloon)

    x_axis = arrow(color = color.red, axis = vec(-3, 0, 0),
                   shaftwidth = 0.02, fixedwidth = 0.01)
    y_axis = arrow(color = color.green, axis = vec(0, 3, 0),
                   shaftwidth = 0.02, fixedwidth = 0.01)
    z_axis = arrow(color = color.blue, axis=vec(0, 0, 3),
                   shaftwidth = 0.02, fixedwidth = 0.01)

    return (scene_3d, objects_3d)

def update3DVisualisationObjects(quaternion_OBJ, objects, balloon_train_length):
    rotation_axis = quaternion_OBJ.get_axis(undefined=[0, 1, 0])
    rotation_angle = quaternion_OBJ.radians
    
    # objects[0] = payload
    objects[0].up = vec(0, 1, 0)
    objects[0].axis = vec(1.2, 0, 0)
    objects[0].rotate(angle = rotation_angle,
                      axis = vector(rotation_axis[0],
                                    rotation_axis[1],
                                    rotation_axis[2]))

    if pendulum_mode:
        # objects[2] = balloon
        objects[2].up = vector(0, 0, 1)
        objects[2].axis = vector(0, 1, 0)
        objects[2].rotate(angle = rotation_angle,
                          axis = vector(rotation_axis[0],
                                        rotation_axis[1],
                                        rotation_axis[2]))

        # objects[1] = balloon train (as a rigid pendulum)
        v = -objects[2].axis
        v.mag = balloon_train_length
        objects[1].axis = v

        objects[0].pos = objects[1].axis + objects[1].pos

def build2DVisualisation():
    # visualisation here will include:
    # temperature - objects_2d[0]
    # 2d representation of rotation around each axis
    #     x_component - objects_2d[1], objects_2d[2]
    #     y_component - objects_2d[3], objects_2d[4]
    #     z_component - objects_2d[5], objects_2d[6]
    # time info - 
    scene_2d = canvas(height = 200, width = 700, y = 710, range = 1)
                      # background = vector(1, 1, 1))

    objects_2d = []
    
    # temperature - objects_2d[0]
    temperature_label = label(pos = vec(-3.4, 0.85, 0),
                              text = "Temperature (C): - ",
                              box = 0,
                              align = "left")
    objects_2d.append(temperature_label)

    # 2d representation of rotation around each axis
    #     x_component - objects_2d[1], objects_2d[2]
    x_component_1 = cylinder(pos = vec(-1, 0, 0),
                             axis = vec(-0.2, 0, 0),
                             color = color.red,
                             radius = 0.01)
    objects_2d.append(x_component_1)
    x_component_2 = cylinder(pos = vec(-1, 0, 0),
                             axis = vec(0.2, 0, 0),
                             color = color.red,
                             radius = 0.01)
    objects_2d.append(x_component_2)
    #     y_component - objects_2d[3], objects_2d[4]
    y_component_1 = cylinder(pos = vec(0.5, 0, 0),
                             axis = vec(-0.2, 0, 0),
                             color = color.green,
                             radius = 0.01)
    objects_2d.append(y_component_1)
    y_component_2 = cylinder(pos = vec(0.5, 0, 0),
                             axis = vec(0.2, 0, 0),
                             color = color.green,
                             radius = 0.01)
    objects_2d.append(y_component_2)
    #     z_component - objects_2d[5], objects_2d[6]
    z_component_1 = cylinder(pos = vec(2, 0, 0),
                             axis = vec(-0.2, 0, 0),
                             color = color.blue,
                             radius = 0.01)
    objects_2d.append(z_component_1)
    z_component_2 = cylinder(pos = vec(2, 0, 0),
                             axis = vec(0.2, 0, 0),
                             color = color.blue,
                             radius = 0.01)
    objects_2d.append(z_component_2)



    return scene_2d, objects_2d

def update2DVisualisation(objects_2d, quaternion_OBJ, temperature):
    objects_2d[0].text = "Temperature (C): " + str(temperature)

    rotation_axis = quaternion_OBJ.get_axis(undefined=[0, 1, 0])
    rotation_angle = quaternion_OBJ.radians

    # need to make the representations of each axis move


def playback(indices, time_deltas, quaternion_OBJs, objects_3d, 
             balloon_train_length, objects_2d, temperatures):
    for index in indices:
        update3DVisualisationObjects(quaternion_OBJs[index], objects_3d,
                                   balloon_train_length)
        update2DVisualisation(objects_2d, quaternion_OBJs[index], 
                              temperatures[index])
        time.sleep(time_deltas[index].total_seconds())

def main(argv):
    file = open(argv[0])
    balloon_train_length = float(argv[1])
    
    mode = argv[2]
    global pendulum_mode
    if mode == "p":
        pendulum_mode = True
    elif mode == "o":
        pendulum_mode = False

    (total_lines, indices, timestamps, gyro_data,
     acc_data, quaternions, temperatures)          = parseFile(file)

    # euler_angles = calculateEulerAngles(quaternions)
    # axis_angles = calculateAxisAngles(quaternions)
    
    (reference_time, average_time_delta,
     time_deltas, cumulative_elapsed_times) = calculateTimeDeltas(timestamps)

    quaternion_OBJs = buildQuaternionObjects(quaternions)

    (scene_3d, objects_3d) = build3DVisualisation(balloon_train_length)

    (scene_2d, objects_2d) = build2DVisualisation()
    
    playback(indices, time_deltas, quaternion_OBJs,
             objects_3d, balloon_train_length, objects_2d,
             temperatures)
    
    print("finished playback")

if __name__ == "__main__":
    main(sys.argv[1:])