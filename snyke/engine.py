import dataclasses

from dataclasses import dataclass
from enum import Enum

import random
import time
from typing import Mapping, List, Tuple, Optional, overload


'''Coordinate
'''
@dataclass
class Coord:
    col: int
    row: int


''' Cell
'''
Cell = Enum('cell', ['EMPTY', 'SNAKE', 'FOOD'])


''' Dimension
'''
@dataclass
class Dimension:
    width: int
    height: int


''' State
'''
@dataclass
class State:

    # The points collected by each snake
    points: List[int]

    # The indices of snakes that have collided a wall or a snake (including itself)
    collisions: List[int]

    # Is the game over
    is_game_over: bool


''' Direction
'''
Direction = Enum('Direction', ['UP', 'DOWN', 'RIGHT', 'LEFT'])


class AbstractView:

    def __init__(self):
        super().__init__()

    @overload
    def draw(self, board: List[List[Cell]], state: State):
        raise NotImplemented


class Food:

    def __init__(self, coord: Coord):
        self._coord = coord

    @property
    def coord(self):
        return self._coord


class Snake:

    def __init__(self, head: Coord, length: int, direction: Direction,):
        super().__init__()
        self._cells = self._create(head, length, direction)
        self._direction = direction
        self._next_direction = direction
        self._points = 0

    def _create(self, head: Coord, length: int, direction: Direction) -> List[Coord]:
        col_offset = 0
        row_offset = 0

        if direction is Direction.UP:
            row_offset = 1
        elif direction is Direction.DOWN:
            row_offset = -1
        elif direction is Direction.LEFT:
            col_offset = -1
        else :
            col_offset = 1

        return [Coord(head.col + i * col_offset, head.row + i * row_offset) for i in range(length)]

    def grow(self, n: int):
        tail = self._cells[-1]
        for i in range(n):
            self._cells.append(dataclasses.replace(tail))

        self._points += n

    @property
    def head(self):
        return self._cells[0]

    @property
    def points(self):
        return self._points

    @property
    def direction(self) -> Direction:
        return self._direction

    @direction.setter
    def direction(self, d: Direction):
        if d is Direction.UP and self._direction is not Direction.DOWN:
            self._next_direction = d
            return

        if d is Direction.DOWN and self._direction is not Direction.UP:
            self._next_direction = d
            return

        if d is Direction.RIGHT and self._direction is not Direction.LEFT:
            self._next_direction = d
            return

        if d is Direction.LEFT and self._direction is not Direction.RIGHT:
            self._next_direction = d
            return

    def contains(self, c: Coord, disregard_head: bool=False) -> bool:
        if disregard_head:
            return c in self._cells[1:]
        
        return c in self._cells

    def collides_with_boundary(self, boundary: Dimension) -> bool:
        return not ((0 < self.head.row < boundary.height) and  \
                    (0 < self.head.col < boundary.width))

    def collides_with_snake(self, snake: 'Snake') -> bool:
        if self is snake:
            return self.head in self._cells[1:]

        return self.head in snake._cells

    def collides_with_food(self, food: Food) -> bool:
        return self.head == food.coord

    def move(self):
        head = self._cells[0]
        new_head: Coord

        self._direction = self._next_direction

        if self._direction is Direction.UP:
            new_head = Coord(head.col, head.row-1)
        elif self._direction is Direction.DOWN:
            new_head = Coord(head.col, head.row+1)
        elif self._direction is Direction.LEFT:
            new_head = Coord(head.col-1, head.row)
        else:
            new_head = Coord(head.col+1, head.row)

        self._cells = [new_head, *self._cells[:-1]]

        self._points += 1


class Engine:

    def __init__(self, view: AbstractView, dim: Dimension, nsnakes: int, snake_len: int, food_interval: int):
        super().__init__()

        random.seed(time.time())

        ''' View things '''
        self._view = view
        self._dim = dim

        ''' Game things '''
        self._board: List[List[Cell]] = [[Cell.EMPTY for x in range(dim.width)] for y in range(dim.height)]
        self._next_food = food_interval

        ''' Snake(s) things '''
        snake_spacing = dim.width // (nsnakes+ 1)
        head_position = (dim.height  + snake_len) // 2
        self._snakes = [Snake(Coord(snake_spacing * (i + 1), head_position), snake_len, Direction.UP) for i in range(nsnakes)]

        ''' Food things '''
        self._food: List[Food] = []
        self._food_interval = food_interval

        ''' State things '''
        self._state = State([], [], False)

        ''' Time and periodic events '''
        self._step_ts = 0
        self._step_dt = 100
        self._food_ts = food_interval
        self._food_dt = food_interval

    @property
    def dim(self):
        return self._dim

    @property
    def board(self):
        return self._board

    '''Run one iteration of the egine.

    Parameters
    ----------
    input : List[Tuple[int, Direction]]
        A list of tuples (<snake_id>, <direction>] containing the updated
        direction of each included snake. The direction is from the perspective
        of the player and not the snake.
    '''
    def step(self, ts: int, inputs: List[Tuple[int, Direction]]=[]) -> State:
        # Always update the snake inputs or the game will feel unresponsive
        self._update_snake_inputs(inputs)

        if ts - self._step_ts < self._step_dt:
            return self._state

        self._step_ts = ts

        add_food = False
        if ts - self._food_ts > self._food_dt:
            add_food = True
            self._food_ts = ts

        self._state = self._update_game_state(add_food)

        self._view.draw(self._board, self._state)

        return self._state


    def _update_snake_inputs(self, inputs: List[Tuple[int, Direction]]):
        for idx, direction in inputs:
            self._snakes[idx].direction = direction

    def _update_game_state(self, add_food: bool) -> State:
        for snake in self._snakes:
            snake.move()

        food_coord: Coord
        i = 0

        for row_idx, row in enumerate(self._board):
            for col_idx, col in enumerate(row):
                # Just keeping track of the number of iterations
                i += 1

                coord = Coord(col_idx, row_idx)

                # Assume the cell is empty
                self._board[row_idx][col_idx] = Cell.EMPTY

                # Add snake segments
                for snake in self._snakes:
                    if snake.contains(coord):
                        self._board[row_idx][col_idx] = Cell.SNAKE

                # find an empty position to hold food
                if self._board[row_idx][col_idx] == Cell.EMPTY:
                    if i == 0:
                        # If this is the first iteration set food_coord to the
                        # current coordinate
                        food_coord = coord
                    elif random.randint(1, i) == 1:
                        # Let the probability be 1 in "number of iterations"
                        # that we update the coordinate to place food at
                        food_coord = coord

        # Add new food item unless there's already 3 item on the board
        if add_food and len(self._food) < 3:
            self._food.append(Food(food_coord)) 

        # Add food items to board
        for food in self._food:
            self._board[food.coord.row][food.coord.col] = Cell.FOOD

        collisions = self._collision_detect()
        points = [snake.points for snake in self._snakes]
        game_over = len(collisions) > 0
        return State(collisions, points, game_over)

    def _collision_detect(self) -> List[int]:
        collisions: List[int] = []

        for i, snake in enumerate(self._snakes):
            # Does the snake collide with the board boundary?
            if snake.collides_with_boundary(self._dim):
                collisions.append(i)
                continue

            # Does the snake collide with itself or another snake?
            for other in self._snakes:
                if snake.collides_with_snake(other):
                    collisions.append(i)

            # Does the snake collide with any food item?
            for food in self._food:
                if snake.collides_with_food(food):
                    self._food.remove(food)
                    snake.grow(5)

                    # increase speed
                    self._step_dt -= 2

        return collisions



import pygame
from pygame.locals import *

class PyGameView(AbstractView):

    def __init__(self, dim: Dimension, screen_sz=Tuple[int, int]):
        super().__init__()


        self._surface = pygame.display.set_mode((screen_sz[0], 100 + screen_sz[1]))
        #self._board_surface = self._surface.subsurface(screen_sz)
        self._score_surface = self._surface.subsurface((0, 0, screen_sz[0], 100))
        self._board_surface = self._surface.subsurface((0, 100, screen_sz[0], screen_sz[1]))

        self._palette: Mapping[Cell, pygame.Color] = {
            Cell.EMPTY: pygame.Color(0, 0, 0),
            Cell.SNAKE: pygame.Color(0, 255, 0),
            Cell.FOOD: pygame.Color(255, 0, 0),
        }

        self._sq_width = screen_sz[0] // dim.width
        self._sq_height = screen_sz[1] // dim.height

    def draw(self, board: List[List[Cell]], state: State):
        self._draw_score()
        self._draw_board(board)

    def _draw_score(self):
        gray = pygame.Color(128, 128, 128)
        pygame.draw.rect(self._score_surface, gray, Rect(0, 0, self._score_surface.get_width(), self._score_surface.get_height()))

    def _draw_board(self, board: List[List[Cell]]):
        for row_idx, rows in enumerate(board):
            y = self._sq_height * row_idx

            for col_idx, _ in enumerate(rows):
                x = self._sq_width * col_idx

                cell = board[row_idx][col_idx]
                color = self._palette[cell]

                pygame.draw.rect(self._board_surface, color, Rect(x, y, self._sq_width, self._sq_height))