from typing import Any

from eth.abc import BlockAPI
from eth.vm.forks import IstanbulVM


class MyVm(IstanbulVM):
    def mine_block(self, *args: Any, **kwargs: Any) -> BlockAPI:
        """
        Overrides _mine_block in IstanbulVM. Please note that using this class means that block headers will not get
        validated and that invalid blocks can be mined. This is intentional and the actual purpose of this class.
        """
        packed_block = self.pack_block(self.get_block(), *args, **kwargs)
        final_block = self.finalize_block(packed_block)

        return final_block
