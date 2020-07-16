# EVM-Simulator
<img align="right" width="100" height="100" alt="App Icon" src="app/icon.png">

This project was created during the course of a Bachelor's Thesis at the Vienna University of Technology. Its goal is to
provide the ability to observe the effects of transactions within the Ethereum Virtual Machine during their execution 
time.

The current landscape of Smart Contract development is one that does not truly enable developers to debug transactions 
comprehensibly during execution time, and while some debuggers like [Remix](http://remix.ethereum.org) or
[EVM.Debugger](https://hexdocs.pm/evm/EVM.Debugger.html) and 
[a GUI implementation of it](https://github.com/xJonathanLEI/EVMDebugger) exist, and all of them do their job well, 
there is no debugging tool available that features:

- A comprehensible GUI,
- the possibility to view transactions during execution time, before being mined,
- loading contracts without ABI,
- supports external calls and
- platform independence*

<sup>*See [Known Issues](#known-issues)</sup>

EVM-Simulator aims to resolve these issues. Using a GUI, users can load contracts and interact with them by sending
transactions, either by using a predefined ABI or raw, while following the resulting changes step-by-step. It makes use 
of [py-evm](https://github.com/ethereum/py-evm) as main component, which is a well-known and proven python 
implementation of the EVM and is essentially used to emulate the Ethereum Blockchain. 


## Quickstart
Here are some platform specific instructions on how to setup further necessary packages as well as the virtual 
environment:

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

Afterwards you can install EVM-Simulator on either platform by following these steps:
#### Installing and Running EVM-Simulator
```shell script
git clone https://github.com/tanmaster/EVM-Simulator.git
cd EVM-Simulator/

virtualenv -p python3 venv
. venv/bin/activate

# install dependencies
pip3 install -e .

# run tests with
pytest tests/

# run the application
python app/main.py
```

#### Used Dependencies
These are the external dependencies which the project relies on, taken from [setup.py](setup.py):

    "eth-utils>=1,<2",
    "py-evm==0.3.0a5",
    "PyQt5==5.13.1",
    "eth-abi==2.0.0",
    "pysha3==1.0.2",
    "pytest>=4.4.0",

    
## Usage
![Screenshot of EVM-Simulator](docs/screenshot_macos.png?raw=true "EVM-Simulator on macOS")

The above image shows what the program looks like while debugging a transaction. As you can see, most of the relevant 
information about the execution environment as well as the world state is represented in real-time.

If you are new to the world of smart contracts, and want to learn more about some of the terminology used, you might 
want to head over to the [Basics Section](docs/basics.md) first.

### Loading a contract
The first thing to do when using EVM-Simulator is to load a contract. Currently, there are two different ways to do so. 
You can either:
- Load a contract with known ABI and Constructor bytecode or
- Load a with unknown ABI, only knowing the bytecode of (the already deployed) contract. You might find this useful when 
trying to debug contracts from any other Ethereum Blockchain, which you don't know the source code of.

Note that when using the latter option, you will lose the ability to select a contract's function. Much rather you will 
have to enter the raw input data, which you will have to compute yourself. Please see the bottom of this section for more 
information on this matter.

Using the first option, you might notice that the expected input formats of ABI and bytecode are exactly the same as the 
output formats you would get if you'd compile a contract in [Remix](http://remix.ethereum.org). If you load a contract 
this way, you gain the ability to select a function you want to call alongside its parameters, instead of painstakingly
having to create the input data yourself.

Regardless of which method you use to load a contract, you will always have the option to send arbitrary raw data 
alongside a transaction.

### Sending a Transaction
If you have loaded a contract and filled in the parameters or the raw data field, the next thing to do (before clicking 
send transaction) is to specify the debug mode. There are two options:
- If you are in debug mode only, you will need to click through a transaction's execution steps one by one. However you 
can also specify the amount of steps to do at once. 
- If you do not feel like stepping through the execution manually (by clicking on step), you can also tick the
Auto Mode checkbox. For this you can also specify a stepping duration, a timespan for which the program will pause 
in between each step.

Either way, you can always abort a transaction's execution (the storage changes made thus far will stay) if you made a 
mistake or don't want to sit through the execution.

#### Notes on Input Format
I tried to validate the input wherever I could, however there could still be some possibility that the program crashes
on unexpected input. To prevent this, please refrain from providing data that is likely to be unexpected by the program.
The placeholder texts usually give away which format is expected in most input fields. Concerning function input 
arguments, JSON-like notation is safe to use:
- Numeric values can be entered as is e.g: 1
- Strings should be enclosed by double quotation marks e.g.: "This is a string!"
- Arrays should be enclosed by square brackets: [0, 1, 2, 3]
- Addresses can be passed like this: 0xaffe... (40 characters long hex string)
- Raw data can be passed as is. For example if you wanted to call a function "setVar" which takes a uint256 as only 
argument, and the integer 3 as its value, you would enter the following into the text input: 
3a885d790000000000000000000000000000000000000000000000000000000000000003

## Known Issues
- Unfortunately EVM-Simulator cannot currently be run on Windows. The reason is missing support for one of py-evm's 
libraries. [See here](https://github.com/ethereum/py-evm/issues/395) for more information.
- The block validation feature of py-evm is disabled since EVM-Simulator relies on being able to arbitrarily change the
world state. However this shouldn't be an issue since a) the user imposes the changes himself and b) 
we do not have to deal with non-trusted parties c) there is no real monetary value behind in the underlying chain.
- When using different call opcodes, storage might display old values sometimes until the transaction is finished.
- Getting refunds from freeing used storage is currently not displayed correctly.
- For specific opcodes (e.g. SSTORE), the gas cost might be shown incorrectly (most likely as zero) until after its 
execution.

## Some Thoughts
The main challenge I had to face during implementation was finding out how to hook into py-evm during computation
time. In order to increase the maintainability and modularity of EVM-Simulator, I spent quite some time trying to look 
for a way to make use of py-evm without making my own version of it, but rather using it as dependency, only swapping 
out necessary components during runtime. However, thanks to its modularity, I was eventually able inject my custom 
classes, overriding relevant functions, which again enabled me to read out state variables and transaction properties 
during the execution time of a contract.

After having overcome these issues, the rest of the work consisted of making the GUI, setting up communication between 
the GUI thread and the worker thread, testing the functionality of the evmhandler using some custom contracts, as well
as testing the GUI.

Since this was my first larger-sized project using python (and PyQt for the GUI), the code quality might not be on par 
with what the makers of py-evm have created. I'm especially unhappy about the main GUI controller file, which I find 
extremely bloated and might be subject to future refactoring.

## Acknowledgment
Special thanks go out to [Lukas](https://github.com/lukas-hetzenecker), who helped me overcome initial obstacles and 
pointed me in the right direction.

This project was initially forked from [Template for new Python Ethereum repositories](https://github.com/ethereum/ethereum-python-project-template).

Thanks to Lee Thomas for his graphic [Ethereum Blockchain Mechanism](https://github.com/4c656554/BlockchainIllustrations/blob/master/Ethereum/EthBlockchain5.svg).

## Useful Links
- [How To Decipher A Smart Contract Method Call](https://medium.com/@hayeah/how-to-decipher-a-smart-contract-method-call-8ee980311603)
- [Keccak-256 online hash function](https://emn178.github.io/online-tools/keccak_256.html)
- [Ethereum Virtual Machine Opcodes](https://ethervm.io/)
- [Online Solidity Decompiler](https://ethervm.io/decompile)
- [Building an app that uses Py-EVM](https://py-evm.readthedocs.io/en/latest/guides/building_an_app_that_uses_pyevm.html)
