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

# Optimizer Constants
TARGET_OTHER_POD = 1
TARGET_BOSS1 = 2
TARGET_BOSS2 = 3
TARGET_NEXT_CHECKPOINT = 4

SAFETY_DISTANCE = 830
BOOST_DISTANCE = 4200
X_DELTA_POSITION = 600
Y_DELTA_POSITION = 600
X_DELTA_FOLLOWER = 600
Y_DELTA_FOLLOWER = 600

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


class Pod:
    def __init__(self, name):
        self.x, self.y, self.vx, self.vy, self.angle, self.nextCheckPointId, self.thrust = 0, 0, 0, 0, 0, 0, 0
        self.next_checkpoint_x, self.next_checkpoint_y = 0, 0
        self.next_checkpoint_angle, self.next_checkpoint_dist = 0, 0
        self.name = name
        self.time_before_availability_shield = 0

        # Refactoring
        self.next_target_x = 0
        self.next_target_y = 0
        self.next_target_dist = 0
        self.next_target_angle = 0
        self.targetID = -1
        self.distance_boss1 = 0
        self.distance_boss2 = 0
        self.distance_other_pod = 0

    def configure_input(self, input, list_checkpoints):
        self.x, self.y, self.vx, self.vy, self.angle, self.nextCheckPointId = [int(i) for i in input().split()]
        self.next_checkpoint_x, self.next_checkpoint_y = list_checkpoints[self.nextCheckPointId]
        self.next_checkpoint_angle = self.compute_angle_next_target()
        self.next_checkpoint_dist = sqrt((self.next_checkpoint_x - self.x) ** 2 + (self.next_checkpoint_y - self.y) ** 2)

    def configure_target(self, other_pod, boss1, boss2, targetID):
        self.targetID = targetID

        if self.targetID == TARGET_OTHER_POD:
            self.next_target_x = other_pod.x
            self.next_target_y = other_pod.y
        elif self.targetID == TARGET_BOSS1:
            self.next_target_x = boss1.x
            self.next_target_y = boss1.y
        elif self.targetID == TARGET_BOSS2:
            self.next_target_x = boss2.x
            self.next_target_y = boss2.y
        elif self.targetID == TARGET_NEXT_CHECKPOINT:
            self.next_target_x = self.next_checkpoint_x
            self.next_target_y = self.next_checkpoint_y
        else:
            self.next_target_x = self.next_checkpoint_x
            self.next_target_y = self.next_checkpoint_y

        self.next_target_dist = sqrt((self.next_target_x - self.x) ** 2 + (self.next_target_y - self.y) ** 2)
        self.next_target_angle = self.compute_angle_next_target()

        self.distance_boss1 = sqrt((self.x - boss1.x) ** 2 + (self.y - boss1.y) ** 2)
        self.distance_boss2 = sqrt((self.x - boss2.x) ** 2 + (self.y - boss2.y) ** 2)
        self.distance_other_pod = sqrt((self.x - other_pod.x) ** 2 + (self.y - other_pod.y) ** 2)

    def compute_angle_next_target(self):
        # Compute the angle between the pod direction and the next target
        # function of the current angle of the pod
        # based of the scalar product of two vectors : cos Angle = dotProduct(v1, v2) / (norm(v1) * norm(v2))
        # To set the pod's orientation vector, use the angle between the x game axis and the pod direction (self.angle)
        # Scale the cos/sin angle by 1000 to be coherent with the game scale (16 0000 x 9 0000)

        # Set the normalized vector between the pod and the next checkpoint
        vect_pod_target_x = self.next_target_x - self.x
        vect_pod_target_y = self.next_target_y - self.y
        norm_vect_pod_target = sqrt(vect_pod_target_x ** 2 + vect_pod_target_y ** 2)
        vect_pod_target_x = vect_pod_target_x / norm_vect_pod_target
        vect_pod_target_y = vect_pod_target_y / norm_vect_pod_target

        # Set the normalized vector of the pod's current direction
        vect_pod_direction_x = 1000 * cos(radians(self.angle))
        vect_pod_direction_y = 1000 * sin(radians(self.angle))
        norm_vect_pod_direction = sqrt(vect_pod_direction_x ** 2 + vect_pod_direction_y ** 2)
        vect_pod_direction_x = vect_pod_direction_x / norm_vect_pod_direction
        vect_pod_direction_y = vect_pod_direction_y / norm_vect_pod_direction

        # use round to avoid float imprecision
        scalar_product = round((vect_pod_target_x * vect_pod_direction_x) + (vect_pod_target_y * vect_pod_direction_y), 8)

        print(self.name + " scalar : " + str(scalar_product), file=sys.stderr)
        print(self.name + " angle : " + str(degrees(acos(scalar_product))), file=sys.stderr)

        # angle = acos(dotProduct(v1, v2) / (norm(v1) * norm(v2))) and normalized vector has a norm of 1
        return degrees(acos(scalar_product))


def optimize_thrust(pod, other_pod, boss1, boss2, laps, checkpointCount, list_checkpoints, is_shield_available):
    new_destination_x, new_destination_y = manage_trajectory(pod, other_pod, boss1, boss2)
    abs_angle = abs(pod.next_target_angle)

    if abs_angle > MAX_ANGLE:
        thrust = MIN_THRUST
    elif abs_angle < MIN_ANGLE:
        thrust = MAX_THRUST
    else:
        thrust = 100 * ((MAX_ANGLE - abs_angle) / MAX_ANGLE)

    coefficient = 1
    if pod.targetID == TARGET_NEXT_CHECKPOINT or pod.targetID == TARGET_OTHER_POD:
        if pod.next_target_dist < MIN_TO_CHECKPOINT:
            # coefficient = 1-((MIN_TO_CHECKPOINT - pod.next_checkpoint_dist) / MIN_TO_CHECKPOINT)
            coefficient = 0
        elif pod.next_target_dist < SECOND_SLOWING_DOWN_COEFF_DIST * MIN_TO_CHECKPOINT:
            coefficient = SECOND_SLOWING_COEFF
        elif pod.next_target_dist < FIRST_SLOWING_DOWN_COEFF_DIST * MIN_TO_CHECKPOINT:
            coefficient = FIRST_SLOWING_COEFF
    else:  # The target is a boss
        coefficient = 1  # TODO : improve the approach of the bosses

    if (thrust < MIN_THRUST):
        thrust = MIN_THRUST

    thrust = ceil(thrust * coefficient)

    if pod.next_target_dist > BOOST_DISTANCE and pod.next_target_angle < MIN_ANGLE:
        thrust = BOOST

    distance_boss_to_check = pod.distance_boss1
    if pod.distance_boss2 < pod.distance_boss1:
        distance_boss_to_check = pod.distance_boss2

    if pod.targetID == TARGET_NEXT_CHECKPOINT:
        if (coefficient < 1 or pod.next_target_dist < SHIELD_ACTIVATION_COEFF_DIST * MIN_TO_CHECKPOINT) and distance_boss_to_check <= SAFETY_DISTANCE and is_shield_available:
            thrust = SHIELD
            pod.time_before_availability_shield = TURN_SHIELD_OFF
    elif pod.targetID == TARGET_OTHER_POD:
        if coefficient < 1 and distance_boss_to_check <= SAFETY_DISTANCE and is_shield_available:
            thrust = SHIELD
            pod.time_before_availability_shield = TURN_SHIELD_OFF
    else:  # Target are bosses
        distance_boss_to_tareget = pod.distance_boss1
        if pod.targetID == TARGET_BOSS2:
            distance_boss_to_tareget = pod.distance_boss2

        if distance_boss_to_tareget <= SAFETY_DISTANCE and is_shield_available:
            thrust = SHIELD
            pod.time_before_availability_shield = TURN_SHIELD_OFF

    return [new_destination_x, new_destination_y, thrust]


def manage_trajectory(pod, other_pod, boss1, boss2):
    # Manage the new destination point function of the bosses positions
    # Take into account the boss that is closer to the pod => avoid contrary measures if two bosses are matching opposing criteria

    if pod.targetID == TARGET_OTHER_POD:
        new_destination_x = other_pod.x - X_DELTA_FOLLOWER
        new_destination_y = other_pod.y - Y_DELTA_FOLLOWER
    elif pod.targetID == TARGET_BOSS1:
        new_destination_x = boss1.x
        new_destination_y = boss1.y
    elif pod.targetID == TARGET_BOSS2:
        new_destination_x = boss2.x
        new_destination_y = boss2.y
    else:
        new_destination_x = pod.next_checkpoint_x
        new_destination_y = pod.next_checkpoint_y

    boss_to_check = boss1
    if pod.distance_boss2 < pod.distance_boss1:
        boss_to_check = boss2

    # Anticipate deviation from the target due to bosses impacts (do not manage it for now when targeting other bosses)
    if pod.targetID == TARGET_OTHER_POD or pod.targetID == TARGET_NEXT_CHECKPOINT:
        if boss_to_check.x < pod.x and pod.x < pod.next_target_x:
            new_destination_x = new_destination_x - X_DELTA_POSITION
        elif boss_to_check.x > pod.x and pod.x > pod.next_target_x:
            new_destination_x = new_destination_x + X_DELTA_POSITION

        if boss_to_check.y < pod.y and pod.y < pod.next_target_y:
            new_destination_y = new_destination_y - Y_DELTA_POSITION
        elif boss_to_check.y > pod.y and pod.y > pod.next_target_y:
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
    cho.configure_input(input, list_checkpoints)
    gall.configure_input(input, list_checkpoints)
    boss1.configure_input(input, list_checkpoints)
    boss2.configure_input(input, list_checkpoints)

    cho.configure_target(gall, boss1, boss2, TARGET_NEXT_CHECKPOINT)
    gall.configure_target(cho, boss1, boss2, TARGET_OTHER_POD)

    # Could be useful later on to approximate bosses destination
    boss1.configure_target(boss1, boss1, boss2, TARGET_NEXT_CHECKPOINT)
    boss2.configure_target(boss2, boss1, boss2, TARGET_NEXT_CHECKPOINT)

    cho_optimized_data = optimize_thrust(cho, gall, boss1, boss2, laps, checkpointCount, list_checkpoints, cho.time_before_availability_shield <= 0)
    gall_optimized_data = optimize_thrust(gall, cho, boss1, boss2, laps, checkpointCount, list_checkpoints, gall.time_before_availability_shield <= 0)

    # Reduce SHIELD Cooldown
    cho.time_before_availability_shield = cho.time_before_availability_shield - 1
    gall.time_before_availability_shield = gall.time_before_availability_shield - 1

    # Write an action using print
    # To debug: print("Debug messages...", file=sys.stderr)
    print(cho.name + " thrust : " + str(cho_optimized_data[2]), file=sys.stderr)
    print(gall.name + " thrust : " + str(gall_optimized_data[2]), file=sys.stderr)

    # You have to output the target position
    # followed by the power (0 <= thrust <= 100)
    # i.e.: "x y thrust"
    print(str(cho_optimized_data[0]) + " " + str(cho_optimized_data[1]) + " " + str(cho_optimized_data[2]))
    print(str(gall_optimized_data[0]) + " " + str(gall_optimized_data[1]) + " " + str(gall_optimized_data[2]))