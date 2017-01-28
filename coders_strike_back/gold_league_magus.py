import sys

import time
from math import sqrt
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
NB_SIMULATION_TURNS = 10
NB_BEST_SOLUTIONS = 5
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


class Pod(Unit):
    def __init__(self, id, radius):
        Unit.__init__(self, id, radius)
        self.angle = 0
        self.next_checkpoint_id = 0
        self.lap = 0
        self.checked = 0  # number of checkpoints checked
        self.timeout = TIMEOUT
        # self.partner = None
        self.is_shield_activated = False

    def set_partner(self, partner):
        self.partner = partner

    def set_parameters(self, input, checked, is_shield_activated):
        self.x, self.y, self.vx, self.vy, self.angle, self.next_checkpoint_id = [int(i) for i in input().split()]

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

        # If the point is below swith the angle sign to be correct
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
        if self.angle >= 360.0:
            self.angle -= 360.0
        elif self.angle < 0.0:
            self.angle += 360.0

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
        self.next_checkpoint_id += 1
        self.checked += 1

        if self.next_checkpoint_id == checkpointCount and self.lap < laps:
            self.next_checkpoint_id = self.next_checkpoint_id - checkpointCount
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
        # return self.checked * 50000 - self.get_distance(self.get_next_checkpoint())
        return (self.checked * 10000) - abs(self.get_delta_angle_orientation(self.get_next_checkpoint())) - self.get_angle(self.get_next_checkpoint()) - (self.get_distance(self.get_next_checkpoint()) * 2)

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
        return list_checkpoints[self.next_checkpoint_id]

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

    def output(self, move, commit):
        '''
        Apply the move on the pod and print result to game engine
        :param move: Move
        :return: none
        '''

        # Code extracted from rotate without blocking to 18°
        angle = self.angle + move.angle

        # Replace the angle between [0; 360] degrees
        # mod operator is slower than if comparison
        if angle >= 360.0:
            angle -= 360.0
        elif angle < 0.0:
            angle += 360.0

        # Look for a point corresponding to the targeted direction
        # Multiply by 10000.0 to limit rounding errors
        radians_angle = angle * pi / 180.0
        px = self.x + cos(radians_angle) * 10000.0;
        py = self.y + sin(radians_angle) * 10000.0;

        # TODO Add shield management to wait real Move implementation
        if commit:
            print(round(px), round(py), move.thrust)

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


class Collision():
    def __init__(self, unit_a, unit_b, time):
        self.a = unit_a
        self.b = unit_b
        self.time = time  # time at which the collision between a and b occurs


class Solution():
    def __init__(self):
        self.pod1_moves = []
        self.pod2_moves = []

    def set_moves(self, pod1_moves, pod2_moves):
        self.pod1_moves = pod1_moves
        self.pod2_moves = pod2_moves

    def score(self, pod1, pod2, boss1, boss2, list_checkpoint):
        '''
        Return the score of the solution after X turns
        :return: score
        '''

        self.save_state(pod1, pod2, boss1, boss2)

        # Play out the turns
        for i in range(NB_SIMULATION_TURNS):
            # Apply the moves to the pod before simulating the current turn
            pod1.apply(self.pod1_moves[i])
            pod2.apply(self.pod2_moves[i])

            boss1.apply(Move(boss1.get_delta_angle_orientation(list_checkpoints[boss1.next_checkpoint_id]), 100))
            boss2.apply(Move(boss2.get_delta_angle_orientation(list_checkpoints[boss2.next_checkpoint_id]), 100))

            self.play([pod1, pod2, boss1, boss2], list_checkpoint)

        # Compute the scores
        result = self.evaluation(pod1, pod2, boss1, boss2)

        # reset everyone to the original state
        self.reset_state(pod1, pod2, boss1, boss2)

        return result

    def evaluation(self, runner_pod, hunter_pod, runner_boss, hunter_boss):
        '''
        Return the score associated to this solution
        '''

        runner = None
        if runner_boss.checked > hunter_boss.checked:
            runner = runner_boss
        elif runner_boss.checked == hunter_boss.checked and runner_boss.next_checkpoint_id > hunter_boss.next_checkpoint_id:
            runner = runner_boss
        else:
            runner = hunter_boss

        if runner_pod.timeout == 0 or hunter_pod.timeout == 0:
            # timeout
            return -inf
        elif runner_pod.next_checkpoint_id == -1 and runner.next_checkpoint_id != -1:
            # boss runner wins the race
            return -inf
        elif runner_pod.next_checkpoint_id == -1 and runner.next_checkpoint_id != -1:
            # player wins the race !!!
            return inf

        # score depends on how much the pod is in advance on the boss
        score = (runner_pod.score() - runner.score()) * (hunter_pod.score() - runner.score())

        return score

    def mutate(self, amplitude):
        '''
        Change the moves in the solution by mutation
        :amplitude: degree of modification
        :return: none
        '''
        # TODO : make a more intelligent mutation :)

        for i in range(NB_SIMULATION_TURNS):
            self.pod1_moves[i].mutate(amplitude)
            self.pod2_moves[i].mutate(amplitude)

    def save_state(self, pod1, pod2, boss1, boss2):
        self.save_pod1 = pod1.clone()
        self.save_pod2 = pod2.clone()
        self.save_boss1 = boss1.clone()
        self.save_boss2 = boss2.clone()

    def reset_state(self, pod1, pod2, boss1, boss2):
        pod1.load(self.save_pod1)
        pod2.load(self.save_pod2)
        boss1.load(self.save_boss1)
        boss2.load(self.save_boss2)

    def play(self, list_pods, list_checkpoint):
        '''
        Simulate a whole turn
        '''
        time = 0.0  # time during the turn (end of the turn = 1.0)

        list_previous_collisions = [None for _ in range(len(list_pods))]
        while time < 1.0:

            # if previous_collision != None:
            #    print('Previous_collision  (' + str(previous_collision.a.id) + ', ' + str(previous_collision.b.id) + ', ' + str(previous_collision.time) + ')', file=sys.stderr)

            # Check all the collisions that are going to happen during this turn
            i = 0
            while i < len(list_pods):
                pod = list_pods[i]
                previous_collision = list_previous_collisions[i]
                first_collision = None

                j = i + 1
                while j < len(list_pods):
                    other_pod = list_pods[j]
                    collision = pod.get_collision(other_pod)

                    if previous_collision != None and collision != None and collision.a == previous_collision.a and collision.b == previous_collision.b and collision.time == 0.0:
                        collision = None

                    # If the collision is earlier in time than the one currently saved, keep it !
                    if collision != None and (collision.time + time < TIME_FULL_TURN) and (
                                    first_collision == None or collision.time < first_collision.time):
                        first_collision = Collision(collision.a, collision.b, round(collision.time, 4))

                    j += 1

                # Collision with another checkpoint?
                # It is unnecessary to check all checkpoints here.We only test the pod's next checkpoint.
                # We could look for the collisions of the pod with all the checkpoints, but if such a collision happens it wouldn't impact the game in any way
                collision = list_pods[i].get_collision(list_checkpoints[list_pods[i].next_checkpoint_id])

                if previous_collision != None and collision != None and collision.a == previous_collision.a and collision.b == previous_collision.b and collision.time == 0.0:
                    collision = None

                # If the collision is earlier in time than the one currently saved, keep it !
                if collision != None and (collision.time + time < TIME_FULL_TURN) and (
                                first_collision == None or collision.time < first_collision.time):
                    first_collision = Collision(collision.a, collision.b, round(collision.time, 4))

                if first_collision == None:
                    # No collision this turn to manage
                    for pod in list_pods:
                        pod.move(TIME_FULL_TURN - round(time, 4))

                    # end of the turn
                    time = TIME_FULL_TURN
                else:
                    # Move the pods to reach the time `t` of the collision
                    for pod in list_pods:
                        pod.move(round(first_collision.time, 4))

                    # Resolve the collision
                    first_collision.a.bounce(first_collision.b)
                    time += round(first_collision.time, PRECISION)

                if first_collision != None:
                    list_previous_collisions[i] = Collision(first_collision.a, first_collision.b,
                                                            round(first_collision.time, 4))

                i += 1

        # Finalize the turn
        for pod in list_pods:
            pod.finalize()

    def clone(self):
        clone = Solution()

        for i in range(NB_SIMULATION_TURNS):
            clone.pod1_moves.append(Move(self.pod1_moves[i].angle, self.pod1_moves[i].thrust))
            clone.pod2_moves.append(Move(self.pod2_moves[i].angle, self.pod2_moves[i].thrust))

        return clone

        # def randomize(self):
        #    ''''
        #    '''
        #    print('TODO', file=sys.stderr)


class Move():
    def __init__(self, angle, thrust):
        self.angle = angle  # between [-18 , 18]
        self.thrust = thrust  # between [-1, 100], -1 is Shield
        # self.shield = False

    def mutate(self, amplitude):
        '''
        Change the move by mutation
        :amplitude: degree of modification
        :return: none
        '''
        angle_min = self.angle - 18.0 * amplitude
        angle_max = self.angle + 18.0 * amplitude

        if angle_min < -18.0:
            angle_min = -18.0
        if angle_max > 18.0:
            angle_max = 18.0

        self.angle = uniform(angle_min, angle_max)

        # TODO Add shield management
        # if !self.shield and random.uniform(0, 100) < SHIELD_PROB:
        #    self.shield = True

        thrust_min = self.thrust - 100 * amplitude
        thrust_max = self.thrust + 100 * amplitude

        if thrust_min < 0:
            thrust_min = 50

        elif thrust_max < thrust_min:
            thrust_max = thrust_min + 30

        if thrust_max > 100:
            thrust_max = 100

        if self.angle < 10 and self.angle > -10:
            self.thrust = 100
        else:
            self.thrust = ceil(uniform(thrust_min, thrust_max))

            # TODO Add shield management
            # self.shield = False


# def test(list_pods, list_checkpoints):
#    for pod in list_pods:
#        pod.rotate(Point(8000, 4000))
#       pod.accelerate(100)
#    play(list_pods, list_checkpoints)

def generate_fastest_individual(pod1, pod2):
    individual = Solution()
    list_moves_pod1 = []
    list_moves_pod2 = []

    for j in range(0, NB_SIMULATION_TURNS):
        list_moves_pod1.append(Move(pod1.get_delta_angle_orientation(list_checkpoints[pod1.next_checkpoint_id]), 100))
        list_moves_pod2.append(Move(pod2.get_delta_angle_orientation(list_checkpoints[pod2.next_checkpoint_id]), 100))

    individual.set_moves(list_moves_pod1, list_moves_pod2)
    return individual


def generate_population(previous_best_solution):
    '''
    Generate the population of the solution
    :return: solution
    '''
    # TODO Include the best previous solution in the population (delete first move, add random move at the end)

    population = []
    if previous_best_solution == None:
        population.append(generate_fastest_individual(cho, gall))
        for i in range(1, NB_BEST_SOLUTIONS):
            individual = Solution()
            list_moves_pod1 = []
            list_moves_pod2 = []

            for j in range(0, NB_SIMULATION_TURNS):
                move = Move(cho.get_delta_angle_orientation(list_checkpoints[cho.next_checkpoint_id]), 100)
                move.mutate(0.2)
                list_moves_pod1.append(move)
                move = Move(gall.get_delta_angle_orientation(list_checkpoints[gall.next_checkpoint_id]), 100)
                move.mutate(0.2)
                list_moves_pod2.append(move)

            individual.set_moves(list_moves_pod1, list_moves_pod2)
            population.append(individual)

    else:
        previous_solution = previous_best_solution.clone()
        thrust_1 = previous_solution.pod1_moves[0].thrust
        thrust_2 = previous_solution.pod1_moves[0].thrust
        first_move_pod1 = Move(cho.get_delta_angle_orientation(list_checkpoints[cho.next_checkpoint_id]), thrust_1)
        first_move_pod1.mutate(0.05)
        first_move_pod2 = Move(gall.get_delta_angle_orientation(list_checkpoints[gall.next_checkpoint_id]), thrust_2)
        first_move_pod2.mutate(0.05)

        previous_solution.pod1_moves = previous_solution.pod1_moves[1:]
        previous_solution.pod1_moves.append(first_move_pod1)
        previous_solution.pod2_moves = previous_solution.pod2_moves[1:]
        previous_solution.pod2_moves.append(first_move_pod2)
        population.append(previous_solution)
        population.append(generate_fastest_individual(cho, gall))

        for i in range(2, NB_BEST_SOLUTIONS):
            individual = Solution()
            list_moves_pod1 = []
            list_moves_pod2 = []

            for j in range(0, NB_SIMULATION_TURNS):
                move = Move(cho.get_delta_angle_orientation(list_checkpoints[cho.next_checkpoint_id]), thrust_1)
                move.mutate(0.05)
                list_moves_pod1.append(move)
                move = Move(gall.get_delta_angle_orientation(list_checkpoints[gall.next_checkpoint_id]), thrust_2)
                move.mutate(0.05)
                list_moves_pod2.append(move)

            individual.set_moves(list_moves_pod1, list_moves_pod2)
            population.append(individual)

    return population


# Initialization
laps = int(input())
checkpointCount = int(input())

list_checkpoints = []
for i in range(checkpointCount):
    x, y = [int(i) for i in input().split()]
    list_checkpoints.append(Checkpoint(i, x, y, RADIUS_CHECKPOINT))

cho = Pod("cho", RADIUS_POD)
gall = Pod("gall", RADIUS_POD)
boss1 = Pod("boss1", RADIUS_POD)
boss2 = Pod("boss2", RADIUS_POD)

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

    # Search the best solution to play function of the current state
    solutions = generate_population(best_solution)
    amplitude = 1.0
    best_score = -inf
    while elapsed_time < 150:
        min_score = best_score

        solution = solutions[randint(0, NB_BEST_SOLUTIONS - 1)]
        solution.mutate(amplitude)

        score = solution.score(cho, gall, boss1, boss2, list_checkpoints)
        if score > min_score:
            best_solution = solution.clone()
            best_score = score
            amplitude = amplitude * 0.4
            print('Turn ' + str(turn) + ' best solution pod 1 thrust : ' + str(best_solution.pod1_moves[0].thrust), file=sys.stderr)

        amplitude = amplitude * 0.6

        elapsed_time += (time.time() - start_time) * 1000.0  # ms

    turn += 1
    cho.output(best_solution.pod1_moves[0], True)
    gall.output(best_solution.pod2_moves[0], True)

    # test([cho, gall], list_checkpoints)

    # cho.play(list_checkpoints[cho.next_checkpoint_id], 100.0)
    # gall.play(list_checkpoints[gall.next_checkpoint_id], 100.0)

    # You have to output the target position
    # followed by the power (0 <= thrust <= 100)
    # i.e.: "x y thrust"
    # print(str(cho.x) + " " + str(cho.y) + " " + str(100))
    # print(str(gall.x) + " " + str(gall.y) + " " + str(100))
    # output(cho, list_checkpoints[cho.next_checkpoint_id])
    # output(gall, list_checkpoints[gall.next_checkpoint_id])

