import sys
from pyquaternion import Quaternion
from vpython import *

import quaternion_conversions as quat_conv
import imu_log_tools as imu

# determines if the payload should be treated as an individual object,
# or as a pendulum. set via arguments
pendulum_mode = False

# each quaternion is stored in the form (w,    x,    y,    z)
#                                       q[0], q[1], q[2], q[3]

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
     acc_data, quaternions, temperatures)          = imu.parseFile(file)

    # euler_angles = quat_conv.calculateEulerAngles(quaternions)
    # axis_angles = quat_conv.calculateAxisAngles(quaternions)
    
    (reference_time, average_time_delta, time_deltas, 
     cumulative_elapsed_times) = imu.calculateTimeDeltas(timestamps)

    quaternion_OBJs = buildQuaternionObjects(quaternions)

    (scene_3d, objects_3d) = build3DVisualisation(balloon_train_length)

    (scene_2d, objects_2d) = build2DVisualisation()
    
    playback(indices, time_deltas, quaternion_OBJs,
             objects_3d, balloon_train_length, objects_2d,
             temperatures)
    
    print("finished playback")

if __name__ == "__main__":
    main(sys.argv[1:])