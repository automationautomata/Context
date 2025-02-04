from collections import namedtuple
from typing import Any, Callable

from state import Context, State, StateInterlayer


class FSM:
    '''Finite State Machine

    Sets rules for state transitions depending on the context.
    '''

    def __init__(
        self,
        name,
        transitions: dict[str, dict[Context, str]] | None,
        states: list | None,
    ) -> None:
        '''
        Args:
            name (str): name of the state.
            transitions (dict[str, dict[Context, str]]): table of transitions where key is name of state.
        '''
        self.name = name
        self.states = {}
        if states is not None:
            self.states = {state.name: state for state in states}

        self.transitions = {}
        if transitions is not None:
            if set(self.transitions).issubset(set(self.states)):
                self.transitions = transitions
            else:
                raise Exception(
                    "list of states in transitions table must be subset of states list"
                )

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

    def isstate(self, name) -> bool:
        return name in self.states


Record = namedtuple("Record", ["context", "state"])


class FSMHistory(list[Record]):
    def __init__(self, machine: FSM, size: int = None) -> None:
        self.machine = machine
        self.size = size
        super().__init__()

    def append(self, context: Context, state: State) -> None:
        if not self.machine.isstate(state.name):
            raise Exception()

        if not any(context in x for x in self.machine.transitions.values()):
            raise Exception()

        super().append(Record(context, state))
        if self.size is not None and len(self) > self.size:
            super().pop(0)

    def show(self) -> None:
        from tabulate import tabulate

        print(
            tabulate(
                map(
                    lambda el: (el[0], el[1].context, el[1].state.name), enumerate(self)
                ),
                headers=["id", "Context", "State"],
                tablefmt="pipe",
            )
        )

    def get_state_sequence(self, sep: str = "") -> str:
        return sep.join(el.state.name for el in self)

    def get_context_sequence(self, sep: str = "") -> str:
        return sep.join(el.context for el in self)

    def __getattr__(self, name):
        if hasattr(super(), name):
            original_method = getattr(super(), name)
            if callable(original_method):

                def wrapper(*args, **kwargs):
                    result = original_method(*args, **kwargs)
                    return result

                return wrapper
        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )


class FSMHandler:
    def __init__(
        self, interlayer: StateInterlayer, machine: FSM, history: FSMHistory = None
    ) -> None:
        self.interlayer = interlayer
        self.machine = machine
        self.history = history

    def handle(self, *args, **kwargs) -> Any | None:
        cur_state = self.interlayer.get_state(*args, **kwargs)
        if not cur_state.entering_condition(*args, **kwargs):
            return

        res = cur_state.action(*args, **kwargs)
        if not cur_state.transition_condition(*args, **kwargs):
            if self.history is not None:
                self.history.append(None, None)
            return res

        context = cur_state.getcontext(*args, **kwargs)
        new_state = self.machine.getnextstate(cur_state.name, context)
        self.interlayer.set_state(new_state)

        if self.history is not None:
            self.history.append(context, new_state)
        return res

    async def async_handle(self, *args, **kwargs) -> Any:
        cur_state: State = await self.interlayer.get_state(*args, **kwargs)

        if not await cur_state.entering_condition(*args, **kwargs):
            return

        res = await cur_state.action(*args, **kwargs)
        if not await cur_state.transition_condition(*args, **kwargs):
            if self.history is not None:
                self.history.append(None, None)
            return res

        context = await cur_state.getcontext(*args, **kwargs)
        new_state = self.machine.getnextstate(cur_state.name, context)
        await self.interlayer.set_state(new_state)

        if self.history is not None:
            self.history.append(context, new_state)
        return res


class FinalStetesFSM(FSM):
    def __init__(
        self,
        name,
        transitions: dict[str, dict[Context, str]] | None,
        states: list | None,
        final_states: list | None,
        final_state_callback: Callable[[State, Context, Any], Any],
    ) -> None:
        super().__init__(name, transitions, states)

        self.final_states = {}
        if final_states is not None:
            if set(self.final_states).issubset(set(self.states)):
                self.transitions = transitions
            else:
                raise Exception(
                    "list of states in transitions table must be subset of states list"
                )
            self.final_states = {state.name: state for state in final_states}
        self.final_state_callback = final_state_callback

    def isfinalstate(self, name) -> State:
        return name in self.final_states


class FinalStetesFSMHandler(FSMHandler):
    def __init__(
        self,
        interlayer: StateInterlayer,
        machine: FinalStetesFSM,
        history: FinalStetesFSM = None,
    ) -> None:
        self.machine: FinalStetesFSM
        if history is None:
            history = FSMHistory(machine, 1)

        super().__init__(interlayer, machine, history)

    def handle(self, *args, **kwargs) -> Any | tuple[Any, Any]:
        res = super().handle(*args, **kwargs)
        record = self.history[-1]
        if not self.machine.isfinalstate(record.state.name):
            return res

        cbk_res = self.machine.final_state_callback(
            record.context, record.state, *args, **kwargs
        )
        return cbk_res, res

    async def async_handle(self, *args, **kwargs) -> Any | tuple[Any, Any]:
        res = await super().async_handle(*args, **kwargs)
        record = self.history[-1]
        if not self.machine.isfinalstate(record.state.name):
            return res

        cbk_res = await self.machine.final_state_callback(
            record.context, record.state, *args, **kwargs
        )
        return cbk_res, res
