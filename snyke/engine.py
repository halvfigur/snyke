import dataclasses
import sys

from dataclasses import dataclass
from enum import Enum

from typing import List, Tuple


@dataclass
class Coord:
    col: int
    row: int


Direction = Enum('Direction', ['UP', 'DOWN', 'RIGHT', 'LEFT'])


class Snake:

    def __init__(self, head: Coord, length: int, direction: Direction,):
        super().__init__()
        self._cells = self._create(head, length, direction)
        self._direction = direction

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

    @property
    def head(self):
        return self._cells[0]

    def contains(self, c: Coord) -> bool:
        return c in self._cells

    def move(self):
        head = self._cells[0]
        new_head: Coord

        if self._direction is Direction.UP:
            new_head = Coord(head.col, head.row-1)
        elif self._direction is Direction.DOWN:
            new_head = Coord(head.col, head.row+1)
        elif self._direction is Direction.LEFT:
            new_head = Coord(head.col-1, head.row)
        else:
            new_head = Coord(head.col+1, head.row)

        self._cells = [new_head, *self._cells[:-1]]

    @property
    def direction(self) -> Direction:
        return self._direction

    @direction.setter
    def direction(self, d: Direction):
        if d is Direction.UP and self._direction is not Direction.DOWN:
            self._direction = d
            return

        if d is Direction.DOWN and self._direction is not Direction.UP:
            self._direction = d
            return

        if d is Direction.RIGHT and self._direction is not Direction.LEFT:
            self._direction = d
            return

        if d is Direction.LEFT and self._direction is not Direction.RIGHT:
            self._direction = d
            return


Cell = Enum('cell', ['EMPTY', 'SNAKE', 'FOOD'])


class Engine:

    def __init__(self, dim: int, nsnakes: int, snake_len: int, food_interval: int):
        super().__init__()

        self._dim = dim
        self._board: List[List[Cell]] = [[Cell.EMPTY for x in range(dim)] for y in range(dim)]
        self._food_interval = food_interval
        self._next_food = food_interval

        snake_spacing = dim // (nsnakes+ 1)
        head_position = (dim  + snake_len) // 2

        self._snakes = [Snake(Coord(head_position, snake_spacing * (i + 1)), snake_len, Direction.UP) for i in range(nsnakes)]
        #import pdb;pdb.set_trace()

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
    def step(self, inputs: List[Tuple[int, Direction]]=[]):
        self._update_snakes(inputs)
        self._update_next_food()

        # 1. Clear all Cells
        # 2. Add snake segments

        for row_idx, row in enumerate(self._board):
            for col_idx, col in enumerate(row):

                self._board[col_idx][row_idx] = Cell.EMPTY

                for snake in self._snakes:
                    if snake.contains(Coord(col_idx, row_idx)):
                        self._board[col_idx][row_idx] = Cell.SNAKE

    def _update_snakes(self, inputs: List[Tuple[int, Direction]]):
        for snake, direction in inputs:
            self._snakes[snake].direction = direction

        for snake in self._snakes:
            snake.move()

    def _collision_detect(self) -> List[int]:
        collisions: List[int]

        heads = [snake.head() for snake in self._snakes]

        for i, head in enumerate(heads):
            for snake in self._snakes:
                if snake.contains(head):
                    collisions.append(i)

        return collisions

    def _update_next_food(self):
        if self._next_food != 0:
            return

        self._next_food = self._food_interval

class Renderer:

    def __init__(self):
        super().__init__()

    def move(self, c: Coord):
        raise NotImplementedError

    def draw_snake_segment(self, c: Coord):
        raise NotImplementedError

    def draw_food(self, c: Coord):
        raise NotImplementedError


class View:

    def __init__(self):
        super().__init__()

    def draw(self, engine):
        self._clear_screen()
        self._outline(engine.dim)
        self._draw_board(engine.board)

        sys.stdout.flush()

    def _clear_screen(self):
        sys.stdout.write('\033[2J')

    def _outline(self, dim):
        horiz = '+' + '-'*dim + '+'
        vert = '|' + ' '*dim + '|'

        line_offset = 1
        self._move(Coord(0, line_offset))
        sys.stdout.write(horiz)

        for i in range(dim):
            self._move(Coord(0, line_offset  + i + 1))
            sys.stdout.write(vert)

        self._move(Coord(0, line_offset + i + 1))
        sys.stdout.write(horiz)

    def _draw_board(self, board: List[List[Cell]]):
        for col, cells in enumerate(board): # y: List[Cell]
            for row, cell in enumerate(cells):
                self._move(Coord(col, row))

                if cell is Cell.SNAKE:
                    sys.stdout.write('@')
                elif cell is Cell.FOOD:
                    sys.stdout.write('0')


    def _move(self, c: Coord):
        sys.stdout.write(f'\033[{c.row};{c.col}H')

    def _put_symbol(self, c: Coord, sym: str):
        self._move(c)
        sys.stdout.write(sym)
