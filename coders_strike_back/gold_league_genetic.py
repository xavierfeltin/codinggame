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
from math import ceil
from math import radians
from math import degrees
from math import pi
from math import inf
from math import exp
from random import randint
from random import uniform
from operator import attrgetter
from collections import deque

# Auto-generated code below aims at helping you parse
# the standard input according to the problem statement.

FRICTION = 0.85  # (game constraint) friction factor applied on pods
PRECISION = 6  # floating precision
TIMEOUT = 100  # number of turns for a pod to reach its next checkpoint
TIME_FULL_TURN = 1.0  # a full turn has a time of 1
NB_TURN_SIMULATION = 6
MAX_WAITING_TURN = 7

RADIUS_POD = 400
RADIUS_CHECKPOINT = 1200
RADIUS_WAYPOINT = 20  # Waypoint used as entry point in checkpoint  => TODO: check if keep it or not
TIME_BEFORE_DETECTION_CHECKPOINT = 5  # turns before collision
NB_TURN_ROLLBACK = 5  # number of turns after an anticipated collisions to check if the checkpoint has been indeed validated (must be >= TIME_BEFORE_DETECTION_CHECKPOINT)

ALIGNMENT_COEFFICIENT = 0.1  # How much we set before the next checkpoint for the alignment phase
POD_ADVANCEMENT_STAGE_1 = 0.2  # distance ratio between past and next checkpoint using stage 1 strategy
POD_ADVANCEMENT_STAGE_2 = 0.5  # distance ration between past and next checkpoint using stage 2 strategy
DEGRESSIVE_COEFFICIENT_STAGE_2 = -0.11  # exponential degressive coefficient used in stage 2 (higher coeff means less brutal)

SAFETY_DISTANCE = RADIUS_POD + RADIUS_POD + 10  # distance of an ennemy to activate the shield
SHIELD = 'SHIELD'
SHIELD_COOLDOWN = 3

MAX_THRUST = 100
MIN_THRUST = 20
BOOST = 'BOOST'
MAX_ANGLE_SPEED = 150
MIN_ANGLE_SPEED = 20
MIN_DISTANCE_BOOST = 5000
FIRST_SLOWING_COEFFICIENT = 0.4
SECOND_SLOWING_COEFFICIENT = 0.2
DEFAULT_SPEED = 100  # Arbitraty value to initiate the game to avoid a null speed

# GENETIC ALGO
NB_MOVES = 6
NB_POPULATION = 10  # must be a pair value
NB_TOURNAMENT = 4  # 1/3 of the global population for now
COEFFCIENT_AMPLITUDE = 0.5
COEFFICIENT_MUTATION_FROM_REF = 0.5


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

    def get_closest(self, a, b):
        '''
        Return the closest point on the line passing through the a and b points of the current point
        '''
        # TODO : understand the mathematical magic behind these equations

        da = b.y - a.y
        db = a.x - b.x
        c1 = da * a.x + db * a.y
        c2 = -db * self.x + da * self.y
        det = da ** 2 + db ** 2

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

    def set_coordinates(self, x, y, vx, vy):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy

    def get_collision(self, other, is_occuring=False):
        '''
        Return the Collision object between the current unit and the unit in parameter
        :param other: Unit on which we detect the collision
        :param is_occuring: True to return only the collisions that will be happening at the current turn
        :return: the collision if there is contact otherwise None
        '''

        # Use square distance to avoid using root function
        distance_to_other = self.get_distance2(other)

        if isinstance(self, Pod) and isinstance(other, Checkpoint):
            length_radii_squared = (other.radius) ** 2  # pod no radius to take into account the center of the pod
        else:
            length_radii_squared = (self.radius + other.radius) ** 2  # pod no radius to take into account the center of the pod

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
        closest_projection = other_in_referential.get_closest(pod_in_referential, Point(x + vx, y + vy))
        # closest_projection = Point(0, 0)

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

            distance_pod_closest_projection = closest_projection.get_distance2(pod_in_referential)

            # If the impact point is further than what the pod can travel in one turn
            # Collision will be managed in another turn
            if distance_pod_closest_projection > speed_distance and is_occuring:
                return None

            # Get the time needed to reach the impact point during this turn
            time = distance_pod_closest_projection / speed_distance

            return Collision(self, other, sqrt(time))
        else:
            return None

    def bounce(self, other):
        '''
        Manage the bounce effect due to the impact of the shield of the current unit and the unit in parameters
        :param other: Unit colliding with the current unit
        :return: none
        '''
        print_msg(None, 'TODO')


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
        print_msg(None, 'TODO')

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
        self.waiting_turn = 0

    def set_path(self, path):
        self.path = path.clone()
        self.next_checkpoint_id = 1
        self.check_next_checkpoint_id = 1

    def set_partner(self, partner):
        self.partner = partner

    def set_parameters(self, input, is_shield_activated):
        self.x, self.y, self.vx, self.vy, self.angle, self.check_next_checkpoint_id = [int(i) for i in input().split()]
        self.is_shield_activated = is_shield_activated

        # no more updated like in deterministic approach
        # if self.check_next_checkpoint_id != check_next_checkpoint_id:
        #    self.check_next_checkpoint_id = check_next_checkpoint_id
        #    self.bounce_with_checkpoint(self.get_next_checkpoint())

    def set_boss_parameters(self, input, is_shield_activated):
        self.x, self.y, self.vx, self.vy, self.angle, check_next_checkpoint_id = [int(i) for i in input().split()]
        self.is_shield_activated = is_shield_activated

        # Update Boss information on its checkpoints from previous turn information
        if self.check_next_checkpoint_id != check_next_checkpoint_id:
            self.check_next_checkpoint_id = check_next_checkpoint_id
            self.bounce_with_checkpoint(self.get_next_checkpoint())

    def check_consistency(self):
        diff_turn = turn - self.switch_checkpoint

        # print_msg(self, str(self.id) + 'diff turn ' + str(diff_turn))

        if self.check_next_checkpoint_id != self.next_checkpoint_id and diff_turn == NB_TURN_ROLLBACK:
            print_msg(None, 'rollback')
            self.switch_checkpoint = turn
            self.next_checkpoint_id = self.check_next_checkpoint_id
            if self.next_checkpoint_id == 0:
                self.lap -= 1

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

        # Replace the angle between [0 360] degrees
        # mod operator is slower than if comparison
        self.angle = formalize_angle(self.angle)

    def rotate_angle(self, delta_angle):
        if delta_angle > 18.0:
            # rotate on the right side
            delta_angle = 18.0
        elif delta_angle < -18:
            # rotate on the left side
            delta_angle = -18.0

        self.angle += delta_angle

        # Replace the angle between [0 360] degrees
        # mod operator is slower than if comparison
        self.angle = formalize_angle(self.angle)

    def accelerate(self, thrust):
        '''
        Determine the new velocity vector of the pod along its direction
        :param thrust: thrust of the pod
        :return: none
        '''

        if thrust == SHIELD:
            thrust = 0
        elif thrust == BOOST:
            thrust = 100
        elif thrust > 100:
            thrust = 100
        elif thrust < 0:
            thrust = 0

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
        self.timeout -= 1

    def bounce(self, other):
        '''
        Manage the bounce effect due to the impact of the shield of the current unit and the unit in parameters
        :param other: Unit colliding with the current unit
        :return: none
        '''

        if isinstance(other, Checkpoint):
            self.bounce_with_checkpoint(other)
        else:
            # If a pod has its shield active its mass is 10 otherwise it's 1
            if self.is_shield_activated:
                mass_pod1 = 10
            else:
                mass_pod1 = 1

            if other.is_shield_activated:
                mass_other = 10
            else:
                mass_other = 1

            mass_coefficient = (mass_pod1 + mass_other) / (mass_pod1 * mass_other)
            distance_x = self.x - other.x
            distance_y = self.y - other.y

            distance_square = distance_x * distance_x + distance_y + distance_y
            if distance_square == 0:
                distance_square = 1

            speed_vector_x = self.vx - other.vx
            speed_vector_y = self.vy - other.vy

            # fx and fy are the components of the impact vector. product is just there for optimisation purposes
            product = (distance_x * speed_vector_x) + (distance_y * speed_vector_y)
            fx = (distance_x * product) / (distance_square * mass_coefficient)
            fy = (distance_y * product) / (distance_square * mass_coefficient)

            # Apply the impact vector once
            self.vx -= fx / mass_pod1
            self.vy -= fy / mass_pod1
            other.vx += fx / mass_other
            other.vy += fy / mass_other

            # If the norm of the impact vector is less than 120, we normalize it to 120
            impulse = sqrt(fx * fx + fy * fy)

            if impulse == 0:
                impulse = 1

            if impulse < 120.0:
                fx = (fx * 120.0) / impulse
                fy = (fy * 120.0) / impulse

            # We apply the impact vector a second time
            self.vx -= fx / mass_pod1
            self.vy -= fy / mass_pod1
            other.vx += fx / mass_other
            other.vy += fy / mass_other

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
        return self.checked * 50000 - self.get_distance(self.get_next_checkpoint())
        # return (self.checked * 10000) - abs(self.get_delta_angle_orientation(self.get_next_checkpoint())) - self.get_angle(self.get_next_checkpoint()) - (self.get_distance(self.get_next_checkpoint()) * 2)

    def apply(self, move):
        '''
        Apply the move onto the player
        turn the pod and apply the thrust
        :param move: move to apply
        :return: non
        '''
        self.rotate_angle(move.angle)
        self.accelerate(move.thrust)

    def get_next_checkpoint(self):
        return self.path.get_node(self.next_checkpoint_id)

    def get_next_checkpoint_entry_point(self):
        '''
         Return the entry point of the next check point function of the direction of the checkpoint coming after
         It is based on the past check point, the next checkpoint and the future checkpoint and the projected position
         of the pod onto the segment past_checkpoint / next_checkpoint to measure the advancement
         3 steps :
         1) Apply to the pod the vector next_checkpoint and future_next_checkpoint
         2) Target an entrypoint inside the checkpoint opposite to the direction to go for the future checkpoint
         3) Target a point front of the next_checkpoint on the line between the previous checkpoint and the next checkpoint
        :return: Point object
        '''

        next_checkpoint = self.get_next_checkpoint()  # list_checkpoints[self.next_checkpoint_id]

        id = self.get_checkpoint_id_coming_after()
        if id != -1:
            id_past = self.get_checkpoint_id_coming_before()
            past_checkpoint = list_checkpoints[id_past]

            closest_pod_on_vector = self.get_closest(past_checkpoint, next_checkpoint)
            distance_pod_next_checkpoint = closest_pod_on_vector.get_distance2(next_checkpoint)
            distance_past_next_checktpoint = past_checkpoint.get_distance2(next_checkpoint)
            pod_advancement = (distance_past_next_checktpoint - distance_pod_next_checkpoint) / distance_past_next_checktpoint

            # print_msg(self, self.id + ' - pod advancement ' + str(past_checkpoint.id) + '/' + str(next_checkpoint.id) + ' : ' + str(pod_advancement))

            if pod_advancement < 0:
                pod_advancement = 1
            elif pod_advancement > 1:
                pod_advancement = 1

            if pod_advancement < POD_ADVANCEMENT_STAGE_1:
                coefficient = 0
                coefficient_2 = 0
                coefficient_3 = 1
            elif pod_advancement < POD_ADVANCEMENT_STAGE_2:
                coefficient = exp(DEGRESSIVE_COEFFICIENT_STAGE_2 * pod_advancement)
                coefficient_2 = 0
                coefficient_3 = 0
            else:
                coefficient_2 = 1
                coefficient_3 = 0
                coefficient = 0

            future_checkpoint = list_checkpoints[id]
            vector_checkpoints = Point(next_checkpoint.x - past_checkpoint.x, next_checkpoint.y - past_checkpoint.y)

            # delta_angle = self.get_delta_angle_orientation(future_checkpoint)
            # delta_angle = self.get_delta_angle_orientation(next_checkpoint)
            pod_checkpoint = Pod(next_checkpoint.id, next_checkpoint.radius)
            pod_checkpoint.angle = 0
            pod_checkpoint.x = next_checkpoint.x
            pod_checkpoint.y = next_checkpoint.y

            # delta_angle = pod_checkpoint.get_delta_angle_orientation(future_checkpoint)
            # final_angle = delta_angle

            final_angle = pod_checkpoint.get_angle(future_checkpoint)

            if final_angle <= 90 or final_angle >= 240:
                # Future checkpoint is on the right side of the actual checkpoint
                if (future_checkpoint.x - self.x) <= 0:
                    # pod is on the right side of the next checkpoint
                    x_coefficient = pi
                else:
                    x_coefficient = 0
            else:
                if (future_checkpoint.x - self.x) <= 0:
                    # pod is on the right side of the next checkpoint
                    x_coefficient = 0
                else:
                    x_coefficient = pi

            if final_angle >= 0 or final_angle <= 180:
                # Future checkpoint is below the next checkpoint
                if (future_checkpoint.y - self.y) <= 0:
                    # pod is onbelow of the next checkpoint
                    y_coefficient = -1
                else:
                    y_coefficient = 1
            else:
                if (future_checkpoint.y - self.y) <= 0:
                    # pod is on the right side of the next checkpoint
                    y_coefficient = 1
                else:
                    y_coefficient = -1

            radians_angle = final_angle * pi / 180.0  # final_angle * pi / 180.0
            vector_pod_checkpoint = Point(next_checkpoint.x - (RADIUS_CHECKPOINT) * cos(radians_angle + x_coefficient), next_checkpoint.y - (RADIUS_CHECKPOINT) * sin(radians_angle * y_coefficient))

            alignment_vector_checkpoints = Point(next_checkpoint.x - (vector_checkpoints.x * ALIGNMENT_COEFFICIENT), next_checkpoint.y - (vector_checkpoints.y * ALIGNMENT_COEFFICIENT))

            vector_final_x = ((self.x + vector_checkpoints.x) * (1 - coefficient) * coefficient_3) + (vector_pod_checkpoint.x * coefficient) + (alignment_vector_checkpoints.x * coefficient_2)
            vector_final_y = ((self.y + vector_checkpoints.y) * (1 - coefficient) * coefficient_3) + (vector_pod_checkpoint.y * coefficient) + (alignment_vector_checkpoints.y * coefficient_2)
            vector_final = Point(vector_final_x, vector_final_y)

            # print_msg(self, self.id + ' entry point (' + str(self.x + vector_final.x) + ', ' + str(self.y + vector_final.y))

            return Checkpoint(self.next_checkpoint_id, vector_final.x, vector_final.y, 50)
            # return Point(vector_final.x, vector_final.y)

        else:
            return Checkpoint(self.next_checkpoint_id, next_checkpoint.x, next_checkpoint.y, 50)
            # return Point(next_checkpoint.x, next_checkpoint.y)

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

    def get_checkpoint_id_coming_before(self):
        past_checkpoint_id = self.next_checkpoint_id - 1
        if past_checkpoint_id == 0 and self.lap > 1:
            past_checkpoint_id = checkpointCount - 1
        elif past_checkpoint_id == 0 and self.lap == 0:
            past_checkpoint_id = -1

        return past_checkpoint_id

    def load(self, saved_pod):
        self.x = saved_pod.x
        self.y = saved_pod.y
        self.vx = saved_pod.vx
        self.vy = saved_pod.vy
        self.angle = saved_pod.angle
        self.next_checkpoint_id = saved_pod.next_checkpoint_id
        self.lap = saved_pod.lap
        self.checked = saved_pod.checked
        self.timeout = saved_pod.timeout
        # self.partner = saved_pod.partner
        self.is_shield_activated = saved_pod.is_shield_activated

    def apply_boss(self, previous_collision):
        thrust = MAX_THRUST  # move.thrust
        speed_distance = sqrt(self.vx ** 2 + self.vy ** 2)

        if speed_distance == 0:
            speed_distance = DEFAULT_SPEED

        collision = self.get_collision(self.get_next_checkpoint())
        checkpoint_entry = self.get_next_checkpoint_entry_point()

        if collision is not None and isinstance(collision.b, Checkpoint):

            angle_with_future_checkpoint = self.get_delta_angle_orientation(self.path.get_node(self.get_checkpoint_id_coming_after()))

            distance_to_checkpoint = self.get_distance(checkpoint_entry)
            condition_1 = (previous_collision is None and collision is not None and isinstance(collision.b, Checkpoint) and int(collision.b.id) == int(
                self.next_checkpoint_id) and collision.time <= TIME_BEFORE_DETECTION_CHECKPOINT)
            condition_2 = (previous_collision is not None and collision is not None and isinstance(collision.b, Checkpoint) and int(collision.b.id) == int(
                self.next_checkpoint_id) and collision.time <= TIME_BEFORE_DETECTION_CHECKPOINT)
            condition_2 = condition_2 and (collision.a.id != previous_collision.a.id or collision.b.id != previous_collision.b.id or collision.time != 0.0)
        elif collision is not None and isinstance(collision.b, Pod):
            self.bounce(collision.b)
        else:
            condition_1 = False
            condition_2 = False

        if condition_1 or condition_2:
            self.bounce_with_checkpoint(collision.b)
            self.apply_boss(collision)
        else:
            if previous_collision is None:
                distance_to_checkpoint = self.get_distance(checkpoint_entry)
            else:
                # print_msg(self, self.id + ' - distance previous collision ')
                distance_to_checkpoint = self.get_distance(previous_collision.b)

            turn_to_reach_checkpoint = (distance_to_checkpoint - RADIUS_WAYPOINT - RADIUS_POD) / speed_distance

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
            elif distance_to_checkpoint < 2.0 * RADIUS_WAYPOINT:
                coefficient = 0.8
            elif distance_to_checkpoint <= 1.0 * RADIUS_WAYPOINT:
                coefficient = 0
            else:
                coefficient = 1

            if thrust != BOOST:
                thrust = round(thrust * coefficient)

                if thrust > MAX_THRUST:
                    thrust = MAX_THRUST
                elif thrust < MIN_THRUST:
                    thrust = MIN_THRUST

        distance_boss_pod1 = self.get_distance(cho)
        distance_boss_pod2 = self.get_distance(gall)

        if (distance_boss_pod1 <= SAFETY_DISTANCE or distance_boss_pod2 <= SAFETY_DISTANCE) and self.shield_ready():
            thrust = SHIELD
            self.turn_activated_shield = turn
            self.is_shield_activated = True

        # Look for a point corresponding to the targeted direction
        checkpoint_angle = self.get_delta_angle_orientation(checkpoint_entry)
        self.angle = formalize_angle(self.angle + checkpoint_angle)

        if thrust == SHIELD:
            thrust = 0
        elif thrust == BOOST:
            thrust = 650

        self.thrust = thrust

        if not self.is_shield_activated:
            radians_angle = self.angle * pi / 180.0
            self.vx = cos(radians_angle) * self.thrust
            self.vy = sin(radians_angle) * self.thrust

    def generate_move_IA(self):
        '''
        Apply the move on the pod and print result to game engine
        :param move: Move
        :return: none
        '''

        thrust = MAX_THRUST

        collision = self.get_collision(self.get_next_checkpoint())
        if collision is not None and isinstance(collision.b, Checkpoint):
            if collision.b.id == self.next_checkpoint_id and collision.time < 1.0:
                self.bounce_with_checkpoint(collision.b)
                print_msg(None, 'collision time = ' + str(collision.time))

        checkpoint_entry = self.get_next_checkpoint()

        angle_checkpoint = self.get_delta_angle_orientation(checkpoint_entry)
        distance_to_checkpoint = self.get_distance(checkpoint_entry)

        if abs(angle_checkpoint) > MAX_ANGLE_SPEED:
            thrust = MIN_THRUST
        elif abs(angle_checkpoint) < MIN_ANGLE_SPEED:
            thrust = MAX_THRUST
        else:
            thrust = thrust * (MAX_ANGLE_SPEED - abs(angle_checkpoint)) / MAX_ANGLE_SPEED

        coefficient = 1
        if distance_to_checkpoint > MIN_DISTANCE_BOOST and abs(angle_checkpoint) < MIN_ANGLE_SPEED:
            thrust = BOOST
        # elif distance_to_checkpoint < 2.0 * RADIUS_WAYPOINT:
        #    coefficient = 0.8
        # elif distance_to_checkpoint <= 1.0 * RADIUS_WAYPOINT:
        #    coefficient = 0
        # else:
        #    coefficient = 1

        if thrust != BOOST:
            thrust = round(thrust * coefficient)

            if thrust > MAX_THRUST:
                thrust = MAX_THRUST
            elif thrust < MIN_THRUST:
                thrust = MIN_THRUST

        distance_pod_boss1 = self.get_distance(boss1)
        distance_pod_boss2 = self.get_distance(boss2)

        # self.is_shield_activated = False
        # if (distance_pod_boss1 <= SAFETY_DISTANCE or distance_pod_boss2 <= SAFETY_DISTANCE) and self.shield_ready():
        #    thrust = SHIELD
        #    self.turn_activated_shield = turn
        #    self.is_shield_activated = True

        # scale :
        if angle_checkpoint > 18:
            angle_checkpoint = 18
        elif angle_checkpoint < -18:
            angle_checkpoint = -18

        return Move(angle_checkpoint, thrust)

    def output(self, move):

        self.rotate_angle(move.angle)

        # Look for a point corresponding to the angle we want
        # Multiply by 10000.0 to limit rounding errors
        radians = self.angle * pi / 180.0
        px = self.x + cos(radians) * 10000.0
        py = self.y + sin(radians) * 10000.0

        if move.shield:
            # print(round(px), round(py), "SHIELD")
            self.activate_shield()
            print(round(px), round(py), 100)
        else:
            thrust = move.thrust
            if isinstance(thrust, str):
                # thrust = thrust
                thrust = 100
            elif thrust > 100:
                thrust = 100
            elif thrust < 0:
                thrust = 0

            print(round(px), round(py), thrust)

    def activate_shield(self):
        self.is_shield_activated = True

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
        clone.vy = self.vy
        clone.angle = self.angle
        clone.next_checkpoint_id = self.next_checkpoint_id
        clone.lap = self.lap
        clone.checked = self.checked
        clone.timeout = self.timeout
        # clone.partner = self.partner
        clone.is_shield_activated = self.is_shield_activated
        clone.path = self.path.clone()
        clone.check_next_checkpoint_id = self.check_next_checkpoint_id
        clone.switch_checkpoint = self.switch_checkpoint
        clone.turn_activated_shield = self.turn_activated_shield
        clone.waiting_turn = self.waiting_turn

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


class Collision:
    def __init__(self, unit_a, unit_b, time):
        self.a = unit_a
        self.b = unit_b
        self.time = time  # time at which the collision between a and b occurs

    def clone(self):
        return Collision(self.a.clone(), self.b.clone(), self.time)


class Move:
    def __init__(self, angle, thrust):
        self.angle = angle  # between [-18 , 18]
        self.thrust = thrust  # between [-1, 100], -1 is Shield
        self.shield = False

    def mutate(self, amplitude):
        ramin = self.angle - 36.0 * amplitude
        ramax = self.angle + 36.0 * amplitude

        if ramin < -18.0:
            ramin = -18.0

        if ramax > 18.0:
            ramax = 18.0

        angle = uniform(ramin, ramax)

        # if not self.shield and randint(0, 100) < 5:
        #    self.shield = True
        # else:

        if self.thrust == BOOST:
            thrust = 100
        # elif self.thrust == SHIELD:
        #    #thrust = 0
        #    thrust= 100
        else:
            thrust = self.thrust

        pmin = thrust - 100 * amplitude
        pmax = thrust + 200 * amplitude

        if pmin < 0:
            pmin = 0
        elif pmin > 100:
            pmin = 100

        if pmax > 100:
            pmax = 100
        elif pmax < 0:
            pmax = 0

        if pmin <= pmax:
            self.thrust = randint(round(pmin), round(pmax))
        else:
            self.thrust = randint(round(pmax), round(pmin))

        self.shield = False


class Solution:
    def __init__(self):
        self.moves1 = deque()
        self.moves2 = deque()
        self.cho = None
        self.gall = None
        self.boss1 = None
        self.boss2 = None
        self.result = -inf
        self.result1 = -inf
        self.result2 = -inf

        self.checked1 = 0
        self.next_checkpoint_id1 = 0
        self.checked2 = 0
        self.next_checkpoint_id2 = 0

    def save(self):
        self.cho = cho.clone()
        self.gall = gall.clone()
        self.boss1 = boss1.clone()
        self.boss2 = boss2.clone()

    def load(self):
        self.cho.load(cho)
        self.gall.load(gall)
        self.boss1.load(boss1)
        self.boss2.load(boss2)

    def clone(self):
        clone = Solution()
        for move in self.moves1:
            clone.moves1.append(Move(move.angle, move.thrust))

        for move in self.moves2:
            clone.moves2.append(Move(move.angle, move.thrust))

        return clone

    def evaluation(self):

        if self.cho.timeout == 0 or self.gall.timeout == 0:
            # timeout
            return -inf
        elif self.boss1.next_checkpoint_id == -1 or self.boss2.next_checkpoint_id == -1:
            # boss runner wins the race
            return -inf
        elif self.cho.next_checkpoint_id == -1 or self.gall.next_checkpoint_id == -1:
            # player wins the race !!!
            return inf
        else:
            # if (self.boss1.checked > self.boss2.checked) or (self.boss1.checked == self.boss2.checked \
            #    and self.boss1.get_distance2(self.boss1.get_next_checkpoint()) < self.boss2.get_distance2(self.boss2.get_next_checkpoint())):
            #    head_boss = self.boss1
            # else:
            #    head_boss = self.boss2

            # print_msg(self.cho, ' next entry point : (' + str(self.cho.get_next_checkpoint().x) + ', ' + str(self.cho.get_next_checkpoint().y) + ')')
            # print_msg(self.gall, ' next entry point : (' + str(self.gall.get_next_checkpoint().x) + ', ' + str(self.gall.get_next_checkpoint().y) + ')')

            # TODO : add criteria on future checkpoint if the checked has been incremented during play
            self.result1 = (self.cho.checked * 50000) - self.cho.get_distance(self.cho.get_next_checkpoint())
            self.result2 = (self.gall.checked * 50000) - self.gall.get_distance(self.gall.get_next_checkpoint())
            result = self.result1 + self.result2
            # result += (self.gall.checked * 50000) -  self.distance_next_waypoint2 - self.distance_future_waypoint2
            # result -= (head_boss.checked * 10000 + head_boss.get_distance(head_boss.get_next_checkpoint()))

            return result

    def score(self):
        self.save()

        # Play out the turns
        for i in range(len(self.moves1)):
            # Apply all the moves to the pods before playing
            self.cho.apply(self.moves1[i])
            self.gall.apply(self.moves2[i])

            # self.boss1.apply_boss(None)  # Set angles and thrust from IA strategy guessing
            # self.boss2.apply_boss(None)  # Set angles and thrust from IA strategy guessing

            # play([self.cho, self.gall, self.boss1, self.boss2])

            play([self.cho, self.gall])

            if i <= 3:
                self.checked1 = self.cho.checked
                self.next_checkpoint_id1 = self.cho.next_checkpoint_id

                self.checked2 = self.gall.checked
                self.next_checkpoint_id2 = self.gall.next_checkpoint_id

        # Compute the score
        self.result = self.evaluation()

        # Reset everyone to their initial states
        self.load()

        return self.result

    def mutate(self, amplitude):
        for i in range(0, NB_MOVES - 1):
            self.moves1[i].mutate(amplitude)
            self.moves2[i].mutate(amplitude)


# UTILS
def formalize_angle(angle):
    # Replace the angle between [0 360] degrees
    # mod operator is slower than if comparison
    if angle >= 360.0:
        return angle - 360.0
    elif angle < 0.0:
        return angle + 360.0
    else:
        return angle


def print_msg(pod, msg):
    if pod is None:
        print(msg, file=sys.stderr)

    if pod is not None:
        print(msg, file=sys.stderr)
        # if (pod.id == "cho" or pod.id == "gall"):
        #
        # else:
        #    print(msg, file=sys.stderr)


def generate_population(is_first_generation):
    if is_first_generation:
        reference_solution = Solution()
        reference_solution.moves1 = generate_IA_moves(cho)
        reference_solution.moves2 = generate_IA_moves(gall)
        solutions.append(reference_solution)

        print_msg(None, 'first generation angle = ' + str(reference_solution.moves1[0].angle))

        for i in range(NB_POPULATION - 1):
            solution = Solution()
            for j in range(NB_MOVES):
                move = Move(reference_solution.moves1[j].angle, reference_solution.moves1[j].thrust)
                move.mutate(COEFFICIENT_MUTATION_FROM_REF)
                solution.moves1.append(move)

                move = Move(reference_solution.moves2[j].angle, reference_solution.moves2[j].thrust)
                move.mutate(COEFFICIENT_MUTATION_FROM_REF)
                solution.moves2.append(move)

            solutions.append(solution)
    else:
        reference_move_cho = generate_IA_next_move(cho, solutions[0].moves1)
        solutions[0].moves1.popleft()
        solutions[0].moves1.append(reference_move_cho)

        reference_move_gall = generate_IA_next_move(gall, solutions[0].moves2)
        solutions[0].moves2.popleft()
        solutions[0].moves2.append(reference_move_gall)

        for i in range(NB_POPULATION - 1):
            move = Move(reference_move_cho.angle, reference_move_cho.thrust)
            move.mutate(COEFFICIENT_MUTATION_FROM_REF)
            solutions[i + 1].moves1.popleft()
            solutions[i + 1].moves1.append(move)

            move = Move(reference_move_gall.angle, reference_move_gall.thrust)
            move.mutate(COEFFICIENT_MUTATION_FROM_REF)
            solutions[i + 1].moves2.popleft()
            solutions[i + 1].moves2.append(move)


def generate_IA_moves(pod):
    backup = pod.clone()

    list_moves = deque()
    list_moves.append(pod.generate_move_IA())

    for j in range(NB_MOVES - 1):
        pod.apply(list_moves[j])
        play([pod])
        list_moves.append(pod.generate_move_IA())

    pod.load(backup)
    return list_moves


def generate_IA_next_move(pod, previous_moves):
    backup = pod.clone()
    # for move in previous_moves:
    #    pod.apply(move)
    #    play([pod])

    move = pod.generate_move_IA()

    pod.load(backup)
    return move


def play(list_pods):
    time = 0.0

    previous_collision = []
    while (time < 1.0):
        first_collision = None

        # Check for all the collisions occuring during the turn
        for i in range(len(list_pods)):
            for j in range(i + 1, len(list_pods)):
                collision = list_pods[i].get_collision(list_pods[j], True)  # TODO modify get_collision to return again collision in time < 1.0

                if collision is not None:
                    found = False
                    for past_collision in previous_collision:
                        if ((collision.a == past_collision.a and collision.b == past_collision.b) \
                                    or (collision.a == past_collision.b and collision.b == past_collision.a)) \
                                and collision.time == past_collision.time:
                            found = True

                    if found:
                        first_collision = None
                    else:
                        first_collision = collision

            # Collision with another checkpoint?
            # It is unnecessary to check all checkpoints here.We only test the pod's next checkpoint.
            # We could look for the collisions of the pod with all the checkpoints, but if such a collision happens it wouldn't impact the game in any way
            collision = list_pods[i].get_collision(list_pods[i].get_next_checkpoint(), False)

            if collision is not None and collision.time < 1.0:
                found = False
                for past_collision in previous_collision:
                    if ((collision.a == past_collision.a and collision.b == past_collision.b) \
                                or (collision.a == past_collision.b and collision.b == past_collision.a)) \
                            and collision.time == past_collision.time:
                        found = True

                if found:
                    first_collision = None
                else:
                    first_collision = collision

        if first_collision is None:
            # No collision so the pod is following its path until the end of the turn
            for pod in list_pods:
                pod.move(1.0 - time)

            time = 1.0  # end of the turn
        else:
            # Move the pod normally until collision time
            for pod in list_pods:
                pod.move(1.0 - first_collision.time)

            # Solve the collision
            first_collision.a.bounce(first_collision.b)

            time += first_collision.time
            previous_collision.append(first_collision)

    for pod in list_pods:
        pod.finalize()


def tournament(solutions):
    winners = []
    winners.append(solutions[0])  # best solution is qualified

    for i in range(0, NB_TOURNAMENT - 1):
        challenger_1 = randint(0, NB_POPULATION / 2)
        challenger_2 = randint(0, NB_POPULATION / 2)

        # if solutions[challenger_1].result > solutions[challenger_2].result:
        if (solutions[challenger_1].result1 > solutions[challenger_2].result1) \
                and (solutions[challenger_1].result2 > solutions[challenger_2].result2):
            winners.append(solutions[challenger_1])
        else:
            winners.append(solutions[challenger_2])

    return winners


def crossing(solutions, amplitude):
    new_generation = solutions

    for i in range(NB_POPULATION - NB_TOURNAMENT):
        parent_1 = solutions[randint(0, NB_TOURNAMENT - 1)]
        parent_2 = solutions[randint(0, NB_TOURNAMENT - 1)]

        child = Solution()
        for j in range(0, NB_MOVES):
            angle = round((parent_1.moves1[j].angle + parent_2.moves1[j].angle) / 2.0)

            if isinstance(parent_1.moves1[j].thrust, str) or isinstance(parent_2.moves1[j].thrust, str):
                if randint(0, 100) < 50:
                    thrust = parent_1.moves1[j].thrust
                else:
                    thrust = parent_2.moves1[j].thrust
            else:
                thrust = ceil((parent_1.moves1[j].thrust + parent_2.moves1[j].thrust) / 2.0)
                # thrust = max(parent_1.moves1[j].thrust, parent_2.moves1[j].thrust)

            move = Move(angle, thrust)
            # move.mutate(amplitude)
            child.moves1.append(move)

            angle = round((parent_1.moves2[j].angle + parent_2.moves2[j].angle) / 2.0)

            if isinstance(parent_1.moves2[j].thrust, str) or isinstance(parent_2.moves2[j].thrust, str):
                if randint(0, 100) < 50:
                    thrust = parent_1.moves2[j].thrust
                else:
                    thrust = parent_2.moves2[j].thrust
            else:
                thrust = round((parent_1.moves2[j].thrust + parent_2.moves2[j].thrust) / 2.0)

            move = Move(angle, thrust)
            # move.mutate(amplitude)
            child.moves2.append(move)

        new_generation.append(child)

    return new_generation


# Initialization
laps = int(input())
checkpointCount = int(input())

path = Path()
list_checkpoints = []
for i in range(checkpointCount):
    x, y = [int(j) for j in input().split()]
    list_checkpoints.append(Checkpoint(i, x, y, RADIUS_CHECKPOINT))
    path.add_node(Checkpoint(i, x, y, RADIUS_CHECKPOINT))
    print_msg(None, 'checkpoint added : ' + str(i))

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
solutions = []
best_solution = None
minScore = 0

while True:
    start_time = time.time()
    elapsed_time = 0.0
    new_time = 0.0
    delta_time = 0.0

    print_msg(None, 'Turn : ' + str(turn))

    cho.set_parameters(input, False)
    gall.set_parameters(input, False)
    boss1.set_boss_parameters(input, False)
    boss2.set_boss_parameters(input, False)

    if turn == 0:
        print(cho.get_next_checkpoint().x, cho.get_next_checkpoint().y, 100)
        print(gall.get_next_checkpoint().x, gall.get_next_checkpoint().y, 100)
        turn += 1
    else:
        cho.check_consistency()
        gall.check_consistency()

        amplitude = 1.0

        if turn == 1:
            generate_population(True)
        else:
            generate_population(False)

        for i in range(NB_POPULATION):
            solution = solutions[i]
            solution.score()

        solutions = sorted(solutions, key=attrgetter('result'), reverse=True)

        new_time = (time.time() - start_time) * 1000.0  # ms
        delta_time = new_time - elapsed_time
        elapsed_time = new_time

        while (elapsed_time + delta_time) < 140:
            selected_parents = tournament(solutions)
            new_generation = crossing(selected_parents, amplitude)

            for i in range(NB_POPULATION):
                solution = new_generation[i]
                solution.mutate(amplitude)
                solution.score()

                # if solution.result > solutions[len(solutions)-1].result:
                if (solution.result1 > solutions[len(solutions) - 1].result1) \
                        and (solution.result2 > solutions[len(solutions) - 1].result2):
                    solutions.pop()
                    solutions.append(solution)
                    # print_msg(None, 'Append solution : ' + str(solution.moves1[0].thrust) + ', ' + str(solution.moves1[0].angle))

                solutions = sorted(solutions, key=attrgetter('result'), reverse=True)

            amplitude = amplitude * COEFFCIENT_AMPLITUDE
            new_time = (time.time() - start_time) * 1000.0  # ms
            delta_time = new_time - elapsed_time
            elapsed_time = new_time
            # print_msg(None, 'new_time : ' + str(elapsed_time) + ', delta time = ' + str(delta_time))

        if solutions[0].next_checkpoint_id1 != cho.next_checkpoint_id:
            cho.bounce_with_checkpoint(cho.get_next_checkpoint())

        if solutions[0].next_checkpoint_id2 != gall.next_checkpoint_id:
            gall.bounce_with_checkpoint(gall.get_next_checkpoint())

        print_msg(cho, cho.id + ' next : ' + str(cho.next_checkpoint_id))

        cho.output(solutions[0].moves1[0])
        gall.output(solutions[0].moves2[0])
        # print(gall.x, gall.y, 0)

        turn += 1