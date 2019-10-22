//pragma experimental ABIEncoderV2;
pragma solidity ^0.5;

/*
	Used to test if parameter/type passing is working correctly.

*/

contract Types {
    bool public boolean;
    int8 public integer8;
    int public integer;
    uint8 public uinteger8;
    uint public uinteger;
    address public addr;
    byte public byte_1;
    bytes2 public bytes_2;
    bytes32 public bytes_32;
    bytes public bytes_;
    string public string_;
    enum Enums {One, Two, Three, Four}
    Enums enum_;
    uint[] uints;
    bool[2][] m_pairsOfFlags;
    mapping(address => uint) public map;

    constructor() public{
    }

    function setBoolean(bool _val) public {
        boolean = _val;
    }

    function setInt8(int8 _val) public {
        integer8 = _val;
    }

    function setInt(int _val) public {
        integer = _val;
    }

    function setUint8(uint8 _val) public {
        uinteger8 = _val;
    }

    function setUint(uint _val) public {
        uinteger = _val;
    }

    function setAddress(address _val) public {
        addr = _val;
    }

    function setByte(byte _val) public {
        byte_1 = _val;
    }

    function setBytes2(bytes2 _val) public {
        bytes_2 = _val;
    }

    function setBytes32(bytes32 _val) public {
        bytes_32 = _val;
    }

    function setBytes(bytes memory _val) public {
        bytes_ = _val;
    }

    function setEnum(Enums _val) public {
        enum_ = _val;
    }

    function setOneIntegerInArray(uint _val) public {
        uints.push(_val);
    }

    function setAllFlagPairs(bool[2][] memory newPairs) public {
        // assignment to a storage array replaces the complete array
        m_pairsOfFlags = newPairs;
    }

    function setFlagPair(uint index, bool flagA, bool flagB) public {
        // access to a non-existing index will throw an exception
        m_pairsOfFlags[index][0] = flagA;
        m_pairsOfFlags[index][1] = flagB;
    }

    function setOneMapping(address _addr, uint _val) public {
        map[_addr] = _val;
    }

    function setString(string memory _val) public {
        string_= _val;
    }


    function getBoolean() public view returns (bool){
        return boolean;
    }

    function getInt8() public view returns (int8){
        return integer8;
    }

    function getInt() public view returns (int){
        return integer;
    }

    function getUint8() public view returns (uint8){
        return uinteger8;
    }

    function getUint() public view returns (uint){
        return uinteger;
    }

    function getAddress() public view returns (address){
        return addr;
    }

    function getByte() public view returns (byte){
        return byte_1;
    }

    function getBytes2() public view returns (bytes2){
        return bytes_2;
    }

    function getBytes32() public view returns (bytes32){
        return bytes_32;
    }

    function getBytes() public view returns (bytes memory){
        return bytes_;
    }

    function getEnum() public view returns (Enums){
        return enum_;
    }

    function getOneIntegerInArray(uint index) public view returns (uint){
        return uints[index];
    }

    function getUintArray() public view returns (uint[] memory){
        return uints;
    }

    function getAllFlagPairs() public view returns (bool[2][] memory){
        return m_pairsOfFlags;
    }

    function getFlagPair(uint index) public view returns (bool[2] memory) {
        // access to a non-existing index will throw an exception
        return m_pairsOfFlags[index];
    }

    function getOneMapping(address _addr) public view returns (uint){
        return map[_addr];
    }

    function getString() public view returns(string memory){
        return string_;
    }

}
