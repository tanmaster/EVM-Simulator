# EVM-Simulator Basics & Terminology

## Account
An Account is basically an Address in the EVM Blockchain. Just like IRL, a person can only transfer
value from an account A to another account B if he is the rightful owner of A. 
## Balance
Every Account comes with a balance. Accounts that have never been interacted with (should) have a balance of 0.
There are several ways to increase the balance of an account, the simplest being just sending Ether to it from another 
account. In EVM-Simulator, there exists the possibility to set the balance without using a transaction. However, this 
means that we are handling a Blockchain which is no longer a valid chain, since blocks with invalid headers are being 
mined.

## Contract
A contract is an account under which additional code is stored. Transactions that are sent to a contract will trigger 
the execution of this code, and depending on the data that is sent along a transaction, different parts of the code gets
processed.

## Storage
Every contract possesses a storage under which data can be persisted. The operation of storing data is a lot more 
expensive than other operations, mostly because in a real world block chain application the storage needs to be mirrored
on every node, and thus comes with permanent costs for each miner. 

The storage is segmented into slots and values. When using solidity, the order of which variable is stored under in 
which slot is defined by the order of occurrence in the contract's source code. While this is straight forward when 
using 256-bit sized data, it gets more complex when using smaller sized data (e.g. it's possible to store two 128-bit values
under one slot to save storage), mappings, arrays, or strings.

## Transactions and Messages
A transaction isn't just a transaction in the financial sense, but in logical way, which means that either the 
transaction is executed and the resulting state is stored entirely, or the changes are dismissed.
Each transaction comes with the following attributes:

### Origin
The original account that has triggered this transaction.
### Sender
The sender of a transaction. This value can differ from origin e.g. when you call a contract function that triggers 
another transaction.
### To
The target address of a transaction. When using EVM-Simulator, and this address is being shown as 0x0, it means that the 
currently shown transaction is in the process of creating a contract.
### Value
The amount of wei that a transaction holds.
### Data
The data field needs to be specified e.g. when you want to call a contract's function.
### Call depth
This property shows the depth of the current call. Whenever a contract makes further calls internally, this value gets 
incremented by one. 
### Gas Price
Specifies the price for 1 gas in wei.
### Gas Limit
Specifies how much gas to send alongside a transaction. 
### Program Counter
The program counter shows how far the execution of a transaction is. It points to the bytecode instruction
of a contract's code that is currently being executed. 
## EVM-Simulator GUI
![Screenshot of EVM-Simulator](screenshot_ubuntu.png?raw=true "EVM-Simulator on Ubuntu")
### Opcodes Table
Shows the contract's entire code, alongside the mnemonic name and gas cost estimate inside a table. 
### Stack Table
Shows the stack of the current execution context. Since the EVM is a stack machine, and most opcodes interact with the 
stack in a certain way, the relevant stuff is most likely to happen here.
### Memory Table
Shows the memory of the current execution context. The memory is a separate area in which a contract can read and write 
data during a transaction's execution data, however the memory's content is not persisted.
### Storage Table
The storage of the currently shown contract. Note that storage slots are only watched at (and shown in the table) after 
their first occurrence in a computation. Until that point every slot's value is assumed to be zero.
### Used Addresses Table
Shows the currently used addresses and whether they're an account or a contract.






