from unittest import TestCase
from app.evmhandler import *
from eth.constants import ZERO_ADDRESS
from eth_typing import Address
from eth_utils.units import units

SAMPLE_CONTRACT_STRING = "608060405234801561001057600080fd5b506084600081905550610103806100286000396000f3fe6080604052348015600f57600080fd5b50600436106059576000357c0100000000000000000000000000000000000000000000000000000000900480630dbe671f14605e5780633fb5c1cb146066578063d811a0f7146091575b600080fd5b606460ad565b005b608f60048036036020811015607a57600080fd5b810190808035906020019092919050505060bb565b005b609760c5565b6040518082815260200191505060405180910390f35b600160005401600081905550565b8060008190555050565b6000805490509056fea265627a7a72315820dbbf7b3aca69db108502547c9d52106e90b87b1f8e80c1538e2bd9131dde542864736f6c634300050b0032"


class TestEVMHandler(TestCase):

    def setUp(self) -> None:
        super().setUp()
        self.evm_handler = EVMHandler()

    def test_send_wei_and_get_balance_and_set_balance(self):
        """
        Tries to set the balance of a contract with 1) normal transactions and 2) dirtily by setting the value and
        omitting block validation. The actual value is compared with the expected
        :return:
        """
        addr1 = Address(decode_hex("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"))
        addr2 = Address(decode_hex("bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"))
        addr3 = Address(decode_hex("9742421b7279129e6791e67921d9787df9779fa7"))
        assert 0 == self.evm_handler.get_balance(addr1)
        assert 0 == self.evm_handler.get_balance(addr2)
        assert 0 == self.evm_handler.get_balance(addr3)
        self.evm_handler.send_wei(addr1, to_wei(20, "finney"))
        self.evm_handler.send_wei(addr2, to_wei(30, "ether"))
        self.evm_handler.send_wei(addr3, to_wei(10, "wei"))
        assert units.get("finney") * 20 == self.evm_handler.get_balance(addr1)
        assert units.get("ether") * 30 == self.evm_handler.get_balance(addr2)
        assert units.get("wei") * 10 == self.evm_handler.get_balance(addr3)
        self.evm_handler.set_balance(addr1, 0)
        self.evm_handler.set_balance(addr2, 0)
        self.evm_handler.set_balance(addr3, 0)
        assert 0 == self.evm_handler.get_balance(addr1)
        assert 0 == self.evm_handler.get_balance(addr2)
        assert 0 == self.evm_handler.get_balance(addr3)

    def test_set_code_and_get_code(self):
        """
        Tries setting the code section of an address dirtily by omitting block validation.
        :return:
        """
        addr1 = Address(decode_hex("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"))
        code = decode_hex(SAMPLE_CONTRACT_STRING)
        self.evm_handler.set_code(code, addr1)
        actual = self.evm_handler.get_code(addr1)
        assert code == actual

    def test_set_storage_and_get_storage(self):
        """
        Tries setting the storage of a contract dirtily by omitting block validation.
        :return:
        """
        addr1 = Address(decode_hex("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"))
        val = 1
        self.evm_handler.set_storage(addr1, 0, val)
        actual = self.evm_handler.get_storage_at(addr1, 0)
        assert val == actual

    def test__mine_block_and_get_block_number(self):
        """
        Tries to mine a block and checks whether the correct block number is returned.
        :return:
        """
        genesis = self.evm_handler.get_block_number()
        assert genesis == 1
        self.evm_handler._mine_block()
        second = self.evm_handler.get_block_number()
        assert second == 2
