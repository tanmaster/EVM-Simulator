import logging
from enum import Enum
from typing import Dict

from eth.abc import CodeStreamAPI, OpcodeAPI, MessageAPI

logger = logging.getLogger(__name__)


class TableWidgetEnum(Enum):
    OPCODES = 0
    STACK = 1
    MEMORY = 2
    STORAGE = 3
    ADDRESSES = 4


class ChangeChainLink:

    def __init__(self, widget: TableWidgetEnum, pre_computation: [int], post_computation: [int]):
        """
        :param widget: The ChangeEnum which represents the table widget in which the changes will take place.
        :param pre_computation: The indices of table to highlight before the computation.
        :param post_computation: The indices of table to highlight after the computation.
        """
        self.widget = widget
        self.pre_computation = pre_computation
        self.post_computation = post_computation
        self.next = None


class ChangeChain:
    """
        ChangeChain class which is used to represent all the changes that happen per step.
        It makes use of the ChangeChainLink above, which stores row indices to highlight for each
        table for pre-computation phase and post-computation phase. It is an iterable class which will
        means looping through it will iterate through each ChainLink in the ChangeChain
    """

    def __init__(self, c: ChangeChainLink):
        self.head = c
        self.current = c

    def add_link(self, c: ChangeChainLink):
        self.current.next = c
        self.current = self.current.next
        return self

    def __iter__(self):
        self.current = self.head
        return self

    def __next__(self):
        if self.current is None:
            raise StopIteration
        else:
            a: ChangeChainLink = self.current
            self.current = self.current.next
            return a


class History:
    """
        History class used to keep track of every change that happens in each step of a transaction. This is necessary
        to provide means to "scroll back" a transaction.
    """
    def __init__(self):
        self.change_chains: [ChangeChain] = []
        self.init: (CodeStreamAPI, Dict[int, OpcodeAPI], MessageAPI) = ()
        self.pre_computations: [(int, int)] = []
        self.post_computations: [()] = []
        self.storage: [(str, str)] = []
        self.history_pointer: int = 0

    def get_init(self) -> (CodeStreamAPI, Dict[int, OpcodeAPI], MessageAPI):
        return self.init

    def set_init(self, code: CodeStreamAPI, opcodes: Dict[int, OpcodeAPI], msg: MessageAPI):
        if self.init != ():
            logger.warning("Setting init value that has already been set", code, opcodes, msg)
        self.init = (code, opcodes, msg)

    def add_link(self, chain: ChangeChain):
        self.change_chains.append(chain)

    def add_pre_computation(self, gas_left: int, pc: int):
        self.pre_computations.append((gas_left, pc))

    def add_post_computation(self, stack, memory, pc, used_gas):
        self.post_computations.append((stack, memory, pc))
        self.history_pointer = self.history_pointer + 1
        pass

    def add_storage(self, slot: str, value: str):
        """ Since there may be steps in which the storage does not change, we are adding None values to keep the indices
        lined up with the other arrays. This might cause some overhead."""
        while len(self.storage) <= self.history_pointer:
            self.storage.append(None)
        self.storage.append((slot, value))

    def __iter__(self):
        self.history_pointer = 0
        return self

    def __next__(self):
        if self.history_pointer == len(self.pre_computations):
            raise StopIteration
        else:
            ptr = self.history_pointer
            res = (self.init, self.change_chains[ptr], self.pre_computations[ptr], self.post_computations[ptr],
                   self.storage[ptr])
            self.history_pointer = self.history_pointer + 1
            return res
