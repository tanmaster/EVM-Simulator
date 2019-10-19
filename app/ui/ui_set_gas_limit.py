# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'qt_templates/ui_set_gas_limit.ui'
#
# Created by: PyQt5 UI code generator 5.13.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_SetGasLimitDialog(object):
    def setupUi(self, SetGasLimitDialog):
        SetGasLimitDialog.setObjectName("SetGasLimitDialog")
        SetGasLimitDialog.resize(300, 140)
        self.buttonBox = QtWidgets.QDialogButtonBox(SetGasLimitDialog)
        self.buttonBox.setGeometry(QtCore.QRect(70, 90, 161, 41))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.label = QtWidgets.QLabel(SetGasLimitDialog)
        self.label.setGeometry(QtCore.QRect(70, 30, 121, 16))
        self.label.setObjectName("label")
        self.lineEdit = QtWidgets.QLineEdit(SetGasLimitDialog)
        self.lineEdit.setGeometry(QtCore.QRect(70, 50, 161, 21))
        self.lineEdit.setObjectName("lineEdit")

        self.retranslateUi(SetGasLimitDialog)
        self.buttonBox.accepted.connect(SetGasLimitDialog.accept)
        self.buttonBox.rejected.connect(SetGasLimitDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(SetGasLimitDialog)

    def retranslateUi(self, SetGasLimitDialog):
        _translate = QtCore.QCoreApplication.translate
        SetGasLimitDialog.setWindowTitle(_translate("SetGasLimitDialog", "Set Gas Limit"))
        self.label.setText(_translate("SetGasLimitDialog", "Gas Limit:"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    SetGasLimitDialog = QtWidgets.QDialog()
    ui = Ui_SetGasLimitDialog()
    ui.setupUi(SetGasLimitDialog)
    SetGasLimitDialog.show()
    sys.exit(app.exec_())
