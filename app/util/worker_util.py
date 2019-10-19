import logging

from PyQt5.QtCore import pyqtSlot, QObject, pyqtSignal, QRunnable
from eth.abc import CodeStreamAPI, MessageAPI
from eth_abi.exceptions import ValueOutOfBounds, EncodingTypeError
from eth_utils import ValidationError

from app.util.changes import ChangeChain

logger = logging.getLogger(__name__)


class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread. Used signals are:

    add_chain:
        The underlying worker thread will emit this signal to send a new ChangeChain object to the main thread.
    pre_computation:
        The underlying worker thread will emit this signal sending information about remaining gas and the current
         program counter (pc).
    post_computation:
        The worker thread will emit this signal sending the current stack, memory, program counter and previously used
        gas.
    init_debug_session:
        The worker emits a signal containing the code stream object which contains all the bytecode to be executed;
        a dictionary to lookup opcodes and their corresponding mnemonic amongst other things;
        a MessageAPI object that contains every relevant message related data.
    set_storage = pyqtSignal(bytes, str, str):
        A signal that tells the main thread to set the storage at a given address and slot to a given value.
    contract_created = pyqtSignal(bytes)
        A signal that tells the main thread that a contract has been created and returns its adress.
    transaction_sent = pyqtSignal()
        A signal that tells the main thread that a transaction has been sent successfully.
    abort_transaction = pyqtSignal()
        A signal that tells the main thread that the currently debugged transaction has been aborted.
    error = pyqtSignal(str)
        Error signal

    """
    add_chain = pyqtSignal(ChangeChain)
    pre_computation = pyqtSignal(int, int)
    post_computation = pyqtSignal(list, bytearray, int, int)
    init_debug_session = pyqtSignal(CodeStreamAPI, dict, MessageAPI)
    set_storage = pyqtSignal(bytes, str, str)
    contract_created = pyqtSignal(bytes)
    transaction_sent = pyqtSignal()
    abort_transaction = pyqtSignal()
    error = pyqtSignal(str)
    result = pyqtSignal(object)


class BaseWorker(QRunnable):
    """
        Worker thread

        Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

        :param callback: The function callback to run on this worker thread. Supplied args and
                         kwargs will be passed through to the runner.
        :type callback: function
        :param args: Arguments to pass to the callback function
        :param kwargs: Keywords to pass to the callback function

        """

    def __init__(self, fn, *args, **kwargs):
        """
        Constructor for every worker. All workers follow the same principles:
        :param fn: This is the function to be called by the worker.
        :param args: The (non-keyword) arguments that will be passed into fn.
        :param kwargs: Keyword arguments that contain necessary data for the execution of fn. The constructor also adds
                        the workers signals to the kwargs object.
        """
        super(BaseWorker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.kwargs['pre_computation'] = self.signals.pre_computation
        self.kwargs['post_computation'] = self.signals.post_computation
        self.kwargs['init_debug_session'] = self.signals.init_debug_session
        self.kwargs['add_chain'] = self.signals.add_chain
        self.kwargs['set_storage'] = self.signals.set_storage
        self.kwargs['contract_created'] = self.signals.contract_created
        self.kwargs['transaction_sent'] = self.signals.transaction_sent
        self.kwargs['abort_transaction'] = self.signals.abort_transaction
        self.kwargs['error'] = self.signals.error
        self.kwargs['result'] = self.signals.result


class TransactionWorker(BaseWorker):
    """
    Worker used to handle transactions.
    """

    @pyqtSlot()
    def run(self):
        """
        Initialise the runner function with passed args, kwargs.
        """
        logger.info(
            "Running new TransactionWorker thread with: {fn}, {a}, {k}".format(fn=self.fn, a=self.args, k=self.kwargs))
        try:
            _, _, computation = self.fn(*self.args, **self.kwargs)
            self.signals.result.emit(computation.output)
            self.signals.transaction_sent.emit()
        except (ValueError, OverflowError, ValidationError, ValueOutOfBounds, EncodingTypeError) as e:
            self.signals.error.emit(str(e))


class ContractWorker(BaseWorker):
    """
    Worker used to handle contract creations.
    """

    @pyqtSlot()
    def run(self):
        logger.info(
            "Running new ContractWorker thread with: {fn}, {a}, {k}".format(fn=self.fn, a=self.args, k=self.kwargs))
        try:
            con = self.fn(*self.args, **self.kwargs)
            self.signals.contract_created.emit(con)
        except (ValueError, OverflowError, ValidationError, ValueOutOfBounds, EncodingTypeError) as e:
            self.signals.error.emit(str(e))
