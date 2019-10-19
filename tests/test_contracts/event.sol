pragma solidity ^0.5;

//used to test if events work
contract Event{

    event Created();
    event CalledBy(address indexed caller);

    constructor() public {
        emit Created();
    }

    function call() public  {
        emit CalledBy(msg.sender);
    }
}
