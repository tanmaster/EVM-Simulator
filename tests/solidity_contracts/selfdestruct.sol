pragma solidity ^0.5;

//contract to test selfdestruction

contract SelfDestruct {

    constructor() public payable {

    }

    function destroy() public {
        selfdestruct(0x0000000000000000000000000000000000000001);
    }

}