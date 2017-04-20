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
from math import copysign
from random import randint
from random import uniform
from random import sample
from operator import attrgetter
from collections import deque

# Auto-generated code below aims at helping you parse
# the standard input according to the problem statement.


# GAME CONSTANTS
FRICTION = 0.85  # (game constraint) friction factor applied on pods
PRECISION = 6  # floating precision
TIMEOUT = 100  # number of turns for a pod to reach its next checkpoint
TIME_FULL_TURN = 1.0  # a full turn has a time of 1
NB_TURN_SIMULATION = 6
MAX_WAITING_TURN = 7

RADIUS_POD = 400.0
RADIUS_CHECKPOINT = 600.0
DOUBLE_RADIUS_CHECKPOINT = 1200.0
SQUARED_RADIUS_CHECKPOINT = 360000.0
SQUARED_DOUBLE_RADIUS_CHECKPOINT = 1440000.0
MAX_DISTANCE_BY_TURN = 1300.0
SQUARED_MAX_DISTANCE_BY_TURN = 1690000.0
DISTANCE_MINIMUM_2_CKPTS_IN_ONE_TURN = 2500.0
RADIUS_WAYPOINT = 20.0  # Waypoint used as entry point in checkpoint  => TODO: check if keep it or not
SQUARED_RADIUS_WAYPOINT = 400.0
TIME_BEFORE_DETECTION_CHECKPOINT = 5.0  # turns before collision
NB_TURN_ROLLBACK = 5  # number of turns after an anticipated collisions to check if the checkpoint has been indeed validated (must be >= TIME_BEFORE_DETECTION_CHECKPOINT)

SAFETY_DISTANCE = RADIUS_POD + RADIUS_POD + 10  # distance of an ennemy to activate the shield
SAFETY_DISTANCE_SQUARED = 656100
SHIELD = 'SHIELD'
SHIELD_COOLDOWN = 3

MAX_THRUST = 100.0
MIN_THRUST = 0.0
BOOST = 'BOOST'
MAX_ANGLE_SPEED = 150.0
MIN_ANGLE_SPEED = 20.0
MIN_DISTANCE_BOOST = 5000.0
SQUARED_MIN_DISTANCE_BOOST = 25000000.0

# GENETIC ALGORITHM
NB_MOVES = 6

# POPULATION CONTROL
NB_POPULATION = 10  # equals to NB_CHILDREN + NB_BEST_PARENTS + NB_MUTATIONS_PARENTS
NB_CHILDREN = 6  # number of crossings (children)

# MUTATION CONTROL
COEFFICIENT_MAX_MUTATION_FROM_REF = 0.4
COEFFICIENT_MIN_MUTATION_FROM_REF = 0.01
BOOST_CHANCE = 5
SHIELD_CHANCE = 5

# SPECIFIC TO TOURNAMENT SELECTION
NB_TOURNAMENT = 4  # number of parents in the pool for crossing
SIZE_TOURNAMENT = 2  # number of contestants at each tournament

# SPECIFIC TO ADAPTATIVE GENETIC ALGORITHM
K1 = 1.0  # ponderation for crossing probability, 1.0 from publication
K3 = 1.0  # ponderation for crossing probability, 1.0 from publication
K2 = 0.5  # ponderation for mutation probability, 0.5 from publication
K4 = 0.5  # ponderation for mutation probability, 0.5 from publication
MIN_PROBA_MUTATION = 0.01  # minimum proba of mutation even on best solution 0.005 from publication
MIN_PROBA_CROSS = 0.1  # own expriment
NB_MOVES_TO_MUTATE = 6
APOCALYPSE_NOW = 10  # Violent mutation to try to find a new maximum if evolution is stuck
APOCALYPSE_MUTATION = 0.15
MAX_NB_CHILDREN = 3


class Point():
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def get_distance2(self, b):
        '''
        Return the square of the euclidian distance between the current point and the b point
        '''
        return (self.x - b.x) * (self.x - b.x) + (self.y - b.y) * (self.y - b.y)

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

        ax = a.x
        bx = b.x
        ay = a.y
        by = b.y
        selfx = self.x
        selfy = self.y

        da = by - ay
        db = ax - bx
        c1 = da * ax + db * ay
        c2 = -db * selfx + da * selfy
        det = da * da + db * db

        if det == 0:
            # Point is already on the line (ab)
            closest_point_x = selfx
            closest_point_y = selfy
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

        if distance_to_other > SQUARED_MAX_DISTANCE_BY_TURN:
            return None

        if isinstance(self, Pod) and isinstance(other, Checkpoint):
            length_radii_squared = (other.radius) * (other.radius)  # pod no radius to take into account the center of the pod
        else:
            length_radii_squared = (self.radius + other.radius) * (self.radius + other.radius)  # pod no radius to take into account the center of the pod

        if distance_to_other <= length_radii_squared:
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
        if distance_unit_closest_projection <= length_radii_squared:
            # The pod speed on the line (norm)
            speed_distance = vx * vx + vy * vy

            # Project the pod on the line to find the point of impact
            distance_intersection_units = sqrt(length_radii_squared - distance_unit_closest_projection)
            closest_projection.x -= distance_intersection_units * (vx / speed_distance)
            closest_projection.y -= distance_intersection_units * (vy / speed_distance)

            # If the projection point is further away means the pod direction is opposite of the other unit
            # => no collision will happen

            new_distance_pod_closest_projection = closest_projection.get_distance2(pod_in_referential)
            if new_distance_pod_closest_projection > distance_pod_closest_projection:
                return None

            distance_pod_closest_projection = new_distance_pod_closest_projection

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
        return None


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
        return None

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
        self.check_next_checkpoint_id = 0
        self.switch_checkpoint = 0
        self.turn_activated_shield = -4  # to avoid an activation at the start of the game
        self.waiting_turn = 0
        self.boost_available = True
        self.race_turn = 0
        self.is_hunter = False
        self.waiting_point = list_entry_points[2]

    def set_partner(self, partner):
        self.partner = partner

    def set_parameters(self, input, turn):
        self.x, self.y, self.vx, self.vy, self.angle, check_next_checkpoint_id = [int(i) for i in input().split()]

        # self.is_shield_activated = is_shield_activated
        self.is_shield_activated = ((self.turn_activated_shield + 3) >= self.race_turn)
        self.race_turn = turn

        ## no more updated like in deterministic approach
        if self.check_next_checkpoint_id != check_next_checkpoint_id:
            self.check_next_checkpoint_id = check_next_checkpoint_id
            self.bounce_with_checkpoint(self.get_next_checkpoint())

    def set_boss_parameters(self, input, turn):
        self.x, self.y, self.vx, self.vy, self.angle, check_next_checkpoint_id = [int(i) for i in input().split()]

        # self.is_shield_activated = is_shield_activated
        self.is_shield_activated = ((self.turn_activated_shield + 3) >= self.race_turn)
        self.race_turn = turn

        # Update Boss information on its checkpoints from previous turn information
        if self.check_next_checkpoint_id != check_next_checkpoint_id:
            self.check_next_checkpoint_id = check_next_checkpoint_id
            self.bounce_with_checkpoint(self.get_next_checkpoint())

    def check_consistency(self):
        diff_turn = self.race_turn - self.switch_checkpoint

        if self.check_next_checkpoint_id != self.next_checkpoint_id and diff_turn == NB_TURN_ROLLBACK:
            self.switch_checkpoint = self.race_turn
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

    def accelerate(self, move):
        '''
        Determine the new velocity vector of the pod along its direction
        :param thrust: thrust of the pod
        :return: none
        '''

        thrust = move.thrust

        # if thrust equals 0 it means no acceleration, so speed stays the same
        # if thrust == 0:
        #    return None

        angle_radians = self.angle * pi / 180.0
        self.vx += cos(angle_radians) * move.thrust
        self.vy += sin(angle_radians) * move.thrust

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

            distance_square = distance_x * distance_x + distance_y * distance_y
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
            self.switch_checkpoint = self.race_turn

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
        return self.checked * 50000 - self.get_distance(self.get_next_entry_point())

    def score_hunter(self):
        '''
        Get the score for the pod
        :return: score
        '''
        return -self.get_distance(self.waiting_point)

    def apply(self, move):
        '''
        Apply the move onto the player
        turn the pod and apply the thrust
        :param move: move to apply
        :return: non
        '''
        self.rotate_angle(move.angle)
        self.accelerate(move)

    def get_next_checkpoint(self):
        return list_checkpoints[self.next_checkpoint_id]

    def get_next_entry_point(self):
        return list_entry_points[self.next_checkpoint_id]

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
        self.race_turn = saved_pod.race_turn
        self.boost_available = saved_pod.boost_available

    def apply_boss(self, with_move=False):
        '''
        Compute the next state of the bosses in the race
        @param with_move: True to move the boss pod during one full turn
        False to only set the boss to be moved afterwards (in play function for AG)
        '''

        checkpoint = self.get_next_checkpoint()
        collision = self.get_collision(checkpoint)
        if collision is not None and isinstance(collision.b, Checkpoint):
            if collision.b.id == self.next_checkpoint_id and collision.time < 1.0:
                self.bounce_with_checkpoint(collision.b)

        checkpoint_entry = checkpoint
        angle_checkpoint = self.get_delta_angle_orientation(checkpoint_entry)
        squared_distance_to_checkpoint = self.get_distance2(checkpoint_entry)

        # Compute thrust :
        if not self.shield_ready():
            thrust = 0  # active shield means no thrust
        elif (self.get_distance2(cho) <= SAFETY_DISTANCE_SQUARED or self.get_distance2(gall) <= SAFETY_DISTANCE_SQUARED) and self.shield_ready():
            self.activate_shield()
            thrust = 0
            # TODO : BOOST management for bosses
        else:
            if abs(angle_checkpoint) > MAX_ANGLE_SPEED:
                thrust = MIN_THRUST
            elif abs(angle_checkpoint) < MIN_ANGLE_SPEED:
                thrust = MAX_THRUST
            else:
                thrust = MAX_THRUST * ((MAX_ANGLE_SPEED - abs(angle_checkpoint)) / MAX_ANGLE_SPEED)

            if squared_distance_to_checkpoint > SQUARED_RADIUS_CHECKPOINT and squared_distance_to_checkpoint <= SQUARED_DOUBLE_RADIUS_CHECKPOINT:
                coefficient = 0.7
            elif squared_distance_to_checkpoint <= SQUARED_RADIUS_CHECKPOINT:
                coefficient = 0
            else:
                coefficient = 1

            thrust = thrust * coefficient

        # Scale angle :
        if angle_checkpoint > 18.0:
            angle_checkpoint = 18.0
        elif angle_checkpoint < -18.0:
            angle_checkpoint = -18.0

        self.angle += angle_checkpoint
        self.angle = formalize_angle(self.angle)

        radians_angle = self.angle * pi / 180.0
        self.vx += cos(radians_angle) * thrust
        self.vy += sin(radians_angle) * thrust

        if with_move:
            self.move(TIME_FULL_TURN)  # time = 1.0 is a complete turn
            self.finalize()

    def generate_move_IA(self):
        '''
        Apply the move on the pod and print result to game engine
        :param move: Move
        :return: none
        '''

        move = Move(0.0, 0.0)

        thrust = MAX_THRUST

        checkpoint = self.get_next_entry_point()
        collision = self.get_collision(checkpoint)
        if collision is not None and isinstance(collision.b, Checkpoint):
            if collision.b.id == self.next_checkpoint_id and collision.time < 1.0:
                self.bounce_with_checkpoint(collision.b)

        checkpoint_entry = checkpoint

        angle_checkpoint = self.get_delta_angle_orientation(checkpoint_entry)
        distance_to_checkpoint = self.get_distance2(checkpoint_entry)

        # Compute thrust :
        if not self.shield_ready():
            thrust = 0.0  # active shield means no thrust
        elif (self.get_distance2(boss1) <= SAFETY_DISTANCE_SQUARED or self.get_distance2(boss2) <= SAFETY_DISTANCE_SQUARED) and self.shield_ready():
            move.shield = True
            thrust = 0.0
        # self.activate_shield()
        #   thrust = SHIELD
        else:
            if distance_to_checkpoint > SQUARED_MIN_DISTANCE_BOOST and abs(angle_checkpoint) < MIN_ANGLE_SPEED and self.boost_available:
                thrust = 100.0
                move.boost = True
            else:

                if abs(angle_checkpoint) > MAX_ANGLE_SPEED:
                    thrust = MIN_THRUST
                elif abs(angle_checkpoint) < MIN_ANGLE_SPEED:
                    thrust = MAX_THRUST
                else:
                    thrust = thrust * ((MAX_ANGLE_SPEED - abs(angle_checkpoint)) / MAX_ANGLE_SPEED)

                if distance_to_checkpoint < 4.0 * SQUARED_RADIUS_WAYPOINT:
                    coefficient = 0.8
                elif distance_to_checkpoint <= 1.0 * SQUARED_RADIUS_WAYPOINT:
                    coefficient = 0
                else:
                    coefficient = 1

                thrust = thrust * coefficient

        # Scale angle :
        if angle_checkpoint > 18:
            angle_checkpoint = 18
        elif angle_checkpoint < -18:
            angle_checkpoint = -18

        move.angle = angle_checkpoint
        move.thrust = thrust

        return move

    def generate_move_IA_hunter(self, boss_runner):
        '''
        Apply the move on the pod and print result to game engine
        :param move: Move
        :return: none
        '''

        move = Move(0.0, 0.0)

        thrust = MAX_THRUST

        collision = self.get_collision(self.get_next_checkpoint())
        if collision is not None and isinstance(collision.b, Checkpoint):
            if collision.b.id == self.next_checkpoint_id and collision.time < 1.0:
                self.bounce_with_checkpoint(collision.b)

        checkpoint_entry = self.waiting_point

        angle_checkpoint = self.get_delta_angle_orientation(checkpoint_entry)
        distance_to_checkpoint = self.get_distance2(checkpoint_entry)

        # Compute thrust :
        if not self.shield_ready():
            thrust = 0.0  # active shield means no thrust
        elif (self.get_distance2(boss1) <= SAFETY_DISTANCE_SQUARED or self.get_distance2(
                boss2) <= SAFETY_DISTANCE_SQUARED) and self.shield_ready():
            move.shield = True
            thrust = 0.0
        # self.activate_shield()
        #   thrust = SHIELD
        else:
            if distance_to_checkpoint > SQUARED_MIN_DISTANCE_BOOST and abs(
                    angle_checkpoint) < MIN_ANGLE_SPEED and self.boost_available:
                thrust = 100.0
                move.boost = True
            else:

                if abs(angle_checkpoint) > MAX_ANGLE_SPEED:
                    thrust = MIN_THRUST
                elif abs(angle_checkpoint) < MIN_ANGLE_SPEED:
                    thrust = MAX_THRUST
                else:
                    thrust = thrust * ((MAX_ANGLE_SPEED - abs(angle_checkpoint)) / MAX_ANGLE_SPEED)

                if distance_to_checkpoint < 4.0 * SQUARED_RADIUS_WAYPOINT:
                    coefficient = 0.0
                else:
                    coefficient = 1

                thrust = thrust * coefficient

        # Scale angle :
        if angle_checkpoint > 18:
            angle_checkpoint = 18
        elif angle_checkpoint < -18:
            angle_checkpoint = -18

        move.angle = angle_checkpoint
        move.thrust = thrust

        return move

    def output(self, move):

        self.rotate_angle(move.angle)

        # Look for a point corresponding to the angle we wantSAME CONDITIONS  SUBMIT
        # Multiply by 10000.0 to limit rounding errors
        radians = self.angle * pi / 180.0
        px = self.x + cos(radians) * 6000.0
        py = self.y + sin(radians) * 6000.0

        if move.shield:
            self.activate_shield()
            print(round(px), round(py), SHIELD)
        elif move.boost:
            self.boost_available = False
            print(round(px), round(py), BOOST)
        else:
            thrust = ceil(move.thrust)
            if thrust > 100:
                thrust = 100
            elif thrust < 0:
                thrust = 0

            print(round(px), round(py), thrust)

    def activate_shield(self):
        self.is_shield_activated = True
        self.turn_activated_shield = self.race_turn

    def shield_ready(self):
        return (self.race_turn - self.turn_activated_shield >= SHIELD_COOLDOWN)

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
        clone.check_next_checkpoint_id = self.check_next_checkpoint_id
        clone.switch_checkpoint = self.switch_checkpoint
        clone.turn_activated_shield = self.turn_activated_shield
        clone.waiting_turn = self.waiting_turn
        clone.boost_available = self.boost_available
        clone.race_turn = self.race_turn
        clone.is_hunter = self.is_hunter

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
        self.thrust = thrust  # between [0, 100]
        self.shield = (thrust == SHIELD)
        self.boost = (thrust == BOOST)

    def clone(self):
        move = Move(self.angle, self.thrust)
        move.shield = self.shield
        move.boost = self.boost
        return move

    def mutate(self, amplitude, pod):
        ramin = self.angle - 36.0 * amplitude
        ramax = self.angle + 36.0 * amplitude

        if ramin < -18.0:
            ramin = -18.0

        if ramax > 18.0:
            ramax = 18.0

        self.angle = uniform(ramin, ramax)

        self.shield = pod.shield_ready and randint(0, 100) < SHIELD_CHANCE
        self.boost = pod.boost_available and not self.shield and randint(0, 100) < BOOST_CHANCE

        pmin = self.thrust - 100 * amplitude
        pmax = self.thrust + 200 * amplitude

        if pmin < MIN_THRUST:
            pmin = MIN_THRUST
        elif pmin > 100:
            pmin = 100

        if pmax > 100:
            pmax = 100
        elif pmax < MIN_THRUST:
            pmax = MIN_THRUST

        if pmin <= pmax:
            self.thrust = uniform(pmin, pmax)
        else:
            self.thrust = uniform(pmin, pmax)

    @staticmethod
    def cross(p1_move, p2_move, pod):
        proba = randint(0, 100)

        if proba < 50:
            thrust = (0.7 * p1_move.thrust) + (0.3 * p2_move.thrust)
            move = Move((0.7 * p1_move.angle) + (0.3 * p2_move.angle), thrust)

        else:
            thrust = (0.7 * p2_move.thrust) + (0.3 * p1_move.thrust)
            move = Move((0.7 * p2_move.angle) + (0.3 * p1_move.angle), thrust)

        if p1_move.shield and p2_move.shield and randint(0, 100) < SHIELD_CHANCE and pod.shield_ready:
            move.shield = True

        if p1_move.boost and p2_move.boost and randint(0, 100) < BOOST_CHANCE and pod.boost_available and not move.shield:
            move.boost = True

        return move


class Solution:
    def __init__(self):
        self.moves1 = deque()
        self.moves2 = deque()
        self.move_shield_1 = -1
        self.move_shield_2 = -1
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

        # Multi Objectives approach
        self.nb_ckpt = 0  # Number of validated checkpoints
        self.distance_next_ckpt = 0.0  # Distance to next ckpt in 6 moves => To minimize
        self.average_thrust = 0.0  # Average thrust during 6 moves => To maximize
        self.distance_future_ckpt = 0.0  # Distance to ckpt +2 in 6 moves => To minimize

    def generate_deterministic_solution(self, is_first_generation):
        '''
        Create a new solution using a deterministic approach
        @is_first_generation: True generate all moves, False delete first move and generate last one
        @return None
        '''

        if is_first_generation:
            self.moves1 = self._generate_IA_moves(cho)
            self.moves2 = self._generate_IA_moves(gall)
        else:
            self.moves1.popleft()
            self.moves1.append(self._generate_IA_next_move(cho, self.moves1))

            self.moves2.popleft()
            self.moves2.append(self._generate_IA_next_move(gall, self.moves2))

    def generate_solution_from_reference(self, reference_solution, is_first_generation):
        '''
        Create a new solution from an existing solution by making mutation on it
        @is_first_generation: True generate all moves, False delete first move and generate last one
        @return None
        '''

        if is_first_generation:
            for i in range(NB_MOVES):
                move = reference_solution.moves1[i].clone()
                move.mutate(uniform(COEFFICIENT_MIN_MUTATION_FROM_REF, COEFFICIENT_MAX_MUTATION_FROM_REF), cho)
                self.moves1.append(move)

                move = reference_solution.moves2[i].clone()
                move.mutate(uniform(COEFFICIENT_MIN_MUTATION_FROM_REF, COEFFICIENT_MAX_MUTATION_FROM_REF), gall)
                self.moves2.append(move)

            self.validate()
        else:
            move = reference_solution.moves1[NB_MOVES - 1].clone()
            move.mutate(uniform(COEFFICIENT_MIN_MUTATION_FROM_REF, COEFFICIENT_MAX_MUTATION_FROM_REF), cho)
            self.moves1.popleft()
            self.moves1.append(move)

            move = reference_solution.moves2[NB_MOVES - 1].clone()
            move.mutate(uniform(COEFFICIENT_MIN_MUTATION_FROM_REF, COEFFICIENT_MAX_MUTATION_FROM_REF), gall)
            self.moves2.popleft()
            self.moves2.append(move)

            self.validate()

    def _generate_IA_moves(self, pod):
        backup = pod.clone()

        list_moves = deque()
        if pod.is_hunter:
            list_moves.append(pod.generate_move_IA_hunter(boss_runner))
        else:
            list_moves.append(pod.generate_move_IA())

        if pod.is_hunter:
            for j in range(NB_MOVES - 1):
                pod.apply(list_moves[j])
                play([pod])
                list_moves.append(pod.generate_move_IA_hunter(boss_runner))
        else:
            for j in range(NB_MOVES - 1):
                pod.apply(list_moves[j])
                play([pod])
                list_moves.append(pod.generate_move_IA())

        pod.load(backup)
        return list_moves

    def _generate_IA_next_move(self, pod, previous_moves):
        backup = pod.clone()

        size = len(previous_moves)
        for i in range(size):
            pod.apply(previous_moves[i])
            play([pod])

        if pod.is_hunter:
            move = pod.generate_move_IA_hunter(boss_runner)
        else:
            move = pod.generate_move_IA()

        pod.load(backup)
        return move

    def clone(self):
        clone = Solution()

        clone.move_shield_1 = self.move_shield_1
        clone.move_shield_2 = self.move_shield_2

        for i in range(NB_MOVES):
            clone.moves1.append(self.moves1[i].clone())

        for i in range(NB_MOVES):
            clone.moves2.append(self.moves2[i].clone())

        clone.result = self.result
        clone.result1 = self.result1
        clone.result2 = self.result2

        clone.checked1 = self.checked1
        clone.next_checkpoint_id1 = self.next_checkpoint_id1
        clone.checked2 = self.checked2
        clone.next_checkpoint_id2 = self.next_checkpoint_id2

        clone.nb_ckpt = self.nb_ckpt
        clone.distance_next_ckpt = self.distance_next_ckpt
        clone.average_thrust = self.average_thrust
        clone.distance_future_ckpt = self.distance_future_ckpt

        return clone

    def is_shield_activated(self, index, move_shield, moves, pod):
        '''
        True if the shield is activated at the current move
        '''
        if index == 0:
            is_shield_activated = pod.is_shield_activated or moves[index].shield
        elif index != 0:
            is_shield_activated = pod.is_shield_activated and (pod.turn_activated_shield + 3 >= pod.race_turn + index)
            is_shield_activated = is_shield_activated or ((move_shield + 3) >= index) or (moves[index].shield)

        return is_shield_activated

    def validate(self):

        counter_boost1 = 0
        counter_boost2 = 0

        self.move_shield_1 = -inf
        self.move_shield_2 = -inf

        for i in range(NB_MOVES):

            move1 = self.moves1[i]
            move2 = self.moves2[i]

            if move1.shield and self.move_shield_1 != -1:
                self.move_shield_1 = i

            if move2.shield and self.move_shield_2 != -1:
                self.move_shield_2 = i

            is_shield_activated_1 = self.is_shield_activated(i, self.move_shield_1, self.moves1, cho)
            is_shield_activated_2 = self.is_shield_activated(i, self.move_shield_2, self.moves2, gall)

            # TODO : add angle check for boost
            if move1.boost and cho.boost_available and not is_shield_activated_1 and not counter_boost1 > 0 and not cho.get_distance2(cho.get_next_entry_point()) > 25000000:
                move1.thrust = 650.0
                counter_boost1 += 1
            else:
                move1.boost = False

            if move2.boost and gall.boost_available and not is_shield_activated_2 and not counter_boost2 > 0 and not gall.get_distance2(gall.get_next_entry_point()) > 25000000:
                move2.thrust = 650.0
                counter_boost2 += 1
            else:
                move2.boost = False

            if is_shield_activated_1:
                move1.thrust = 0.0
            else:
                move1.shield = False

            if is_shield_activated_2:
                move2.thrust = 0.0
            else:
                move2.shield = False

    def evaluation(self):

        if cho.timeout == 0:  # or gall.timeout == 0:
            # timeout
            return -100000

        score = 0.0
        if cho.is_hunter:
            score += cho.score_hunter() + boss_runner.get_distance(cho.waiting_point)  # - abs((boss_runner.get_angle(cho.waiting_point) - boss_runner.get_angle(cho)))
        else:
            score += cho.score()

        if gall.is_hunter:

            boss_next_checkpoint = boss_runner.get_next_checkpoint()
            angle_boss_gall = boss_runner.get_delta_angle_orientation(gall)
            angle_gall_boss = gall.get_delta_angle_orientation(boss_runner)

            # distance_boss = boss_runner.get_distance2(boss_next_checkpoint)
            # distance_boss = boss_runner.get_distance2(gall)
            distance_boss = boss_runner.get_distance(gall)
            angle_boss_pod = gall.get_delta_angle_orientation(boss_runner)
            if distance_boss > 1500.0 and abs(angle_gall_boss) <= 20.0:  # 1500*1500 - and gall.score_hunter() < 2000.0:
                coeff_kill_boss = 0.0
                coeff_waiting_point = 1.0
            else:
                coeff_kill_boss = 1.0  # 1-(distance_boss/2000.0)
                coeff_waiting_point = 0.0  # 1.0 - coeff_kill_boss

            if coeff_waiting_point:
                score_waiting_point = coeff_waiting_point * gall.score_hunter()
                # score_between_boss_checkpoint = coeff_waiting_point * -(abs(boss_runner.get_delta_angle_orientation(gall.waiting_point)) - abs(angle_boss_gall))
                score += score_waiting_point  # + score_between_boss_checkpoint
            else:
                score_block_boss_runner = coeff_kill_boss * -distance_boss  # boss_runner.get_distance(gall.waiting_point)
                score_between_boss_checkpoint = coeff_kill_boss * -(abs(boss_runner.get_delta_angle_orientation(boss_next_checkpoint)) - abs(angle_boss_gall))
                score_look_for_runner = coeff_kill_boss * -abs(angle_gall_boss)
                score_between_boss_checkpoint = coeff_kill_boss * -(abs(boss_runner.get_delta_angle_orientation(boss_next_checkpoint)) - abs(angle_boss_gall))
                score += score_block_boss_runner + score_look_for_runner

        else:
            score += gall.score()

        return score

    def score(self):
        # Play out the turns
        boss1_collided = False
        boss2_collided = False

        cho_checked = cho.checked
        gall_checked = gall.checked
        boss1_checked = boss1.checked
        boss2_checked = boss2.checked

        check_ckpts = [True, True, True, True]

        average_thrust1 = 0.0
        average_thrust2 = 0.0

        for i in range(NB_MOVES):
            # Apply all the moves to the pods before playing
            cho.apply(self.moves1[i])
            gall.apply(self.moves2[i])

            if boss1_collided:
                boss1.apply_boss()
            else:
                boss1.load(caches_boss1[i])

            if boss2_collided:
                boss2.apply_boss()
            else:
                boss2.load(caches_boss2[i])

            b1, b2 = play([cho, gall, boss1, boss2], check_ckpts)

            average_thrust1 += self.moves1[i].thrust / NB_MOVES
            average_thrust2 += self.moves2[i].thrust / NB_MOVES

            # flag if two checkpoints are really close to avoid ignoring checkpoints for next moves
            check_ckpts[0] = (cho_checked == cho.checked)  # and cho_not_two_checkpoints
            check_ckpts[1] = (gall_checked == gall.checked)  # and gall_not_two_checkpoints
            check_ckpts[2] = (boss1_checked == boss1.checked)  # and boss1_not_two_checkpoints
            check_ckpts[3] = (boss2_checked == boss2.checked)  # and boss2_not_two_checkpoints

            boss1_collided = boss1_collided or b1
            boss2_collided = boss2_collided or b2

            cho.race_turn += 1
            gall.race_turn += 1
            boss1.race_turn += 1
            boss2.race_turn += 1

        # Compute the score
        self.result = self.evaluation()

        load_pod_states(save_cho, save_gall, save_boss1, save_boss2)

        return self.result

    def mutate(self, amplitude, is_apocalypse=False):

        if race_turn > 2 and not is_apocalypse:
            for i in reversed(range(NB_MOVES_TO_MUTATE)):
                self.moves1[NB_MOVES - 1 - i].mutate(amplitude, cho)
                self.moves2[NB_MOVES - 1 - i].mutate(amplitude, gall)
        else:
            for i in range(NB_MOVES):
                self.moves1[i].mutate(amplitude, cho)
                self.moves2[i].mutate(amplitude, gall)

        self.validate()


class GeneticAlgorithm():
    def __init__(self):
        self.solutions = []  # current generation of solutions
        self.parents = []  # selected parents for crossing
        self.children = []  # used only for the preselection approach

        self.average = 0.0
        self.maximum = 0.0
        self.apocalypse = 0

    def tournament(self):
        '''
        Select the parents for crossing with the tournament algorithm
        @return: highest score of selected parents
        '''
        self.parents.clear()
        # self.parents.append(self.solutions[0]) # Add best solution to be sure it is once
        self.parents.append(0)

        maximum_result = -10000

        for i in range(NB_TOURNAMENT):
            index_winner = randint(0, NB_POPULATION - 1)
            winner = self.solutions[index_winner]
            for j in range(SIZE_TOURNAMENT):
                index_opponent = randint(0, NB_POPULATION - 1)

                if self.solutions[index_opponent].result > winner.result:
                    index_winner = index_opponent
                    winner = self.solutions[index_opponent]

            if winner.result > maximum_result:
                maximum_result = winner.result

            self.parents.append(index_winner)
            # self.parents.append(winner.clone())

        return maximum_result

    def crossing_mutation_single(self):
        parent_1 = self.solutions[self.parents[randint(0, NB_TOURNAMENT)]]
        parent_2 = self.solutions[self.parents[randint(0, NB_TOURNAMENT)]]

        child = Solution()
        p1_moves1 = parent_1.moves1
        p2_moves1 = parent_2.moves1
        p1_moves2 = parent_1.moves2
        p2_moves2 = parent_2.moves2

        for j in range(NB_MOVES):
            child.moves1.append(Move.cross(p1_moves1[j], p2_moves1[j], cho))
            child.moves2.append(Move.cross(p1_moves2[j], p2_moves2[j], gall))

        child.validate()
        return child

    def build_generation_proba(self):

        maximum_parent = self.tournament()
        crossing_probability = self.compute_probability_crossing(maximum_parent)
        new_average = 0.0
        nb_children = 0

        self.solutions.append(self.solutions[0].clone())

        for i in range(NB_POPULATION):

            solution = self.solutions[i]
            if self.apocalypse < APOCALYPSE_NOW:
                mutation_probability = self.compute_probability_mutation(solution.result)

                if uniform(0.0, 1.0) <= mutation_probability:
                    solution.mutate(mutation_probability)
                    solution.score()
                    new_average += solution.result
            else:
                solution.mutate(APOCALYPSE_MUTATION, True)
                solution.score()
                new_average += solution.result

            child = None
            if uniform(0.0, 1.0) <= crossing_probability:  # and nb_children <= MAX_NB_CHILDREN:
                child = self.crossing_mutation_single()
                child.score()
                self.solutions.append(child)
                new_average += child.result
                nb_children += 1

        self.solutions.sort(key=attrgetter('result'), reverse=True)
        self.solutions = self.solutions[0:NB_POPULATION]

        self.average = new_average / NB_POPULATION

        if self.solutions[0].result > self.maximum:
            self.maximum = self.solutions[0].result
            self.apocalypse = 0
        else:
            self.apocalypse += 1

    def update_avg_max(self, result):

        self.average += result / NB_POPULATION
        if result > self.maximum:
            self.maximum = result

    def compute_probability_crossing(self, maximum_parent):

        if maximum_parent >= self.average:
            return max(K1 * ((self.maximum - maximum_parent) / (self.maximum - self.average)), MIN_PROBA_CROSS)
        else:
            return K3

    def compute_probability_mutation(self, result):

        if result >= self.average:
            return max(K2 * ((self.maximum - result) / (self.maximum - self.average)), MIN_PROBA_MUTATION)
        else:
            return K4

    def get_best_solution(self):
        return self.solutions[0]

    def generate_population(self, is_first_generation):
        '''
        Generate the population of solutions
        The populations is sorted with the best solution first
        @param is_first_generation: True if the generation is the really first one
        @return: None
        '''

        self.maximum = -10000
        self.average = 0.0

        if is_first_generation:
            reference_solution = Solution()
            reference_solution.generate_deterministic_solution(True)
            reference_solution.score()
            self.solutions.append(reference_solution)
            self.update_avg_max(reference_solution.result)

            for i in range(NB_POPULATION - 1):
                solution = Solution()
                solution.generate_solution_from_reference(reference_solution, True)
                solution.score()
                self.solutions.append(solution)
                self.update_avg_max(solution.result)
        else:
            self.solutions[0].generate_deterministic_solution(False)
            self.solutions[0].score()
            self.update_avg_max(self.solutions[0].result)

            for i in range(1, NB_POPULATION - 1):
                self.solutions[i + 1].generate_solution_from_reference(self.solutions[0], False)
                self.solutions[i + 1].score()
                self.update_avg_max(self.solutions[i + 1].result)

        self.solutions.sort(key=attrgetter('result'), reverse=True)


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


def save_pod_states():
    save_cho = cho.clone()
    save_gall = gall.clone()
    save_boss1 = boss1.clone()
    save_boss2 = boss2.clone()
    return cho.clone(), gall.clone(), boss1.clone(), boss2.clone()


def load_pod_states(save_cho, save_gall, save_boss1, save_boss2):
    cho.load(save_cho)
    gall.load(save_gall)
    boss1.load(save_boss1)
    boss2.load(save_boss2)


def generate_boss_cache():
    caches_boss1.clear()
    caches_boss2.clear()

    previous_boss1 = boss1.clone()
    previous_boss1.apply_boss(True)
    caches_boss1.append(previous_boss1.clone())

    previous_boss2 = boss2.clone()
    previous_boss2.apply_boss(True)
    caches_boss2.append(previous_boss2.clone())

    for i in range(1, NB_MOVES):
        previous_boss1 = previous_boss1.clone()
        previous_boss1.apply_boss(True)
        caches_boss1.append(previous_boss1.clone())

        previous_boss2 = previous_boss2.clone()
        previous_boss2.apply_boss(True)
        caches_boss2.append(previous_boss2.clone())


def play(list_pods, check_ckpts=[False]):
    '''
    @param list_pods pods to play this turn
    @param check_ckpts avoid checking checkpoints if it has been already checked this generation (can not have 2 checkpoints so close)
    Return if a collision with boss1 or boss2 happened
    '''

    is_boss1_collided = False
    is_boss2_collided = False

    time = 0.0
    nb_pods = len(list_pods)

    previous_collision = None
    while (time < 1.0):
        first_collision = None
        new_collision = None
        is_checkpoint_collision = False

        # Check for all the collisions occuring during the turn
        for i in range(nb_pods):
            pod = list_pods[i]
            for j in range(i + 1, nb_pods):

                other_pod = list_pods[j]

                # Collision is not possible if pods are going in opposite directions
                if (pod.x < other_pod.x and pod.vx < 0.0 and other_pod.vx > 0.0) \
                        or (other_pod.x < pod.x and other_pod.vx < 0.0 and pod.vx > 0.0) \
                        or (pod.y < other_pod.y and pod.vy < 0.0 and other_pod.vy > 0.0) \
                        or (other_pod.y < pod.y and other_pod.vy < 0.0 and pod.vy > 0.0):
                    collision = None
                else:
                    collision = pod.get_collision(other_pod, True)

                if collision is not None:
                    if previous_collision is not None \
                            and ((collision.a == previous_collision.a and collision.b == previous_collision.b and collision.time == previous_collision.time) \
                                         or (collision.b == previous_collision.a and collision.a == previous_collision.b and collision.time == previous_collision.time)):
                        new_collision = None
                    else:
                        new_collision = collision

                        # If the collision happens earlier than the current one we keep it
                        if (new_collision.time + time) < 1.0 and (first_collision is None or new_collision.time < first_collision.time):
                            first_collision = new_collision

            # Collision with another checkpoint?
            # It is unnecessary to check all checkpoints here.We only test the pod's next checkpoint.
            # We could look for the collisions of the pod with all the checkpoints, but if such a collision happens it wouldn't impact the game in any way
            if check_ckpts[i]:
                collision = pod.get_collision(pod.get_next_checkpoint(), True)
            else:
                collision = None

            if collision is not None:
                if previous_collision is not None and (collision.a == previous_collision.a and collision.b == previous_collision.b) \
                        and collision.time == previous_collision.time:
                    new_collision = None
                else:
                    new_collision = collision

                    # If the collision happens earlier than the current one we keep it
                    if (new_collision.time + time) < 1.0 and (first_collision is None or new_collision.time < first_collision.time):
                        first_collision = new_collision

        if first_collision is None:
            # No collision so the pod is following its path until the end of the turn
            for i in range(nb_pods):
                list_pods[i].move(1.0 - time)
                list_pods[i].finalize()

            time = 1.0  # end of the turn
        else:

            collision_time = first_collision.time
            if collision_time == 0.0:
                collision_time = 0.1

            # Move the pod normally until collision time
            for i in range(nb_pods):
                list_pods[i].move(1.0 - collision_time)

            # Solve the collision
            first_collision.a.bounce(first_collision.b)

            is_boss1_collided = is_boss1_collided or (first_collision.a.id == 'boss1' or first_collision.b.id == 'boss1')
            is_boss2_collided = is_boss2_collided or (first_collision.a.id == 'boss2' or first_collision.b.id == 'boss2')

            time += collision_time
            previous_collision = first_collision

            if time >= 1.0:  # end of the turn
                for i in range(nb_pods):
                    list_pods[i].finalize()

    return is_boss1_collided, is_boss2_collided


def get_next_entry_point(previous_ckpt, current_ckpt, next_ckpt):
    '''
    Return the entry point of the next checkpoint based on parallels between the current and future checkpoint
    https://www.codingame.com/blog/coders-strike-back-pb4608s-ai-rank-3rd/
    '''

    # Search director coefficient of the line between past and future checkpoints
    a = (next_ckpt.y - previous_ckpt.y) / (next_ckpt.x - previous_ckpt.x)

    # Compute b for the line going through actual checkpoint y = ax+b
    b = current_ckpt.y - a * current_ckpt.x

    # Determines the two intersections with the checkpoint radius
    A = 1.0 + a * a
    B = current_ckpt.x * ((-2.0 * a * a) - 2.0)
    C = (current_ckpt.x * current_ckpt.x) * (1.0 + a * a) - SQUARED_RADIUS_CHECKPOINT
    delta = B * B - 4 * A * C

    x1 = (-1.0 * B + sqrt(delta)) / (2 * A)
    x2 = (-1.0 * B - sqrt(delta)) / (2 * A)

    intersection_1 = Checkpoint(current_ckpt.id, floor(x1), floor(a * x1 + b), RADIUS_WAYPOINT)
    intersection_2 = Checkpoint(current_ckpt.id, floor(x2), floor(a * x2 + b), RADIUS_WAYPOINT)

    if intersection_1.x < intersection_2.x:
        top_left = intersection_1
        bottom_left = intersection_1
        top_right = intersection_2
        bottom_right = intersection_2
    elif intersection_1.x > intersection_2.x:
        top_left = intersection_2
        bottom_left = intersection_2
        top_right = intersection_1
        bottom_right = intersection_1
    else:
        if intersection_1.y < intersection_2.y:
            top_left = intersection_1
            top_right = intersection_1
            bottom_left = intersection_2
            bottom_right = intersection_2
        else:
            top_left = intersection_2
            top_right = intersection_2
            bottom_left = intersection_1
            bottom_right = intersection_1

    # Choose correct intersections function of previous checkpoint
    if previous_ckpt.x < current_ckpt.x:
        if previous_ckpt.y < current_ckpt.y:
            return top_left
        else:
            return bottom_left
    else:
        if previous_ckpt.y < current_ckpt.y:
            return top_right
        else:
            return bottom_right


# Initialization
laps = int(input())
checkpointCount = int(input())

list_checkpoints = []
for i in range(checkpointCount):
    x, y = [int(j) for j in input().split()]
    list_checkpoints.append(Checkpoint(i, x, y, RADIUS_CHECKPOINT))

list_distance_checkpoints = []
for i in range(checkpointCount):
    if i == checkpointCount - 1:
        next_ckpt = 0
    else:
        next_ckpt = i

    list_distance_checkpoints.append(list_checkpoints[i].get_distance(list_checkpoints[next_ckpt]))

list_entry_points = []
for i in range(len(list_checkpoints)):
    if i == 0:
        previous_ckpt = list_checkpoints[len(list_checkpoints) - 1]
    else:
        previous_ckpt = list_checkpoints[i - 1]

    if i == len(list_checkpoints) - 1:
        next_ckpt = list_checkpoints[0]
    else:
        next_ckpt = list_checkpoints[i + 1]

    current_ckpt = list_checkpoints[i]
    list_entry_points.append(get_next_entry_point(previous_ckpt, current_ckpt, next_ckpt))

cho = Pod("cho", RADIUS_POD)
gall = Pod("gall", RADIUS_POD)
boss1 = Pod("boss1", RADIUS_POD)
boss2 = Pod("boss2", RADIUS_POD)
boss_runner = boss1

cho.set_partner(gall)
gall.set_partner(cho)
boss1.set_partner(boss2)
boss2.set_partner(boss1)

caches_boss1 = []
caches_boss2 = []

AG = GeneticAlgorithm()

race_turn = 0
best_solution = None
minScore = 0

json = '{"game":{'
json += '"configuration":{'
json += '"nb_ckpt":' + str(len(list_checkpoints)) + ','
json += '"nb_moves":' + str(NB_MOVES) + ','
json += '"nb_population":' + str(NB_POPULATION) + ','
json += '"nb_tournament":' + str(NB_TOURNAMENT) + ''
json += '},'
json += '"data":{'

print(json, file=sys.stderr)

while True:
    start_time = time.clock()
    elapsed_time = 0.0
    new_time = 0.0
    delta_time = 0.0

    cho.set_parameters(input, race_turn)
    gall.set_parameters(input, race_turn)
    boss1.set_boss_parameters(input, race_turn)
    boss2.set_boss_parameters(input, race_turn)

    boss1.is_hunter = boss1.score() > boss2.score()
    boss2.is_hunter = not boss1.is_hunter

    boss_runner = boss1
    if boss2.is_hunter:
        boss_runner = boss2

    cho.is_hunter = False
    gall.is_hunter = True

    # cho.is_hunter  = cho.score() > gall.score() and (race_turn - cho.switch_checkpoint < 80) #add check on nb turn before losing
    # gall.is_hunter = not (cho.is_hunter) and (race_turn - gall.switch_checkpoint < 80) #add check on nb turn before losing

    if ((boss_runner.checked - 1) % checkpointCount) == gall.waiting_point.id:
        cho.waiting_point = list_checkpoints[boss_runner.get_checkpoint_id_coming_after()]
        gall.waiting_point = list_checkpoints[boss_runner.get_checkpoint_id_coming_after()]

    if race_turn == 0:
        print(cho.get_next_entry_point().x, cho.get_next_entry_point().y, 100)
        print(gall.get_next_entry_point().x, gall.get_next_entry_point().y, 100)

        race_turn += 1
    else:
        json = ''
        json += '"' + str(race_turn) + '":{'
        json += '"turn":' + str(race_turn) + ','
        json += '"checked_pod1":' + str(cho.checked) + ','
        json += '"checked_pod2":' + str(gall.checked) + ','
        json += '"scores":['

        cho.check_consistency()
        gall.check_consistency()

        save_cho, save_gall, save_boss1, save_boss2 = save_pod_states()
        generate_boss_cache()

        if race_turn == 1:
            AG.generate_population(True)
        else:
            AG.generate_population(False)

        scores_to_print = str(round(AG.get_best_solution().result, 2))

        new_time = (time.clock() - start_time) * 1000.0  # ms
        delta_time = new_time - elapsed_time
        elapsed_time = new_time

        index = 0
        best_solution = AG.get_best_solution().clone()
        AG.maximum = best_solution.result

        while (elapsed_time + delta_time) <= 145:
            index += 1

            AG.build_generation_proba()
            current_best_solution = AG.get_best_solution()

            scores_to_print += ',' + str(round(current_best_solution.result, 2))
            if current_best_solution.result > best_solution.result:
                best_solution = current_best_solution.clone()

            new_time = (time.clock() - start_time) * 1000.0  # ms
            delta_time = new_time - elapsed_time
            elapsed_time = new_time

        json += scores_to_print + '],'
        json += '"nb_generation":' + str(index) + ','
        json += '"best_score":' + str(round(best_solution.result, 2)) + ','
        json += '"max_fitness":' + str(round(AG.maximum, 2)) + '},'
        print(json, file=sys.stderr)

        cho.output(best_solution.moves1[0])
        gall.output(best_solution.moves2[0])

        race_turn += 1