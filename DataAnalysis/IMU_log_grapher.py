import sys
import matplotlib.pyplot as plt
import imu_log
import quaternion_conv 

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

def main(argv):
    file = open(argv[0])
    
    (total_lines, indices, timestamps, gyro_data,
     acc_data, quaternions, temperatures)          = imu_log.parseFile(file)
    
    euler_angles = quaternion_conv.calculateEulerAngles(quaternions)
    axis_angles = quaternion_conv.calculateAxisAngles(quaternions)
    
    (reference_time, average_time_delta, time_deltas, 
     cumulative_elapsed_times) = imu_log.calculateTimeDeltas(timestamps)

    plotQuaternions(quaternions, cumulative_elapsed_times, 1)
    plotEulerAngles(euler_angles, cumulative_elapsed_times, 2)
    plotAxisAngles(axis_angles, cumulative_elapsed_times, 3)

    plt.show()

if __name__ == "__main__":
    main(sys.argv[1:])