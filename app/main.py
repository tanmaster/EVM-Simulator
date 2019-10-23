import json
import logging
import sys
from types import FunctionType
from typing import Dict, Any
from threading import Lock
from PyQt5.QtCore import *
from PyQt5.QtGui import QDesktopServices, QFont, QBrush, QColor, QIcon
from PyQt5.QtWidgets import *
from eth.abc import CodeStreamAPI, OpcodeAPI, MessageAPI
from eth.validation import validate_canonical_address
from eth.vm.logic.invalid import InvalidOpcode
from eth_typing import Address
from eth_utils import ValidationError, decode_hex, encode_hex
from eth_utils.units import units

from app import evmhandler
from app.util.changes import ChangeChainLink, TableWidgetEnum, ChangeChain, History
from app.evmhandler import EVMHandler, MASTER_ADDRESS
from app.subcomponents.mycomputation import MyComputation
from app.util.workers import TransactionWorker, ContractWorker, BaseWorker
from app.ui.ui_add_addresses import Ui_AddAdressesDialog
from app.ui.ui_add_contract import Ui_AddContractDialog
from app.ui.ui_main import Ui_MainWindow
from app.ui.ui_set_gas_limit import Ui_SetGasLimitDialog
from app.ui.ui_set_gas_price import Ui_SetGasPriceDialog
from app.ui.ui_set_storage import Ui_set_storage_dialog
from app.util.util import MyContract, MyTransaction, hex2, MyAddress
import operator

logger = logging.getLogger(__name__)


class ApplicationWindow(QMainWindow):

    def __init__(self):
        super(ApplicationWindow, self).__init__()
        self.evm_handler = EVMHandler()

        logger.info("Prettify UI.")
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.actionAddress_Balance.triggered.connect(self.show_set_balance_dialog)
        self.ui.actionContract.triggered.connect(self.show_set_contract_dialog)
        self.ui.actionSet_Gas_Limit.triggered.connect(self.show_set_gas_limit_dialog)
        self.ui.actionSet_Gas_Price.triggered.connect(self.show_set_gas_price_dialog)
        self.ui.actionStorage.triggered.connect(self.show_set_storage_dialog)
        self.relevant_addresses = {}
        self.blockLabel = QLabel()
        self.statusLabel = QLabel()
        self.statusBar().addPermanentWidget(self.blockLabel)
        self.statusBar().addWidget(self.statusLabel)
        self._refresh_statusbar()
        self.ui.select_address_combobox.currentIndexChanged.connect(self.contract_selected)
        self.ui.select_function_combobox.currentIndexChanged.connect(self.contract_function_selected)
        self.ui.send_transaction_button.clicked.connect(self.send_transaction_clicked)
        self.ui.select_function_combobox.hide()
        self.ui.used_addresses_table_widget.setColumnWidth(0, 200)
        self.ui.used_addresses_table_widget.setColumnWidth(1, 100)
        self.ui.used_addresses_table_widget.setColumnWidth(2, 69)
        self.ui.storage_table_widget.hide()
        self.ui.execution_groupbox.hide()
        self.ui.message_groupbox.hide()
        self.ui.opcodes_table_widget.hide()
        self.ui.stack_table_widget.hide()
        self.ui.memory_table_widget.hide()
        self.ui.abort_automode_button.hide()
        self.ui.step_duration_label.hide()
        self.ui.step_duration_le.hide()
        self.ui.automode_checkbox.hide()

        logger.info("Connecting buttons to callbacks.")
        self.ui.abort_automode_button.clicked.connect(self.abort_clicked)
        self.ui.debug_checkbox.stateChanged.connect(self.debug_mode_changed)
        self.ui.automode_checkbox.stateChanged.connect(self.auto_mode_changed)
        self.ui.steps_button.clicked.connect(self.steps_clicked)

        logger.info("Initializing objects needed for debugging")
        # contains mappings from addresses to mappings of storage slots to indices of table widgets
        # address -> {
        #   slot -> index
        #   slot -> index
        # }
        self.storage_lookup: {{}} = {}
        self.table_lookup = {
            TableWidgetEnum.OPCODES: self.ui.opcodes_table_widget,
            TableWidgetEnum.STACK: self.ui.stack_table_widget,
            TableWidgetEnum.MEMORY: self.ui.memory_table_widget,
            TableWidgetEnum.STORAGE: self.ui.storage_table_widget,
            TableWidgetEnum.ADDRESSES: self.ui.used_addresses_table_widget
        }
        self.change_chains: [ChangeChain] = []
        self.history = History()
        self.current_contract: MyContract = None
        self.setting_storage = False

        logger.info("Initialize threading objects. ThreadPool size: 1")
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(1)
        self.init_lock = Lock()
        self.step_lock = Lock()
        self.storage_lock = Lock()
        self.step_semaphore = QSemaphore(1)
        self.init_lock.acquire(True)
        self.step_lock.acquire(True)
        self.storage_lock.acquire(True)

        logger.info("Put master Account into observed Accounts")
        self.relevant_addresses["0x" + MASTER_ADDRESS.hex()] = MyAddress(MASTER_ADDRESS.hex())
        self._refresh_relevant_addresses()
        if sys.platform.__contains__("linux"):
            logger.info("Prettify UI for linux")
            font: QFont = QFont("Ubuntu")
            font.setPointSizeF(10)
            qApp.setFont(font)
            for w in qApp.allWidgets():
                w.setFont(font)

    def steps_clicked(self):
        val = self._parse_string(self.ui.steps_line_edit.text(), int, [(operator.ge, [1])])
        if val is not None:
            self._refresh_statusbar()
            self.step_semaphore.release(val)

    def abort_clicked(self):
        logger.info("Abort has been clicked!")
        MyComputation.abort = True
        self._refresh_statusbar("Aborting Transaction")

    def auto_mode_changed(self, i: int):
        if i > 0:
            self.ui.step_duration_label.show()
            self.ui.step_duration_le.show()
            self.ui.steps_button.hide()
            self.ui.steps_line_edit.hide()
        else:
            self.ui.steps_button.show()
            self.ui.steps_line_edit.show()
            self.ui.step_duration_label.hide()
            self.ui.step_duration_le.hide()

    def debug_mode_changed(self, i: int):
        if i > 0:
            self.ui.automode_checkbox.show()
            if self.ui.automode_checkbox.checkState():
                self.ui.step_duration_label.show()
                self.ui.step_duration_le.show()
            self.ui.storage_table_widget.show()
            self.ui.execution_groupbox.show()
            self.ui.message_groupbox.show()
            self.ui.opcodes_table_widget.show()
            self.ui.stack_table_widget.show()
            self.ui.memory_table_widget.show()
            self.ui.storage_address_label.show()
        else:
            self.ui.automode_checkbox.hide()
            self.ui.step_duration_label.hide()
            self.ui.step_duration_le.hide()
            self.ui.storage_table_widget.hide()
            self.ui.execution_groupbox.hide()
            self.ui.message_groupbox.hide()
            self.ui.opcodes_table_widget.hide()
            self.ui.stack_table_widget.hide()
            self.ui.memory_table_widget.hide()
            self.ui.storage_address_label.hide()
        pass

    def show_set_storage_dialog(self):
        set_storage_dialog = QDialog()
        ui = Ui_set_storage_dialog()
        ui.setupUi(set_storage_dialog)
        for addr in self.relevant_addresses.values():
            if type(addr) is MyContract:
                ui.address_cb.addItem(addr.get_readable_address())
        le: QLineEdit = ui.address_le
        cb: QComboBox = ui.address_cb
        kp = le.keyPressEvent
        lines = 0
        val: QLineEdit = None
        fl: QFormLayout = ui.formLayout

        def add_line(e=None):
            nonlocal lines
            nonlocal val
            if val is not None:
                val.focusInEvent = lambda x: None
            if lines < 6:
                slot = QLineEdit()
                val = QLineEdit()
                slot.setPlaceholderText("slot")
                val.setPlaceholderText("value")
                val.focusInEvent = add_line
                fl.addRow(slot, val)
                lines += 1

        def le_callback(event):
            kp(event)
            if len(le.text()) > 0:
                ui.select_address_lb.setDisabled(True)
                ui.address_cb.setDisabled(True)
                if lines == 0:
                    add_line()
            else:
                ui.select_address_lb.setDisabled(False)
                ui.address_cb.setDisabled(False)

        def cb_callback():
            if cb.currentIndex() != 0:
                ui.enter_address_lb.setDisabled(True)
                ui.address_le.setDisabled(True)
                if lines == 0:
                    add_line()
            else:
                ui.enter_address_lb.setDisabled(False)
                ui.address_le.setDisabled(False)

        le.keyPressEvent = le_callback
        cb.currentIndexChanged.connect(cb_callback)
        set_storage_dialog.show()
        if set_storage_dialog.exec_() == QDialog.Accepted:
            self.setting_storage = True
            if cb.currentIndex() != 0 or len(le.text()) != 0:
                if cb.isEnabled():
                    addr = Address(decode_hex(cb.currentText()[2:]))
                else:
                    parsed = self._parse_string(le.text(), decode_hex, [])
                    addr = Address(parsed)
                    err = False
                    try:
                        validate_canonical_address(addr)
                    except ValidationError:
                        err = True
                    if parsed is None or err:
                        self._refresh_statusbar(le.text() + " is not a valid address")
                        return
                st = "Successfully set storage values"
                for i in range(0, fl.count()):
                    slot = fl.itemAt(i, QFormLayout.LabelRole)
                    val = fl.itemAt(i, QFormLayout.FieldRole)
                    if slot is not None and val is not None:
                        slot = slot.widget().text()
                        val = val.widget().text()
                        if slot != "" and val != "":
                            slot = self._parse_string(slot, int, [(operator.ge, [0])])
                            val = self._parse_string(val, int, [(operator.ge, [0])])
                            if slot is None or val is None:
                                st = "Could not set at least one slot"
                                continue
                            self.evm_handler.set_storage(addr, slot, val)
                            self.set_storage_signal_cb(addr, hex2(slot), hex2(val))
                self._refresh_statusbar(st)
            self.setting_storage = False

    def show_set_gas_limit_dialog(self):
        self._set_gas_price_or_limit(set_price=False)

    def show_set_gas_price_dialog(self):
        self._set_gas_price_or_limit(set_price=True)

    def show_set_balance_dialog(self):
        Dialog = QDialog()
        dialog_ui = Ui_AddAdressesDialog()
        dialog_ui.setupUi(Dialog)
        dialog_ui.comboBox.addItems(units.keys())
        current_focus_le = dialog_ui.lineEdit_2
        line_ctr: int = 1

        def add_line(event):
            """" Callback function for when a QLineEdit gets focus. Will add new line for adding funds."""
            nonlocal dialog_ui
            nonlocal current_focus_le
            nonlocal line_ctr
            if line_ctr == 7:
                return
            else:
                line_ctr += 1
            left_le = QLineEdit(dialog_ui.gridLayoutWidget)
            left_le.setInputMask("")
            left_le.setText("")
            left_le.setObjectName("lineEdit_" + str(line_ctr) + "l")
            dialog_ui.gridLayout.addWidget(left_le, line_ctr, 0, 1, 1)
            right_le = QLineEdit(dialog_ui.gridLayoutWidget)
            right_le.setEnabled(True)
            sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(right_le.sizePolicy().hasHeightForWidth())
            right_le.setSizePolicy(sizePolicy)
            right_le.setObjectName("lineEdit_" + str(line_ctr) + "r")
            right_le.focusInEvent = add_line
            current_focus_le.focusInEvent = lambda x: None
            current_focus_le = right_le
            dialog_ui.gridLayout.addWidget(right_le, line_ctr, 1, 1, 1)
            comboBox = QComboBox(dialog_ui.gridLayoutWidget)
            comboBox.setCurrentText("")
            comboBox.setObjectName("comboBox")
            comboBox.addItems(units.keys())
            _translate = QCoreApplication.translate
            left_le.setPlaceholderText(_translate("Dialog", "0x1337...."))
            right_le.setPlaceholderText(_translate("Dialog", "0"))
            dialog_ui.gridLayoutWidget.setGeometry(QRect(30, 20, 661, 51 + (line_ctr - 1) * 33))
            dialog_ui.gridLayout.addWidget(comboBox, line_ctr, 2, 1, 1)

        dialog_ui.lineEdit_2.focusInEvent = add_line
        Dialog.setFixedSize(Dialog.size())
        Dialog.show()
        txs = []
        if Dialog.exec_() == QDialog.Accepted:
            for i in range(1, line_ctr + 1):
                addr = dialog_ui.gridLayout.itemAtPosition(i, 0).widget().text()[2:]
                val = self._parse_string(dialog_ui.gridLayout.itemAtPosition(i, 1).widget().text(), int,
                                         [(operator.ge, [0])])
                val = 0 if val is None else val
                unit = dialog_ui.gridLayout.itemAtPosition(i, 2).widget().currentText()
                if addr != "":
                    txs.append(MyTransaction(addr, val * int(units.get(unit))))
                    logger.info("Add tx to addr {a} with value {v} in unit {u}".format(a=addr, v=val, u=unit))
            st = ""
            for tx in txs:
                st = "Set balances successfully"
                try:
                    to = tx.addr.get_typed_address()
                    validate_canonical_address(to)
                    assert tx.val >= 0
                    self.evm_handler.set_balance(Address(to), tx.val)
                    to = tx.addr.get_readable_address()
                    if self.relevant_addresses[to] is None:
                        self.relevant_addresses[to] = tx.addr
                    self._refresh_relevant_addresses()
                except (ValidationError, AssertionError, ValueError) as e:
                    st = "Could not set at least one balance"
            self._refresh_statusbar(st)

    def show_set_contract_dialog(self):
        AddContractDialog = QDialog()
        ui = Ui_AddContractDialog()
        ui.setupUi(AddContractDialog)
        ui.info_label_2.linkActivated.connect(lambda link: QDesktopServices.openUrl(QUrl(link)))
        ui.info_label.linkActivated.connect(lambda link: QDesktopServices.openUrl(QUrl(link)))
        AddContractDialog.setFixedSize(AddContractDialog.size())
        AddContractDialog.show()
        if AddContractDialog.exec_() == QDialog.Accepted:
            try:
                if ui.tabWidget.currentIndex() == 0:
                    self.pre_transaction_handling()
                    step_duration = float(self.ui.step_duration_le.text())
                    abi = ui.abi_te.toPlainText()
                    abi = "[]" if abi == "" else abi
                    byte_code = ui.bytecode_te_2.toPlainText()
                    if byte_code == "":
                        raise ValueError("Please enter a valid contract.")
                    self.current_contract = MyContract(abi, byte_code)
                    self._clear_table_widget(TableWidgetEnum.STORAGE)
                    qApp.processEvents()
                    wei = self._parse_string(self.ui.value_le.text(), int, [(operator.ge, [0])])
                    if wei is None:
                        wei = 0
                        self._refresh_statusbar("Invalid amount. Continue with " + str(wei))
                    worker = ContractWorker(self.evm_handler.create_contract, self.current_contract.bytecode.object,
                                            wei, self._current_debug_mode(), storage_lookup=self.storage_lookup,
                                            init_lock=self.init_lock, step_lock=self.step_lock,
                                            storage_lock=self.storage_lock, step_semaphore=self.step_semaphore,
                                            step_duration=step_duration
                                            )
                    self._connect_signals_and_start_worker(worker)
                else:
                    self.current_contract = MyContract("[]", ui.bytecode_te.toPlainText())
                    addr = Address(decode_hex(ui.contract_le.text()))
                    addr = self.evm_handler.set_code(addr=addr, code=decode_hex(self.current_contract.bytecode.object))
                    self.storage_lookup[addr] = {}
                    self.contract_created_cb(addr)
            except (TypeError, json.JSONDecodeError, ValueError) as e:
                self._refresh_statusbar(str(e))
                self.post_transaction_handling()

    def send_transaction_clicked(self):
        con = self.relevant_addresses.get(self.ui.select_address_combobox.currentText())
        if con is None:
            self._refresh_statusbar("Please Load a Contract first via New -> Contract")
            return
        step_duration = self._parse_string(self.ui.step_duration_le.text(), float, [(operator.gt, [0])])
        wei = self._parse_string(self.ui.value_le.text(), int, [(operator.ge, [0])])
        if step_duration is None or wei is None:
            return
        inputs: [] = con.get_function_params(self.ui.select_function_combobox.currentIndex())
        args: [{}] = []
        for i in range(0, self.ui.function_params_form_layout.rowCount()):
            value = self.ui.function_params_form_layout.itemAt(2 * i + 1).widget().text()
            props = inputs[i]._asdict()  # turn namedtuple into dictionary
            args.append({"type": props.get("type"), "name": props.get("name"), 'value': value})
        self.pre_transaction_handling()
        worker: TransactionWorker = TransactionWorker(self.evm_handler.call_contract_function, con.get_typed_address(),
                                                      self.ui.select_function_combobox.currentText(), args,
                                                      self._current_debug_mode(), wei,
                                                      storage_lookup=self.storage_lookup, init_lock=self.init_lock,
                                                      step_lock=self.step_lock, storage_lock=self.storage_lock,
                                                      step_semaphore=self.step_semaphore, step_duration=step_duration
                                                      )
        self._connect_signals_and_start_worker(worker)

    def contract_function_selected(self):
        self.ui.select_function_combobox.show()
        con = self.relevant_addresses.get(self.ui.select_address_combobox.currentText())
        fp = con.get_function_params(self.ui.select_function_combobox.currentIndex())
        while self.ui.function_params_form_layout.rowCount() > 0:
            self.ui.function_params_form_layout.removeRow(0)

        for p in fp:
            le = QLineEdit()
            le.setPlaceholderText(p.type)
            self.ui.function_params_form_layout.addRow(p.name + ":", le)

    def contract_selected(self):
        self.ui.select_function_combobox.clear()
        self.current_contract = self.relevant_addresses.get(self.ui.select_address_combobox.currentText())
        self.ui.select_function_combobox.addItems(self.current_contract.signatures)
        self._refresh_storage(Address(decode_hex(self.ui.select_address_combobox.currentText()[2:])))

    def post_transaction_handling(self):
        """
        Post transaction processes.
        """
        self._refresh_relevant_addresses()
        addr = self.ui.select_address_combobox.currentText()
        if addr != "Load a contract first!":
            self._refresh_storage(Address(decode_hex(addr[2:])))
        self.ui.debug_checkbox.setDisabled(False)
        self.ui.automode_checkbox.setDisabled(False)
        self.ui.send_transaction_button.setDisabled(False)
        self.ui.step_duration_label.setDisabled(False)
        self.ui.step_duration_le.setDisabled(False)
        self.ui.select_address_combobox.setDisabled(False)
        self.ui.select_function_combobox.setDisabled(False)
        self.ui.abort_automode_button.hide()

    def pre_transaction_handling(self):
        """
        Prepares the UI and other objects for a transaction.
        """
        self.ui.debug_checkbox.setDisabled(True)
        self.ui.automode_checkbox.setDisabled(True)
        self.ui.send_transaction_button.setDisabled(True)
        self.ui.step_duration_le.setDisabled(True)
        self.ui.step_duration_label.setDisabled(True)
        self.ui.select_address_combobox.setDisabled(True)
        self.ui.select_function_combobox.setDisabled(True)
        if self.ui.automode_checkbox.checkState():
            self.ui.abort_automode_button.show()
        self.change_chains: [ChangeChain] = []
        self.step_semaphore = QSemaphore(1)

    def transaction_sent_signal_cb(self):
        self.post_transaction_handling()
        self._refresh_statusbar("Transaction mined successfully.")

    def contract_created_signal_cb(self, addr: Address):
        cb: QComboBox = self.ui.select_address_combobox
        if addr != b'':
            self.current_contract.set_address(addr.hex())
            a = self.current_contract.get_readable_address()
            self.relevant_addresses[a] = self.current_contract
            self._refresh_statusbar("Mined new Contract at address " + a)
            cb.currentIndexChanged.disconnect()
            cb.clear()
            for addr in self.relevant_addresses.values():
                if self.evm_handler.get_code(addr.get_typed_address()) != b'':
                    cb.addItem(addr.get_readable_address())
            cb.currentIndexChanged.connect(self.contract_selected)
            cb.setCurrentIndex(cb.count() - 1)
            if cb.count() == 1:
                self.contract_selected()
        else:
            self._refresh_statusbar("Error processing transaction.")
        self.post_transaction_handling()

    def transaction_aborted_signal_cb(self):
        self.transaction_sent_signal_cb()
        self._clear_table_widget(TableWidgetEnum.MEMORY)
        self._clear_table_widget(TableWidgetEnum.STACK)
        self._refresh_statusbar("Transaction aborted")
        MyComputation.abort = False

    def add_change_chain_signal_cb(self, chain: ChangeChain):
        self.change_chains.append(chain)

    def pre_computation_signal_cb(self, remaining_gas: int, pc: int):
        # pc and gasleft
        self.ui.gas_label.setText("Gas: " + str(remaining_gas))
        self.ui.pc_label.setText("PC: " + str(pc))

        last_elem = len(self.change_chains) - 1
        if last_elem > 0:
            # remove previous post highlighting
            self._highlight_from_chain(self.change_chains[last_elem - 1], False, False)
        if last_elem >= 0:
            self._highlight_from_chain(self.change_chains[last_elem], True, True)
        self.step_lock.release()

    def post_computation_signal_cb(self, stack: [tuple], memory: bytearray, pc: int, last_gas: int):
        logger.info("Entering post compute in main")
        # remove current pre highlighting
        last_elem = len(self.change_chains) - 1
        if last_elem >= 0:
            self._highlight_from_chain(self.change_chains[last_elem], True, False)

        # for some opcodes it would be very hard to calculate the gas usage in advance (e.g. SSTORE, might be write
        # for 20k or just for 15k or you might even get a refund) so we fill in those gas prices once the information
        # is available
        v = self.ui.opcodes_table_widget.item(pc - 1, 2)
        v.setText(str(last_gas))

        # handling changes in stack stack
        self._clear_table_widget(TableWidgetEnum.STACK)

        size = len(stack) - 1
        if size >= 0:
            for i in range(size, -1, -1):
                if stack[i][0] is int:
                    val = hex(stack[i][1])
                else:
                    val = "0x" + stack[i][1].hex()
                v = QTableWidgetItem()
                v.setText(val)
                self.ui.stack_table_widget.insertRow(size - i)
                self.ui.stack_table_widget.setItem(size - i, 0, v)

        # handling changes in memory
        self._clear_table_widget(TableWidgetEnum.MEMORY)

        size = len(memory)
        new_font = QFont("Courier", 12)
        if sys.platform.__contains__("linux"):
            new_font = QFont("Courier", 9)
        if size >= 32:
            for i in range(0, size, 32):
                val = "0x" + memory[i:i + 32].hex()
                v = QTableWidgetItem()
                v.setText(val)
                v.setFont(new_font)
                self.ui.memory_table_widget.insertRow(i / 32)
                self.ui.memory_table_widget.setItem(i / 32, 0, v)

        # highlighting
        if last_elem >= 0:
            self._highlight_from_chain(self.change_chains[last_elem], False, True)

        # scroll to correct place
        v2 = self.ui.opcodes_table_widget.item(pc, 2)
        self.ui.opcodes_table_widget.scrollToItem(v2)
        self.step_lock.release()

    def init_debug_session_signal_cb(self, code: CodeStreamAPI, opcode_lookup: Dict[int, OpcodeAPI],
                                     message: MessageAPI):
        """
        :param code: Must be a deepcopy() version of the real code object.
        :param opcode_lookup:
        :param message:
        :return:
        """
        logger.info("Init_debug signal received")

        # self.history.init = (code, opcode_lookup, message)
        # self.change_chains: [ChangeChain] = []

        self._clear_table_widget(TableWidgetEnum.OPCODES)
        self._clear_table_widget(TableWidgetEnum.STACK)
        self._clear_table_widget(TableWidgetEnum.MEMORY)

        # reset the program counter, it might not be 0 and we need the whole thing.
        code.pc = 0
        for opcode in code:
            c = self.ui.opcodes_table_widget.rowCount()
            self.ui.opcodes_table_widget.insertRow(c)
            try:
                opcode_fn = opcode_lookup[opcode]
            except KeyError:
                opcode_fn = InvalidOpcode(opcode)

            o = QTableWidgetItem()
            m = QTableWidgetItem()
            g = QTableWidgetItem()
            o.setText(hex2(opcode))
            m.setText(opcode_fn.mnemonic)
            g.setText(str(opcode_fn.gas_cost))
            g.setTextAlignment(130)
            self.ui.opcodes_table_widget.setItem(c, 0, o)
            self.ui.opcodes_table_widget.setItem(c, 1, m)
            self.ui.opcodes_table_widget.setItem(c, 2, g)

        self.ui.origin_label.setText("origin: 0x" + MASTER_ADDRESS.hex())
        self.ui.origin_label.setToolTip("origin: 0x" + MASTER_ADDRESS.hex())
        self.ui.from_label.setText("from: 0x" + message.sender.hex())
        self.ui.from_label.setToolTip("from: 0x" + message.sender.hex())
        self.ui.to_label.setText("to: 0x" + message.to.hex())
        self.ui.to_label.setToolTip("to: 0x" + message.to.hex())
        self.ui.value_label.setText("value: " + str(message.value))
        self.ui.value_label.setToolTip("value: " + str(message.value))
        self.ui.gas_limit_label.setText("gas limit: " + str(message.gas))
        self.ui.gas_limit_label.setToolTip("gas limit: " + str(message.gas))
        if message.is_create:
            self.ui.data_label.setText("data: 0x" + message.code.hex()[:8] + "...")
            self.ui.data_label.setToolTip("<FONT COLOR=white>0x" + message.code.hex() + "</FONT>")
        else:
            self.ui.data_label.setText("data: 0x" + message.data.hex()[:8] + "...")
            self.ui.data_label.setToolTip("<FONT COLOR=white>0x" + message.data.hex() + "</FONT>")
        self.ui.call_depth_label.setText("call depth: " + str(message.depth))
        self.ui.call_depth_label.setToolTip("call depth: " + str(message.depth))

        self._refresh_storage(message.storage_address)

        # I think the processEvents function does also process signals in the background. This isn't really documented
        # anywhere besides at some places in the docs where signals are also called events. The reason why I am
        # thinking that is that when this line is reached, the pre_computation_cb callback is called immediately
        # afterwards, which should not be and is only the case if there already is a signal in the queue waiting to be
        # handled and the processEvents function handles all the signals before updating the gui (which
        # is what we actually want).
        # To circumvent this, we need to put a lock in the worker thread that locks immediately after
        # firing the init_debug signal and will only release after processEvents has been called. That way the worker
        # thread will not add another signal to the queue before the current events (namely updating the gui which
        # is happening in this function) are processed.

        qApp.processEvents()
        self.init_lock.release()

    def error_signal_cb(self, reason: str):
        """
        Callback function for the error signal.
        """
        self._refresh_statusbar(reason)
        self.post_transaction_handling()

    def set_storage_signal_cb(self, addr: Address, slot: str = "", value: str = ""):
        lkp = self.storage_lookup.get(addr)
        if lkp is None:
            self.storage_lookup[addr] = {}

        c = self.storage_lookup.get(addr).get(slot)
        if c is None:
            self.storage_lookup[addr][slot] = len(self.storage_lookup.get(addr))

        # if we are handling a contract address that is currently being displayed OR if we are in the process of
        # creating a new contract
        if self.ui.debug_checkbox.checkState() or self.current_contract.get_typed_address() == b'':
            if c is None:
                c = self.storage_lookup.get(addr).get(slot)
                self.ui.storage_table_widget.insertRow(c)
                s = QTableWidgetItem()
                v = QTableWidgetItem()
                s.setText(slot)
                v.setText(value)
                v.setTextAlignment(130)
                self.ui.storage_table_widget.setItem(c, 0, s)
                self.ui.storage_table_widget.setItem(c, 1, v)
            else:
                v = self.ui.storage_table_widget.item(c, 1)
                v.setText(value)

            self.ui.storage_table_widget.scrollToItem(v)
            if self.ui.debug_checkbox.checkState() and not self.setting_storage:
                self.storage_lock.release()

    def _highlight_from_chain(self, c: ChangeChain, pre_computation: bool, set_properties: bool):
        # highlighting
        for link in c:
            logger.info("Now doing widget {w}".format(w=link.widget))
            link: ChangeChainLink = link
            widget: QTableWidget = self.table_lookup[link.widget]
            if pre_computation:
                comp = link.pre_computation
            else:
                comp = link.post_computation
            for index in comp:
                for i in range(0, widget.columnCount()):
                    item: QTableWidgetItem = widget.item(index, i)
                    if item is None:
                        logger.info("Skipping item {ind}, {i} because it is None".format(ind=index, i=i))
                        continue
                    if set_properties:
                        font: QFont = QFont()
                        font.setBold(True)
                        if pre_computation:
                            col = QColor(255, 0, 0)
                        else:
                            col = QColor(0, 255, 0)
                        item.setFont(font)
                        item.setForeground(QBrush(col))
                    else:  # reset
                        it: QTableWidgetItem = QTableWidgetItem()
                        it.setText(item.text())
                        if link.widget == TableWidgetEnum.OPCODES and i == 2 \
                                or link.widget == TableWidgetEnum.STORAGE and i == 1:
                            it.setTextAlignment(130)
                        widget.setItem(index, i, it)

        #  Put a lock around this and process only one step at a time. MyComputation must wait until the
        #  produced is consumed
        qApp.processEvents()

    def _refresh_storage(self, addr: Address = None):
        """
        Helper function that refreshes the displayed storage table widget with values for the specified address.
        """
        self._clear_table_widget(TableWidgetEnum.STORAGE)
        if addr is None:
            return
        self.ui.storage_address_label.setText("Address: 0x" + addr.hex())
        self.ui.storage_address_label.setToolTip("Showing storage for address: 0x" + addr.hex())
        lkp = self.storage_lookup.get(addr)
        if lkp is not None:
            for i in range(0, len(lkp.keys())):
                self.ui.storage_table_widget.insertRow(i)

            for slot in lkp.keys():
                value = hex(self.evm_handler.get_storage_at(addr, int(slot, 0)))
                k = QTableWidgetItem()
                v = QTableWidgetItem()
                k.setText(slot)
                v.setText(value)
                v.setTextAlignment(130)
                self.ui.storage_table_widget.setItem(lkp.get(slot), 0, k)
                self.ui.storage_table_widget.setItem(lkp.get(slot), 1, v)

    def _refresh_statusbar(self, status: str = ""):
        self.blockLabel.setText("Current Block: " + str(self.evm_handler.get_block_number())
                                + " | Gas Price: " + str(self.evm_handler.get_gas_price()) + " wei"
                                + " | Current Gas Limit: " + str(self.evm_handler.get_gas_limit()))
        self.statusLabel.setText("  " + status)

    def _refresh_relevant_addresses(self):
        """ should refresh all balances at least... """
        self._clear_table_widget(TableWidgetEnum.ADDRESSES)
        cb: QComboBox = self.ui.select_address_combobox
        for key, addr in self.relevant_addresses.items():
            if type(addr) == MyContract and self.evm_handler.get_code(addr.get_typed_address()) == b'':
                for i in range(0, len(cb)):
                    if cb.itemText(i) == addr.get_readable_address():
                        cb.removeItem(i)
                        break
                if self.storage_lookup.get(addr.get_readable_address()) is not None:
                    self.storage_lookup.pop(addr.get_readable_address())
                    self._refresh_storage()
            c = self.ui.used_addresses_table_widget.rowCount()
            self.ui.used_addresses_table_widget.insertRow(c)
            a = QTableWidgetItem()
            a.setText(addr.get_readable_address())
            b = QTableWidgetItem()
            bal = self.evm_handler.get_balance(addr.get_typed_address())
            b.setText(str(bal) + " wei")
            b.setTextAlignment(130)
            t = QTableWidgetItem()
            t.setText("Account" if self.evm_handler.get_code(addr.get_typed_address()) == b'' else "Contract")
            self.ui.used_addresses_table_widget.setItem(c, 0, a)
            self.ui.used_addresses_table_widget.setItem(c, 1, b)
            self.ui.used_addresses_table_widget.setItem(c, 2, t)

    def _clear_table_widget(self, enum: TableWidgetEnum):
        """
        Helper function that clears a table widget.
        """
        widget = self.table_lookup.get(enum)
        while widget.rowCount() > 0:
            widget.removeRow(0)

    def _connect_signals_and_start_worker(self, worker: BaseWorker):
        """
        Helper function that connects a workers signals to the callback functions and starts the worker.
        """
        worker.signals.init_debug_session.connect(self.init_debug_session_signal_cb)
        worker.signals.post_computation.connect(self.post_computation_signal_cb)
        worker.signals.pre_computation.connect(self.pre_computation_signal_cb)
        worker.signals.set_storage.connect(self.set_storage_signal_cb)
        worker.signals.add_chain.connect(self.add_change_chain_signal_cb)
        worker.signals.contract_created.connect(self.contract_created_signal_cb)
        worker.signals.transaction_sent.connect(self.transaction_sent_signal_cb)
        worker.signals.abort.connect(self.transaction_aborted_signal_cb)
        worker.signals.result.connect(self.show_result_signal_cb)
        worker.signals.error.connect(self.error_signal_cb)
        self.thread_pool.start(worker)

    def _set_gas_price_or_limit(self, set_price: bool):
        """
        Generic function that's used to show either the set gas price or set gas limit dialog.
        :param set_price: Defines which of the dialogs to show.
        """
        dialog = QDialog()
        ui = Ui_SetGasPriceDialog() if set_price else Ui_SetGasLimitDialog()
        ui.setupUi(dialog)
        dialog.show()
        if dialog.exec_() == QDialog.Accepted:
            val = self._parse_string(ui.lineEdit.text(), int, [(operator.ge, [0])])
            if val is not None:
                if set_price:
                    evmhandler.DEFAULT_GAS_PRICE = val
                else:
                    evmhandler.DEFAULT_TRANSACTION_GAS_AMOUNT = val
                self._refresh_statusbar()

    def _parse_string(self, val: str, conversion_fn: FunctionType, constraints: [(FunctionType, [])]) -> Any:
        """
        This function is used to convert user input into data types that are internally used.
        It will receive the input as string, a conversion function e.g. int or decode_hex, and constraints.
        To support more than one constraint, a list of two-element tuples is expected. The first element is the
        constraint function, meaning a function that returns true if the constraint is fulfilled. The second element
        is a list of arguments, which will be passed along with the converted value of val.
        In the case that a conversion error happens, or that at least one constraint is violated, the user will be
        notified by statusbar updates.
        :param val: The string to convert.
        :param conversion_fn: The conversion function that converts the string.
        :param constraints: A list of constraints that are checked for.
        :return: None if type conversion failed or if a constraint is violated. Else the converted value will be
        returned.
        """
        try:
            res = conversion_fn(val)
            for constraint in constraints:
                fn = constraint[0]
                args = [res] + constraint[1]
                if not fn(*args):
                    self._refresh_statusbar(val + " does not fulfill one or more constraints")
                    return None
        except ValueError as e:
            self._refresh_statusbar(str(e))
            return None
        return res

    def _current_debug_mode(self) -> int:
        """
        :return: The current debug mode that is internally used. The values correspond to the ones defined in the
        util.py file.
        """
        return int(int(self.ui.debug_checkbox.checkState()) / 2 + int(self.ui.automode_checkbox.checkState()) / 2)

    @staticmethod
    def show_result_signal_cb(result: bytes):
        if result != b'':
            d = QDialog()
            d.setBaseSize(300, 300)
            te = QPlainTextEdit(d)
            te.setFixedSize(290, 270)
            te.setPlainText(encode_hex(result))
            b1 = QPushButton("OK", d)
            b1.clicked.connect(d.close)
            b1.move(250, 270)
            d.setWindowTitle("Return Value")
            d.setWindowModality(Qt.ApplicationModal)
            d.exec_()


def main():
    logging.basicConfig()
    logging.getLogger().setLevel(logging.WARN)

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('icon.png'))
    application = ApplicationWindow()
    application.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
