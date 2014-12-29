from collections import OrderedDict
import pygame,random
from pygame.locals import *

#-----PARAMS-----

speed = 10 # how many iterations per second
squares = 16 # size of squares: 8 or 16 or 32 or 64
map_size = 32 # the width and height
RO = 0.2 # the density

class Tile(object):
    def __init__(self, size):
        self.alive_img = "res/alive_" + str(size) + ".png"
        self.dead_img = "res/dead_" + str(size) + ".png"
        self.size = size

class Cell(object):
    def __init__(self, location, alive = False):
        self.next_state = {'N' : 0, 'E' : 0, 'S' : 0, 'W' : 0}
        self.state = Cell.generate_state(alive)
        self.pressed = False
        self.location = location

    def is_empty(self):
        return self.state == {'N' : 0, 'E' : 0, 'S' : 0, 'W' : 0}

    @staticmethod
    def generate_state(alive=False):
        state = {'N' : 0, 'E' : 0, 'S' : 0, 'W' : 0}
        if alive:
            direction = random.choice(['N', 'E', 'S', 'W'])
            state[direction] = 1
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
                    self.map[i].insert(g, Cell(location, random.random() < RO))
                else:
                    self.map[i].insert(g, Cell(location))            

    def draw(self):
        for i in xrange(map_size):
            for g in xrange(map_size):
                cell = self.map[i][g]
                loc = cell.location
                img = alive_img if not cell.is_empty() else dead_img
                screen.blit(img, (loc[0] * tiles.size, loc[1] * tiles.size))

    def calculate_cell(self, cell):
        """Computes the cell.next_state value based on its neighbourhood"""
        m = self.map
        x, y = cell.location
        st = cell.state
        next_st = cell.next_state

        if st['N'] != 0:
            m[x][(y + 1) % map_size].next_state['N'] += 1
        if st['S'] != 0:
            m[x][y - 1].next_state['S'] += 1
        if st['E'] != 0:
            m[(x + 1) % map_size][y].next_state['E'] += 1
        if st['W'] != 0:
            m[x - 1][y].next_state['W'] += 1

    def next_iteration(self):
        for i in xrange(map_size):
            for g in xrange(map_size):
                cell = self.map[i][g]
                self.calculate_cell(cell)

    def update_board(self):
        """Refreshes the board (GUI)"""
        for i in xrange(map_size):
            for g in xrange(map_size):
                cell = self.map[i][g]
                loc = cell.location
                cell.state = cell.next_state
                self.refresh_cell(cell)

    def refresh_cell(self, cell):
        loc = cell.location
        
        img = alive_img if not cell.is_empty() else dead_img
        screen.blit(img, (loc[0] * tiles.size, loc[1] * tiles.size))
        cell.next_state = {'N' : 0, 'E' : 0, 'S' : 0, 'W' : 0}

pygame.init()
tiles = Tile(squares)
screen_size = map_size * tiles.size, map_size * tiles.size
screen = pygame.display.set_mode(screen_size)
clock = pygame.time.Clock()
alive_img = pygame.image.load(tiles.alive_img).convert()
dead_img = pygame.image.load(tiles.dead_img).convert()
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

        if event.type == MOUSEBUTTONUP:
            for i in xrange(map_size):
                for g in xrange(map_size):
                    board.map[i][g].pressed = False

    pressed = pygame.key.get_pressed()
    mouse = pygame.mouse.get_pressed()
    pos = pygame.mouse.get_pos()

    if pressed[K_r]:
        board.map = []
        board.fill(False)
        board.draw()

    if pressed[K_a]:
        board.map = []
        board.fill(True)
        board.draw()

    if run and tp >= 1000/speed :
        tp = 0
        board.next_iteration()
        board.update_board()

    if mouse[0] or mouse[2]:
        for i in xrange(map_size):
            for g in xrange(map_size):
                cell = board.map[i][g]
                x_begin = cell.location[0] * tiles.size
                y_begin = cell.location[1] * tiles.size

                if 0 <= pos[0] - x_begin < tiles.size \
                and 0 <= pos[1] - y_begin < tiles.size \
                and not cell.pressed:
                    is_alive = True if mouse[0] else False
                    cell.state = Cell.generate_state(is_alive)
                    cell.pressed = is_alive
                    board.refresh_cell(cell)

    pygame.display.flip()

pygame.quit()