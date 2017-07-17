import sys
import math
import time
from heapq import heappop, heappush
from numpy import zeros, int32

PLAYER = 0
BOMB = 1
ITEM = 2

ME = 0
ENNEMY = 0

BOMB_INIT_SIZE = 3

MAP_BOX = '0'
MAP_RANGE = '1'
MAP_EXTRA = '2'
MAP_BOMB = 'B'
MAP_ITEM = 'I'
MAP_EMPTY = '.'
MAP_WALL = 'X'
MAP_NOT_YET = 'b'

ITEM_RANGE = 1
ITEM_BOMB = 2

def get_neighbors(area, position, to_avoid):
    '''
    Generator for neighbors
    '''
    
    for i in [-1, 1]:
        pos = (position[0] + i, position[1])
        
        if (pos[0] < 0 or pos[0] >= width) \
        or area[pos[1]][pos[0]] in to_avoid:
            continue        
        
        yield pos
    
    for j in [-1,1]:
        pos = (position[0], position[1] + j)
        
        if (pos[1] < 0 or pos[1] >= height) \
        or area[pos[1]][pos[0]] in to_avoid:
            continue        
        
        yield pos

def find_closest_priority(area, priority_map, root, priority):
    '''
    Implementation  of BFS
    '''
    
    front_nodes = []
    visited_nodes = []
    
    front_nodes.append(root)
    visited_nodes.append(root)
    
    while len(front_nodes) > 0:
        cur = front_nodes.pop(0)
        if priority_map[cur[1]][cur[0]] == priority :
            return cur
        
        for neighbor in get_neighbors(area, cur, [MAP_BOX, MAP_RANGE, MAP_EXTRA, MAP_BOMB, MAP_WALL]):
            if neighbor not in visited_nodes: #and area[neighbor[1]][neighbor[0]] != 'C':
                visited_nodes.append(neighbor)                
                front_nodes.append(neighbor)
                
    return (-1, -1)
        
def heuristic(cell, goal):
    '''
    Heuristic for A*, here manhattan distance
    '''    
    return abs(cell[0] - goal[0]) + abs(cell[1] - goal[1])


def find_path_astar(area, root, goal, to_avoid):
    '''
    Implementation of A*
    '''
    
    pr_queue = []
    heappush(pr_queue, (0 + heuristic(root, goal), 0, [], root))
    visited = set()
    
    while len(pr_queue) > 0:
        _, cost, path, current = heappop(pr_queue) #return the priority in the heap, cost, path and current element
        
        if current == goal: #Maybe change here to return the element and compute the path after ...
            return path, cost
            
        if current in visited:
            continue
        
        visited.add(current)
        for neighbour in get_neighbors(area, current, to_avoid):
            new_path = path[:]
            new_path.append(neighbour)
            heappush(pr_queue, (cost + heuristic(neighbour, goal), cost + 1, new_path, neighbour))
            
    return [], -1

def get_boxes_impacted_by_flame(p_area, pos_bomb, range_bomb, is_including_box = False):
    for i in [-1, 1]:
        blocked = False
        for j in range(1, range_bomb):
            new_x = pos_bomb[0] + j*i
            if not blocked and new_x < 0 or new_x >= width:
                blocked = True
            
            if not blocked:
                #if area[pos_bomb[1]][new_x] == MAP_BOX or area[pos_bomb[1]][new_x] == MAP_BOMB:
                if p_area[pos_bomb[1]][new_x] in [MAP_BOX, MAP_RANGE, MAP_EXTRA, MAP_BOMB, MAP_ITEM, MAP_WALL, MAP_NOT_YET]:
                    blocked = True
                    
                    if is_including_box:            
                        yield (new_x, pos_bomb[1])
                else:
                    yield (new_x, pos_bomb[1])
                                        
    for i in [-1, 1]:
        blocked = False
        for j in range(1, range_bomb):
            new_y = pos_bomb[1] + j*i            
            if not blocked and new_y < 0 or new_y >= height:
                blocked = True
                    
            if not blocked:        
                #if area[new_y][pos_bomb[0]] == MAP_BOX or area[new_y][pos_bomb[0]] == MAP_BOMB:
                if p_area[new_y][pos_bomb[0]] in [MAP_BOX, MAP_RANGE, MAP_EXTRA, MAP_BOMB, MAP_ITEM, MAP_WALL, MAP_NOT_YET]:
                    
                    if new_y == 10  and pos_bomb[0] == 2:
                        print('BLOCKED HERE !', file=sys.stderr)
                    
                    blocked = True
                                                        
                    if is_including_box:
                        
                        if new_y == 10  and pos_bomb[0] == 2:
                            print('INCLUDED BLOCKED HERE !', file=sys.stderr)
                        
                        yield (pos_bomb[0], new_y)
                else:
                    if new_y == 10  and pos_bomb[0] == 2:
                        print('NOT BLOCKED HERE !', file=sys.stderr)
                        
                    yield (pos_bomb[0], new_y)


def clean_boxes_to_be_deleted(p_area, p_area_clean, p_bombs):
    '''
    Delete boxes that will be destroyed by the currently setted bombs
    p_area: is the reference area (non modified)
    p_area_clean: area without the destroyed boxes (modificed)
    p_bombs: list of bombs to apply (non modified)
    '''
    for bomb in bombs:        
        for pos in get_boxes_impacted_by_flame(p_area, bomb, bomb[3], True):            
            if p_area[pos[1]][pos[0]] in [MAP_BOX, MAP_EXTRA, MAP_RANGE]:
                if bomb[2] == 0:
                    p_area_clean[pos[1]][pos[0]] = '.'
                else:
                    p_area_clean[pos[1]][pos[0]] = MAP_NOT_YET

def define_safe_area(p_area, p_safe_area, p_bombs):        
    for bomb in bombs:        
        for pos in get_boxes_impacted_by_flame(p_area, bomb, bomb[3], True):            
            if p_area[pos[1]][pos[0]] in ['.']:
                p_safe_area[pos[1]][pos[0]] = bomb[2]
                
    return p_safe_area
    
def define_best_bombs_placement_area(p_area_size, p_area_clean):
    '''
    Return a map with the best places to put a bomb
    Return as well the highest defined priority
    p_area_size: size of the area
    p_area_clean: area without the boxes that will be deleted by currently setted bombs
    '''
    best_bombs_area = zeros(p_area_size, dtype=int32)
    max_priority = 0
    for y in range(height):
        for x in range(width):
            if p_area_clean[y][x] in [MAP_BOX, MAP_RANGE, MAP_EXTRA]:
                boxes.append((x,y))
                                
                for pos in get_boxes_impacted_by_flame(p_area_clean, (x,y), me[3]):
                    best_bombs_area[pos[1]][pos[0]] += 1    
                    
                    if best_bombs_area[pos[1]][pos[0]] > max_priority:
                        max_priority = best_bombs_area[pos[1]][pos[0]]  
    
    return best_bombs_area, max_priority

def debug_area(p_area):
    for y in range(height):
        line = ''
        for x in range(width):
            line += str(p_area[y][x])            
        print(line, file=sys.stderr)     

# Auto-generated code below aims at helping you parse
# the standard input according to the problem statement.

width, height, my_id = [int(i) for i in input().split()]
size = (height, width)
area = []
area_bomb_solved = []
boxes = []
area_safe = []

me = None
ennemy = None

bombs_me = []
bombs_enn = []
bombs = []

items_range = []
items_bomb = []

# game loop
turn = 0
while True:
    
    start = time.time()
    
    area.clear()
    area_bomb_solved.clear()    
    area_items = zeros(size, dtype=int32)
    area_safe = zeros(size, dtype=int32)
    bombs.clear()
    items_range.clear()
    items_bomb.clear()
    
    #Initialisation: get the new state of the map
    for y in range(height):
        row = input()
        area.append(list(row))
        area_bomb_solved.append(list(row))
    
    #Initialisation: get entities positions         
    entities = int(input())
    for i in range(entities):
        entity_type, owner, x, y, param_1, param_2 = [int(j) for j in input().split()]
        
        if entity_type == PLAYER and owner == my_id:
            me = (x, y, param_1, param_2)
            #area[y][x] = 'M'
        
        elif entity_type == PLAYER and owner != my_id:
            ennemy = (x,y, param_1, param_2)
            #area[y][x] = 'E'
        
        elif entity_type == BOMB and owner == my_id:   
            bombs.append((x, y, param_1, param_2))
            bombs_me.append((x,y, param_1, param_2))
            area[y][x] = MAP_BOMB
            area_bomb_solved[y][x] = MAP_BOMB
            area_safe[y][x] = param_1
        
        elif entity_type == BOMB and owner != my_id:
            bombs.append((x, y, param_1, param_2))
            bombs_enn.append((x,y, param_1, param_2))
            area[y][x] = MAP_BOMB
            area_bomb_solved[y][x] = MAP_BOMB
            area_safe[y][x] = param_1
        
        elif entity_type == ITEM:
            if param_1 == ITEM_RANGE:
                items_range.append((x, y))
            elif param_1 == ITEM_BOMB:
                items_bomb.append((x, y))   
            
            area[y][x] = MAP_ITEM    
            area_bomb_solved[y][x] = MAP_ITEM
            area_items[y][x] = param_1
 
    #Clean map of boxes that will be destroyed by existing bombs
    clean_boxes_to_be_deleted(area, area_bomb_solved, bombs)
    
    #Define safe areas
    area_safe = define_safe_area(area, area_safe, bombs)
                
    #Initialisation: find hottest spot for bombs    
    best_bombs_area, max_priority = define_best_bombs_placement_area(size, area_bomb_solved)                        

    #For debug                 
    debug_area(area_safe)
        
    #Find closest hottest spot (BFS)
    spot = (-1,-1)
    while spot == (-1,-1) and max_priority > 0:
        spot = find_closest_priority(area, best_bombs_area, me, max_priority)
        
        if spot == (-1,-1):
            max_priority -= 1
            
    #if max_priority != 0:
    #    spot = find_closest_priority(area, best_bombs_area, me, max_priority)
    #else:
    #    spot = (-1,-1)
    print('max prio: ' + str(max_priority), file=sys.stderr)
    print('best spot: ' + str(spot), file=sys.stderr)
    
    #Find path
    if spot != (-1,-1):
        path, cost = find_path_astar(area, me, spot, [MAP_BOX, MAP_RANGE, MAP_EXTRA, MAP_BOMB, MAP_WALL])
    else:
        path, cost = [], -1
    
    #Find closest item range and bomb
    spot_range = find_closest_priority(area, area_items, (me[0], me[1]), ITEM_RANGE)        
    spot_bomb  = find_closest_priority(area, area_items, (me[0], me[1]), ITEM_BOMB)
    
    print('item range: ' + str(spot_range), file=sys.stderr)
    print('item bomb: ' + str(spot_bomb), file=sys.stderr)
    
    path_range, cost_range = [], -1
    if spot_range != (-1,-1):
        path_range, cost_range = find_path_astar(area, me, spot_range, [MAP_BOX, MAP_RANGE, MAP_EXTRA, MAP_BOMB, MAP_WALL])
    
    path_bomb, cost_bomb = [], -1
    if spot_bomb != (-1,-1):
        path_bomb, cost_bomb = find_path_astar(area, me, spot_bomb, [MAP_BOX, MAP_RANGE, MAP_EXTRA, MAP_BOMB, MAP_WALL])
        

    #Solve actions
    #Etape 1: bomb or move?
    action = 'MOVE'
    if spot == me or (best_bombs_area[me[1]][me[0]] >= 1 and (me[2] > 1 or (me[2] == 1 and cost > 8))):
        action = 'BOMB'

    #Etape 2: where to move?
    if spot == me:
        #Search a new spot to start moving by deleting the boxes impacted by the new bomb!
        clean_boxes_to_be_deleted(area_bomb_solved, area_bomb_solved, [spot])
        best_bombs_area, max_priority = define_best_bombs_placement_area(size, area_bomb_solved)
        
        #Find new closest hottest spot (BFS)
        if max_priority != 0:
            new_spot = find_closest_priority(area, best_bombs_area, (me[0], me[1]), max_priority)    
        else:
            new_spot = (-1,-1)
            
        if new_spot != (-1,-1):
            path, cost = find_path_astar(area, me, new_spot, [MAP_BOX, MAP_RANGE, MAP_EXTRA, MAP_BOMB, MAP_WALL])
        else:
            path, cost = [], -1
                
    #Get closest priority bomb, items or do not move if there is no path
    if (cost_range < cost or cost == -1) and cost_range < cost_bomb and cost_range != -1:
        next_pos = path_range[0]
    elif (cost_bomb < cost or cost == -1) and cost_bomb < cost_range and cost_bomb != -1:
        next_pos = path_bomb[0]
    elif ((cost_bomb < cost and cost_range < cost) or cost == -1) and cost_bomb == cost_range and cost_bomb != -1:    
        next_pos = path_range[0]
    elif cost != -1:
        next_pos = path[0]       
    else:
        next_pos = me
    
    print(action + ' ' + str(next_pos[0]) + ' ' + str(next_pos[1]))
    
    '''        
    if spot == me:
        #If already right on the spot
        print('BOMB ' + str(me[0]) + ' ' + str(me[1]))
    else:    
        #Get path to spot (A*)
        if spot != (-1,-1):
            path, cost = find_path_astar(area, me, spot, [MAP_BOX, MAP_RANGE, MAP_EXTRA, MAP_BOMB])                                                 
        
        #Get closest priority bomb, items or do not move if there is no path
        if cost_range < cost and cost_range < cost_bomb and cost_range != -1:
            next_pos = path_range[0]
        elif cost_bomb < cost and cost_bomb < cost_range and cost_bomb != -1:
            next_pos = path_bomb[0]
        elif cost_bomb < cost and cost_range < cost and cost_bomb == cost_range and cost_bomb != -1:    
            next_pos = path_range[0]
        elif cost != -1:
            next_pos = path[0]       
        else:
            next_pos = me
        
        print('MOVE ' + str(next_pos[0]) + ' ' + str(next_pos[1]))
    '''
    
    print('elapsed time: ' + str((time.time() - start)*1000), file=sys.stderr)
    
    turn += 1