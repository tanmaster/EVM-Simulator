import logging
import os
from unittest import TestCase

from eth_typing import Address
from eth_utils import decode_hex

from app.evmhandler import EVMHandler
from app.util import MyContract

logger = logging.getLogger(__name__)


class DummySignal:
    def __init__(self, _type: str = ""):
        self._type = _type

    def emit(self, *args, **kwargs):
        logger.info(self, args, kwargs)


class TestContracts(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.evm_handler = EVMHandler()
        self.dummy = DummySignal("storage")

    def test_call(self):
        """
        Tries to create a contract which has a function that calls itself 10 times recursively.
        """
        call_contract = get_contract("Call")
        self.create_contract_and_set_address(call_contract, False)
        assert 0 == self.evm_handler.get_storage_at(call_contract.get_typed_address(), 1)
        self.evm_handler.call_contract_function(
            call_contract.get_typed_address(), "increment()", [], 0, 0, set_storage=self.dummy
        )
        assert 10 == self.evm_handler.get_storage_at(call_contract.get_typed_address(), 1)

    def test_create(self):
        """
        Tries to create a contract which internally creates another contract. The inner contract is passed a
        parameter during construction, that is queried and compared with what was passed to the outer contract.
        :return:
        """
        create_contract = get_contract("Creation")
        factory_contract = get_contract("Factory")

        self.create_contract_and_set_address(factory_contract, False)
        test_value = 65  # character 'A'
        args: [{}] = [{"type": "bytes32", "name": "name", "value": str(test_value)}]
        self.evm_handler.call_contract_function(
            factory_contract.get_typed_address(), "createContract(bytes32)", args, 0, 0,
            set_storage=self.dummy
        )

        addr = self.evm_handler.call_contract_function(factory_contract.get_typed_address(),
                                                       "getNewContractAddress()", [], 0, 0,
                                                       set_storage=self.dummy)[2].output.hex()[-40:]
        create_contract.set_address(addr)
        actual_val = int.from_bytes(
            self.evm_handler.call_contract_function(
                create_contract.get_typed_address(),
                "getName()", [], 0, 0,
                set_storage=self.dummy)[2].output,
            "little")
        assert test_value == actual_val

    def test_delegate(self):
        """
        Creates two contracts, base and front. Front delegates all calls to base. Base changes a variable in the front's
        storage. The variable is queried and checked if new value matches up with what was passed.
        :return:
        """
        base_contract = get_contract("DelegateBase")
        front_contract = get_contract("DelegateFront")
        self.create_contract_and_set_address(base_contract, False)
        self.create_contract_and_set_address(front_contract, False)

        args: [{}] = [{"type": "address", "name": "name", "value": str(base_contract.get_readable_address())}]
        self.evm_handler.call_contract_function(front_contract.get_typed_address(),
                                                "setBase(address)", args, 0, 0,
                                                set_storage=self.dummy)

        actual_value = self.evm_handler.get_storage_at(base_contract.get_typed_address(), 0)
        assert 0 == actual_value
        test_value = 3
        args: [{}] = [{"type": "uint256", "name": "name", "value": str(test_value)}]
        self.evm_handler.call_contract_function(front_contract.get_typed_address(), "setVar(uint256)", args, 0, 0,
                                                set_storage=self.dummy)
        actual_value = self.evm_handler.get_storage_at(front_contract.get_typed_address(), 0)
        assert test_value == actual_value

    # raw test data : setVar(uint256) 3a885d790000000000000000000000000000000000000000000000000000000000000003

    def test_event(self):
        """
        Creates a contract that fires an event. The logs of the receipt are read and it is asserted that they are not
        empty.
        :return:
        """
        event_contract = get_contract("Event")
        self.create_contract_and_set_address(event_contract, False)
        block, receipt, computation = self.evm_handler.call_contract_function(
            event_contract.get_typed_address(), "call()", [], 0, 0, set_storage=self.dummy
        )
        log = receipt.logs[0]
        assert log != {}

    def test_modifier(self):
        """
        Creates a contract that uses a modifier which checks whether msg.value > 1. A variable is incremented if true.
        The function is first called with a value of 1 wei which should increment the value.
        Then the function is called with a value of 0 wei which should result in an error and the value should remain 1.
        :return:
        """
        modifier_contract = get_contract("Modifier")
        self.create_contract_and_set_address(modifier_contract, False)
        actual_val = self.evm_handler.get_storage_at(modifier_contract.get_typed_address(), 0)
        assert 0 == actual_val

        self.evm_handler.call_contract_function(
            modifier_contract.get_typed_address(), "doThing()", [], 0, 1, set_storage=self.dummy
        )
        actual_val = self.evm_handler.get_storage_at(modifier_contract.get_typed_address(), 0)
        assert 1 == actual_val
        _, _, comp = self.evm_handler.call_contract_function(
            modifier_contract.get_typed_address(), "doThing()", [], 0, 0, set_storage=self.dummy
        )
        assert comp.is_error
        actual_val = self.evm_handler.get_storage_at(modifier_contract.get_typed_address(), 0)
        assert 1 == actual_val

    def test_payable(self):
        """
        Creates a payable contract and tries to send wei to it.
        :return:
        """
        payable_contract = get_contract("Payable")
        self.create_contract_and_set_address(payable_contract, True)
        _, _, computation = self.evm_handler.call_contract_function(
            payable_contract.get_typed_address(),
            "a()", [], 0, 1,
            set_storage=self.dummy
        )
        assert computation.is_success
        assert 2 == self.evm_handler.get_balance(payable_contract.get_typed_address())

    def test_selfdestruct(self):
        """
        Creates a contract with inital value of 1 wei which then selfdestructs onto address 0x00...01 whose vale is then
        asserted to be 1.
        :return:
        """
        destroy_contract = get_contract("SelfDestruct")
        self.create_contract_and_set_address(destroy_contract, True)
        assert 0 == self.evm_handler.get_balance(Address(decode_hex("0000000000000000000000000000000000000001")))
        _, _, comp = self.evm_handler.call_contract_function(
            destroy_contract.get_typed_address(), "destroy()", [], 0, 0, set_storage=self.dummy
        )
        assert comp.is_success
        assert 1 == self.evm_handler.get_balance(Address(decode_hex("0000000000000000000000000000000000000001")))

    def test_types(self):
        """
        Creates a contract which makes use of varying types in solidity.
        :return:
        """
        type_contract = get_contract("Types")
        self.create_contract_and_set_address(type_contract, False)
        assert type_contract.get_typed_address() != b''

    def create_contract_and_set_address(self, con: MyContract, with_value: bool = False):
        """
        Helper function that will create contracts.
        :param con:
        :param with_value:
        :return:
        """
        con.set_address(
            self.evm_handler.create_contract(
                con.bytecode.object, 1 if with_value else 0, 0, set_storage=self.dummy
            ).hex()
        )


def get_contract(filename: str) -> MyContract:
    targetDir = os.path.dirname(os.path.realpath(__file__)) + "/../test_contracts/output/"
    with open(targetDir + filename + ".abi", 'r') as openfile:
        _abi = openfile.read()
    with open(targetDir + filename + ".bin", 'r') as openfile:
        _bin = openfile.read()
    return MyContract(_abi, "{\"object\":\"" + _bin + "\"}")
