from abc import ABC, abstractmethod
from typing import Any, Callable, Protocol


class Context(ABC):
    @abstractmethod
    def __hash__(self) -> int:
        pass


TRUE_CONDITION = lambda _: True  # noqa: E731
FALSE_CONDITION = lambda _: False  # noqa: E731


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


class FSM:
    '''Finite State Machine
    
    Sets rules for state transitions depending on the context.
    '''

    def __init__(
        self,
        transitions: dict[str, dict[Context, str]] | None,
        states: list | None,
    ) -> None:
        '''
        Args:
            name (str): name of the state.
            transitions (dict[str, dict[Context, str]]): table of transitions where key is name of state.
        '''
        self.states = {}
        if states is not None:
            self.states = {state.name: state for state in states}

        self.transitions = {}
        if transitions is not None:
            if set(self.transitions).issubset(set(self.states)):
                self.transitions = transitions

    def getnextstate(self, state: str, context: Context) -> State:
        return self.states[self.transitions[state][context]]

    def __getitem__(self, name) -> State:
        '''
        Args:
            name (str): name of the state.
        
        Returns:
            State with given name.
        '''
        return self.states[name]


class StateInterlayer(Protocol):
    ''' 
    
    '''
    def get_state(self, *args, **kwargs) -> State:
        '''Must return State by given data.'''
        pass

    def set_state(self, state: State) -> None:
        '''Must set State.'''
        pass


class FSMHandler:
    def __init__(self, interlayer: StateInterlayer, machine: FSM) -> None:
        self.interlayer = interlayer
        self.machine = machine

    def handle(self, user: int | str | tuple, *args, **kwargs) -> Any:
        cur_state = self.interlayer.get_state(user)
        if not cur_state.entering_condition(*args, **kwargs):
            return

        res = cur_state.action(*args, **kwargs)
        if cur_state.transition_condition(*args, **kwargs):
            context = cur_state.getcontext(*args, **kwargs)
            new_state = self.machine.getnextstate(cur_state.name, context)
            self.interlayer.set_state(new_state)

        return res

    async def async_handle(self, user: int | str | tuple, *args, **kwargs) -> Any:
        cur_state: State = await self.interlayer.get_state(user)

        if not await cur_state.entering_condition(*args, **kwargs):
            return

        res = await cur_state.action(*args, **kwargs)
        if await cur_state.transition_condition(*args, **kwargs):
            context = await cur_state.getcontext(*args, **kwargs)
            new_state = self.machine.getnextstate(cur_state.name, context)
            await self.interlayer.set_state(new_state)

        return res
