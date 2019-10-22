pragma solidity ^0.5;

// used to test if delegate call contracts work as expected

contract DelegateBase {
    uint public checkVar;

    constructor() public {
        checkVar = 0;
    }

    function setVar(uint _new) public {
        checkVar = _new;
    }
}

contract DelegateFront {
    uint public checkVar;
    address public baseImplementation;

    constructor() public {
    }

    function setBase(address _baseImplementation) public {
        baseImplementation = _baseImplementation;
    }

    function() payable external {
        (bool success,) = baseImplementation.delegatecall(msg.data);
        if(!success) {
          revert();
        }
    }
}