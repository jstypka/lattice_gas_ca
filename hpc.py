from __future__ import division
from collections import OrderedDict
import pygame, random
from pygame.locals import *

# -----PARAMS-----

speed = 10  # how many iterations per second
squares = 16  # size of squares: 8 or 16 or 32 or 64
map_size = 32  # the width and height
margin = 1

DENSITY = 0.2  # RO
ENERGY_INIT = 20  # N
ENERGY_GAIN = 10  # M
ENERGY_SPLIT = 'good_or_bad'  # 'equal' | 'winner_takes_it_all' | 'good_or_bad'
GOOD_TO_BAD_RATIO = 0.8

DEAD_COLOUR = (30, 30, 30)
GOOD_COLOUR = (10, 20, 40)
BAD_COLOUR = (40, 20, 10)

alive_colours = {
    "bad": BAD_COLOUR,
    "good": GOOD_COLOUR
}
alive_states = [False, True, True]
behaviours = ["", "good", "bad"]


class Particle(object):
    def __init__(self, ptype='random'):
        diff = 0.1 * ENERGY_INIT
        self.energy = random.uniform(ENERGY_INIT - diff, ENERGY_INIT + diff)
        if ptype == 'random':
            self.ptype = 'good' if random.random() < GOOD_TO_BAD_RATIO else 'bad'
        else:
            self.ptype = ptype

    def decrease_energy(self):
        self.energy -= 1


class Tile(object):
    def __init__(self, size):
        self.size = size


class Cell(object):
    def __init__(self, location, alive=False):
        self.next_state = {'N': 0, 'E': 0, 'S': 0, 'W': 0}
        self.state = Cell.generate_state(alive)
        self.pressed_count = 0
        self.location = location

    def is_empty(self):
        return self.state == {'N': 0, 'E': 0, 'S': 0, 'W': 0}

    def is_collision(self):
        d = self.state
        non_zeros = len([x for x in d.values() if x != 0])
        if non_zeros == 2:
            """not doing a xor, because 1 might be replaced
            by something else in the future (maybe a class)"""
            return (d['N'] == 0 and d['S'] == 0) \
                   or (d['E'] == 0 and d['W'] == 0)
        return False

    def decrease_energy(self):
        s = self.state
        for direction, part in s.items():
            if part != 0:
                if part.energy <= 0:
                    s[direction] = 0
                else:
                    part.decrease_energy()


    @staticmethod
    def generate_state(alive=False, behaviour=None):
        behaviour = "random" if not behaviour else behaviour
        state = {'N': 0, 'E': 0, 'S': 0, 'W': 0}
        if alive:
            direction = random.choice(['N', 'E', 'S', 'W'])
            state[direction] = Particle(behaviour)
        return state


class Board(object):
    def __init__(self):
        self.map = []

    def fill(self, ran):
        for i in xrange(map_size):
            self.map.append([])
            for g in xrange(map_size):
                location = (i, g)
                if ran == True:
                    self.map[i].insert(g, Cell(location,
                                               random.random() < DENSITY))
                else:
                    self.map[i].insert(g, Cell(location))

    def draw(self):
        for i in xrange(map_size):
            for g in xrange(map_size):
                cell = self.map[i][g]
                self.refresh_cell(cell)

    @staticmethod
    def good_collision(p1, p2):
        p1.energy += ENERGY_GAIN / 2
        p2.energy += ENERGY_GAIN / 2

    @staticmethod
    def bad_collision(p1, p2):
        if p1.energy > p2.energy:
            p1.energy += ENERGY_GAIN
        else:
            p2.energy += ENERGY_GAIN

    @staticmethod
    def collide_particles(p1, p2):
        if ENERGY_SPLIT == 'equal':
            Board.good_collision(p1, p2)

        elif ENERGY_SPLIT == 'winner_takes_it_all':
            Board.bad_collision(p1, p2)

        elif ENERGY_SPLIT == 'good_or_bad':
            if p1.ptype == p2.ptype == 'good':
                Board.good_collision(p1, p2)
            else:
                Board.bad_collision(p1, p2)

        return p1, p2

    def calculate_cell(self, cell):
        """Computes the cell.next_state value based on its neighbourhood"""
        m = self.map
        x, y = cell.location
        st = cell.state

        if cell.is_collision():
            if st['N'] == 0:  # EW collision
                if random.random() < 0.5:
                    st['W'], st['E'] = st['E'], st['W']

                st['N'], st['S'] = self.collide_particles(st['W'], st['E'])
                st['W'], st['E'] = 0, 0
            else:  # NS collision
                if random.random() < 0.5:
                    st['N'], st['S'] = st['S'], st['N']

                st['W'], st['E'] = self.collide_particles(st['N'], st['S'])
                st['N'], st['S'] = 0, 0

        if st['N'] != 0:
            m[x][(y + 1) % map_size].next_state['N'] = st['N']
        if st['S'] != 0:
            m[x][y - 1].next_state['S'] = st['S']
        if st['E'] != 0:
            m[(x + 1) % map_size][y].next_state['E'] = st['E']
        if st['W'] != 0:
            m[x - 1][y].next_state['W'] = st['W']

    def next_iteration(self):
        for i in xrange(map_size):
            for g in xrange(map_size):
                cell = self.map[i][g]
                cell.decrease_energy()
                self.calculate_cell(cell)

    def update_board(self):
        """Refreshes the board (GUI)"""
        for i in xrange(map_size):
            for g in xrange(map_size):
                cell = self.map[i][g]
                cell.state = cell.next_state
                self.refresh_cell(cell)
                cell.next_state = {'N': 0, 'E': 0, 'S': 0, 'W': 0}


    def refresh_cell(self, cell):
        loc = cell.location
        if not cell.is_empty():
            particles_colours = [alive_colours[part.ptype] for el, part in cell.state.items() if part]
            colour = tuple(sum(t) / len(particles_colours) for t in zip(*particles_colours))
        else:
            colour = DEAD_COLOUR
        # colour = (50, 80, 200) if not cell.is_empty() else (30, 30, 30)
        pygame.draw.rect(screen, colour, (
            loc[0] * (margin + tiles.size) + margin, loc[1] * (margin + tiles.size) + margin, tiles.size, tiles.size))


pygame.init()
tiles = Tile(squares)
screen_size = map_size * tiles.size, map_size * tiles.size
screen = pygame.display.set_mode(screen_size)
clock = pygame.time.Clock()
done = False

board = Board()
board.fill(False)
board.draw()
tp = 0
run = False

while not done:
    milliseconds = clock.tick(60)
    seconds = milliseconds / 1000.0
    tp += milliseconds

    for event in pygame.event.get():
        if event.type == QUIT:
            done = True

        if event.type == KEYDOWN:
            if event.key == K_SPACE:
                run = not run

            if event.key == K_q:
                run = False
                board.next_iteration()
                board.update_board()


            def redraw_board(fill=True):
                board.map = []
                board.fill(fill)
                board.draw()

            if event.key == K_r:
                redraw_board(False)

            if event.key == K_a:
                redraw_board((True))

        # if event.type == MOUSEBUTTONUP:
        # for i in xrange(map_size):
        #         for g in xrange(map_size):
        #             board.map[i][g].pressed = 0
        if event.type == MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            (button1, button2, button3) = pygame.mouse.get_pressed()
            for i in xrange(map_size):
                for g in xrange(map_size):
                    cell = board.map[i][g]
                    x_begin = cell.location[0] * (tiles.size + margin)
                    y_begin = cell.location[1] * (tiles.size + margin)

                    if 0 <= pos[0] - x_begin < tiles.size and 0 <= pos[1] - y_begin < tiles.size:

                        if button1:
                            cell.pressed_count = (cell.pressed_count + 1) % len(alive_states)
                        else:
                            cell.pressed_count = (cell.pressed_count - 1) % len(alive_states)

                        cell.state = Cell.generate_state(alive_states[cell.pressed_count],
                                                         behaviours[cell.pressed_count])

                        board.refresh_cell(cell)
                        cell.next_state = {'N': 0, 'E': 0, 'S': 0, 'W': 0}




    # pressed = pygame.key.get_pressed()
    # mouse = pygame.mouse.get_pressed()
    # event = pygame.event.get()

    if run and tp >= 1000 / speed:
        tp = 0
        board.next_iteration()
        board.update_board()

    # if mouse[0] or mouse[2]:
    # for i in xrange(map_size):
    #         for g in xrange(map_size):
    #             cell = board.map[i][g]
    #             x_begin = cell.location[0] * (tiles.size + margin)
    #             y_begin = cell.location[1] * (tiles.size + margin)
    #
    #             if 0 <= pos[0] - x_begin < tiles.size and 0 <= pos[1] - y_begin < tiles.size:
    #
    #                 if mouse[0]:
    #                     cell.pressed_count = (cell.pressed_count + 1) % len(alive_states)
    #                 else:
    #                     cell.pressed_count = (cell.pressed_count - 1) % len(alive_states)
    #
    #                 cell.state = Cell.generate_state(alive_states[cell.pressed_count], behaviours[cell.pressed_count])
    #
    #                 board.refresh_cell(cell)
    #                 cell.next_state = {'N': 0, 'E': 0, 'S': 0, 'W': 0}

    pygame.display.flip()

pygame.quit()