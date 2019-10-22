//pragma experimental ABIEncoderV2;
pragma solidity ^0.5;

/*
	Will make 10 recursive calls to itself. Used to check whether call depth etc. is represented correctly.

*/

contract Call{
    Call public con;
    uint public ctr;

    constructor()public{
        con = Call(address(this));
    }

    function increment() public{
        if (ctr < 10){
            ctr += 1;
            con.increment();
        }
    }

}
