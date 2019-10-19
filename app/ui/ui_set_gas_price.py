# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'qt_templates/ui_set_gas_price.ui'
#
# Created by: PyQt5 UI code generator 5.13.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_SetGasPriceDialog(object):
    def setupUi(self, SetGasPriceDialog):
        SetGasPriceDialog.setObjectName("SetGasPriceDialog")
        SetGasPriceDialog.resize(300, 140)
        self.buttonBox = QtWidgets.QDialogButtonBox(SetGasPriceDialog)
        self.buttonBox.setGeometry(QtCore.QRect(70, 90, 161, 41))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.label = QtWidgets.QLabel(SetGasPriceDialog)
        self.label.setGeometry(QtCore.QRect(70, 30, 121, 16))
        self.label.setObjectName("label")
        self.lineEdit = QtWidgets.QLineEdit(SetGasPriceDialog)
        self.lineEdit.setGeometry(QtCore.QRect(70, 50, 161, 21))
        self.lineEdit.setObjectName("lineEdit")

        self.retranslateUi(SetGasPriceDialog)
        self.buttonBox.accepted.connect(SetGasPriceDialog.accept)
        self.buttonBox.rejected.connect(SetGasPriceDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(SetGasPriceDialog)

    def retranslateUi(self, SetGasPriceDialog):
        _translate = QtCore.QCoreApplication.translate
        SetGasPriceDialog.setWindowTitle(_translate("SetGasPriceDialog", "Set Gas Price"))
        self.label.setText(_translate("SetGasPriceDialog", "Gas Price:"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    SetGasPriceDialog = QtWidgets.QDialog()
    ui = Ui_SetGasPriceDialog()
    ui.setupUi(SetGasPriceDialog)
    SetGasPriceDialog.show()
    sys.exit(app.exec_())
