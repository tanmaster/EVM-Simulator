import json
from collections import namedtuple
from eth_typing import Address
from eth.vm.opcode_values import *

# list of opcodes that call code from another contract
ADDRESS_CALLING_OPCODES = [CALL, CALLCODE, STATICCALL, DELEGATECALL]

# list of opcodes that read addresses from the top of the stack
ADDRESS_READING_OPCODES = [BALANCE, EXTCODESIZE, EXTCODECOPY, EXTCODEHASH, SELFDESTRUCT]

# list of opcodes that write addresses onto the top of the stack
ADDRESS_CREATING_OPCODES = [CREATE, CREATE2]

# debug modes
MODE_NONE = 0  # transaction is just sent and mined
MODE_DEBUG = 1  # user is able to step through the computation steps
MODE_DEBUG_AUTO = 2  # user sees the changes that happen, but stepping happens in a given time interval


def _json_object_hook(d):
    return namedtuple('X', d.keys())(*d.values())


def json2obj(data):
    return json.loads(data, object_hook=_json_object_hook)


class MyTransaction:
    def __init__(self, addr: str, val: int):
        self.addr = MyAddress(addr)
        self.val = val


class MyAddress:
    """
    Own data structure used to store Addresses and other relevant information.
    """
    def __init__(self, addr: str = ""):
        self.addr = addr

    def get_typed_address(self) -> Address:
        return Address(bytes.fromhex(self.addr))

    def set_address(self, addr: str):
        self.addr = addr

    def get_readable_address(self) -> str:
        return "0x" + self.addr


class MyContract(MyAddress):
    """
    Own Contract data structure which parses abi and bytecode as json and provides methods to access them.
    """
    def __init__(self, abi_string: str, bytecode_string: str):
        super().__init__()
        # Custom ABI that is added to the given ABI which makes it possible to pass raw data for any given contract.
        raw_func = '{"constant":false,"inputs":[{"internalType":"any","name":"rawdata","type":"any"}],' \
                   '"name":"rawdata","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"}'

        self._abi_string = abi_string
        self.abi = json2obj(abi_string)
        self._bytecode_string = bytecode_string
        self.bytecode = json2obj(bytecode_string)
        self.functions = []
        self.signatures = []

        for func in self.abi:
            if func.type == "function":
                self.functions.append(func)
        self.functions.append(json2obj(raw_func))

        for func in self.functions:
            self.signatures.append(func.name + "(" + ",".join("{}".format(i.type) for i in func.inputs) + ")")

    def get_function_params(self, i: int) -> []:
        return self.functions[i].inputs


def get_stack_content(stack: [], n: int) -> []:
    """
    :param stack: The stack object as it is used by py-evm. This should be an array of Tuples which consists of the type
    and value of the element. Example: [Tuple(int, 1), Tuple(bytes, b'\x00'] would be a stack with 2 elements.
    :param n: The number of elements to retrieve.
    :return: An array of length containing the first n elements of the stack, converted to a string and prepended
        with "0x".
    """
    size = len(stack)
    result = []
    for i in range(0, n):
        if stack[size - (i + 1)][0] is int:
            val = hex(stack[size - (i + 1)][1])
        else:
            val = "0x" + stack[size - (i + 1)][1].hex()
        result.append(val)
    return result


def hex2(n):
    """
    Pads zeroes to an int so that the returned value has an even numbered length.
    Examples: 1 -> "0x01", 100 -> "0x64", 255 -> "0xff", 256 -> "0x0100"
    :param n: The int value to convert.
    :return: Hex representation of n with "0x" prepended.
    """
    x = '%x' % (n,)
    return '0x' + ('0' * (len(x) % 2)) + x
