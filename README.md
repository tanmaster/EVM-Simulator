# EVM-Simulator

This project was created during the course of a Bachelor's Thesis at the Vienna University of Technology. Its goal is to
provide the ability to observe the effects of transactions within the Ethereum Virtual Machine during their execution 
time.

The current landscape of Smart Contract development is one that does not truly enable developers to debug transactions 
during execution, and aside from [Remix](http://remix.ethereum.org), there is no mainstream debugging tool 
available. While the Remix debugger does it's job well, it does not provide means to debug contracts of which the source
code is unknown, and furthermore, it also isn't possible to debug transactions while they're being processed, but only
after they have been mined. 

EVM-Simulator aims to resolve these issues. Using a simple GUI, users can load contracts and interact with them by sending
transactions, either by using a predefined ABI or raw, while following the resulting changes step-by-step. It is built 
on top of [py-evm](https://github.com/ethereum/py-evm), a well-known and widespread python implementation of the EVM, 
which is basically used to simulate an Ethereum Blockchain. 

In order to be able to read out the state variables and the world state during the execution time of a contract, it was
necessary to swap out some of the modules that are used by py-evm. Thanks to the modularity of it, injecting custom 
classes and overriding relevant functions was possible without much effort. 

The project was initially forked from 


## Quickstart
Here are some OS specific instructions on how to setup further necessary packages as well as the virtual environment:
#### macOS
```shell script
# using homebrew:
brew install python3
pip3 install virtualenv
```

#### Ubuntu
```shell script
# using apt-get 
sudo apt-get install python3
sudo apt-get install python3.6-dev
sudo apt-get install python3-pip
sudo apt-get install virtualenv
```

#### Installing and Running EVM-Simulator
```shell script
git clone https://github.com/tanmaster/EVM-Simulator.git
cd EVM-Simulator/

virtualenv -p python3 venv
. venv/bin/activate

pip install -e .[dev]
# running the application
python app/main.py
```

    
## Usage

![Screenshot of EVM-Simulator](screenshot.png?raw=true "EVM-Simulator on macOS")

The above image shows what the program looks like while debugging a transaction. As you can see, the most relevant 
information about the execution environment as well as the world state is represented in real-time.

The first thing to do when using EVM-Simulator is to load a contract. Currently, there are two different ways to do so. 
You can either:
- Load a contract with known ABI and Constructor bytecode or
- Load a with unknown ABI, only knowing the bytecode of (the already deployed) contract. You might find this useful when 
trying to debug contracts from any other Ethereum Blockchain, which you don't know the source code of.

Note that when using the latter option, you will lose the ability to select a contract's function. Much rather you will 
have to enter the raw input data, which you will have to compute yourself. Please see the bottom of this page for more 
resources on this matter.

Using the first option, you might notice that the expected format is exactly the same as the output formats you would get
if you'd compile a contract in [Remix](http://remix.ethereum.org). If you load a contract like this, you get the 
possibility be able to select which function you want to call alongside its parameters.

Regardless of which method to use to load a contract, you will always have the possibility to send arbitrary raw data 
alongside a transaction.

#### Notes on Input Format
I tried to validate the input wherever I could, however there could still be some possibility that the program crashes
on unexpected input. To prevent this, please refrain from providing data that is likely to be unexpected by the program.
The placeholder texts usually give away which format is expected in most input fields. Concerning function input 
arguments, JSON-like notation is expected:
- Numeric values can be entered as is e.g: 1
- Strings should be enclosed by double quotation marks e.g.: "This is a string!"
- Arrays should be enclosed by square brackets: [0, 1, 2, 3]
- Addresses can be passed as like this: 0xaffe... (40 characters long hex string)
- Raw data can be passed as is. For example if you wanted to call a function "setVar" which takes a uint256 as only 
argument, and the integer 3 as its value, you would enter the following into the text input: 
3a885d790000000000000000000000000000000000000000000000000000000000000003

#### Known Issues
- Unfortunately EVM-Simulator can currently not be run on Windows. The reason is missing support for a library for py-evm.
 [See here](https://github.com/ethereum/py-evm/issues/395) for more information.
- The block validation feature of py-evm is disabled since EVM-Simulator relies on being able to arbitrarily change the
world state. However this shouldn't be an issue since a) the user imposes the changes himself and b) 
we do not have to deal with non-trusted parties c) there is no real monetary value behind in the underlying chain.
- When using different call opcodes, storage might display old values sometimes until the transaction is finished.
- Getting refunds from freeing used storage is currently not displayed correctly.

#### Used Dependencies
    "eth-utils>=1,<2",
    "py-evm==0.3.0a5",
    "PyQt5==5.13.1",
    "eth-abi==2.0.0",
    "pysha3==1.0.2",
    "pytest>=4.4.0",
    
#### Useful Links
- [How To Decipher A Smart Contract Method Call](https://medium.com/@hayeah/how-to-decipher-a-smart-contract-method-call-8ee980311603)
- [Keccak-256 online hash function](https://emn178.github.io/online-tools/keccak_256.html)
- [Ethereum Virtual Machine Opcodes](https://ethervm.io/)
- [Online Solidity Decompiler](https://ethervm.io/decompile)
