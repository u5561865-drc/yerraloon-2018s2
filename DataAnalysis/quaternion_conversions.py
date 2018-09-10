import math

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

def calculateEulerAngles(quaternions):
    euler_angles = []
    for q in quaternions:
        euler_angles.append(quaternionToEulerAngle(q[0], q[1], q[2], q[3]))
    return euler_angles

def quaternionToAxisAngle(quaternion):
    equation_part = math.sqrt(1 - (quaternion[0] * quaternion[0]))
    angle = 2 * math.acos(quaternion[0])
    # need to handle potential divide by zero here
    if equation_part < 0.001:
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