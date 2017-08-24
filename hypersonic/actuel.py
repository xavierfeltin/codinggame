import sys
import math
import time
import numpy
import gc
from collections import deque
from numpy import zeros, int32, copy

BEAM_WIDTH = 30
MAX_DEPTH = 15
TIMEOUT = 0.09

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

INT_ITEM_EXTRA = 10
INT_ITEM_RANGE = 11 
INT_WALL = 12
INT_BOX = 13
INT_BOX_RANGE = 14
INT_BOX_EXTRA = 15
INT_EMPTY = 0
INT_FLAME = 16

ACT_BOMB = 1
ACT_MOVE = 0

gc.disable()

class GameState:
    
    def __init__(self):
        self.area = None
        self.next_area = None
        self.safety_matrix = None
        
        self.bombs = None
        self.impacted_by_flames_from_me = None
        self.prev_moves = None
                
        self.nb_boxes = 0
        
        self.me = None
        self.move = None
        
        self.score = 0
        self.action = ''
        
        self.my_id = -1
        self.ennemies = None
        self.max_bombs = 0
        self.nb_remain_bombs = 0
        self.nb_destroyed_boxes = 0
        
        self.bomb_range = 0
        
        self.is_dead = False
        self.depth = 0
            
    def set_state(self, game_state):
        state = GameState()
        
        self.area = numpy.copy(game_state.area)
        self.next_area = game_state.next_area
        self.safety_matrix = game_state.safety_matrix
        
        self.bombs = game_state.bombs[:]
        self.impacted_by_flames_from_me = game_state.impacted_by_flames_from_me
            
        self.nb_boxes = game_state.nb_boxes
        self.me = game_state.me              
        self.score = game_state.score
        self.action = game_state.action
        self.move = game_state.move
        
        self.my_id = game_state.my_id
        self.ennemies = game_state.ennemies
        self.max_bombs = game_state.max_bombs
        self.nb_remain_bombs = game_state.nb_remain_bombs
        self.nb_destroyed_boxes = game_state.nb_destroyed_boxes
                
        self.bomb_range = game_state.bomb_range
        
        self.is_dead = game_state.is_dead
        self.depth = game_state.depth
        
        self.prev_moves = game_state.prev_moves[:]                       
        
    def clone(self):
        
        state = GameState()
        state.set_state(self)
        state.add_move(self.move, self.action)
        
        return state
        
    def set_attr(self, p_area, p_next_area, p_safety_matrix, p_my_id, p_ennemies, p_max_bombs, p_bomb_range, p_nb_rem_bombs, p_bombs, p_nb_boxes, p_nb_detroyed_boxes, p_prev_moves, p_max_priority, p_me, p_score):
        
        self.area = numpy.copy(p_area)
        self.next_area = p_next_area
        self.safety_matrix = p_safety_matrix
        
        self.bombs = p_bombs[:]
        self.impacted_by_flames_from_me = None
            
        self.nb_boxes = p_nb_boxes
        self.me = p_me      
        self.nodes = deque()
        self.score = p_score
        self.action = 'MOVE'
        self.move = (0,0)
        
        self.my_id = p_my_id
        self.ennemies = p_ennemies
        self.max_bombs = p_max_bombs
        self.nb_remain_bombs = p_nb_rem_bombs
        self.nb_destroyed_boxes = p_nb_detroyed_boxes
                
        self.bomb_range = p_bomb_range
        
        self.is_dead = False
        self.depth = 0
                
        self.prev_moves = p_prev_moves[:]       
        
    def add_move(self, p_move, p_action):
        if p_action == ACT_BOMB:
            self.prev_moves.clear()
        
        self.prev_moves.append((p_move[0], p_move[1]))
    
    def set_action(self, p_action, p_move, p_depth):
        self.action = p_action
        self.move = (p_move[0], p_move[1])
        self.depth = p_depth
    
    def is_bomb_interesting(self):
        '''
        Return a map with the best places to put a bomb
        Return as well the highest defined priority
        p_area_size: size of the area
        p_area_clean: area without the boxes that will be deleted by currently setted bombs
        '''
        
        nb_possible = False        
        if self.nb_remain_bombs == 0 or 0 < self.area[self.me[1], self.me[0]] <= 8 or self.nb_boxes == 0:
            #no bomb ...no interest, 
            #already a bomb at the position not interesting as well...
            return False
        
        for pos in self.impacted_by_flames_from_me:            
            nb_possible = True
            break
                                        
        return nb_possible
        
    def get_moves(self):
        '''
        Generator to return new available positions for player
        '''
        
        cases =  [[-1, 0], [1, 0], [0, -1], [0, 1], [0,0]]        
                
        me_x = self.me[0]
        me_y = self.me[1]
        map_actual_item = self.next_area[me_y, me_x]
        
        is_first_iter = (self.depth == MAX_DEPTH -1)        
        if is_first_iter:
            close_ennemies = [e for e in self.ennemies if (e[1] == me_y or e[0] == me_x)]
            same_case_ennemies = [e for e in self.ennemies if (e[1] == me_y and e[0] == me_x)]
        else:
            close_ennemies = []
            same_case_ennemies = []
        
        for x_offset, y_offset in cases:
            new_x = self.me[0] + x_offset
            new_y = self.me[1] + y_offset
                                    
            if 0 <= new_x < width and 0 <= new_y < height:
                                
                move_safe, bomb_safe = self.is_safe((new_x, new_y), self.is_bomb_interesting, close_ennemies, same_case_ennemies)
                
                #print('depth: ' + str(self.depth) + ', move: ' + str((new_x, new_y)) + ' = ' + str(self.next_area[new_y, new_x]), file=sys.stderr, flush=True)
                
                is_safe = move_safe
                
                map_item = self.area[new_y, new_x]
                map_next_item = self.next_area[new_y, new_x]
                
                #Case 1 : we are in future flames, need to get out !    
                if is_safe and map_actual_item == INT_FLAME:
                    #Case 1a : next solution is out of flames so great !
                    if map_next_item != INT_FLAME:
                        yield(new_x, new_y, bomb_safe)        
                        
                    #Case 1b : next solution is in flames, go forward if no other solution ...
                    else:
                        #print(str((new_x, new_y)) + ', me:' + str(self.area[self.me[1],self.me[0]]) + ', new: ' + str(self.area[new_y,new_x]) + ', nme: ' + str(self.next_area[self.me[1],self.me[0]]) + ', nnew: ' + str(self.next_area[new_y,new_x]), file=sys.stderr, flush=True)
                        other_solution = None
                        cases =  [[-1, 0], [1, 0], [0, -1], [0, 1]]
                        for x_offset, y_offset in cases:
                            neighbor_x = me_x + x_offset
                            neighbor_y = me_y + y_offset
                            if 0 <= neighbor_x < width and 0 <= neighbor_y < height and neighbor_x != new_x and neighbor_y != new_y:
                                if self.area[neighbor_y,neighbor_x] in [INT_EMPTY, INT_ITEM_EXTRA, INT_ITEM_RANGE] and  self.next_area[neighbor_y,neighbor_x] != INT_FLAME:
                                    other_solution = (neighbor_x, neighbor_y, bomb_safe)
                                    break                           
                        
                        if other_solution is None and self.is_not_cycling((new_x, new_y)) and (new_x != me_x or new_y != me_y):
                            yield (new_x, new_y, bomb_safe)    
                        elif other_solution is not None :
                            yield other_solution
                                             
                #Case 2 : everything is fine and do not enter into flames
                elif is_safe and map_next_item != INT_FLAME:
                    #print(str((new_x, new_y)) + ' is case 2', file=sys.stderr, flush=True)
                    if self.is_not_cycling((new_x, new_y)): yield(new_x, new_y, bomb_safe) 
                
                                                                                                                                                                   
    def is_not_cycling(self, p_move):
        '''
        Return True if the new move is making a cycle with previous moves
        '''
        
        nb_moves = len(self.prev_moves)
        if nb_moves > 3:
            distance = 0
            last_move = p_move
            
            sequence = str(p_move)
            
            nb_different_moves = 0
            nb_identic_moves = 0
                        
            for move in reversed(self.prev_moves):
                
                if move != last_move: 
                    nb_different_moves += 1
                    if nb_identic_moves > 0: break #consecutive moves only
                else: 
                    nb_identic_moves += 1
                    if nb_different_moves > 0: break #consecutive moves only
                
                distance += last_move[0] - move[0] + last_move[1] - move[1]
                last_move = (move[0], move[1])
                
                sequence += ', ' + str(move)                
                                
                if 3 <= nb_different_moves <= 8 and distance == 0:
                    #print(str(self.depth) + ', len: ' + str(nb_different_moves) + ', dist: ' + str(distance) + ', seq: ' + sequence, file=sys.stderr, flush=True)
                    return False
                elif nb_identic_moves > 3:
                    #print(str(self.depth) + ', len: ' + str(nb_identic_moves) + ', dist: ' + str(distance) + ', seq: ' + sequence, file=sys.stderr, flush=True)                    
                    return False                                
                    
        return True
                
                                
    def get_boxes_impacted_by_flame(self, pos_bomb, range_bomb):
        cases =  [[-1, 0], [1, 0], [0, -1], [0, 1]]
        
        for x_offset, y_offset in cases:
            blocked = False
            
            for j in range(1, range_bomb):
                if blocked:
                    break
                
                new_x = pos_bomb[0] + j*x_offset
                new_y = pos_bomb[1] + j*y_offset
                
                if 0 <= new_x < width and 0 <= new_y < height:
                    map_item = self.area[new_y,new_x]                    
                    if map_item != INT_EMPTY:
                        blocked = True
                        yield (new_x, new_y, map_item)
                    elif new_x == self.me[0] and new_y == self.me[1] :
                        yield (new_x, new_y, -1)
                        
        if pos_bomb[0] == self.me[0] and pos_bomb[1] == self.me[1] :
            yield (pos_bomb[0], pos_bomb[1], -1)
    
    def is_new_state(self, previous_states):
        
        key = (self.me[0], self.me[1], self.bomb_range, len(self.bombs), self.max_bombs, self.nb_remain_bombs, self.nb_boxes, self.nb_destroyed_boxes)
        
        if len(previous_states) == 0:
            #previous_states.append(self)
            hash_states[key] = self.bombs
            return True
        
        if key in hash_states:
            hash_states[key] = self.bombs
            for bomb in self.bombs:
                if bomb not in hash_states:
                    hash_states[key] = self.bombs
                    return True
            return False
        else:
            hash_states[key] = self.bombs
            return True
        
    def check_safe_from_pos(self, p_pos, p_range, p_is_x_axis, p_is_positive):
        '''
        Return True if there is a safe place from the position at the indicated range
        '''
        
        if p_is_positive:
            coeff = 1
        else:
            coeff = -1
        
        if p_is_x_axis:    
                                    
            for i in range(1, p_range):
                new_x = p_pos[0] + coeff * i
                if 0 <= new_x < width:
                    if self.area[p_pos[1],new_x] in [INT_EMPTY, INT_ITEM_EXTRA, INT_ITEM_RANGE]:
                        for j in [-1,1]:
                            new_y = p_pos[1] + j
                            if 0 <= new_y < height:
                                if self.depth == MAX_DEPTH -1:
                                    nb_ennemies = len([e for e in self.ennemies if e[0] == new_x and e[1] == new_y])
                                else:
                                    nb_ennemies = 0
                                                                        
                                if self.area[new_y,new_x] in [INT_EMPTY, INT_ITEM_EXTRA, INT_ITEM_RANGE] and nb_ennemies == 0:                                                                                                                
                                    return True
                    else:
                        return False
                else:
                    return False
        else:
            for i in range(1, p_range):
                new_y = p_pos[1] + coeff * i
                if 0 <= new_y < height:
                    if self.area[new_y,p_pos[0]] in [INT_EMPTY, INT_ITEM_EXTRA, INT_ITEM_RANGE]:
                        for j in [-1,1]:
                            new_x = p_pos[0] + j
                            if 0 <= new_x < width:
                                if self.depth == MAX_DEPTH -1:
                                    nb_ennemies = len([e for e in self.ennemies if e[0] == new_x and e[1] == new_y])
                                else:
                                    nb_ennemies = 0
                                    
                                if self.area[new_y,new_x] in [INT_EMPTY, INT_ITEM_EXTRA, INT_ITEM_RANGE] and nb_ennemies == 0:
                                    return True
                    else:
                        return False        
                else:
                    return False
        
        if p_is_x_axis:
            new_x = p_pos[0] + (p_range + 1) * coeff
            if 0 <= new_x < width and new_x != self.me[0]:
                if self.depth == MAX_DEPTH -1:
                    nb_ennemies = len([e for e in self.ennemies if e[0] == new_x and e[1] == p_pos[1]])
                else:
                    nb_ennemies = 0
                    
                if self.area[p_pos[1],new_x] in [INT_EMPTY, INT_ITEM_EXTRA, INT_ITEM_RANGE] and nb_ennemies == 0:
                    return True
        else:
            new_y = p_pos[1] + (p_range + 1) * coeff
            if 0 <= new_y < height and new_y != self.me[1]:
                if self.depth == MAX_DEPTH -1:
                    nb_ennemies = len([e for e in self.ennemies if e[0] == p_pos[0] and e[1] == new_y])
                else:
                    nb_ennemies = 0
                    
                if self.area[new_y,p_pos[0]] in [INT_EMPTY, INT_ITEM_EXTRA, INT_ITEM_RANGE] and nb_ennemies == 0:
                    return True
        
        return False    
        
    def action_to_str(self):
        if self.action == ACT_MOVE:
            return 'MOVE'
        else:
            return 'BOMB'

    def solve_bombs(self):
        '''
        Solve the bombs at the current turn
        '''
                    
        #start = time.time()
        
        exploding_bombs = []
                
        for bomb in self.bombs:
            
            timer = max(self.area[bomb[1],bomb[0]]-1, 0)                                    
            self.area[bomb[1],bomb[0]] = timer
            
            if timer == 0:
                
                if bomb[2] == self.my_id: 
                    self.nb_remain_bombs += 1
                 
                #nb_boxes_coeff = 1    
                for pos in self.get_boxes_impacted_by_flame(bomb, bomb[3]):
                    #print('impacted ' + str(pos), file=sys.stderr, flush=True)
                    
                    map_item = pos[2]
                    position = (pos[0], pos[1])
                    
                    if map_item == -1:
                        #And so you're dead ...
                        #print('dead', file=sys.stderr, flush=True)
                        self.is_dead = True
                    elif map_item == INT_BOX_RANGE:
                        self.area[pos[1],pos[0]] = INT_ITEM_RANGE
                        self.nb_boxes -= 1
                        #if bomb[2] == self.my_id: 
                            #self.score += 20 * nb_boxes_coeff 
                            #nb_boxes_coeff += 10
                    elif map_item == INT_BOX_EXTRA:
                        self.area[pos[1],pos[0]] = INT_ITEM_EXTRA
                        self.nb_boxes -= 1
                        #if bomb[2] == self.my_id: 
                            #self.score += 20 * nb_boxes_coeff 
                            #nb_boxes_coeff += 10
                    elif map_item == INT_BOX:
                        self.area[pos[1],pos[0]] = INT_EMPTY
                        self.nb_boxes -= 1
                        #if bomb[2] == self.my_id: 
                            #self.score += 20 * nb_boxes_coeff 
                            #nb_boxes_coeff += 10
                    elif map_item in [INT_ITEM_EXTRA, INT_ITEM_RANGE]:
                        self.area[pos[1],pos[0]] = INT_EMPTY
                                       
                exploding_bombs.append(bomb)    
                        
        is_the_end = False
        
        #print('exploding bombs: ' + str(len(exploding_bombs)), file=sys.stderr)
        for bomb in exploding_bombs: 
            self.area[bomb[1],bomb[0]] = INT_EMPTY
            self.bombs.remove(bomb)
            
        #self.score += self.nb_destroyed_boxes_me * 20 + self.nb_destroyed_boxes_range_me * 23 + self.nb_destroyed_boxes_extra_me * 25
        
    def get_flames(self, pos_bomb, range_bomb, blockInAccount = True, current_area=True):
        '''
        Generator to get all the positions covered by the flames of a bomb
        '''
        cases =  [[-1, 0], [1, 0], [0, -1], [0, 1]]
        
        if current_area:
            area = self.area
        else:
            area = self.next_area
        
        for x_offset, y_offset in cases:
            blocked = False
            
            for j in range(1, range_bomb):
                if blocked:
                    break
                
                new_x = pos_bomb[0] + j*x_offset
                new_y = pos_bomb[1] + j*y_offset
                
                if 0 <= new_x < width and 0 <= new_y < height:
                    map_item = area[new_y,new_x]      
                    if map_item in [INT_EMPTY, INT_FLAME]:
                        yield (new_x, new_y, map_item)
                    else:
                        blocked = True
                        if blockInAccount: yield (new_x, new_y, map_item)                                        
                                                            
        yield (pos_bomb[0], pos_bomb[1], area[pos_bomb[1],pos_bomb[0]])
    
    def synchronize_bombs(self):
        '''
        Set bomb to the minimum of the timer that they depends of
        '''
        
        if len(self.bombs) == 0:
            return
        
        sorted_bombs = sorted(self.bombs, key= lambda b: b[4])
        
        front = deque()
        front.append(sorted_bombs[0])
        
        while len(sorted_bombs) > 0:            
            if len(front) == 0:
                front.append(sorted_bombs[0])
            
            b = front.popleft()
            sorted_bombs.remove(b)            
            
            map_item = self.area[b[1], b[0]]            
            for pos in self.get_boxes_impacted_by_flame(b, b[3]):
                if 0 < pos[2] <= 8:
                    target = [bomb for bomb in sorted_bombs if bomb[0] == pos[0] and bomb[1] == pos[1]]
                    
                    if len(target) != 0:
                        target = target[0]                        
                        if target[4] > map_item:                            
                            self.area[pos[1], pos[0]] = map_item
                        
                        if target not in front:
                            front.append(target)
        
        
        
        '''
        sorted_bombs = sorted(self.bombs, key= lambda b: b[4])
        for i in range(2):
            for b in sorted_bombs:
                for pos in self.get_boxes_impacted_by_flame(b, b[3]):
                    if self.area[b[1], b[0]] < pos[2] <= 8:
                        self.area[pos[1], pos[0]] = self.area[b[1], b[0]]
        '''        
                                                                    
    def solve_next_step(self):
        '''
        Solve the next step to identify which place will be sure death
        To call after solving the actual step
        '''
        
        self.next_area = numpy.copy(self.area)
        
        sorted_bombs = sorted(self.bombs, key= lambda b: self.next_area[b[1],b[0]]) 
        for bomb in sorted_bombs:
            if 1 < self.next_area[bomb[1],bomb[0]] <= 4:   
                self.next_area[bomb[1],bomb[0]] = INT_FLAME
                for pos in self.get_flames(bomb, bomb[3], True, False):
                    if pos[2] != INT_WALL and not (0 < pos[2] <= 8) :
                        self.next_area[pos[1],pos[0]] = INT_FLAME
            elif self.next_area[bomb[1],bomb[0]] > 4:
                break
        
        
    def is_safe(self, p_pos, is_bomb_available, p_close_ennemies, p_same_case_ennemies):
        '''
        Set safety matrix around the character area
        If it is safe for move set 1
        and it is safe for bomb set 2
        Otherwise value is 0
        '''
        
        #TODO: si une bombe est dans le mur du couloir, prendre en compte son explosion pour s'il y a une sortie qu'elle ne 
        #soit pas dans le range ...
        
        me_x = self.me[0]
        me_y = self.me[1]
        
        new_x = p_pos[0]
        new_y = p_pos[1]
        
        move_safe = False
        bomb_safe = False
        
        is_first_iter = (self.depth == MAX_DEPTH -1) 
        
        if is_first_iter:
            ennemies = [e for e in self.ennemies if (e[1] == me_y or e[0] == me_x)]
        else:
            ennemies = []
            
        if 0 <= new_x < width and 0 <= new_y < height:
             map_item = self.area[new_y,new_x]
             map_next_item = self.next_area[new_y,new_x]                 
             
             if new_x > self.me[0]:
                x_axis = True
                is_positive = True
                n_cases = [[1, 0], [0, -1], [0, 1]]
             elif new_x < self.me[0]:
                x_axis = True
                is_positive = False
                n_cases = [[-1, 0], [0, -1], [0, 1]]
             elif new_y > self.me[1]:
                x_axis = False
                is_positive = True
                n_cases = [[1, 0], [-1, 0], [0, 1]]
             elif new_y < self.me[1]:
                x_axis = False
                is_positive = False
                n_cases = [[1, 0], [-1, 0], [0, -1]] 
             else: #same place
                x_axis = False #unused
                is_positive = False #unused
                n_cases = [[1, 0], [-1, 0], [0, 1], [0, -1]]
             
             
             if map_item in [INT_EMPTY, INT_ITEM_EXTRA, INT_ITEM_RANGE]:                                      
                 #Precase: same case as a new bomb (or didn't move from a new bomb), avoid to be blocked if moving
                 #Extend to include ennemies for first turn of the search
                 move_safe = True                 
                 nb_ennemies = len(p_same_case_ennemies)
                     
                 if 1 <= self.area[me_y, me_x] <= 8 or nb_ennemies > 0 :
                    if nb_ennemies == 0:
                        bomb = [b for b in self.bombs if b[0] == me_x and b[1] == me_y][0]                                                                                        
                        b_range = bomb[3]
                    else:
                        b_range = p_same_case_ennemies[0][3]
                        
                    move_safe = self.check_safe_from_pos((me_x, me_y), b_range, x_axis, is_positive)                    
                                
                 #Manage the case where an ennemy can put a bomb to block the player in an alley
                 if move_safe and is_first_iter:
                    
                    for ennemy in p_close_ennemies:
                        distance = abs(ennemy[0] - me_x) + abs(ennemy[1] - me_y)
                        if distance <= 1:                            
                            if new_x != ennemy[0] or new_y != ennemy[1]:
                                #new position is next to the ennemy, check around the new position if we have a way out
                                
                                way_out = False
                                for xn_offset, yn_offset in n_cases:
                                     neighbor_x = new_x + xn_offset
                                     neighbor_y = new_y + yn_offset
                                                                                                          
                                     if 0 <= neighbor_x < width and 0 <= neighbor_y < height and (neighbor_x != ennemy[0] or neighbor_y != ennemy[1]):                                                                                
                                        if self.area[neighbor_y,neighbor_x] in [INT_EMPTY, INT_ITEM_EXTRA, INT_ITEM_RANGE]: 
                                            #Can add the check of another player as a wall
                                            way_out = True
                                            break #safe
                                
                                move_safe = move_safe and way_out                                                                  
                            #else: Same position as the ennemy is safe
                        #else: ennemy is too far: can be managed but will be more costful                    
                                                                                        
                 if move_safe and is_bomb_available:                         
                    #Check if to put a bomb is safe as well                                                         
                    range_bomb = self.bomb_range
                    
                    if self.next_area[me_y, me_x] == INT_FLAME:                        
                        #Do not put a bomb where an explosion is coming soon
                        #print('there is flame at ' + str((me_x, me_y))  + ' you know ?', file=sys.stderr, flush=True)
                        return [move_safe, False]
                    
                    if new_x == me_x and new_y == me_y:
                        for is_x_axis in [False, True]:
                            for is_positive in [False, True]:
                                if self.check_safe_from_pos((new_x, new_y), range_bomb, is_x_axis, is_positive):
                                    bomb_safe = True
                                    break
                            
                            if bomb_safe: break
                    else:                                                                        
                        bomb_safe = self.check_safe_from_pos((new_x, new_y), range_bomb, x_axis, is_positive)                    
                    
                        if bomb_safe:
                            bombs_to_check = []
                            other_bombs = [b for b in self.bombs if b[1] == new_y or b[0] == new_x]
                            for b in bombs:
                                can_kill = False
                                for pos in self.get_boxes_impacted_by_flame((b[0], b[1]), b[3]):
                                    if pos[2] == -1:
                                        can_kill = True
                                        break
                                if can_kill: bombs_to_check.append(b)
                            
                            #Manage the case where an ennemy can put a bomb to block the player in an alley
                            if self.depth == MAX_DEPTH -1:
                                
                                for ennemy in p_close_ennemies:
                                    can_kill = False                        
                                    distance = min(abs(ennemy[0] - me_x) + abs(ennemy[1] - me_y), ennemy[3])
                                    if 0 <= distance <= 1:
                                        can_kill = True
                                    else:
                                        for pos in self.get_boxes_impacted_by_flame((ennemy[0], ennemy[1]), ennemy[3]):
                                            if pos[2] == -1:
                                                can_kill = True
                                                break                                                
                                    if can_kill: bombs_to_check.append(ennemy)                
                            
                            for b in bombs_to_check:
                                distance = min(abs(b[0] - new_x) + abs(b[1] - new_y), b[3])
                                
                                #0 is same place as the other player so it is safe
                                #print('pos: '  + str(p_pos) + ', bomb: ' + str(b) + ', dist: ' + str(distance) + ' check if safe:' + str(self.check_safe_from_pos((b[0], b[1]), distance, x_axis, not is_positive)), file=sys.stderr, flush=True)                    
                                if distance != 0 and bomb_safe:                        
                                    bomb_safe = bomb_safe and self.check_safe_from_pos((b[0], b[1]), distance, x_axis, not is_positive)                                        

                                if not bomb_safe: break
                                
        return [move_safe, bomb_safe]
                                                                                                                                                                                                                                                                                                                                            
    def precompute(self):
        '''
        Precompute data common to all child nodes
        '''
        
        hash_bomb = {}
        for bomb in self.bombs:
            hash_bomb[(bomb[0], bomb[1])] = bomb
        
        self.impacted_by_flames_from_me = []
        for pos in self.get_boxes_impacted_by_flame((self.me[0],self.me[1]), self.bomb_range):            
            if pos[2] in [INT_BOX, INT_BOX_EXTRA, INT_BOX_RANGE]:
                #self.impacted_by_flames_from_me.append(pos)
                
                is_bomb = False
                min_timer = 8
                possible_timer = -1
                for pos2 in self.get_boxes_impacted_by_flame((pos[0],pos[1]), self.bomb_range):
                    if 0 < pos2[2] <= 8:
                        is_bomb = True
                        bomb = hash_bomb[(pos2[0],pos2[1])]
                        if bomb[2] != self.my_id \
                        and (pos[0] < self.me[0] < bomb[0] or pos[0] > self.me[0] > bomb[0] \
                        or pos[1] < self.me[1] < bomb[1] or pos[1] > self.me[1] > bomb[1]):
                            #print('steal the kill !', file=sys.stderr, flush=True)
                            possible_timer = pos2[2]                                       
                        else:
                            min_timer = min(min_timer, pos2[2])
                
                if not is_bomb or (possible_timer != -1 and possible_timer <= min_timer) :                    
                    self.impacted_by_flames_from_me.append(pos)
                                                                        
        self.is_bomb_interesting = self.is_bomb_interesting()            
        
    def apply_movement(self):
        '''
        Apply the movement for the current turn
        '''
        
        potential_boxes = 0
        potential_boxes_range = 0
        potential_boxes_extra = 0        
        nb_range_collected = 0
        nb_bomb_collected = 0
        
        me_x = self.me[0]
        me_y = self.me[1]
        
        #Move and act   
        #self.nb_destroyed_boxes = 0
        predictly_destroyed_boxes = 0
        if self.action == ACT_BOMB:
            #print('set bomb !', file=sys.stderr)
            
            max_timer = 8
            for pos in self.impacted_by_flames_from_me:
                map_item = pos[2]
                if 1 < map_item < max_timer: max_timer = map_item
                elif map_item == INT_BOX:
                    self.nb_destroyed_boxes += 1
                    predictly_destroyed_boxes += 1
                elif map_item == INT_BOX_RANGE:
                    self.nb_destroyed_boxes += 1
                    predictly_destroyed_boxes += 1
                elif map_item == INT_BOX_EXTRA:
                    self.nb_destroyed_boxes += 1
                    predictly_destroyed_boxes += 1
            
            self.area[me_y, me_x] = max_timer
            new_bomb = (me_x, me_y, self.my_id, self.bomb_range, max_timer)
            self.bombs.append(new_bomb)
            
            self.nb_remain_bombs -= 1
        
        self.me = (self.move[0], self.move[1], self.me[2])    
        me_x = self.me[0]
        me_y = self.me[1]        
                                        
        #Check if there is an item in new position
        map_item = self.area[me_y, me_x]        
        if map_item == INT_ITEM_RANGE:
            self.bomb_range += 1
            #self.score += 15
            self.area[me_y, me_x] = INT_EMPTY
        elif map_item == INT_ITEM_EXTRA:
            self.nb_remain_bombs += 1
            self.max_bombs += 1
            #self.score += 25
            self.area[me_y, me_x] = INT_EMPTY
       
        self.score = (min(self.nb_destroyed_boxes, game_max_boxes) / game_max_boxes) * 2 + (min(self.max_bombs,5.0) / 5.0) * 4 + (min(self.bomb_range,8.0) / 8.0)
        #if turn_max_boxes > 0:
        #    self.score += predictly_destroyed_boxes / turn_max_boxes
                      
        self.score = self.score / 7.0
                                
class Node:
    def __init__(self, p_game_state, p_parent):
        self.game_state = p_game_state.clone()
        self.nodes = deque()
        self.parent = p_parent        
    
    def get_solution(self, p_beam_width, p_depth):        
        #max_node, max_score = self.generate_solutions_beam_search(p_beam_width, p_depth)
        nodes = self.generate_solutions_beam_search(p_beam_width, p_depth)
        if len(nodes) > 0:
            sorted_nodes = sorted(nodes, key= lambda node: node.game_state.score, reverse=True)   
            max_node = sorted_nodes[0]
            max_score = max_node.game_state.score
        else:
            max_node = self
            max_score = 0
        
        print('sol depth: ' + str(max_node.game_state.depth) + ', score: ' + str(max_score) + ', boxes: ' + str(max_node.game_state.nb_boxes), file=sys.stderr, flush=True)
        
        if max_node == self:
            node = max_node
            #print('depth: ' + str(node.game_state.depth) + ', action: ' + node.game_state.action_to_str() + ', move: ' + str(node.game_state.move), file=sys.stderr)
        else:
            node = max_node
            #print('depth: ' + str(node.game_state.depth) + ', action: ' + node.game_state.action_to_str() + ', move: ' + str(node.game_state.move) + ', score: ' + str(node.game_state.score), file=sys.stderr)
            while node.parent.parent is not None:
                node = node.parent
                #print('depth: ' + str(node.game_state.depth) + ', action: ' + node.game_state.action_to_str() + ', move: ' + str(node.game_state.move) + ', score: ' + str(node.game_state.score), file=sys.stderr)
        
        return node.game_state.action_to_str(), node.game_state.move, max_score, node.game_state.nb_destroyed_boxes
     
     
    def generate_solutions_beam_search(self, p_beam_width, p_depth): 
        '''
        Generate a tree keeping the p_beam_width more promising nodes at each depth level
        '''
                                
        max_node = self
        max_score = 0
        nb_solved = 0        
        nb_new_nodes = 0
        depth = p_depth -1
        
        #Initialisation
        self.game_state.synchronize_bombs()
        
        #debug_area(self.game_state.area, True)
        
        #self.game_state.solve_bombs()
        self.game_state.solve_next_step()
        
        #print(' ', file=sys.stderr,flush=True)
        #debug_area(self.game_state.next_area, True)
        
        self.game_state.precompute()
        self.game_state.depth = p_depth-1
        
        
        current_nodes = deque()
        current_nodes.append(self)
        sorted_nodes = deque()
        sorted_nodes.append(self)
        
        nb_nodes = 1
        
        while depth >= 0 and nb_nodes > 0 and not self.game_state.is_dead:
            #print('depth: ' + str(depth) + ', nodes: ' + str(nb_nodes), file=sys.stderr, flush=True)
            
            hash_nodes_depth = {}
            index = 0
            
            for current in current_nodes:
                list_nodes = []
                max_score = 0
                
                for move in current.game_state.get_moves():
                    node = Node(current.game_state, current)                        
                    node.game_state.set_action(ACT_MOVE, move, depth)                    
                    node.game_state.apply_movement()
                    
                    if node.game_state.score > max_score: max_score = node.game_state.score
                    list_nodes.append(node)
                    nb_new_nodes += 1
                     
                    if move[2]:                        
                        node = Node(current.game_state, current)            
                        node.game_state.set_action(ACT_BOMB, move, depth)
                        node.game_state.apply_movement()
                        
                        if node.game_state.score > max_score: max_score = node.game_state.score
                        list_nodes.append(node)                                                
                        nb_new_nodes += 1
                                            
                    if (time.clock() - ref_start_time) >= TIMEOUT:
                        #Protect timer to avoid timeout
                        list_nodes.sort(key=lambda x: x.game_state.score, reverse=True)
                        hash_nodes_depth[index] = [max_score, list_nodes]
                        depth = 0
                        break
                
                list_nodes.sort(key=lambda x: x.game_state.score, reverse=True)
                value = []
                value.append(max_score)
                value.append(list_nodes)
                hash_nodes_depth[index] = value
                index += 1
            
            #Get most promising states            
            sorted_nodes = sorted(hash_nodes_depth.items(), key=lambda x: x[1][0], reverse=True)
            
            '''            
            list_nodes_depth = []
            for current in current_nodes:                
                for move in current.game_state.get_moves():                          
                    
                    node = Node(current.game_state, current)                        
                    node.game_state.set_action(ACT_MOVE, move, depth)                    
                    node.game_state.apply_movement()
                    
                    #current.nodes.append(node)
                    list_nodes_depth.append(node)
                    nb_new_nodes += 1
                    
                    if move[2]:                        
                        node = Node(current.game_state, current)            
                        node.game_state.set_action(ACT_BOMB, move, depth)
                        #start = time.clock()
                        node.game_state.apply_movement()
                        #print('time: ' + str(round((time.clock()-start)*1000, 4)), file=sys.stderr, flush=True)     
                        
                        #current.nodes.append(node)
                        list_nodes_depth.append(node)
                        nb_new_nodes += 1                                            
                    
                    if (time.clock() - ref_start_time) >= TIMEOUT:
                        #Protect timer to avoid timeout
                        depth = 0         
                        #print('timeout', file=sys.stderr, flush=True)
                        break
                
            #Get most promising states            
            sorted_nodes = sorted(list_nodes_depth, key= lambda node: node.game_state.score, reverse=True)                                                  
            '''
            
            current_nodes.clear()
            
            i = 0
            nb_sorted_nodes = len(sorted_nodes)
            print('nb cases: ' + str(nb_sorted_nodes), file=sys.stderr, flush=True)
            nb_nodes = 0
            
            while i < nb_new_nodes and nb_nodes <= p_beam_width:
                #for j in range(3):
                
                range_size = min (10, len(sorted_nodes))    
                to_remove = []
                for k in range(range_size):
                      
                    is_alive = True
                    
                    while is_alive and len(sorted_nodes[k][1][1]) > 0:
                        node = sorted_nodes[k][1][1].pop(0)
                        node.game_state.solve_bombs()
                        i += 1
                        
                        if not node.game_state.is_dead and node.game_state.is_new_state(hash_states):
                            is_alive = False
                            node.game_state.precompute()            
                            node.game_state.solve_next_step()
                            current_nodes.append(node)
                            nb_nodes += 1
                        
                        nb_solved += 1
                        
                sorted_nodes = [node for node in sorted_nodes if len(sorted_nodes[k][1][1]) > 0]
                
                if (time.clock() - ref_start_time) >= TIMEOUT:
                    #Protect timer to avoid timeout
                    depth = 0         
                    #print('timeout', file=sys.stderr, flush=True)
                    break
                            
            '''                                
            #Solve map for most promosing states
            i = 0
            nb_sorted_nodes = len(sorted_nodes)
            nb_nodes = 0
            while i < nb_sorted_nodes and nb_nodes <= p_beam_width: 
                                
                sorted_nodes[i].game_state.solve_bombs()                     
                
                #print(str(depth) + ', m: ' + str(sorted_nodes[i].game_state.move) + ', a: ' + sorted_nodes[i].game_state.action_to_str() + ', d? ' + str(sorted_nodes[i].game_state.is_dead) + ', s: ' + str(sorted_nodes[i].game_state.score), file=sys.stderr, flush=True)     
                                
                if not sorted_nodes[i].game_state.is_dead and sorted_nodes[i].game_state.is_new_state(hash_states):                      
                    #print(str(depth) + ', m: ' + str(sorted_nodes[i].game_state.move) + ', a: ' + sorted_nodes[i].game_state.action_to_str() + ', d? ' + str(sorted_nodes[i].game_state.is_dead) + ', s: ' + str(sorted_nodes[i].game_state.score), file=sys.stderr, flush=True)     
                    
                    sorted_nodes[i].game_state.precompute()
                                        
                    sorted_nodes[i].game_state.solve_next_step()
                    current_nodes.append(sorted_nodes[i])
                    nb_nodes += 1                                                              
                
                i += 1    
                nb_solved += 1
                    
                if (time.clock() - ref_start_time) >= TIMEOUT:
                    #Protect timer to avoid timeout
                    depth = 0         
                    #print('timeout', file=sys.stderr, flush=True)
                    break
            '''
            
            depth -= 1
            #print('solved nodes: ' + str(nb_solved) + ', evaluated possibilities: ' + str(nb_new_nodes), file=sys.stderr, flush=True)
                    
        print('nodes: ' + str(nb_nodes) + ', solved nodes: ' + str(nb_solved) + ', possibilities: ' + str(nb_new_nodes), file=sys.stderr, flush=True)        
        #return max_node, max_score 
        return current_nodes
        
    def get_nodes_depth(self, root, p_depth):
        '''
        Get all nodes of a given depth in the tree
        Implementation  of BFS
        '''
        
        front_nodes = deque()
        visited_nodes = deque()
        depth_nodes = deque()
        
        front_nodes.append(root)
        visited_nodes.append(root)
        cur_depth = p_depth
        
        nb_front_nodes = 1 
        
        while nb_front_nodes > 0 and cur_depth >= p_depth:
            cur = front_nodes.popleft()
            nb_front_nodes -= 1
            cur_depth = cur.game_state.depth
            if cur_depth == p_depth :
                depth_nodes.append(cur)
            
            for neighbor in cur.nodes:
                if neighbor not in visited_nodes:
                    visited_nodes.append(neighbor)                
                    front_nodes.append(neighbor)
                    nb_front_nodes += 1
                    
        return depth_nodes
        
def debug_area(p_area, is_int = False):
    for y in range(height):
        line = ''
        for x in range(width):
            line += str(p_area[y][x])
            if is_int:
                line += '  '
        print(line, file=sys.stderr, flush=True)     

# Auto-generated code below aims at helping you parse
# the standard input according to the problem statement.

width, height, my_id = [int(i) for i in input().split()]
size = (height, width)

me = None
ennemies = []

bombs = []
hash_states = {}

game_max_boxes = 0
turn_max_boxes = 0
nb_destroyed_boxes = 0

# game loop
turn = 0
while True:
    #print('Initialisation', file=sys.stderr)
    
    ref_start_time = time.clock()
    
    area = zeros(size, dtype=int32)            
    bombs.clear()
    ennemies.clear()
    turn_max_boxes = 0
    hash_states.clear()    
    
    #Initialisation: get the new state of the map
    row = ''
    for y in range(height):
        row = row + input()

    for i, char in enumerate(list(row)):            
        
        y = int(i/width)
        x = i - (y*width)
        
        if char == MAP_BOX:
            if turn == 0: game_max_boxes += 1
            turn_max_boxes += 1
            area[y,x] = INT_BOX
        elif char == MAP_EXTRA:
            if turn == 0: game_max_boxes += 1
            turn_max_boxes += 1
            area[y,x] = INT_BOX_EXTRA
        elif char == MAP_RANGE:
            if turn == 0: game_max_boxes += 1
            turn_max_boxes += 1
            area[y,x] = INT_BOX_RANGE
        elif char == MAP_WALL:                
            area[y,x] = INT_WALL
    
    
    #Initialisation: get entities positions         
    entities = int(input())
    news = []
    for i in range(entities):
        entity_type, owner, x, y, param_1, param_2 = [int(j) for j in input().split()]
        
        if entity_type == PLAYER and owner == my_id:
            me = (x, y, param_1, param_2)    
        elif entity_type == PLAYER:
            ennemies.append((x, y, param_1, param_2))    
        elif entity_type == BOMB:   
            
            others = [b for b in bombs if b[0] ==x and b[1] == y]
            if len(others)>0:
                kept_my_id = False
                for other in others:
                    bombs.remove(other)
                    if other[2] == my_id:
                        kept_my_id = True
                    
                    area[y,x] = min(area[y,x], param_1)
                    param_2 = max(param_2, other[3])
                
                if kept_my_id:
                    owner = my_id                                    
            else:                                        
                area[y,x] = param_1
                
            bombs.append((x, y, owner, param_2, param_1))
                
        elif entity_type == ITEM:
            if param_1 == ITEM_RANGE:
                area[y,x] = INT_ITEM_RANGE
            elif param_1 == ITEM_BOMB:
                area[y,x] = INT_ITEM_EXTRA
    
    #debug_area(area, True)
    #print(' ', file=sys.stderr, flush=True)
    
    initial_state = GameState()
    
    initial_state.set_attr(area, numpy.copy(area), zeros(size, dtype=int32), my_id, ennemies, 1, me[3], me[2], bombs, turn_max_boxes, nb_destroyed_boxes, [], 0, me, 0)
    
    decision_tree = Node(initial_state, None)
    decision_tree.game_state.set_action(ACT_MOVE, (me[0], me[1]), MAX_DEPTH)
    
    action, new_pos, score, nb_destroyed_boxes = decision_tree.get_solution(BEAM_WIDTH, MAX_DEPTH)
    
    print(action + ' ' + str(new_pos[0]) + ' ' + str(new_pos[1]) + ' ' + str(round(((time.clock() - ref_start_time)*1000),2)), flush=True)
    
    turn += 1