from typing import Any, List, Optional
from dataclasses import dataclass
from .engine import State


class Action:
    def __init__(self, data: Optional[Any] = None):
        self._data = data

    @property
    def data(self) -> Any:
        return self._data


class ActionNewGame(Action):
    ...


class ActionExitGame(Action):
    ...


class ActionGameOver(Action):
    ...


class Controller:
    def __init__(self):
        super().__init__()
        self._nil_action = Action()

    def enter(self, tick: int, data: Any = None):
        ...

    def exit(self, tick: int):
        ...

    def left_pressed(self, tick: int) -> Action:
        return self._nil_action

    def right_pressed(self, tick: int) -> Action:
        return self._nil_action

    def up_pressed(self, tick: int) -> Action:
        return self._nil_action

    def down_pressed(self, tick: int) -> Action:
        return self._nil_action

    def enter_pressed(self, tick: int) -> Action:
        return self._nil_action

    def update(self, tick: int) -> Action:
        return self._nil_action


import pygame
from pygame.locals import *


from .engine import GameModel
from .engine import Direction


class GameController(Controller):
    def __init__(self, model: GameModel):
        super().__init__()
        self._nil_action = Action()

        self._repeat_setting = pygame.key.get_repeat()
        self._model = model

    def enter(self, tick: int, data: Any = None):
        self._model.reset()
        self.update(tick)

    def exit(self, tick: int):
        pygame.key.set_repeat(*self._repeat_setting)

    def left_pressed(self, tick: int) -> Action:
        self._model.step(tick, [(0, Direction.LEFT)])
        return Action()

    def right_pressed(self, tick: int) -> Action:
        self._model.step(tick, [(0, Direction.RIGHT)])
        return Action()

    def up_pressed(self, tick: int) -> Action:
        self._model.step(tick, [(0, Direction.UP)])
        return Action()

    def down_pressed(self, tick: int) -> Action:
        self._model.step(tick, [(0, Direction.DOWN)])
        return Action()

    def update(self, tick: int) -> Action:
        state = self._model.step(tick)
        if state.is_game_over:
            return ActionGameOver(state)

        return self._nil_action


from .engine import MenuModel


class MenuController(Controller):
    def __init__(self, model: MenuModel):
        super().__init__()

        self._repeat_setting = pygame.key.get_repeat()
        self._model = model

    def enter(self, tick: int, *data):
        self._model.refresh()

    def exit(self, tick: int):
        pygame.key.set_repeat(*self._repeat_setting)

    def up_pressed(self, tick: int) -> Action:
        self._model.prev()
        return Action()

    def down_pressed(self, tick: int) -> Action:
        self._model.next()
        return Action()

    def enter_pressed(self, tick: int) -> Action:
        action = self._model.selected()

        match action:
            case "new_game":
                return ActionNewGame()
            case "exit_game":
                return ActionExitGame()
            case _:
                # Unreachable
                return Action()


class ControllerController:
    _current: Controller

    def __init__(self, menu: MenuController, game: GameController):
        super().__init__()

        self._nil_action = Action()
        self._menu = menu
        self._game = game

        self._current = menu

        self._nil_action = Action()

    def enter(self, tick: int):
        self._current.enter(tick)

    def left_pressed(self, tick: int) -> Action:
        action = self._current.left_pressed(tick)
        return self._handle_action(tick, action)

    def right_pressed(self, tick: int) -> Action:
        action = self._current.right_pressed(tick)
        return self._handle_action(tick, action)

    def up_pressed(self, tick: int) -> Action:
        action = self._current.up_pressed(tick)
        return self._handle_action(tick, action)

    def down_pressed(self, tick: int) -> Action:
        action = self._current.down_pressed(tick)
        return self._handle_action(tick, action)

    def enter_pressed(self, tick: int) -> Action:
        action = self._current.enter_pressed(tick)
        return self._handle_action(tick, action)

    def update(self, tick: int) -> Action:
        action = self._current.update(tick)
        return self._handle_action(tick, action)

    def _handle_action(self, tick: int, action: Action):
        next: Controller

        if isinstance(action, ActionNewGame):
            next = self._game
        elif isinstance(action, ActionExitGame):
            return action
        elif isinstance(action, ActionGameOver):
            next = self._menu
        else:
            return action

        if next is not self._current:
            self._current.exit(tick)
            self._current = next
            self._current.enter(tick, action.data)

        return self._nil_action


"""
class ControllerController:

    def __init__(self, controllers: List[Controller]):
        super().__init__()
        self._controllers = controllers
        self._current = controllers[0]

    def run(self):  
        fps = pygame.time.Clock()

        self._current.enter(pygame.time.get_ticks())
        while True:

            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()

                ticks = pygame.time.get_ticks()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        self._current.left_pressed(ticks)
                    elif event.key == pygame.K_RIGHT:
                        self._current.right_pressed(ticks)
                    elif event.key == pygame.K_UP:
                        self._current.up_pressed(ticks)
                    elif event.key == pygame.K_DOWN:
                        self._current.down_pressed(ticks)
                    elif event.key == pygame.K_RETURN:
                        self._current.enter_pressed(ticks)

            pygame.display.flip()
            fps.tick(60)
"""
