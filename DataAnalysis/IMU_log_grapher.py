import csv
import math
import sys
import matplotlib.pyplot as plt
import datetime

# Method for converting from quaternions to Euler angles, taken from:
# https://en.wikipedia.org/wiki/Conversion_between_quaternions_and_Euler_angles
def quaternion_to_euler_angle(x, y, z, w):
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
                    quat.append((float(quat_temp[0]),\
                                 float(quat_temp[1]),\
                                 float(quat_temp[2]),\
                                 float(col)))
                if col_i == 11: # temperature
                    temp_c.append(float(col))
                col_i += 1
        row_i += 1

    total_lines = row_i - 1

    # calculate things in seconds since start
    time_fmt = '%H:%M:%S.%f'
    reference_time = datetime.datetime.strptime(tstamp[0], time_fmt)
    elapsed_time = []
    average_data_rate = 0
    time_since_previous = []
    for index in i:
        elapsed_time.append((datetime.datetime.strptime(tstamp[index],\
                                                       time_fmt) -\
                             reference_time).total_seconds())
        # I want to calculate the time difference between each piece of 
        # data here, and spit out an average frequency
        # also keep the times between each piece of data, as this will allow
        # for me space datapoints correctly on the graph
        if index == 0:
            time_since_previous.append(0)
        else:   
            time_since_previous.append((datetime.datetime.strptime(\
                                                            tstamp[index],\
                                                            time_fmt)) -\
                                        datetime.datetime.strptime(\
                                                            tstamp[index-1],\
                                                            time_fmt))
            average_data_rate += (time_since_previous[index].microseconds)

    average_data_rate = average_data_rate / total_lines
    # convert to Hz
    average_data_rate = (1000000 / average_data_rate)
    average_data_rate_string = "Average IMU read rate: " +\
                               str(round(average_data_rate, 3)) +\
                               " (Hz)"

    x_data = []
    y_data = []
    z_data = []
    w_data = []
    for index in i:
        x_data.append(quat[index][0])
        y_data.append(quat[index][1])
        z_data.append(quat[index][2])
        w_data.append(quat[index][3])
    # convert all data to euler angles
    eul_x = []
    eul_y = []
    eul_z = []
    for index in i: 
        eul_temp = quaternion_to_euler_angle(quat[index][0],\
                                             quat[index][1],\
                                             quat[index][2],\
                                             quat[index][3])
        eul_x.append(eul_temp[0])
        eul_y.append(eul_temp[1])
        eul_z.append(eul_temp[2])

    # convert quaternions to axis angles (position relative to origin)
    ax_angle = []
    ax_x = []
    ax_y = []
    ax_z = []
    #http://www.euclideanspace.com/maths/geometry/rotations/conversions/quaternionToAngle/index.htm
        # angle = 2 * acos(qw)
        # x = qx / sqrt(1-qw*qw)
        # y = qy / sqrt(1-qw*qw)
        # z = qz / sqrt(1-qw*qw)
    for index in i:
        eq_part = math.sqrt(1 - (w_data[index] * w_data[index]))
        ax_angle.append(2 * math.acos(w_data[index]))
        # need to handle the potential divide be zero here
        ax_x.append(x_data[index] / eq_part)
        ax_y.append(y_data[index] / eq_part)
        ax_z.append(z_data[index] / eq_part)


    # draw all quaternions 
    plt.figure(1)
    plt.subplot(411)
    plt.title("Orientation in quaternions\n"+average_data_rate_string)
    plt.plot(elapsed_time, w_data)
    plt.ylabel("w")
    plt.subplot(412)
    plt.plot(elapsed_time, x_data)
    plt.ylabel("x")
    plt.subplot(413)
    plt.plot(elapsed_time, y_data)
    plt.ylabel("y")
    plt.subplot(414)
    plt.plot(elapsed_time, z_data)
    plt.ylabel("z")
    plt.xlabel("elapsed seconds") 

    # draw all euler angles
    plt.figure(2)  
    plt.subplot(311)
    plt.title("Orientation in Euler angles\n"+average_data_rate_string)
    plt.plot(elapsed_time, eul_x)
    plt.ylabel("roll (degrees)")
    plt.subplot(312)
    plt.plot(elapsed_time, eul_y)
    plt.ylabel("pitch (degrees)")
    plt.subplot(313)
    plt.plot(elapsed_time, eul_z)
    plt.ylabel("yaw (degrees)")
    plt.xlabel("elapsed seconds (s)")

    # draw all axis angles 
    plt.figure(3)
    plt.subplot(221)
    plt.title("Orientation in axis angles\n"+average_data_rate_string)
    plt.plot(elapsed_time, ax_angle)
    plt.ylabel("angle")
    plt.subplot(222)
    plt.plot(elapsed_time, ax_x)
    plt.ylabel("x")
    plt.subplot(223)
    plt.plot(elapsed_time, ax_y)
    plt.ylabel("y")
    plt.subplot(224)
    plt.plot(elapsed_time, ax_z)
    plt.ylabel("z")
    plt.xlabel("elapsed seconds") 

    plt.show()

if __name__ == "__main__":
    main(sys.argv[1:])