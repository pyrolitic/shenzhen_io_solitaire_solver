import time

import astar

from .constants import *

def col_pos(ci, si):
    return (table_card_drag_pos[0] + ci*table_offset_x, table_card_drag_pos[1] + si*table_offset_y)

def side_pos(i):
    return (top_card_drag_pos[0] + i*table_offset_x, top_card_drag_pos[1])
    
def dst_pos(i):
    return (top_card_drag_pos[0] + (i+5)*table_offset_x, top_card_drag_pos[1])

def stacks(x, onto):
    return x[0].isnumeric() and onto[0].isnumeric() and \
            onto[1] != x[1] and int(x[0])+1 == int(onto[0])

def advances(x, onto):
    return onto[1] == x[1] and int(x[0]) == int(onto[0])+1

def run_len(col):
    if len(col) == 0:
        return 0
    elif len(col) == 1:
        return 1
    else:
        lst = col[-1]
        if lst[0].isalpha():
            return 1
            
        run = 1
        for i in reversed(range(len(col)-1)):
            v = col[i]
            if v[0].isalpha():
                break
            if v[1] == lst[1]:
                break
            if int(v[0]) != int(lst[0])+1:
                break
            lst = v
            run += 1
        return run

class State(object):
    best_rem = 9999
    timeout = 0

    def __init__(self, side, rose, dst, cols, dragon, from_state, move):
        #sanity
        assert len(side) == 3
        assert len(dst) == 3
        for i in range(3):
            assert dst[i] not in DRAGONS
            assert dst[i] == 'BL' or dst[i][0].isnumeric()
        dstsz = 0
        for sym in dst:
            if sym != "BL":
                dstsz += int(sym[0])
        drgsz = sum(map(int, dragon))
        sidesz = 0
        for sym in side:
            if sym != 'XX' and sym != 'BL':
                sidesz += 1
        assert drgsz == len([sym for sym in side if sym == 'XX'])
        rsz = 1 if rose == 'RO' else 0
        assert sum(len(col) for col in cols) + dstsz + drgsz*4 + sidesz + rsz == 8*5

        self.side = tuple(side)
        self.rose = rose
        self.dst = tuple(dst)
        self.cols = tuple(tuple(col) for col in cols)
        self.dragon = tuple(dragon)
        #not considered for __eq__ and __hash__
        self.prev = from_state
        self.move = move

    def __eq__(self, other):
        return (self.side, self.rose, self.dst, self.dst, self.cols, self.dragon) == (other.side, other.rose, other.dst, other.dst, other.cols, other.dragon)

    def __hash__(self):
        return hash((self.side, self.rose, self.dst, self.dst, self.cols, self.dragon))

    def remaining(self):
        rem = 0
        if self.rose == 'BL':
            rem += 1
        for d in self.dragon:
            if not d:
                rem += 4
        for sym in self.dst:
            if sym == 'BL':
                rem += 9
            else:
                rem += 9 - int(sym[0])
        for col in self.cols:
            lst = None
            for sym in col:
                if lst is not None:
                    if not stacks(sym, lst):
                        rem += 1
                lst = sym
                
        if rem < State.best_rem:
            State.best_rem = rem
            print("new best rem", rem)
        return rem

    def neighbours(self):
        neigh = []

        if time.time() > State.timeout:
            raise TimeoutError

        if self.rose == 'BL':
            # rose automatic move
            for ci in range(num_cols):
                col = self.cols[ci]
                if len(col) > 0:
                    if col[-1] == "RO":
                        ncols = tuple(col[:-1] if i == ci else col[:] for i, col in enumerate(self.cols))
                        return [State(self.side, 'RO', self.dst, ncols, self.dragon, self, None)]
        
        #automatic number card move
        def canStackOnto(v):
            for di in range(3):
                d = self.dst[di]
                if d != 'BL':
                    #see if there's any card remaining that can possibly be stacked _onto_ v
                    if d[1] != v[1] and int(v[0]) > int(d[0])-1:
                        return True
            return False

        for ci in range(num_cols):
            col = self.cols[ci]
            if len(col) > 0:
                v = col[-1]
                if v[0] == '1':
                    # see if it can be moved to dest pile
                    for di in range(3):
                        if self.dst[di] == 'BL':
                            #stack.append((col_pos(ci), dst_pos(di)))
                            ncols = tuple(col[:-1] if i == ci else col[:] for i, col in enumerate(self.cols))
                            ndst = tuple(col[-1] if i == di else self.dst[i] for i in range(3))
                            return [State(self.side, self.rose, ndst, ncols, self.dragon, self, None)] # can't avoid this move
                
                if v[0].isnumeric() and not canStackOnto(v):
                    for di in range(3):
                        od = self.dst[di]
                        if advances(v, od):	
                            ncols = tuple(col[:-1] if i == ci else col[:] for i, col in enumerate(self.cols))
                            ndst = tuple(v if i == di else self.dst[i] for i in range(3))
                            return [State(self.side, self.rose, ndst, ncols, self.dragon, self, None)] # can't avoid this move

        for si in range(3):
            v = self.side[si]
            if v[0].isnumeric() and not canStackOnto(v):
                for di in range(3):
                    od = self.dst[di]
                    if advances(v, od):	
                        nside = tuple('BL' if i == si else self.side[i] for i in range(3))
                        ndst = tuple(v if i == di else self.dst[i] for i in range(3))
                        return [State(nside, self.rose, ndst, self.cols, self.dragon, self, None)] # can't avoid this move

        #stack dragons
        rev_obs = [0, 0, 0]
        for i in range(3):
            if self.side[i] in DRAGONS:
                rev_obs[DRAGONS.index(self.side[i])] += 1
        
        for ci in range(num_cols):
            col = self.cols[ci]
            if len(col) > 0 and col[-1] in DRAGONS:
                rev_obs[DRAGONS.index(col[-1])] += 1
        
        for i, rev in enumerate(rev_obs):
            o = DRAGONS[i]
            if rev == 4:
                assert not self.dragon[i]
                
                #find place where stack will appear
                pl = -1
                for si in range(3):
                    if self.side[si] == 'BL':
                        pl = si
                    if self.side[si] == o:
                        pl = si
                        break
                
                if pl >= 0:
                    nside = tuple('XX' if i == pl else 'BL' if sym == o else sym for i, sym in enumerate(self.side))
                    ncols = tuple(col[:-1] if len(col) > 0 and col[-1] == o else col for col in self.cols)
                    ndrag = tuple(True if _i == i else self.dragon[_i] for _i in range(3))
                    move = ((dragon_x, dragon_y[i]), None)
                    neigh.append(State(nside, self.rose, self.dst, ncols, ndrag, self, move))
        
        #deepst stack to elsewhere
        for ci in range(num_cols):
            col = self.cols[ci]
            if len(col) > 0:
                if col[-1] == "RO":
                    assert False #see above
                    
                if col[-1][0].isnumeric():
                    # see if it can be moved to dest pile
                    for di in range(3):
                        od = self.dst[di]
                        if advances(col[-1], od):
                            ncols = tuple(col[:-1] if i == ci else col[:] for i, col in enumerate(self.cols))
                            ndst = tuple(col[-1] if i == di else self.dst[i] for i in range(3))
                            move = (col_pos(ci, len(col)-1), dst_pos(di))
                            neigh.append(State(self.side, self.rose, ndst, ncols, self.dragon, self, move))
                            break #can't stack anywhere else
                
                mrl = run_len(col)
                for rl in reversed(range(1, mrl+1)):
                    v = col[-rl]
                    for cc in range(num_cols):
                        if cc == ci:
                            continue
                        #don't move entire stack to empty space
                        #if (len(self.cols[cc]) == 0 and rl < mrl) \
                        #	or 
                        if len(self.cols[cc]) == 0 or stacks(v, self.cols[cc][-1]):
                            ncols = [col[:] for col in self.cols]
                            ncols[cc] += col[-rl:]
                            ncols[ci] = col[:-rl]
                            move = (col_pos(ci, len(col)-rl), col_pos(cc, len(self.cols[cc])))
                            neigh.append(State(self.side, self.rose, self.dst, ncols, self.dragon, self, move))
        
        #side to stack or dest
        ff = -1 #first free
        for si in range(3):
            v = self.side[si]
            if v == 'BL' and ff == -1:
                ff = si
            
            if v != 'XX' and v != 'BL':
                if v[0].isnumeric():
                    for di in range(3):
                        od = self.dst[di]
                        if advances(v, od):
                            move = (side_pos(si), dst_pos(di))
                            nside = tuple('BL' if i == si else self.side[i] for i in range(3))
                            ndst = tuple(v if i == di else self.dst[i] for i in range(3))
                            neigh.append(State(nside, self.rose, ndst, self.cols, self.dragon, self, move))
                            break #can't stack anywhere else

                for ci in range(num_cols):
                    col = self.cols[ci]
                    if len(col) == 0 or stacks(v, col[-1]):
                        move = (side_pos(si), col_pos(ci, len(col)))
                        nside = tuple('BL' if i == si else self.side[i] for i in range(3))
                        ncols = tuple(col + (v,) if i == ci else col for i, col in enumerate(self.cols))
                        neigh.append(State(nside, self.rose, self.dst, ncols, self.dragon, self, move))

        #bottom of stack to side
        if ff >= 0:
            for ci in range(num_cols):
                col = self.cols[ci]
                if len(col) > 0:
                    ncols = tuple(col[:-1] if i == ci else col[:] for i, col in enumerate(self.cols))
                    nside = tuple(col[-1] if i == ff else self.side[i] for i in range(3))
                    move = ((col_pos(ci, len(col)-1), side_pos(ff)))
                    neigh.append(State(nside, self.rose, self.dst, ncols, self.dragon, self, move))

        return neigh
        #ret = []
        #for n in neigh:
        #	if n not in State.found_states:
        #		ret.append(n)
        #return ret

    def gen_move(self, next):
        #rose
        if self.rose == 'BL' and next.rose == 'RO':
            return None #automatic move
        #stack 1x to dest
        for i in range(3):
            if self.dst[i] == 'BL' and next.dst[i][0] == '1':
                return None #automatic move
        #dragon button
        for i in range(3):
            if not self.dragon[i] and next.dragon[i]:
                return ((dragon_x, dragon_y[i]), None)
        #stack to side or side to stack
        for i in range(3):
            if self.side[i] == 'BL' and next.side[i] != 'BL':
                v = next.side[i]
                for ci in range(num_cols):
                    if len(self.cols[ci]) > 0 and self.cols[ci][-1] == v:
                        return (col_pos(ci, len(self.cols[ci])-1), side_pos(i))

            if self.side[i] != 'BL' and next.side[i] == 'BL':
                v = self.side[i]
                for ci in range(num_cols):
                    if len(next.cols[ci]) > 0 and next.cols[ci][-1] == v:
                        return (side_pos(i), col_pos(ci, len(next.cols[ci])-1))
        #stack or side to dest
        for i in range(3):
            if self.dst[i] != 'BL' and advances(next.dst[i], self.dst[i]):
                v = next.dst[i]
                for ci in range(num_cols):
                    if len(self.cols[ci]) > 0 and self.cols[ci][-1] == v:
                        return (col_pos(ci, len(self.cols[ci])-1), dst_pos(i))
                for si in range(3):
                    if self.side[si] == v:
                        return (side_pos(si), dst_pos(i))
        #stack to stack
        for i in range(num_cols):
            dsl = len(self.cols[i])
            dnl = len(next.cols[i])
            if dsl < dnl:
                for j in range(num_cols):
                    if j != i:
                        ssl = len(self.cols[j])
                        snl = len(next.cols[j])
                        if ssl > snl:
                            assert dsl - dnl == snl - ssl
                            return (col_pos(j, snl), col_pos(i, dsl))
        assert False #move not covered

class Solver(astar.AStar):
    def __init__(self):
        pass

    def heuristic_cost_estimate(self, state, goal):
        return state.remaining()

    def distance_between(self, state, next):
        return 1

    def is_goal_reached(self, current, goal):
        return current.remaining() == 0

    def neighbors(self, node):
        return node.neighbours()

def solve_game(side, rose, dst, cols, dragons):
    State.timeout = time.time() + 100
    State.best_rem = 9999

    state = State(side, rose, dst, cols, dragons, None, None)
    print(hash(state))

    ret = []
    lst = None
    for nxt in Solver().astar(state, None):
        if lst is not None:
            #mv = lst.gen_move(nxt)
            if nxt.prev is lst:
                #neighbour generator created the move, this is ideal
                mv = nxt.move
            else:
                #recreate the move based on state difference, this might be buggier
                mv = lst.gen_move(nxt)
            ret.append(mv)
        lst = nxt

    return ret