import dataclasses

from dataclasses import dataclass
from enum import Enum

import random
import time
from typing import Mapping, List, Tuple, Optional, overload


"""Coordinate
"""


@dataclass
class Coord:
    col: int
    row: int


""" Dimension
"""


@dataclass
class Dimension:
    width: int
    height: int


""" State
"""


@dataclass
class State:
    # The indices of snakes that have collided a wall or a snake (including itself)
    collisions: List[int]

    # Is the game over
    is_game_over: bool


""" Direction
"""
Direction = Enum("Direction", ["UP", "DOWN", "RIGHT", "LEFT"])


class Food:
    def __init__(self, coord: Coord):
        self._coord = coord

    @property
    def coord(self):
        return self._coord


class Snake:
    def __init__(
        self,
        head: Coord,
        length: int,
        direction: Direction,
    ):
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
        else:
            col_offset = 1

        return [
            Coord(head.col + i * col_offset, head.row + i * row_offset)
            for i in range(length)
        ]

    def grow(self, n: int):
        tail = self._cells[-1]
        for i in range(n):
            self._cells.append(dataclasses.replace(tail))

        self._points += n

    @property
    def head(self):
        return self._cells[0]

    @property
    def cells(self):
        return self._cells

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

    def contains(self, c: Coord, disregard_head: bool = False) -> bool:
        if disregard_head:
            return c in self._cells[1:]

        return c in self._cells

    def collides_with_boundary(self, boundary: Dimension) -> bool:
        return not (
            (0 <= self.head.row <= boundary.height)
            and (0 <= self.head.col <= boundary.width)
        )

    def collides_with_snake(self, snake: "Snake") -> bool:
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
            new_head = Coord(head.col, head.row - 1)
        elif self._direction is Direction.DOWN:
            new_head = Coord(head.col, head.row + 1)
        elif self._direction is Direction.LEFT:
            new_head = Coord(head.col - 1, head.row)
        else:
            new_head = Coord(head.col + 1, head.row)

        self._cells = [new_head, *self._cells[:-1]]

        self._points += 1


class AbstractView:
    def __init__(self, dim: Dimension):
        super().__init__()
        self._dim = dim

    @overload
    def draw(self, snakes: List[Snake], food: List[Food]):
        raise NotImplemented


class Engine:
    def __init__(
        self,
        view: AbstractView,
        dim: Dimension,
        nsnakes: int,
        snake_len: int,
        food_interval: int,
    ):
        super().__init__()

        random.seed(time.time())

        """ View things """
        self._view = view
        self._dim = dim

        """ Game things """
        self._next_food = food_interval

        """ Snake(s) things """
        snake_spacing = dim.width // (nsnakes + 1)
        head_position = (dim.height + snake_len) // 2
        self._snakes = [
            Snake(
                Coord(snake_spacing * (i + 1), head_position), snake_len, Direction.UP
            )
            for i in range(nsnakes)
        ]

        """ Food things """
        self._food: List[Food] = []
        self._food_interval = food_interval

        """ State things """
        self._state = State([], False)

        """ Time and periodic events """
        self._step_ts = 0
        self._step_dt = 100
        self._food_ts = food_interval
        self._food_dt = food_interval

    @property
    def dim(self):
        return self._dim

    """Run one iteration of the egine.

    Parameters
    ----------
    input : List[Tuple[int, Direction]]
        A list of tuples (<snake_id>, <direction>] containing the updated
        direction of each included snake. The direction is from the perspective
        of the player and not the snake.
    """

    def step(self, ts: int, inputs: List[Tuple[int, Direction]] = []) -> State:
        # Always update the snake inputs or the game will feel unresponsive
        self._update_snake_inputs(inputs)

        if ts - self._step_ts < self._step_dt:
            return self._state

        self._step_ts = ts

        add_food = False
        if ts - self._food_ts > self._food_dt:
            # No more than three food items on the board at any one time
            add_food = len(self._food) < 3
            self._food_ts = ts

        self._state = self._update_game_state(add_food)

        # self._view.draw(self._snake, self._food, self._state)
        self._view.draw(self._snakes, self._food)

        return self._state

    def _update_snake_inputs(self, inputs: List[Tuple[int, Direction]]):
        for idx, direction in inputs:
            self._snakes[idx].direction = direction

    def _snake_at(self, c: Coord) -> bool:
        for snake in self._snakes:
            if snake.contains(c):
                return True
        return False

    def _food_at(self, c: Coord) -> bool:
        for food in self._food:
            if food.coord == c:
                return True
        return False

    def _add_food(self):
        food_coord: Coord
        i = 0

        for row in range(self._dim.height):
            for col in range(self._dim.width):
                i += 1
                coord = Coord(col, row)

                if not self._snake_at(coord) and not self._food_at(coord):
                    if i == 0:
                        # If this is the first iteration set food_coord to the
                        # current coordinate
                        food_coord = coord
                    elif random.randint(1, i) == 1:
                        # Let the probability be 1 in "number of iterations"
                        # that we update the coordinate to place food at
                        food_coord = coord

        self._food.append(Food(food_coord))

    def _update_game_state(self, add_food: bool) -> State:
        for snake in self._snakes:
            snake.move()

        if add_food:
            self._add_food()

        collisions = self._detect_collisions()
        game_over = len(collisions) > 0

        return State(collisions, game_over)

    def _detect_collisions(self) -> List[int]:
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
    def __init__(
        self, font: pygame.font.Font, dim: Dimension, screen_sz=Tuple[int, int]
    ):
        super().__init__(dim)
        self._font = font

        self._surface = pygame.display.set_mode((screen_sz[0], 100 + screen_sz[1]))
        # self._board_surface = self._surface.subsurface(screen_sz)
        self._score_surface = self._surface.subsurface((0, 0, screen_sz[0], 100))
        self._board_surface = self._surface.subsurface(
            (0, 100, screen_sz[0], screen_sz[1])
        )

        self._sq_width = screen_sz[0] // dim.width
        self._sq_height = screen_sz[1] // dim.height

        self._board_bg_color = pygame.Color(0, 0, 0)
        self._score_bg_color = pygame.Color(0x10, 0x10, 0x10)
        self._score_fg_color = pygame.Color(0xFF, 0xFF, 0xFF)
        self._food_color = pygame.Color(0xFF, 0, 0)

    def draw(self, snakes: List[Snake], food: List[Food]):
        self._draw_score(snakes)
        self._draw_board()
        self._draw_snakes(snakes)
        self._draw_food(food)

    def _draw_score(self, snakes: List[Snake]):
        pygame.draw.rect(
            self._score_surface,
            self._score_bg_color,
            Rect(
                0, 0, self._score_surface.get_width(), self._score_surface.get_height()
            ),
        )

        img = self._font.render(
            f"Score: {snakes[0].points}", True, self._score_fg_color
        )
        self._score_surface.blit(img, (20, 20))

    def _snake_color(self, i) -> pygame.Color:
        return pygame.Color(0, 0xFF, 0)

    def _draw_snakes(self, snakes: List[Snake]):
        for i, snake in enumerate(snakes):
            for cell in snake._cells:
                pygame.draw.rect(
                    self._board_surface,
                    self._snake_color(i),
                    Rect(
                        cell.col * self._sq_width,
                        cell.row * self._sq_height,
                        self._sq_width,
                        self._sq_height,
                    ),
                )

    def _draw_food(self, food: List[Food]):
        for f in food:
            pygame.draw.rect(
                self._board_surface,
                self._food_color,
                Rect(
                    f.coord.col * self._sq_width,
                    f.coord.row * self._sq_height,
                    self._sq_width,
                    self._sq_height,
                ),
            )

    def _draw_board(self):
        pygame.draw.rect(
            self._board_surface,
            self._board_bg_color,
            Rect(
                0, 0, self._board_surface.get_width(), self._board_surface.get_height()
            ),
        )
