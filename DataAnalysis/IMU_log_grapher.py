import csv
import math
import sys
import matplotlib.pyplot as plt
import datetime

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
        euler_angles.append(quaternionToEulerAngle(q[0], q[1], q[2], q[3]))
    return euler_angles

def calculateAxisAngles(quaternions):
    axis_angles = []
    for q in quaternions:
        eq_part = math.sqrt(1 - (q[0] * q[0]))
        angle = 2 * math.acos(q[0])
        # need to handle potential divide by zero here
        # axis may need to be normalised
        if eq_part < 0.001:
            axis_angles.append((angle,\
                               q[1],\
                               q[2],\
                               q[3]))
        else:
            axis_angles.append((angle,\
                               q[1] / eq_part,\
                               q[2] / eq_part,\
                               q[3] / eq_part))
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

    # average_time_delta = average_time_delta / index
    # convert to Hz
    # average_time_delta_Hz = (1000000 / average_time_delta)
    # average_data_rate_string = "Average IMU read rate: " +\
                               # str(round(average_time_delta_Hz, 3)) +\
                               # " (Hz)"
    # print(average_data_rate_string)

    return (reference_time, average_time_delta,\
            time_deltas, cumulative_elapsed_times)

def plotQuaternions(quaternions, cumulative_elapsed_times, figure_no):
    plt.figure(figure_no)
    plt.subplot(411)
    # plt.title("Orientation in quaternions\n"+average_data_rate_string)
    w_data = []
    x_data = []
    y_data = []
    z_data = []
    for q in quaternions:
        w_data.append(q[0])
        x_data.append(q[1])
        y_data.append(q[2])
        z_data.append(q[3])

    plt.plot(cumulative_elapsed_times, w_data)
    plt.ylabel("w")
    plt.subplot(412)
    plt.plot(cumulative_elapsed_times, x_data)
    plt.ylabel("x")
    plt.subplot(413)
    plt.plot(cumulative_elapsed_times, y_data)
    plt.ylabel("y")
    plt.subplot(414)
    plt.plot(cumulative_elapsed_times, z_data)
    plt.ylabel("z")
    plt.xlabel("elapsed seconds") 

def plotEulerAngles(euler_angles, cumulative_elapsed_times, figure_no):
    plt.figure(figure_no)
    plt.subplot(311)
    # plt.title("Orientation in Euler angles\n"+average_data_rate_string)
    eul_x = []
    eul_y = []
    eul_z = []
    for e in euler_angles:
        eul_x.append(e[0])
        eul_y.append(e[1])
        eul_z.append(e[2])
    plt.plot(cumulative_elapsed_times, eul_x)
    plt.ylabel("roll (degrees)")
    plt.subplot(312)
    plt.plot(cumulative_elapsed_times, eul_y)
    plt.ylabel("pitch (degrees)")
    plt.subplot(313)
    plt.plot(cumulative_elapsed_times, eul_z)
    plt.ylabel("yaw (degrees)")
    plt.xlabel("elapsed seconds (s)")

def plotAxisAngles(axis_angles, cumulative_elapsed_times, figure_no):
    plt.figure(figure_no)
    plt.subplot(221)
    # plt.title("Orientation in axis angles\n"+average_data_rate_string)
    ax_angle = []
    ax_x = []
    ax_y = []
    ax_z = []
    for a in axis_angles:
        ax_angle.append(a[0])
        ax_x.append(a[1])
        ax_y.append(a[2])
        ax_z.append(a[3])
    plt.plot(cumulative_elapsed_times, ax_angle)
    plt.ylabel("angle")
    plt.subplot(222)
    plt.plot(cumulative_elapsed_times, ax_x)
    plt.ylabel("x")
    plt.subplot(223)
    plt.plot(cumulative_elapsed_times, ax_y)
    plt.ylabel("y")
    plt.subplot(224)
    plt.plot(cumulative_elapsed_times, ax_z)
    plt.ylabel("z")
    plt.xlabel("elapsed seconds") 

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
    
    (total_lines, indices, timestamps, gyro_data,\
     acc_data, quaternions, temperatures)          = parseFile(file)
    
    euler_angles = calculateEulerAngles(quaternions)
    axis_angles = calculateAxisAngles(quaternions)
    
    (reference_time, average_time_delta,\
     time_deltas, cumulative_elapsed_times) = calculateTimeDeltas(timestamps)
    
    # convert data rate to Hz
    # average_time_delta_Hz = (1000000 / average_time_delta)
    # average_data_rate_string = "Average IMU read rate: " +\/
                               # str(round(average_time_delta_Hz, 3)) +\
                               # " (Hz)"
                            
    plotQuaternions(quaternions, cumulative_elapsed_times, 1)
    plotEulerAngles(euler_angles, cumulative_elapsed_times, 2)
    plotAxisAngles(axis_angles, cumulative_elapsed_times, 3)

    plt.show()

if __name__ == "__main__":
    main(sys.argv[1:])