from typing import Any

from eth.abc import BlockAPI
from eth.chains.base import MiningChain


class MyChain(MiningChain):
    def mine_block(self, *args: Any, **kwargs: Any) -> BlockAPI:
        """
        Overrides _mine_block in MiningChain. Please note that using this class means that block headers will not get
        validated and invalid blocks can be mined. This is intentional and the actual purpose of this class.
        """

        my_vm = kwargs.get("current_vm")
        if my_vm is not None:
            kwargs.pop("current_vm")
            mined_block = my_vm.mine_block(*args, **kwargs)
        else:
            mined_block = self.get_vm(self.header).mine_block(*args, **kwargs)

        self.chaindb.persist_block(mined_block)
        self.header = self.create_header_from_parent(mined_block.header)
        return mined_block
