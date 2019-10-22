pragma solidity ^0.5;

/*
    Used to test if payable contracts work as expected.
*/
contract Payable {

    constructor()public payable{

    }

    function() payable external {

    }

}
