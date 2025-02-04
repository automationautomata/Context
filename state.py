from abc import abstractmethod
from typing import Any, Callable, Protocol

from tools import constant


class Context(Protocol):
    @abstractmethod
    def __hash__(self) -> int:
        pass


TRUE_CONDITION = constant(True)  # noqa: E731
FALSE_CONDITION = constant(False)  # noqa: E731


class State:
    def __init__(
        self,
        name: str,
        action: Callable[[Any], Any],
        getcontext: Callable[[Any], Context],
        entering_condition: Callable[[Any], bool] | bool,
        transition_condition: Callable[[Any], bool] | bool,
    ) -> None:
        '''
        Args:
            name (str): name of state.
            action (Callable[[Any], Any]): the action that will be executed after entering it.
            getcontext (Callable[[Any], Context]): must return context of tranition to the next state.
            entering_condition (Callable[[Any], bool]): condition of entering in state.
            transition_condition (Callable[[Any], bool]): condition of transition to other state.
        '''
        self.name = name
        self.action = action
        self.getcontext = getcontext

        if type(entering_condition) is not bool:
            self.entering_condition = entering_condition
        elif entering_condition:
            self.entering_condition = TRUE_CONDITION
        else:
            self.entering_condition = FALSE_CONDITION

        if type(entering_condition) is not bool:
            self.transition_condition = transition_condition
        elif entering_condition:
            self.transition_condition = TRUE_CONDITION
        else:
            self.transition_condition = FALSE_CONDITION


class StateInterlayer(Protocol):
    def get_state(self, *args, **kwargs) -> State:
        '''Must return State by given data.'''
        pass

    def set_state(self, state: State) -> None:
        '''Must set State.'''
        pass


class SimpleStateContainer:
    '''
    Save last state.
    '''
    def __init__(self, start_state: State):
        self.state = start_state

    def get_state(self, *args, **kwargs) -> State:
        return self.state

    def set_state(self, state: State) -> None:
        self.state = state
