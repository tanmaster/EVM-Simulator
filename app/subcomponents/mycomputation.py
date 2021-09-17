import logging
from copy import deepcopy
from threading import Lock
from time import sleep
from typing import Any

from PyQt5.QtCore import QSemaphore
from eth.abc import (
    MessageAPI,
    ComputationAPI,
    StateAPI,
    TransactionContextAPI,
)
from eth.exceptions import Halt
from eth.vm.computation import NO_RESULT
from eth.vm.forks.istanbul.computation import IstanbulComputation
from eth.vm.logic.invalid import InvalidOpcode
from eth.vm.opcode_values import *

from app.util.changes import ChangeChain, ChangeChainLink, TableWidgetEnum
# prevents circular dependency
from app.util.stack_effects import stack_effects
from app.util.util import MODE_DEBUG, MODE_DEBUG_AUTO, get_stack_content

logger = logging.getLogger(__name__)


class MyComputation(IstanbulComputation):
    """
    Custom Computation Class which basically acts as if it was a ByzantiniumComputation class, with
    some extra stuff in order to be able to read out environment information.

    A class for all execution computations in the ``Byzantium`` fork.
    Inherits from :class:`~eth.vm.forks.spurious_dragon.computation.SpuriousDragonComputation`
    """

    debug_mode: int = 0
    abort: bool = False
    last_consumed_gas_amount = 0
    kwargs = {}
    init_debug_session = None
    init_lock: Lock = None
    abort_transaction = None
    step_duration = None
    storage_lock: Lock = None
    step_semaphore: QSemaphore = None
    storage_lookup = None
    pre_computation = None
    add_chain = None
    step_lock = None
    post_computation = None
    set_storage = None
    returned = False

    @classmethod
    def parse_kwargs(cls):
        cls.returned = False
        cls.set_storage = cls.kwargs.get("set_storage")
        cls.init_debug_session = cls.kwargs.get("init_debug_session")
        cls.init_lock: Lock = cls.kwargs.get("init_lock")
        cls.abort_transaction = cls.kwargs.get("abort")
        cls.step_duration = cls.kwargs.get("step_duration")
        cls.storage_lock: Lock = cls.kwargs.get("storage_lock")
        cls.step_semaphore: QSemaphore = cls.kwargs.get("step_semaphore")
        cls.storage_lookup = cls.kwargs.get("storage_lookup")
        cls.pre_computation = cls.kwargs.get("pre_computation")
        cls.post_computation = cls.kwargs.get("post_computation")
        cls.add_chain = cls.kwargs.get("add_chain")
        cls.step_lock: Lock = cls.kwargs.get("step_lock")

    @classmethod
    def apply_computation(cls,
                          state: StateAPI,
                          message: MessageAPI,
                          transaction_context: TransactionContextAPI) -> ComputationAPI:
        """
        Perform the computation that would be triggered by the VM message.
        """
        cls.parse_kwargs()
        with cls(state, message, transaction_context) as computation:
            # Early exit on pre-compiles
            precompile = computation.precompiles.get(message.code_address, NO_RESULT)
            if precompile is not NO_RESULT:
                precompile(computation)
                return computation

            opcode_lookup = computation.opcodes

            if cls.debug_mode:
                cls.init_debug_session.emit(
                    deepcopy(computation.code), computation.opcodes, message
                )
                cls.init_lock.acquire(True)

            for opcode in computation.code:
                try:
                    opcode_fn = opcode_lookup[opcode]
                except KeyError:
                    opcode_fn = InvalidOpcode(opcode)

                try:
                    if cls.abort:
                        logger.warning("Abort has been received")
                        raise Halt

                    if cls.debug_mode == MODE_DEBUG:
                        cls.step_semaphore.acquire(1)
                        cls.before_computation(computation, opcode, opcode_fn)
                    elif cls.debug_mode == MODE_DEBUG_AUTO:
                        sleep(cls.step_duration)
                        cls.before_computation(computation, opcode, opcode_fn)
                    # Since we cannot really read out every storage position that has been filled, we need
                    # to keep track of every storage slot that gets filled from the beginning of a contracts
                    # creation. This has to be done regardless of whether the user has activated debug mode or not,
                    # since else we might never get to see a storage variable ever again.
                    slot = ""
                    value = ""
                    if opcode == SSTORE:
                        # first param is key second param is value
                        arr = get_stack_content(computation._stack.values, 2)
                        slot = arr[0]
                        value = arr[1]
                    opcode_fn(computation=computation)
                    if cls.returned:
                        cls.init_debug_session.emit(deepcopy(computation.code), computation.opcodes, message)
                        cls.init_lock.acquire(True)
                        cls.returned = False
                    if opcode == REVERT:
                        logger.info("Revert has been processed")
                        cls.abort = True
                        raise Halt
                    elif opcode == SSTORE:
                        cls.set_storage.emit(message.storage_address, slot, value)
                        if cls.debug_mode:
                            cls.storage_lock.acquire(True)
                    if cls.debug_mode == MODE_DEBUG:
                        cls.step_semaphore.acquire(1)
                        cls.after_computation(computation, cls.last_consumed_gas_amount)
                    elif cls.debug_mode == MODE_DEBUG_AUTO:
                        sleep(cls.step_duration)
                        cls.after_computation(computation, cls.last_consumed_gas_amount)
                except Halt:
                    # if current opcode is RETURN, opcode_fn() will throw exception before next line is reached
                    # this is to ensure that the UI gets updated in the last iteration as well
                    if cls.debug_mode and not cls.abort:
                        cls.returned = True
                        cls.after_computation(computation, cls.last_consumed_gas_amount)
                    elif cls.abort:
                        cls.abort_transaction.emit()
                    break
        return computation

    @classmethod
    def before_computation(cls, computation: ComputationAPI, next_opcode: int, next_opcode_fn: Any):
        logger.info("Entering pre_computation with opcode {o}".format(o=next_opcode_fn.mnemonic))
        head = ChangeChainLink(TableWidgetEnum.OPCODES, pre_computation=[computation.code.pc - 1], post_computation=[])
        chain = ChangeChain(head)

        chain.add_link(stack_effects.get(next_opcode))
        stack = computation._stack.values
        lkp = cls.storage_lookup.get(computation.msg.storage_address)

        # Big if construct that determines which opcode has which causer and has which effect. This could be
        # simplified a bit, however it was not possible to determine the effects statically like in stack effects,
        # since the changes in memory and storage are dependent on the varying contents of memory, stack and storage,
        # instead of the only the opcode as it is the case with the stack.
        if next_opcode == SSTORE:
            slot = get_stack_content(stack, 1)[0]
            if lkp is None:
                index = 0
            else:
                index = lkp.get(slot)
                if index is None:
                    index = len(lkp)
            chain.add_link(ChangeChainLink(TableWidgetEnum.STORAGE, [], [index]))
        elif next_opcode == SLOAD:
            slot = get_stack_content(stack, 1)[0]
            if lkp is None or lkp.get(slot) is None:
                cls.set_storage.emit(computation.msg.storage_address, slot, "0x00")
                cls.storage_lock.acquire(True)
                # refresh because the main storage should have set this in the meantime
                lkp = cls.storage_lookup.get(computation.msg.storage_address)
            logger.info("Trying to SLOAD storage key -> index: {k} -> {i}".format(k=slot, i=lkp.get(slot)))
            chain.add_link(ChangeChainLink(TableWidgetEnum.STORAGE, [lkp.get(slot)], []))
        elif next_opcode == MSTORE or next_opcode == MSTORE8:
            offset = get_stack_content(stack, 1)[0]
            chain.add_link(
                ChangeChainLink(TableWidgetEnum.MEMORY, [], [int(offset, 16) / 32])
            )
        elif next_opcode == MLOAD:
            offset = get_stack_content(stack, 1)[0]
            chain.add_link(
                ChangeChainLink(TableWidgetEnum.MEMORY, [int(offset, 16) / 32], [])
            )
        elif next_opcode == SHA3 or (LOG0 <= next_opcode <= LOG4) \
                or next_opcode == RETURN or next_opcode == REVERT:
            arr = get_stack_content(stack, 2)
            offset = arr[0]
            length = arr[1]
            chain.add_link(ChangeChainLink(TableWidgetEnum.MEMORY,
                                           list(range(int(int(offset, 16) / 32), int(int(length, 16) / 32) + 1)), [])
                           )
        elif next_opcode == CALLDATACOPY or next_opcode == CODECOPY \
                or next_opcode == RETURNDATACOPY:
            arr = get_stack_content(stack, 3)
            offset = arr[0]
            length = arr[2]
            chain.add_link(ChangeChainLink(TableWidgetEnum.MEMORY, [],
                                           [] if "0x" == length or "0x" == offset else list(
                                               range(int(int(offset, 16) / 32), int(int(length, 16) / 32) + 1)))
                           )
        elif next_opcode == EXTCODECOPY:
            arr = get_stack_content(stack, 4)
            offset = arr[1]
            length = arr[3]
            chain.add_link(ChangeChainLink(TableWidgetEnum.MEMORY, [],
                                           list(range(int(int(offset, 16) / 32), int(int(length, 16) / 32) + 1)))
                           )
        elif next_opcode == CREATE or next_opcode == CREATE2:
            arr = get_stack_content(stack, 3)
            offset = arr[1]
            length = arr[2]
            chain.add_link(ChangeChainLink(TableWidgetEnum.MEMORY,
                                           list(range(int(int(offset, 16) / 32), int(int(length, 16) / 32) + 1)), [])
                           )
        elif next_opcode == CALL or next_opcode == CALLCODE:
            arr = get_stack_content(stack, 7)
            argoffset = arr[3]
            arglength = arr[4]
            retOffset = arr[5]
            retLength = arr[6]
            chain.add_link(
                ChangeChainLink(TableWidgetEnum.MEMORY,
                                list(range(int(int(argoffset, 16) / 32), int(int(arglength, 16) / 32) + 1)),
                                list(range(int(int(retOffset, 16) / 32), int(int(retLength, 16) / 32) + 1)))
            )
        elif next_opcode == DELEGATECALL or next_opcode == STATICCALL:
            arr = get_stack_content(stack, 6)
            argoffset = arr[2]
            arglength = arr[3]
            retOffset = arr[4]
            retLength = arr[5]
            chain.add_link(
                ChangeChainLink(TableWidgetEnum.MEMORY,
                                list(range(int(int(argoffset, 16) / 32), int(int(arglength, 16) / 32) + 1)),
                                list(range(int(int(retOffset, 16) / 32), int(int(retLength, 16) / 32) + 1)))
            )

        cls.add_chain.emit(chain)
        cls.pre_computation.emit(computation.get_gas_remaining(), computation.code.pc - 1)
        if cls.debug_mode:
            cls.step_lock.acquire(True)

    @classmethod
    def after_computation(cls, computation: ComputationAPI, last_gas: int):
        cls.post_computation.emit(computation._stack.values, computation._memory._bytes, computation.code.pc, last_gas)
        if cls.debug_mode:
            cls.step_lock.acquire(True)

    @classmethod
    def abort_callback(cls):
        cls.abort = True

    def consume_gas(self, amount: int, reason: str) -> None:
        """
        Overrides consume_gas. The only purpose is to set a static variable to the amount of gas that has been used
        during the processing of the previous last opcode, so that we can update the GUI to represent the correct amount
        of gas used.
        """
        MyComputation.last_consumed_gas_amount = amount
        return self._gas_meter.consume_gas(amount, reason)
