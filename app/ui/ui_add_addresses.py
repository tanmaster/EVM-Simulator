# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'qt_templates/ui_add_addresses.ui'
#
# Created by: PyQt5 UI code generator 5.13.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_AddAdressesDialog(object):
    def setupUi(self, AddAdressesDialog):
        AddAdressesDialog.setObjectName("AddAdressesDialog")
        AddAdressesDialog.setEnabled(True)
        AddAdressesDialog.resize(720, 360)
        self.buttonBox = QtWidgets.QDialogButtonBox(AddAdressesDialog)
        self.buttonBox.setGeometry(QtCore.QRect(530, 300, 171, 41))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.buttonBox.sizePolicy().hasHeightForWidth())
        self.buttonBox.setSizePolicy(sizePolicy)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayoutWidget = QtWidgets.QWidget(AddAdressesDialog)
        self.gridLayoutWidget.setGeometry(QtCore.QRect(30, 20, 661, 51))
        self.gridLayoutWidget.setObjectName("gridLayoutWidget")
        self.gridLayout = QtWidgets.QGridLayout(self.gridLayoutWidget)
        self.gridLayout.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout")
        self.lineEdit = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.lineEdit.setInputMask("")
        self.lineEdit.setText("")
        self.lineEdit.setObjectName("lineEdit")
        self.gridLayout.addWidget(self.lineEdit, 1, 0, 1, 1)
        self.lineEdit_2 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.lineEdit_2.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineEdit_2.sizePolicy().hasHeightForWidth())
        self.lineEdit_2.setSizePolicy(sizePolicy)
        self.lineEdit_2.setObjectName("lineEdit_2")
        self.gridLayout.addWidget(self.lineEdit_2, 1, 1, 1, 1)
        self.label = QtWidgets.QLabel(self.gridLayoutWidget)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.comboBox = QtWidgets.QComboBox(self.gridLayoutWidget)
        self.comboBox.setCurrentText("")
        self.comboBox.setObjectName("comboBox")
        self.gridLayout.addWidget(self.comboBox, 1, 2, 1, 1)
        self.label_4 = QtWidgets.QLabel(self.gridLayoutWidget)
        self.label_4.setObjectName("label_4")
        self.gridLayout.addWidget(self.label_4, 0, 2, 1, 1)
        self.label_3 = QtWidgets.QLabel(self.gridLayoutWidget)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 0, 1, 1, 1)
        self.label_2 = QtWidgets.QLabel(AddAdressesDialog)
        self.label_2.setGeometry(QtCore.QRect(40, 310, 491, 21))
        self.label_2.setObjectName("label_2")
        self.label.setBuddy(self.label)
        self.label_4.setBuddy(self.label_4)
        self.label_3.setBuddy(self.label_3)

        self.retranslateUi(AddAdressesDialog)
        self.buttonBox.accepted.connect(AddAdressesDialog.accept)
        self.buttonBox.rejected.connect(AddAdressesDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(AddAdressesDialog)

    def retranslateUi(self, AddAdressesDialog):
        _translate = QtCore.QCoreApplication.translate
        AddAdressesDialog.setWindowTitle(_translate("AddAdressesDialog", "Add Fundings to Adresses"))
        self.lineEdit.setPlaceholderText(_translate("AddAdressesDialog", "0x1337...."))
        self.lineEdit_2.setPlaceholderText(_translate("AddAdressesDialog", "0"))
        self.label.setText(_translate("AddAdressesDialog", "Address"))
        self.label_4.setText(_translate("AddAdressesDialog", "Unit"))
        self.label_3.setText(_translate("AddAdressesDialog", "Value"))
        self.label_2.setText(_translate("AddAdressesDialog", "ℹ︎ All specified fundings will be sent from the same master address."))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    AddAdressesDialog = QtWidgets.QDialog()
    ui = Ui_AddAdressesDialog()
    ui.setupUi(AddAdressesDialog)
    AddAdressesDialog.show()
    sys.exit(app.exec_())
