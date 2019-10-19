# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'qt_templates/ui_set_storage.ui'
#
# Created by: PyQt5 UI code generator 5.13.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_set_storage_dialog(object):
    def setupUi(self, set_storage_dialog):
        set_storage_dialog.setObjectName("set_storage_dialog")
        set_storage_dialog.resize(405, 452)
        self.buttonBox = QtWidgets.QDialogButtonBox(set_storage_dialog)
        self.buttonBox.setGeometry(QtCore.QRect(30, 400, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.select_address_lb = QtWidgets.QLabel(set_storage_dialog)
        self.select_address_lb.setGeometry(QtCore.QRect(40, 20, 111, 16))
        self.select_address_lb.setObjectName("select_address_lb")
        self.address_cb = QtWidgets.QComboBox(set_storage_dialog)
        self.address_cb.setGeometry(QtCore.QRect(40, 40, 331, 26))
        self.address_cb.setObjectName("address_cb")
        self.address_cb.addItem("")
        self.address_le = QtWidgets.QLineEdit(set_storage_dialog)
        self.address_le.setGeometry(QtCore.QRect(40, 110, 321, 21))
        self.address_le.setObjectName("address_le")
        self.enter_address_lb = QtWidgets.QLabel(set_storage_dialog)
        self.enter_address_lb.setGeometry(QtCore.QRect(40, 90, 111, 16))
        self.enter_address_lb.setObjectName("enter_address_lb")
        self.or_lb = QtWidgets.QLabel(set_storage_dialog)
        self.or_lb.setGeometry(QtCore.QRect(10, 70, 21, 20))
        self.or_lb.setObjectName("or_lb")
        self.formLayoutWidget = QtWidgets.QWidget(set_storage_dialog)
        self.formLayoutWidget.setGeometry(QtCore.QRect(40, 150, 321, 181))
        self.formLayoutWidget.setObjectName("formLayoutWidget")
        self.formLayout = QtWidgets.QFormLayout(self.formLayoutWidget)
        self.formLayout.setContentsMargins(0, 0, 0, 0)
        self.formLayout.setObjectName("formLayout")

        self.retranslateUi(set_storage_dialog)
        self.buttonBox.accepted.connect(set_storage_dialog.accept)
        self.buttonBox.rejected.connect(set_storage_dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(set_storage_dialog)

    def retranslateUi(self, set_storage_dialog):
        _translate = QtCore.QCoreApplication.translate
        set_storage_dialog.setWindowTitle(_translate("set_storage_dialog", "Set Storage"))
        self.select_address_lb.setText(_translate("set_storage_dialog", "Select Address"))
        self.address_cb.setItemText(0, _translate("set_storage_dialog", "Select Contract Address"))
        self.address_le.setPlaceholderText(_translate("set_storage_dialog", "0xaffe..."))
        self.enter_address_lb.setText(_translate("set_storage_dialog", "Enter Address"))
        self.or_lb.setText(_translate("set_storage_dialog", "Or"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    set_storage_dialog = QtWidgets.QDialog()
    ui = Ui_set_storage_dialog()
    ui.setupUi(set_storage_dialog)
    set_storage_dialog.show()
    sys.exit(app.exec_())
