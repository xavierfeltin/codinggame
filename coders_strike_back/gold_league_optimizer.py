import sys
import math
from math import sqrt
from math import cos
from math import acos
from math import sin
from math import ceil
from math import radians
from math import degrees

# Auto-generated code below aims at helping you parse
# the standard input according to the problem statement.

class Pod:
    def __init__(self, name):
        self.x, self.y, self.vx, self.vy, self.angle, self.nextCheckPointId, self.thrust = 0, 0, 0, 0, 0, 0, 0
        self.next_checkpoint_x, self.next_checkpoint_y = 0, 0
        self.next_checkpoint_angle, self.next_checkpoint_dist = 0, 0
        self.name = name
        self.time_before_availability_shield = 0

    def configure(self, input, list_checkpoints):
        self.x, self.y, self.vx, self.vy, self.angle, self.nextCheckPointId = [int(i) for i in input().split()]
        self.next_checkpoint_x, self.next_checkpoint_y = list_checkpoints[self.nextCheckPointId]
        self.next_checkpoint_angle = self.compute_angle_next_checkpoint()
        self.next_checkpoint_dist = sqrt((self.next_checkpoint_x - self.x) ** 2 + (self.next_checkpoint_y - self.y) ** 2)

    def compute_angle_next_checkpoint(self):
        # Compute the angle between the pod direction and the next checkpoint
        # function of the current angle of the pod
        # based of the scalar product of two vectors : cos Angle = dotProduct(v1, v2) / (norm(v1) * norm(v2))
        # To set the pod's orientation vector, use the angle between the x game axis and the pod direction (self.angle)
        # Scale the cos/sin angle by 1000 to be coherent with the game scale (16 0000 x 9 0000)

        # Set the normalized vector between the pod and the next checkpoint
        vect_pod_checkpoint_x = self.next_checkpoint_x - self.x
        vect_pod_checkpoint_y = self.next_checkpoint_y - self.y
        norm_vect_pod_checkpoint = sqrt(vect_pod_checkpoint_x ** 2 + vect_pod_checkpoint_y ** 2)
        vect_pod_checkpoint_x = vect_pod_checkpoint_x / norm_vect_pod_checkpoint
        vect_pod_checkpoint_y = vect_pod_checkpoint_y / norm_vect_pod_checkpoint

        # Set the normalized vector of the pod's current direction
        vect_pod_direction_x = 1000 * cos(radians(self.angle))
        vect_pod_direction_y = 1000 * sin(radians(self.angle))
        norm_vect_pod_direction = sqrt(vect_pod_direction_x ** 2 + vect_pod_direction_y ** 2)
        vect_pod_direction_x = vect_pod_direction_x / norm_vect_pod_direction
        vect_pod_direction_y = vect_pod_direction_y / norm_vect_pod_direction

        # use round to avoid float imprecision
        scalar_product = round(
            (vect_pod_checkpoint_x * vect_pod_direction_x) + (vect_pod_checkpoint_y * vect_pod_direction_y), 8)

        print(self.name + " scalar : " + str(scalar_product), file=sys.stderr)
        print(self.name + " angle : " + str(degrees(acos(scalar_product))), file=sys.stderr)

        # angle = acos(dotProduct(v1, v2) / (norm(v1) * norm(v2))) and normalized vector has a norm of 1
        return degrees(acos(scalar_product))


#def optimize_thrust(pod.x, pod.y, boss1.x, boss1.y, checkpoint_x, checkpoint_y, checkpoint_angle, pod.next_checkpoint_dist, is_shield_available):
def optimize_thrust(pod, other_pod, boss1, boss2, laps, checkpointCount, list_checkpoints, is_shield_available):
    SAFETY_DISTANCE = 830
    BOOST_DISTANCE = 4200
    MIN_THRUST = 10
    MAX_THRUST = 100
    BOOST = 'BOOST'
    SHIELD = 'SHIELD'
    MIN_TO_CHECKPOINT = 100
    MAX_ANGLE = 120
    MIN_ANGLE = 20
    SLOWING_COEFF = 0.4
    TURN_SHIELD_OFF = 4
    FIRST_SLOWING_DOWN_COEFF_DIST = 8
    FIRST_SLOWING_COEFF = 0.9
    SECOND_SLOWING_DOWN_COEFF_DIST = 4
    SECOND_SLOWING_COEFF = 0.2
    SHIELD_ACTIVATION_COEFF_DIST = 7

    distance_player_boss1 = sqrt((pod.x - boss1.x) ** 2 + (pod.y - boss1.y) ** 2)
    distance_player_boss2 = sqrt((pod.x - boss2.x) ** 2 + (pod.y - boss2.y) ** 2)

    new_destination_x, new_destination_y = manage_trajectory (pod, boss1, boss2, distance_player_boss1, distance_player_boss2)
    #new_destination_x = pod.next_checkpoint_x
    #new_destination_y = pod.next_checkpoint_y

    ## if distance_player_boss1 < SAFETY_DISTANCE :
    #if boss1.x < pod.x and pod.x < pod.next_checkpoint_x:
    #    new_destination_x = new_destination_x - X_DELTA_POSITION
    #elif boss1.x > pod.x and pod.x > pod.next_checkpoint_x:
    #    new_destination_x = new_destination_x + X_DELTA_POSITION

    #if boss1.y < pod.y and pod.y < pod.next_checkpoint_y:
    #    new_destination_y = new_destination_y - Y_DELTA_POSITION
    #elif boss1.y > pod.y and pod.y > pod.next_checkpoint_y:
    #    new_destination_y = new_destination_y + Y_DELTA_POSITION

    abs_angle = abs(pod.next_checkpoint_angle)

    if abs_angle > MAX_ANGLE:
        thrust = MIN_THRUST
    elif abs_angle < MIN_ANGLE:
        thrust = MAX_THRUST
    else:
        thrust = 100 * ((MAX_ANGLE - abs_angle) / MAX_ANGLE)

    coefficient = 1
    if pod.next_checkpoint_dist < MIN_TO_CHECKPOINT:
        # coefficient = 1-((MIN_TO_CHECKPOINT - pod.next_checkpoint_dist) / MIN_TO_CHECKPOINT)
        coefficient = 0
    elif pod.next_checkpoint_dist < SECOND_SLOWING_DOWN_COEFF_DIST * MIN_TO_CHECKPOINT:
        coefficient = SECOND_SLOWING_COEFF
    elif pod.next_checkpoint_dist < FIRST_SLOWING_DOWN_COEFF_DIST * MIN_TO_CHECKPOINT:
        coefficient = FIRST_SLOWING_COEFF

    if (thrust < MIN_THRUST):
        thrust = MIN_THRUST

    thrust = ceil(thrust * coefficient)

    if pod.next_checkpoint_dist > BOOST_DISTANCE and pod.next_checkpoint_angle < MIN_ANGLE:
        thrust = BOOST

    # if pod.next_checkpoint_dist < SHIELD_ACTIVATION_COEFF_DIST * MIN_TO_CHECKPOINT and distance_player_boss1 <= SAFETY_DISTANCE and is_shield_available :
    if (coefficient < 1 or pod.next_checkpoint_dist < SHIELD_ACTIVATION_COEFF_DIST * MIN_TO_CHECKPOINT) and distance_player_boss1 <= SAFETY_DISTANCE and is_shield_available:
        thrust = SHIELD
        pod.time_before_availability_shield = TURN_SHIELD_OFF

    return [new_destination_x, new_destination_y, thrust]

def manage_trajectory (pod, boss1, boss2, distance_player_boss1, distance_player_boss2) :
    #Manage the new destination point function of the bosses positions
    #Take into account the boss that is closer to the pod => avoid contrary measures if two bosses are matching opposing criteria

    X_DELTA_POSITION = 600
    Y_DELTA_POSITION = 600

    new_destination_x = pod.next_checkpoint_x
    new_destination_y = pod.next_checkpoint_y

    boss_to_check = boss1
    if distance_player_boss2 < distance_player_boss1:
        boss_to_check = boss2

    # if distance_player_boss1 < SAFETY_DISTANCE :
    if boss_to_check.x < pod.x and pod.x < pod.next_checkpoint_x:
        new_destination_x = new_destination_x - X_DELTA_POSITION
    elif boss_to_check.x > pod.x and pod.x > pod.next_checkpoint_x:
        new_destination_x = new_destination_x + X_DELTA_POSITION

    if boss_to_check.y < pod.y and pod.y < pod.next_checkpoint_y:
        new_destination_y = new_destination_y - Y_DELTA_POSITION
    elif boss_to_check.y > pod.y and pod.y > pod.next_checkpoint_y:
        new_destination_y = new_destination_y + Y_DELTA_POSITION

    return [new_destination_x, new_destination_y]

# game loop

# Initialization
laps = int(input())
checkpointCount = int(input())

list_checkpoints = []
for i in range(checkpointCount):
    list_checkpoints.append([int(i) for i in input().split()])

is_boost_used = False
time_before_availability_shield = 0  # TODO : one shield by pod

cho = Pod("cho")
gall = Pod("gall")
boss1 = Pod("boss1")
boss2 = Pod("boss2")

while True:
    cho.configure(input, list_checkpoints)
    gall.configure(input, list_checkpoints)
    boss1.configure(input, list_checkpoints)
    boss2.configure(input, list_checkpoints)

    # Write an action using print
    # To debug: print("Debug messages...", file=sys.stderr)

    #cho_optimized_data = optimize_thrust(cho.x, cho.y, boss1.x, boss1.y, cho.next_checkpoint_x, cho.next_checkpoint_y, cho.next_checkpoint_angle, cho.next_checkpoint_dist, time_before_availability_shield <= 0)
    #gall_optimized_data = optimize_thrust(gall.x, gall.y, boss1.x, boss1.y, gall.next_checkpoint_x, gall.next_checkpoint_y, gall.next_checkpoint_angle, gall.next_checkpoint_dist, time_before_availability_shield <= 0)

    cho_optimized_data = optimize_thrust(cho, gall, boss1, boss2, laps, checkpointCount, list_checkpoints, cho.time_before_availability_shield <= 0)
    gall_optimized_data = optimize_thrust(gall, cho, boss1, boss2, laps, checkpointCount, list_checkpoints, gall.time_before_availability_shield <= 0)

    #Reduce SHIELD Cooldown
    cho.time_before_availability_shield = cho.time_before_availability_shield - 1
    gall.time_before_availability_shield = gall.time_before_availability_shield - 1

    print(cho.name + " thrust : " + str(cho_optimized_data[2]), file=sys.stderr)
    print(gall.name + " thrust : " + str(gall_optimized_data[2]), file=sys.stderr)

    # You have to output the target position
    # followed by the power (0 <= thrust <= 100)
    # i.e.: "x y thrust"
    print(str(cho_optimized_data[0]) + " " + str(cho_optimized_data[1]) + " " + str(cho_optimized_data[2]))
    print(str(gall_optimized_data[0]) + " " + str(gall_optimized_data[1]) + " " + str(gall_optimized_data[2]))