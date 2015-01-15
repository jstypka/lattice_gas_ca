from __future__ import division
import random

import pygame
from pygame.locals import *
import matplotlib.pyplot as plt
import numpy

# -----PARAMS-----

speed = 10  # how many iterations per second
squares = 25  # size of squares
map_size = 32  # the width and height
margin = 1
show_energy = False
font_size = 15
plot = False
children = True

DENSITY = 0.2  # RO
ENERGY_INIT = 20  # N
ENERGY_GAIN = 40  # M
MAX_ENERGY = 200
ENERGY_SPLIT = 'good_or_bad'  # 'equal' | 'winner_takes_it_all' | 'good_or_bad'
ENERGY_CHILD = 120
GOOD_TO_BAD_RATIO = 0.8

MAX_COLOUR = 220
MIN_COLOUR = 20

DEAD_COLOUR = (30, 30, 30)
GOOD_COLOUR = (0, 0, 1)
BAD_COLOUR = (1, 0, 0)

alive_colours = {
    "bad": BAD_COLOUR,
    "good": GOOD_COLOUR
}

alive_states = [False, True, True]
behaviours = ["", "good", "bad"]


class Particle(object):
    def __init__(self, ptype='random', energy=None):
        diff = 0.1 * ENERGY_INIT
        self.energy = energy if energy else int(random.uniform(ENERGY_INIT - diff, ENERGY_INIT + diff))
        if ptype == 'random':
            self.ptype = 'good' if random.random() < GOOD_TO_BAD_RATIO else 'bad'
        else:
            self.ptype = ptype

    def decrease_energy(self):
        self.energy -= 1

    def calculate_colour(self):
        colour_multiplier = max(MIN_COLOUR, self.energy / MAX_ENERGY * MAX_COLOUR)
        added_colour = tuple(n * colour_multiplier for n in alive_colours[self.ptype])
        return (sum(t) for t in zip(DEAD_COLOUR, added_colour))

    def increase_energy(self, energy):
        self.energy = min(MAX_ENERGY, self.energy + energy)


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
            return (d['N'] == 0 and d['S'] == 0) or (d['E'] == 0 and d['W'] == 0)
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
        p1.increase_energy(ENERGY_GAIN // 2)
        p2.increase_energy(ENERGY_GAIN // 2)

    @staticmethod
    def winner_takes_it_all(p1, p2):
        if p1.energy > p2.energy:
            p1.increase_energy(ENERGY_GAIN)
        elif p2.energy > p1.energy:
            p2.increase_energy(ENERGY_GAIN)
        else:
            random.choice((p1, p2)).increase_energy(ENERGY_GAIN)
            # p1.increase_energy(ENERGY_GAIN // 2)
            # p2.increase_energy(ENERGY_GAIN // 2)

    @staticmethod
    def bad_collision(p1, p2):
        if p1.ptype == "good":
            p2.increase_energy(ENERGY_GAIN)
        elif p2.ptype == "good":
            p1.increase_energy(ENERGY_GAIN)
        else:
            Board.winner_takes_it_all(p1, p2)

    @staticmethod
    def collide_particles(p1, p2):
        if ENERGY_SPLIT == 'equal':
            Board.good_collision(p1, p2)

        elif ENERGY_SPLIT == 'winner_takes_it_all':
            Board.winner_takes_it_all(p1, p2)

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


        if children:
            self.create_children(st)

        if st['N'] != 0:
            m[x][(y + 1) % map_size].next_state['N'] = st['N']
        if st['S'] != 0:
            m[x][y - 1].next_state['S'] = st['S']
        if st['E'] != 0:
            m[(x + 1) % map_size][y].next_state['E'] = st['E']
        if st['W'] != 0:
            m[x - 1][y].next_state['W'] = st['W']


    def create_children(self, state):
        parents_dict = {}
        found_child = False
        available_positions = []
        for key in state:
            if state[key] != 0:
                parents_dict[(state[key].energy, key)] = state[key].ptype
            else:
                available_positions.append(key)

        for key in sorted(parents_dict.keys()):
            if not len(available_positions):
                break
            else:
                if key[0] >= ENERGY_CHILD:
                    pos = random.choice(available_positions)
                    state[pos] = Particle(parents_dict[key], key[0]//2)
                    state[key[1]].energy = key[0]//2
                    available_positions.remove(pos)
                    found_child = True
                else:
                    break

        return found_child

    def next_iteration(self):
        for i in xrange(map_size):
            for g in xrange(map_size):
                cell = self.map[i][g]
                cell.decrease_energy()
                self.calculate_cell(cell)

    def update_board(self):
        """Refreshes the board (GUI)"""
        total_energy = num_good = num_bad = 0
        for i in xrange(map_size):
            for g in xrange(map_size):
                cell = self.map[i][g]
                cell.state = cell.next_state
                energy_now, good_now, bad_now = self.refresh_cell(cell)
                total_energy += energy_now
                num_good += good_now
                num_bad += bad_now
                cell.next_state = {'N': 0, 'E': 0, 'S': 0, 'W': 0}
        return total_energy, num_good + num_bad, num_good, num_bad

    @staticmethod
    def refresh_cell(ref_cell):
        loc = ref_cell.location
        drawn_text = ""
        energy = 0
        num_good = 0
        num_bad = 0
        if not ref_cell.is_empty():
            particles_colours = [part.calculate_colour() for el, part in ref_cell.state.items() if part]
            colour = tuple(sum(t) / len(particles_colours) for t in zip(*particles_colours))
            energy = sum([part.energy for _, part in ref_cell.state.items() if part])
            num_good = len([part for _, part in ref_cell.state.items() if part and part.ptype == "good"])
            num_bad = len(particles_colours) - num_good
            if show_energy and len(particles_colours) == 1:
                drawn_text = [part for _, part in ref_cell.state.items() if part][0].energy
        else:
            colour = DEAD_COLOUR
        # colour = (50, 80, 200) if not cell.is_empty() else (30, 30, 30)
        pygame.draw.rect(screen, colour, (
            loc[0] * (margin + tiles.size) + margin, loc[1] * (margin + tiles.size) + margin, tiles.size, tiles.size))
        if show_energy and drawn_text:
            label = label_font.render("{0:d}".format(drawn_text), 1, (255, 255, 255))
            screen.blit(label,
                        (loc[0] * (margin + tiles.size) + 2 * margin, loc[1] * (margin + tiles.size) + 2 * margin))
        return energy, num_good, num_bad

    def redraw(self, fill=True):
        self.map = []
        self.fill(fill)
        self.draw()


def update_line(updated_line, updated_axes, x_data, y_data):
    updated_line.set_xdata(numpy.append(updated_line.get_xdata(), x_data))
    updated_line.set_ydata(numpy.append(updated_line.get_ydata(), y_data))
    if plot:
        updated_axes.relim()
        updated_axes.autoscale_view(True, True, True)
        plt.draw()


def update_game(board, turn):
    board.next_iteration()
    energy, num_all, num_good, num_bad = board.update_board()
    if fig:
        update_line(line, axes, turn, energy)
        update_line(line2, axes2, turn, num_all)
        update_line(line3, axes3, turn, num_good)
        update_line(line4, axes4, turn, num_bad)


if __name__ == "__main__":

    pygame.init()

    label_font = pygame.font.SysFont("Helvetica", font_size)
    fig = None

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
    turns = 0

    while not done:
        milliseconds = clock.tick(60)
        seconds = milliseconds / 1000.0
        tp += milliseconds

        for event in pygame.event.get():
            if event.type == QUIT:
                done = True
            elif event.type == KEYDOWN:
                if event.key == K_SPACE:
                    run = not run
                elif event.key == K_e:
                    show_energy = not show_energy
                elif event.key == K_q:
                    run = False
                    update_game(board, turns)
                    turns += 1
                elif event.key == K_r:
                    board.redraw(False)
                    if fig:
                        axes.clear()
                        line, = axes.plot([], [])
                        axes2.clear()
                        line2, = axes2.plot([], [])
                        axes3.clear()
                        line3, = axes3.plot([], [])
                        axes4.clear()
                        line4, = axes4.plot([], [])
                elif event.key == K_a:
                    board.redraw(True)
                elif event.key == K_p:
                    if not fig:
                        plt.ion()
                        fig = plt.figure()
                        axes = fig.add_subplot(2, 2, 1)
                        axes2 = fig.add_subplot(2, 2, 2)
                        axes3 = fig.add_subplot(2, 2, 3)
                        axes4 = fig.add_subplot(2, 2, 4)

                        axes.set_autoscale_on(True)
                        axes.autoscale_view(True, True, True)
                        axes.set_xlabel("turns")
                        axes.set_ylabel("energy")
                        line, = axes.plot([], [])

                        axes2.set_autoscale_on(True)
                        axes2.autoscale_view(True, True, True)
                        axes2.set_xlabel("turns")
                        axes2.set_ylabel("number of all")
                        line2, = axes2.plot([], [])

                        axes3.set_autoscale_on(True)
                        axes3.autoscale_view(True, True, True)
                        axes3.set_xlabel("turns")
                        axes3.set_ylabel("number of good")
                        line3, = axes3.plot([], [])

                        axes4.set_autoscale_on(True)
                        axes4.autoscale_view(True, True, True)
                        axes4.set_xlabel("turns")
                        axes4.set_ylabel("number of bad")
                        line4, = axes4.plot([], [])
                    plot = not plot
            elif event.type == MOUSEBUTTONDOWN:
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

        if run and tp >= 1000 / speed:
            tp = 0
            update_game(board, turns)
            turns += 1

        pygame.display.flip()

    pygame.quit()