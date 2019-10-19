pragma solidity ^0.5;

//test contract to check if modifiers work

contract Modifier {
    uint public value;

    modifier correctData(){
        require(msg.value > 0);
        _;
    }
    constructor()public{
    }

    function doThing() public payable correctData {
        value = value + 1;
    }


}