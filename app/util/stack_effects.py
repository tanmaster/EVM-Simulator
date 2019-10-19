from eth.vm.opcode_values import *
from app.util.changes import ChangeChainLink
from app.util.changes import TableWidgetEnum

"""
    The file is used to store the changes that happen in the stack for any given opcode.
    The changes that happen in the stack are static and always the same. 
    The information was taken from: https://ethervm.io/. It appears that some opcodes that are supported by
    py-evm are not in that list. 

"""

stack_effects: {} = {}
memory_effects: {} = {}
storage_effects: {} = {}


def create_link(pre_size: int, post_size: int) -> ChangeChainLink:
    """
    Creates a Stack ChangeChainLink which will have a list containing integers from 0 to pre_size as
    pre computation changes index list, and integers from 0 to post_size as the other.
    """
    return ChangeChainLink(
        TableWidgetEnum.STACK,
        [item for item in range(0, pre_size)],
        [item for item in range(0, post_size)]
    )


#
# Stop and Arithmetic
#

stack_effects[STOP] = create_link(0, 0)
stack_effects[ADD] = create_link(2, 1)
stack_effects[MUL] = create_link(2, 1)
stack_effects[SUB] = create_link(2, 1)
stack_effects[DIV] = create_link(2, 1)
stack_effects[SDIV] = create_link(2, 1)
stack_effects[MOD] = create_link(2, 1)
stack_effects[SMOD] = create_link(2, 1)
stack_effects[ADDMOD] = create_link(3, 1)
stack_effects[MULMOD] = create_link(3, 1)
stack_effects[EXP] = create_link(2, 1)
stack_effects[SIGNEXTEND] = create_link(2, 1)

#
# Comparison and Bitwise Logic
#
stack_effects[LT] = create_link(2, 1)
stack_effects[GT] = create_link(2, 1)
stack_effects[SLT] = create_link(2, 1)
stack_effects[SGT] = create_link(2, 1)
stack_effects[EQ] = create_link(2, 1)
stack_effects[ISZERO] = create_link(1, 1)
stack_effects[AND] = create_link(2, 1)
stack_effects[OR] = create_link(2, 1)
stack_effects[XOR] = create_link(2, 1)
stack_effects[NOT] = create_link(1, 1)
stack_effects[BYTE] = create_link(2, 1)

stack_effects[SHL] = create_link(2, 1)
stack_effects[SHR] = create_link(2, 1)
stack_effects[SAR] = create_link(2, 1)

#
# Sha3
#
stack_effects[SHA3] = create_link(2, 1)

#
# Environment Information
#
stack_effects[ADDRESS] = create_link(0, 1)
stack_effects[BALANCE] = create_link(1, 1)
stack_effects[ORIGIN] = create_link(0, 1)
stack_effects[CALLER] = create_link(0, 1)
stack_effects[CALLVALUE] = create_link(0, 1)
stack_effects[CALLDATALOAD] = create_link(1, 1)
stack_effects[CALLDATASIZE] = create_link(0, 1)
stack_effects[CALLDATACOPY] = create_link(3, 0)
stack_effects[CODESIZE] = create_link(0, 1)
stack_effects[CODECOPY] = create_link(3, 0)
stack_effects[GASPRICE] = create_link(0, 1)

stack_effects[EXTCODESIZE] = create_link(1, 1)
stack_effects[EXTCODECOPY] = create_link(4, 0)
stack_effects[RETURNDATASIZE] = create_link(0, 1)
stack_effects[RETURNDATACOPY] = create_link(3, 0)

# As defined in https://github.com/ethereum/EIPs/blob/master/EIPS/eip-1052.md
stack_effects[EXTCODEHASH] = create_link(1, 1)

#
# Block Information
#
stack_effects[BLOCKHASH] = create_link(1, 1)
stack_effects[COINBASE] = create_link(0, 1)
stack_effects[TIMESTAMP] = create_link(0, 1)
stack_effects[NUMBER] = create_link(0, 1)
stack_effects[DIFFICULTY] = create_link(0, 1)
stack_effects[GASLIMIT] = create_link(0, 1)

#
# Stack, Memory, Storage and Flow Operations
#

stack_effects[POP] = create_link(1, 0)
stack_effects[MLOAD] = create_link(1, 1)
stack_effects[MSTORE] = create_link(2, 0)
stack_effects[MSTORE8] = create_link(2, 0)
stack_effects[SLOAD] = create_link(1, 1)
stack_effects[SSTORE] = create_link(2, 0)
stack_effects[JUMP] = create_link(1, 0)
stack_effects[JUMPI] = create_link(2, 0)
stack_effects[PC] = create_link(0, 1)
stack_effects[MSIZE] = create_link(0, 1)
stack_effects[GAS] = create_link(0, 1)
stack_effects[JUMPDEST] = create_link(0, 0)

#
# Push Operations
#

for i in range(PUSH1, PUSH32 + 1):
    stack_effects[i] = create_link(0, 1)
#
# Duplicate Operations
#

for i in range(DUP1, DUP16 + 1):
    stack_effects[i] = ChangeChainLink(TableWidgetEnum.STACK, [i - DUP1], [0, i - DUP1 + 1])

#
# Exchange Operations
#

for i in range(SWAP1, SWAP16 + 1):
    stack_effects[i] = ChangeChainLink(TableWidgetEnum.STACK, [0, i - SWAP1 + 1], [0, i - SWAP1 + 1])

#
# Logging
#
stack_effects[LOG0] = create_link(2, 0)
stack_effects[LOG1] = create_link(3, 0)
stack_effects[LOG2] = create_link(4, 0)
stack_effects[LOG3] = create_link(5, 0)
stack_effects[LOG4] = create_link(6, 0)

#
# System
#
stack_effects[CREATE] = create_link(3, 1)
stack_effects[CALL] = create_link(7, 1)
stack_effects[CALLCODE] = create_link(7, 1)
stack_effects[RETURN] = create_link(2, 0)
stack_effects[DELEGATECALL] = create_link(6, 1)

# from https://eips.ethereum.org/EIPS/eip-1014
stack_effects[CREATE2] = create_link(4, 1)

stack_effects[STATICCALL] = create_link(6, 1)
stack_effects[REVERT] = create_link(2, 0)
stack_effects[SELFDESTRUCT] = create_link(1, 0)
