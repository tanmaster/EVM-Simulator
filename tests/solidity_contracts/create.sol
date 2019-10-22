
//Used to test if contracts creating other contracts is working as expected.
pragma solidity ^0.5;

contract Factory {
    Creation public con;

    constructor() public{}

    function createContract(bytes32 name) public {
        con = new Creation(name);
    }

    function getConName() public view returns(bytes32){
        return con.getName();
    }

    function getNewContractAddress() public view returns(address){
        return address(con);
    }
}

contract Creation {
    bytes32 public name;

    constructor(bytes32 _name) public{
        name = _name;
    }

    function getName() public view returns(bytes32){
        return name;
    }
}
