import time
from typing import Tuple

from eth import constants
from eth._utils.address import generate_contract_address
from eth.abc import BlockAPI, ReceiptAPI
from eth.consensus.pow import mine_pow_nonce
from eth.db.atomic import AtomicDB
from eth_abi import encode_abi
from eth_keys import keys
from eth_typing import Address
from eth_utils import decode_hex
from eth_utils import to_wei
from sha3 import keccak_256

from app.subcomponents.mychain import MyChain
from app.subcomponents.mycomputation import *
from app.subcomponents.myvm import MyVm
from app.util.util import MODE_NONE, json2obj

logger = logging.getLogger(__name__)

MASTER_PRIVATE_KEY = keys.PrivateKey(decode_hex('0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8'))
MASTER_ADDRESS = Address(MASTER_PRIVATE_KEY.public_key.to_canonical_address())
DEFAULT_MASTER_BALANCE = to_wei(100, 'ether')

DEFAULT_GAS_PRICE: int = 1
DEFAULT_TRANSACTION_GAS_AMOUNT: int = 1000000000

GENESIS_PARAMS = {
    'parent_hash': constants.GENESIS_PARENT_HASH,
    'uncles_hash': constants.EMPTY_UNCLE_HASH,
    'coinbase': constants.ZERO_ADDRESS,
    'transaction_root': constants.BLANK_ROOT_HASH,
    'receipt_root': constants.BLANK_ROOT_HASH,
    'difficulty': 1,
    'block_number': constants.GENESIS_BLOCK_NUMBER,
    'gas_limit': to_wei(1, 'ether'),
    'timestamp': int(time.time()),
    'extra_data': constants.GENESIS_EXTRA_DATA,
    'nonce': constants.GENESIS_NONCE
}

GENESIS_STATE = {
    MASTER_ADDRESS: {
        "balance": DEFAULT_MASTER_BALANCE,
        "nonce": 0,
        "code": b'',
        "storage": {}
    }
}


class EVMHandler:

    def __init__(self):
        klass = MyChain.configure(
            __name__='EVMSimulatorChain',
            vm_configuration=((constants.GENESIS_BLOCK_NUMBER, MyVm),)
        )
        self.used_addresses = {MASTER_ADDRESS}
        self.chain = klass.from_genesis(AtomicDB(), GENESIS_PARAMS, GENESIS_STATE)
        self.vm = self.chain.get_vm()
        self.vm.state.computation_class = MyComputation
        self.vm.get_state_class().computation_class = MyComputation
        self.seed = keccak_256(time.time().hex().encode("utf-8")).hexdigest()

    def send_wei(self, addr: bytes, value: int) -> Address:
        """
        Will send wei from the MASTER_ADDRESS to another address.
        :param addr: The receiver address of the transaction.
        :param value: The amount of wei to be sent.
        :return: The receiver address.
        """
        logger.info("Sending {v} wei to {a} ".format(v=value, a=addr.hex()))
        dbg = MyComputation.debug_mode
        MyComputation.debug_mode = MODE_NONE
        receiver = Address(addr)
        self.used_addresses.add(receiver)
        nonce = self.vm.state.get_nonce(MASTER_ADDRESS)
        block, receipt, computation = self._make_transaction(nonce, DEFAULT_GAS_PRICE, DEFAULT_TRANSACTION_GAS_AMOUNT,
                                                             receiver, value, b'')
        logger.info("Mined {b} with receipt {r}, and computation {c}".format(b=block, r=receipt,
                                                                             c=computation))
        self._mine_block()
        MyComputation.debug_mode = dbg
        return receiver

    def create_contract(self, data: str, value: int = 0, debug: int = 0, **kwargs) -> Address:
        """
        Creates a new smart contract.
        :param data: The data field. Must include constructor code in order for new contract to be created.
        :param value: The value to be sent alongside the transaction.
        :param debug: Signalizes whether the user wants the current transaction to be debugged or just send it out.
        :return: The address under which the newly created contract is located.
        """
        nonce = self.vm.state.get_nonce(MASTER_ADDRESS)
        MyComputation.debug_mode = debug
        MyComputation.kwargs = kwargs
        MyComputation.call_depth = 0
        block, receipt, computation = self._make_transaction(nonce, DEFAULT_GAS_PRICE, DEFAULT_TRANSACTION_GAS_AMOUNT,
                                                             constants.CREATE_CONTRACT_ADDRESS, value, decode_hex(data))
        logger.info("Created contract with {b}, receipt {r}, and computation {c}".format(b=block, r=receipt,
                                                                                         c=computation))
        self._mine_block()
        if computation.is_error:
            return Address(b'')
        else:
            return generate_contract_address(MASTER_ADDRESS, nonce)

    def call_contract_function(self, addr: bytes, function_signature: str, function_params: [], debug: int = 0,
                               value: int = 0, **kwargs):
        """
        Calls the function of a smart contract.
        :param addr: The address of the contract.
        :param function_signature: The signature of the function that is to be called. Example: setValue(uint256)
        :param function_params: Function params as parsed by json.
        :param debug: Signalizes whether the user wants to debug the transaction.
        :param value: Value of the transaction.
        :return:
        """
        MyComputation.debug_mode = debug
        MyComputation.kwargs = kwargs
        MyComputation.call_depth = 0
        logger.info(
            "Calling function {f} at addr {a} with params {p} and debugmode set to {d}".format(f=function_signature,
                                                                                               a=addr,
                                                                                               p=function_params,
                                                                                               d=debug))
        if function_signature == "rawdata(any)":
            data = function_params[0].get("value")
        else:
            types = []
            args = []
            for elem in function_params:
                type2: str = elem.get("type")
                if type2 == "address":
                    parsed = elem.get("value")
                elif type2 == "bool":
                    val = elem.get("value")
                    parsed = False if val in ["", "0", "false", "False", "F"] else True
                else:
                    parsed = json2obj(elem.get("value"))
                if type2.__contains__("byte"):
                    size = ''.join(list(filter(str.isdigit, type2)))
                    size = '32' if size == '' else size
                    bytesize = int(size)
                    if type(parsed) == int:
                        parsed = parsed.to_bytes(bytesize, "little")
                    elif type(parsed) == list:
                        parsed = b''.join(i.to_bytes(bytesize, "little") for i in parsed)
                types.append(type2)
                args.append(parsed)

            res = encode_abi(types, args)
            # decode_abi
            ketchup = keccak_256(function_signature.encode("utf-8")).hexdigest()
            method_id = ketchup[:8]
            logger.info("Hash of signature {s} is: {d}".format(s=function_signature, d=ketchup))

            data = method_id + res.hex()
            logger.info("Data string: {d}".format(d=data))

        #        MyComputation.debug = debug
        nonce = self.vm.state.get_nonce(MASTER_ADDRESS)
        new_block, receipt, computation = self._make_transaction(nonce, DEFAULT_GAS_PRICE,
                                                                 DEFAULT_TRANSACTION_GAS_AMOUNT,
                                                                 Address(addr), value, decode_hex(data))
        self._mine_block()
        return new_block, receipt, computation

    def get_balance(self, addr: bytes) -> int:
        """
        Gets the balance of an address.
        :param addr: Address to query the balance of.
        :return: The address balance.
        """
        return self.vm.state.get_balance(Address(addr))

    def get_block_number(self) -> int:
        """
        :return: The current block number.
        """
        return self.vm.get_block().number

    def get_code(self, addr: bytes) -> bytes:
        """
        Gets the code of an address. We can distinguish between normal addresses and smart contracts
        by looking if the code is equal to b'', in which case it is a normal address, or anything else which
        means that <param>addr</param> holds a smart contract.
        :param addr: Address to query the code of.
        :return: The address code.
        """
        return self.vm.state.get_code(Address(addr))

    def get_storage_at(self, addr: Address, slot: int) -> int:
        """
        :param addr: Address of smart contract.
        :param slot: Slot of storage to query.
        :return: The value in storage slot at the given address.
        """
        return self.vm.state.get_storage(address=addr, slot=slot)

    def set_balance(self, addr: Address, balance: int):
        """
        Sets the balance of an address.
        :param addr: The address to set the balance of
        :param balance: The balance to set the address to in wei.
        :return:
        """
        self.vm.state.set_balance(addr, balance)
        self._mine_block_dirty()

    def set_code(self, code: bytes, addr: Address = Address(b'')) -> Address:
        """
        Sets the code of an address.
        :param addr: The address to set the code of.
        :param code: The code to set. This should not be constructor bytecode.
        :return:
        """
        if addr == Address(b''):
            addr = self.get_random_address()
        self.vm.state.set_code(addr, code)
        self._mine_block_dirty()
        return addr

    def set_storage(self, addr: Address, slot: int, value: int):
        """
        Note that this function will not check whether the address you want to set the storage of is an actual contract
        or not.
        :param addr: The address to set the storage of.
        :param slot: The slot to set the value of.
        :param value: The value to set.
        :return:
        """
        self.vm.state.set_storage(addr, slot, value)
        self._mine_block_dirty()

    def _make_transaction(self, nonce: int, gas_price: int, gas: int, to: Address, value: int, data: bytes) \
            -> Tuple[BlockAPI, ReceiptAPI, ComputationAPI]:
        """
        Helper function to send out a transaction.
        :param nonce: Current nonce of master address.
        :param gas_price: Gas price to set.
        :param gas: Gas to use.
        :param to: Recipient address.
        :param value: Value in wei.
        :param data: Data field.
        :return: The Transaction receipt tuple as it is returned by the apply_transaction() function.
        """
        tx = self.vm.create_unsigned_transaction(
            nonce=nonce,
            gas_price=gas_price,
            gas=gas,
            to=to,
            value=value,
            data=data
        )
        signed_tx = tx.as_signed_transaction(MASTER_PRIVATE_KEY)
        return self.chain.apply_transaction(signed_tx)

    def _mine_block_dirty(self):
        """
        Mines a block <dirty> which means basically that block header validation is omitted. This gives us the ability
        to change the state of the vm at will (like changing an addresses' code) and still being able to <mine> the next
        block. Since the application is not being executed in a trustless environment, and the EVM is actually only
        needed for debugging purposes, this does not make a difference at all.
        :return:
        """
        self.chain.mine_block(mix_hash=b'', nonce=b'', current_vm=self.vm)
        self.vm = self.chain.get_vm()
        self.vm.state.computation_class = MyComputation
        self.vm.get_state_class().computation_class = MyComputation

    def _mine_block(self):
        """
        Mines a new block with everything that needs to be done. The computation classes reset with every
        block that is mined, so they are set again within this function.
        :return:
        """
        block = self.chain.get_vm().finalize_block(self.chain.get_block())
        nonce, mix_hash = mine_pow_nonce(
            block.number,
            block.header.mining_hash,
            block.header.difficulty
        )
        self.chain.mine_block(mix_hash=mix_hash, nonce=nonce)
        logger.info("Mined block {no} with nonce {n} and hash {h}".format(no=block.number,
                                                                          n=int.from_bytes(nonce, "big", signed=False),
                                                                          h=mix_hash.hex()))
        self.vm = self.chain.get_vm()
        self.vm.state.computation_class = MyComputation
        self.vm.get_state_class().computation_class = MyComputation

    def get_random_address(self) -> Address:
        addr = Address(decode_hex(self.seed[:40]))
        self.seed = keccak_256(self.seed.encode("utf-8")).hexdigest()
        return addr

    @staticmethod
    def get_gas_price() -> int:
        return DEFAULT_GAS_PRICE

    @staticmethod
    def get_gas_limit() -> int:
        return DEFAULT_TRANSACTION_GAS_AMOUNT
