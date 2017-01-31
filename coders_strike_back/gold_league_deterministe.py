import sys

import time
from math import sqrt
from math import log
from math import cos
from math import acos
from math import sin
from math import asin
from math import ceil
from math import floor
from math import radians
from math import degrees
from math import pi
from math import inf
from random import randint
from random import uniform

# Auto-generated code below aims at helping you parse
# the standard input according to the problem statement.

FRICTION = 0.85  # (game constraint) friction factor applied on pods
PRECISION = 6  # floating precision
TIMEOUT = 100  # number of turns for a pod to reach its next checkpoint
TIME_FULL_TURN = 1.0  # a full turn has a time of 1

RADIUS_POD = 400
RADIUS_CHECKPOINT = 600
RADIUS_WAYPOINT = 72
POSITION_WAYPOINT_CHECKPOINT = 300
MIN_ANGLE_TAKE_ACCOUNT_COLLISION = 10
TIME_BEFORE_DETECTION_CHECKPOINT = 0.02
COEFFICIENT_DISTANCE_COLLISION = 15  # nb times checkpoint raidus to validate a checkpoint collision (use to fix high speed and too early detection)
NB_TURN_ROLLBACK = 2

TIME_BEFORE_DETECTION_POD = 0.001
SAFETY_DISTANCE = RADIUS_POD + RADIUS_POD + 50
SHIELD = 'SHIELD'
SHIELD_COOLDOWN = 3
SHIELD_ACTIVATION_SPEED = 50

MAX_THRUST = 100
MIN_THRUST = 20
BOOST = 'BOOST'
MAX_ANGLE_SPEED = 120
MIN_ANGLE_SPEED = 20
MIN_DISTANCE_BOOST = 3000
FIRST_SLOWING_COEFFICIENT = 0.7
SECOND_SLOWING_COEFFICIENT = 0.2
NB_TURN_DECREASE = 3
DEFAULT_SPEED = 100

BIG_SCORE_TO_OPTIMIZE = 100000


class Point():
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def get_distance2(self, b):
        '''
        Return the square of the euclidian distance between the current point and the b point
        '''
        return (self.x - b.x) ** 2 + (self.y - b.y) ** 2

    def get_distance(self, b):
        '''
        Return the euclidian distance between the current point and the b point
        '''
        return sqrt(self.get_distance2(b))

    def get_closest(a, b):
        '''
        Return the closest point on the line passing through the a and b points of the current point
        '''
        # TODO : understand the mathematical magic behind these equations

        da = b.y - a.y
        db = a.x - b.x
        c1 = da * a.x + db * a.y
        c2 = -db.self.x + da * self.y
        det = da ** 2 + db ** 2

        closest_point_x = 0
        closest_point_y = 0

        if det == 0:
            # Point is already on the line (ab)
            closest_point_x = self.x
            closest_point_y = self.y
        else:
            # Compute orthogonal projection of current point on the line (ab)
            closest_point_x = (da * c1 - db * c2) / det
            closest_point_y = (da * c2 + db * c1) / det

        return Point(closest_point_x, closest_point_y)


class Unit(Point):
    def __init__(self, id, radius):
        Point.__init__(self, 0, 0)
        self.id = id
        self.radius = radius
        self.vx = 0.0
        self.vy = 0.0

    def get_collision(self, other):
        '''
        Return the Collision object between the current unit and the unit in parameter
        :param other: Unit on which we detect the collision
        :return: the collision if there is contact otherwise None
        '''

        # Use square distance to avoid using root function
        distance_to_other = self.get_distance2(other)
        length_radii_squared = (self.radius + other.radius) ** 2  # +1000 to anticipate checkpoints

        if distance_to_other < length_radii_squared:
            # Units are already in contact so there is an immediate collision
            return Collision(self, other, 0.0)

        # Optimisation : units with the same vector speed will never collide
        if self.vx == other.vx and self.vy == other.vy:
            return None

        # Set other unit as the new reference (other is stationary and is positionned at (0, 0)
        x = self.x - other.x
        y = self.y - other.y
        pod_in_referential = Point(x, y)
        vx = self.vx - other.vx
        vy = self.vy - other.vy
        other_in_referential = Point(0, 0)

        # Get the closest point to other unit (which is in (0,0)) on the line described by the pod speed vector
        # closest_projection = other_in_referential.get_closest(pod_in_referential, Point(x + vx, y + vy))
        closest_projection = Point(0, 0)

        # Distance(squared) between the other unit and the closest point to the other unit on the line described by our speed vector
        distance_unit_closest_projection = other_in_referential.get_distance2(closest_projection)

        # Distance(squared) between the pod and the projection
        distance_pod_closest_projection = pod_in_referential.get_distance2(closest_projection)

        # If the distance between other unit and this line is less than the sum of the radii, there might be a collision
        if distance_unit_closest_projection < length_radii_squared:
            # The pod speed on the line (norm)
            speed_distance = vx ** 2 + vy ** 2

            # Project the pod on the line to find the point of impact
            distance_intersection_units = sqrt(length_radii_squared - distance_unit_closest_projection)
            closest_projection.x = closest_projection.x - distance_intersection_units * (vx / speed_distance)
            closest_projection.y = closest_projection.y - distance_intersection_units * (vy / speed_distance)

            # If the projection point is further away means the pod direction is opposite of the other unit
            # => no collision will happen
            if pod_in_referential.get_distance2(closest_projection) > distance_pod_closest_projection:
                return None

            distance_pod_closest_projection = closest_projection.get_distance(pod_in_referential)

            # If the impact point is further than what the pod can travel in one turn
            # Collision will be managed in another turn
            if distance_pod_closest_projection > speed_distance:
                return None

            # Get the time needed to reach the impact point during this turn
            time = round(distance_pod_closest_projection / speed_distance, 4)

            return Collision(self, other, time)
        else:
            return None

    def bounce(self, other):
        '''
        Manage the bounce effect due to the impact of the shield of the current unit and the unit in parameters
        :param other: Unit colliding with the current unit
        :return: none
        '''
        print('TODO', file=sys.stderr)


class Checkpoint(Unit):
    def __init__(self, id, x, y, radius):
        Unit.__init__(self, id, radius)
        self.x = x
        self.y = y

    def bounce(self, other):
        '''
        Manage the bounce effect due to the impact of the shield of the current unit and the unit in parameters
        :param other: Unit colliding with the current unit
        :return: none
        '''
        print('TODO', file=sys.stderr)

    def clone(self):
        return Checkpoint(self.id, self.x, self.y, self.radius)


class Pod(Unit):
    def __init__(self, id, radius):
        Unit.__init__(self, id, radius)
        self.angle = 0
        self.next_checkpoint_id = 0
        self.lap = 1
        self.checked = 0  # number of checkpoints checked
        self.timeout = TIMEOUT
        # self.partner = None
        self.is_shield_activated = False
        self.path = None
        self.check_next_checkpoint_id = 0
        self.switch_checkpoint = 0
        self.turn_activated_shield = 5

    def set_path(self, path):
        self.path = path.clone()
        self.next_checkpoint_id = 1

    def set_partner(self, partner):
        self.partner = partner

    def set_parameters(self, input, checked, is_shield_activated):
        # self.x, self.y, self.vx, self.vy, self.angle, self.next_checkpoint_id = [int(i) for i in input().split()]
        self.x, self.y, self.vx, self.vy, self.angle, self.check_next_checkpoint_id = [int(i) for i in input().split()]

        self.checked = checked
        self.is_shield_activated = is_shield_activated

    def get_angle(self, p):
        '''
        Get the angle between the vector (pod, p) and the x game axis vector (1, 0)
        (game constraint) 0° pod faces East, 90° pod faces South, ...
        :param p: Point to compute the angle with the pod
        :return: an angle
        '''

        # normalized vector pod - p
        norm = self.get_distance(p)
        vector_x = (p.x - self.x) / norm
        vector_y = (p.y - self.y) / norm

        # get angle in degrees (radians / 180.0 * PI)
        angle = acos(vector_x) * 180.0 / pi  # acos (vector_x * 1.0 - vector_y * 0.0)

        # If the point is below switch the angle sign to be correct
        if vector_y < 0:
            angle = 360.0 - angle

        return angle

    def get_delta_angle_orientation(self, p):
        '''
        Define the oriented delta angle for the rotation that the pod must perform to move from its current angle to the new angle with the point p
        :param p: Point targeted by the pod
        :return: oriented angle to move from the current angle to the angle with the point p
        '''

        angle_pod_p = self.get_angle(p)

        # To know whether the pod turns clockwise or not, check the left and right direction and keep the smallest
        if self.angle <= angle_pod_p:
            right_side_angle = angle_pod_p - self.angle
        else:
            right_side_angle = 360.0 - self.angle + angle_pod_p

        if self.angle >= angle_pod_p:
            left_side_angle = self.angle - angle_pod_p
        else:
            left_side_angle = self.angle + 360.0 - angle_pod_p

        if right_side_angle < left_side_angle:
            return right_side_angle
        else:
            # Return a negative angle to rotate on the left
            return left_side_angle * -1.0

    def rotate(self, p):
        '''
        Rotate the pod in order to face the point p
        (game constraint) The rotation is limited to 18° by turn
        :param p: Point to face for the pod
        :return: none
        '''

        delta_angle = self.get_delta_angle_orientation(p)

        if delta_angle > 18.0:
            # rotate on the right side
            delta_angle = 18.0
        elif delta_angle < -18:
            # rotate on the left side
            delta_angle = -18.0

        self.angle += delta_angle

        # Replace the angle between [0; 360] degrees
        # mod operator is slower than if comparison
        self.angle = formalize_angle(self.angle)

    def rotate_move(self, move):

        delta_angle = move.angle

        # if delta_angle > 18.0:
        # rotate on the right side
        #    delta_angle = 18.0
        # elif delta_angle < -18:
        # rotate on the left side
        #    delta_angle = -18.0

        self.angle += delta_angle

        # Replace the angle between [0; 360] degrees
        # mod operator is slower than if comparison
        self.angle = formalize_angle(self.angle)

    def accelerate(self, thrust):
        '''
        Determine the new velocity vector of the pod along its direction
        :param thrust: thrust of the pod
        :return: none
        '''

        if not self.is_shield_activated:
            angle_radians = self.angle * pi / 180.0
            self.vx += cos(angle_radians) * thrust
            self.vy += sin(angle_radians) * thrust

    def move(self, time):
        '''
        Move the pod function of its velocity vector function of the time
        :param time: time between [0.0, 1.0]
        :return: none
        '''
        self.x += self.vx * time
        self.y += self.vy * time

    def finalize(self):
        '''
        Apply the remaining forces to the pod at the end of the turn
        - Friction
        - Round values
        - Timeout to reach the next checkpoint
        :return:
        '''

        self.x = floor(self.x)
        self.y = floor(self.y)
        self.vx = round(self.vx * FRICTION, PRECISION)
        self.vy = round(self.vy * FRICTION, PRECISION)

        # Timeout goes down by 1 each turn. It is reset to 100 when the pod passes its next checkpoint
        self.timeout -= 1;

    def play(self, p, thrust):
        '''
        Play the current turn of the pod to move toward the point P a the thrust given in parameters
        :param p: Point to reach
        :param thrust: thrust applied on the pod
        :return: none
        '''
        self.rotate(p)
        self.accelerate(thrust)
        self.move(TIME_FULL_TURN)  # time = 1.0 is a complete turn
        self.finalize()

    def bounce(self, other):
        '''
        Manage the bounce effect due to the impact of the shield of the current unit and the unit in parameters
        :param other: Unit colliding with the current unit
        :return: none
        '''

        if isinstance(other, Checkpoint):
            self.bounce_with_checkpoint(other)

    def bounce_with_checkpoint(self, checkpoint):
        '''
        Manage collosion with a checkpoint
        '''

        if int(checkpoint.id) == int(self.next_checkpoint_id):
            self.next_checkpoint_id += 1
            self.checked += 1
            self.switch_checkpoint = turn

            if self.next_checkpoint_id == checkpointCount and self.lap < laps:
                self.next_checkpoint_id = 0
                self.lap += 1
            elif self.next_checkpoint_id == checkpointCount and self.lap == laps:
                self.next_checkpoint_id = -1

            self.timeout = TIMEOUT

    def score(self):
        '''
        Get the score for the pod
        :return: score
        '''
        # passing checkpoints is the top priority
        return self.checked * 50000 - self.get_distance(self.get_next_checkpoint_entry_point())
        # return (self.checked * 10000) - abs(self.get_delta_angle_orientation(self.get_next_checkpoint())) - self.get_angle(self.get_next_checkpoint()) - (self.get_distance(self.get_next_checkpoint()) * 2)

    def apply(self, move):
        '''
        Apply the move onto the player
        turn the pod and apply the thrust
        :param move: move to apply
        :return: non
        '''

        # self.output(move, False)
        self.angle += move.angle
        self.accelerate(move.thrust)
        ##self.play(list_checkpoints[self.next_checkpoint_id], move.thrust)

    def get_next_checkpoint(self):
        return self.path.get_node(self.next_checkpoint_id)
        # return list_checkpoints[self.next_checkpoint_id]

    def get_next_checkpoint_entry_point(self):
        '''
        Return the entry point of the next check point function of the direction of the checkpoint coming after
        :return:
        '''
        next_checkpoint = list_checkpoints[self.next_checkpoint_id]

        id = self.get_checkpoint_id_coming_after()
        if id != -1:
            future_checkpoint = list_checkpoints[id]

            delta_angle = self.get_delta_angle_orientation(future_checkpoint)

            final_angle = self.angle + delta_angle

            # Replace the angle between [0; 360] degrees
            # mod operator is slower than if comparison
            if final_angle >= 360.0:
                final_angle -= 360.0
            elif final_angle < 0.0:
                final_angle += 360.0

            radians_angle = final_angle * pi / 180.0

            return Point(next_checkpoint.x + (RADIUS_CHECKPOINT - POSITION_WAYPOINT_CHECKPOINT) * cos(radians_angle), next_checkpoint.y + (RADIUS_CHECKPOINT - POSITION_WAYPOINT_CHECKPOINT) * sin(radians_angle))

        else:
            return Point(next_checkpoint.x, next_checkpoint.y)

    def get_checkpoint_id_coming_after(self):
        '''
        Return the id of the checkpoint coming after the next one
        :return: checkpoint id
        '''

        future_checkpoint_id = self.next_checkpoint_id + 1
        if future_checkpoint_id == checkpointCount and self.lap < laps:
            future_checkpoint_id = 0
        elif future_checkpoint_id == checkpointCount and self.lap == laps:
            future_checkpoint_id = -1

        return future_checkpoint_id

    def load(self, saved_pod):
        self.x = saved_pod.x
        self.y = saved_pod.y
        self.vx = saved_pod.vx
        self.pod = saved_pod.vy
        self.angle = saved_pod.angle
        self.next_checkpoint_id = saved_pod.next_checkpoint_id
        self.lap = saved_pod.lap
        self.checked = saved_pod.checked
        self.timeout = saved_pod.timeout
        # self.partner = saved_pod.partner
        self.is_shield_activated = saved_pod.is_shield_activated

    def output(self, move, commit, previous_collision):
        '''
        Apply the move on the pod and print result to game engine
        :param move: Move
        :return: none
        '''

        if previous_collision is None:
            print(str(self.id) + ' - Next checkpoint ID : ' + str(self.next_checkpoint_id), file=sys.stderr)
        else:
            print(str(self.id) + ' - Recursive checkpoint ID : ' + str(self.next_checkpoint_id), file=sys.stderr)

        # self.rotate_move(move)
        thrust = move.thrust

        speed_distance = sqrt(self.vx ** 2 + self.vy ** 2)
        if speed_distance == 0:
            speed_distance = DEFAULT_SPEED

        # collision = self.get_collision(self.get_next_checkpoint())
        checkpoint_entry = self.get_next_checkpoint_entry_point()
        collision = self.get_collision(Checkpoint(self.next_checkpoint_id, checkpoint_entry.x, checkpoint_entry.y, RADIUS_WAYPOINT))
        if collision is not None and isinstance(collision.b, Checkpoint):

            angle_with_future_checkpoint = self.get_delta_angle_orientation(self.path.get_node(self.get_checkpoint_id_coming_after()))

            if abs(angle_with_future_checkpoint) < MIN_ANGLE_TAKE_ACCOUNT_COLLISION:
                turn_coefficient = COEFFICIENT_DISTANCE_COLLISION
            else:
                turn_coefficient = ((180.0 - abs(angle_with_future_checkpoint)) / 180.0) * COEFFICIENT_DISTANCE_COLLISION + COEFFICIENT_DISTANCE_COLLISION

            distance_to_checkpoint = self.get_distance(checkpoint_entry)
            condition_1 = (previous_collision is None and collision is not None and isinstance(collision.b, Checkpoint) and int(collision.b.id) == int(
                self.next_checkpoint_id) and collision.time <= TIME_BEFORE_DETECTION_CHECKPOINT and distance_to_checkpoint < turn_coefficient * RADIUS_WAYPOINT)
            condition_2 = (previous_collision is not None and collision is not None and isinstance(collision.b, Checkpoint) and int(collision.b.id) == int(
                self.next_checkpoint_id) and collision.time <= TIME_BEFORE_DETECTION_CHECKPOINT and distance_to_checkpoint < turn_coefficient * RADIUS_WAYPOINT)
            condition_2 = condition_2 and (collision.a.id != previous_collision.a.id or collision.b.id != previous_collision.b.id or collision.time != 0.0)

            print(str(self.id) + ' - ckpt : ' + str(collision.b.id) + ', time : ' + str(collision.time) + ' - condition 1 ' + str(condition_1) + ', condition 2 ' + str(condition_2), file=sys.stderr)
            print(str(self.id) + ' - distance : ' + str(distance_to_checkpoint) + ' turning angle = ' + str(angle_with_future_checkpoint) + ' coeff : ' + str(turn_coefficient), file=sys.stderr)

        else:
            condition_1 = False
            condition_2 = False

        if condition_1 or condition_2:
            self.bounce_with_checkpoint(collision.b)
            self.output(Move(self.get_delta_angle_orientation(checkpoint_entry), MAX_THRUST), False, collision)
        else:
            distance_to_checkpoint = self.get_distance(checkpoint_entry)
            turn_to_reach_checkpoint = (distance_to_checkpoint - RADIUS_CHECKPOINT - RADIUS_POD) / speed_distance

            thrust = MAX_THRUST  # move.thrust
            angle_checkpoint = self.get_delta_angle_orientation(checkpoint_entry)
            if abs(angle_checkpoint) > MAX_ANGLE_SPEED:
                thrust = MIN_THRUST
            elif abs(angle_checkpoint) < MIN_ANGLE_SPEED:
                thrust = MAX_THRUST
            else:
                thrust = thrust * (MAX_ANGLE_SPEED - abs(angle_checkpoint)) / MAX_ANGLE_SPEED

            coefficient = 1
            if distance_to_checkpoint > MIN_DISTANCE_BOOST and abs(angle_checkpoint) < MIN_ANGLE_SPEED:
                thrust = BOOST
            elif distance_to_checkpoint < 2 * RADIUS_CHECKPOINT:
                coefficient = FIRST_SLOWING_COEFFICIENT
            elif distance_to_checkpoint < RADIUS_CHECKPOINT:
                coefficient = SECOND_SLOWING_COEFFICIENT
            else:
                coefficient = 1 / (max(NB_TURN_DECREASE - turn_to_reach_checkpoint, 1))

            if thrust != BOOST:
                thrust = round(thrust * coefficient)

                if thrust > MAX_THRUST:
                    thrust = MAX_THRUST
                elif thrust < MIN_THRUST:
                    thrust = MIN_THRUST

            print(self.id + ' distance2 = ' + str(self.get_distance2(checkpoint_entry)) + ', speed : ' + str(speed_distance) + ', turn to reach : ' + str(turn_to_reach_checkpoint), file=sys.stderr)
            print(self.id + ' thrust = ' + str(thrust) + ', coeff : ' + str(coefficient), file=sys.stderr)

        collision_boss1 = self.get_collision(boss1)
        collision_boss2 = self.get_collision(boss2)
        distance_pod_boss1 = self.get_distance(boss1)
        distance_pod_boss2 = self.get_distance(boss2)

        self.is_shield_activated = False
        if collision_boss1 is not None and isinstance(collision_boss1.b, Pod) and collision_boss1.time <= TIME_BEFORE_DETECTION_POD:
            if distance_pod_boss <= SAFETY_DISTANCE and self.shield_ready():
                print('Activate SHIELD Boss 1 !!!', file=sys.stderr)
                thrust = SHIELD
                self.turn_activated_shield = turn
                self.is_shield_activated = True

        if collision_boss2 is not None and isinstance(collision_boss2.b, Pod) and collision_boss2.time <= TIME_BEFORE_DETECTION_POD:
            if distance_pod_boss <= SAFETY_DISTANCE and self.shield_ready():
                print('Activate SHIELD Boss 2 !!!', file=sys.stderr)
                thrust = SHIELD
                self.turn_activated_shield = turn
                self.is_shield_activated = True

        if (distance_pod_boss1 <= SAFETY_DISTANCE or distance_pod_boss2 <= SAFETY_DISTANCE) and self.shield_ready() and thrust <= SHIELD_ACTIVATION_SPEED:
            print('Safety SHIELD !!!', file=sys.stderr)
            thrust = SHIELD
            self.turn_activated_shield = turn
            self.is_shield_activated = True

        # Look for a point corresponding to the targeted direction
        checkpoint_angle = self.get_delta_angle_orientation(checkpoint_entry)
        new_angle = formalize_angle(self.angle + checkpoint_angle)
        radians_angle = new_angle * pi / 180.0

        # px = self.x + cos(radians_angle) * 5000.0;
        # py = self.y + sin(radians_angle) * 5000.0;
        px = self.x + cos(radians_angle) * distance_to_checkpoint;
        py = self.y + sin(radians_angle) * distance_to_checkpoint;

        if commit:
            print(round(px), round(py), thrust)
            # print(self.get_next_checkpoint().x, self.get_next_checkpoint().y, thrust)

    def check_consistency(self):
        diff_turn = turn - self.switch_checkpoint

        print(str(self.id) + 'diff turn ' + str(diff_turn), file=sys.stderr)

        if self.check_next_checkpoint_id != self.next_checkpoint_id and diff_turn == NB_TURN_ROLLBACK:
            print(self.id + ' ROLLBACK ' + str(self.check_next_checkpoint_id) + ' to ' + str(self.next_checkpoint_id), file=sys.stderr)
            self.switch_checkpoint = turn
            self.next_checkpoint_id = self.check_next_checkpoint_id
            if self.next_checkpoint_id == 0:
                self.lap -= 1

    def shield_ready(self):
        return (turn - self.turn_activated_shield >= SHIELD_COOLDOWN)

    def clone(self):
        '''
        Return a copy of the pod
        :return: Pod
        '''
        clone = Pod(self.id, self.radius)
        clone.x = self.x
        clone.y = self.y
        clone.vx = self.vx
        clone.pod = self.vy
        clone.angle = self.angle
        clone.next_checkpoint_id = self.next_checkpoint_id
        clone.lap = self.lap
        clone.checked = self.checked
        clone.timeout = self.timeout
        # clone.partner = self.partner
        clone.is_shield_activated = self.is_shield_activated

        return clone


class Path:
    def __init__(self):
        self.nodes = []

    def add_node(self, node):
        self.nodes.append(node)

    def get_nodes(self):
        return self.nodes

    def get_node(self, id):
        if id >= len(self.nodes):
            return None
        else:
            return self.nodes[id]

    def clone(self):
        clone = Path()
        for node in self.nodes:
            clone.add_node(node.clone())
        return clone


class Collision():
    def __init__(self, unit_a, unit_b, time):
        self.a = unit_a
        self.b = unit_b
        self.time = time  # time at which the collision between a and b occurs


class Move():
    def __init__(self, angle, thrust):
        self.angle = angle  # between [-18 , 18]
        self.thrust = thrust  # between [-1, 100], -1 is Shield
        # self.shield = False


# UTILS
def formalize_angle(angle):
    # Replace the angle between [0; 360] degrees
    # mod operator is slower than if comparison
    if angle >= 360.0:
        return angle - 360.0
    elif angle < 0.0:
        return angle + 360.0
    else:
        return angle


# Initialization
laps = int(input())
checkpointCount = int(input())

path = Path()
list_checkpoints = []
for i in range(checkpointCount):
    x, y = [int(j) for j in input().split()]
    list_checkpoints.append(Checkpoint(i, x, y, RADIUS_CHECKPOINT))
    path.add_node(Checkpoint(i, x, y, RADIUS_CHECKPOINT))
    print('checkpoint added : ' + str(i), file=sys.stderr)

cho = Pod("cho", RADIUS_POD)
gall = Pod("gall", RADIUS_POD)
boss1 = Pod("boss1", RADIUS_POD)
boss2 = Pod("boss2", RADIUS_POD)

cho.set_path(path)
gall.set_path(path)
boss1.set_path(path)
boss2.set_path(path)

cho.set_partner(gall)
gall.set_partner(cho)
boss1.set_partner(boss2)
boss2.set_partner(boss1)

turn = 0
best_solution = None

while True:
    start_time = time.time()
    elapsed_time = 0.0

    cho.set_parameters(input, False, False)
    gall.set_parameters(input, False, False)
    boss1.set_parameters(input, False, False)
    boss2.set_parameters(input, False, False)

    cho.check_consistency()
    gall.check_consistency()
    turn += 1

    cho.output(Move(cho.get_delta_angle_orientation(cho.get_next_checkpoint_entry_point()), MAX_THRUST), True, None)
    gall.output(Move(gall.get_delta_angle_orientation(gall.get_next_checkpoint_entry_point()), MAX_THRUST), True, None)