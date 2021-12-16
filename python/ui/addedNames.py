# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/addedNames.ui'
#
# Created by: PyQt5 UI code generator 5.15.6
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(435, 224)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName("tabWidget")
        self.AddedNamesReport = QtWidgets.QWidget()
        self.AddedNamesReport.setObjectName("AddedNamesReport")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.AddedNamesReport)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem)
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.xmlFile_btn = QtWidgets.QPushButton(self.AddedNamesReport)
        self.xmlFile_btn.setObjectName("xmlFile_btn")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.xmlFile_btn)
        self.select_label = QtWidgets.QLabel(self.AddedNamesReport)
        self.select_label.setObjectName("select_label")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.select_label)
        self.verticalLayout_2.addLayout(self.formLayout)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem1)
        self.rub_btn = QtWidgets.QPushButton(self.AddedNamesReport)
        self.rub_btn.setMaximumSize(QtCore.QSize(256, 16777215))
        self.rub_btn.setObjectName("rub_btn")
        self.verticalLayout_2.addWidget(self.rub_btn, 0, QtCore.Qt.AlignHCenter)
        spacerItem2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem2)
        self.tabWidget.addTab(self.AddedNamesReport, "")
        self.CheckFM = QtWidgets.QWidget()
        self.CheckFM.setObjectName("CheckFM")
        self.tabWidget.addTab(self.CheckFM, "")
        self.verticalLayout.addWidget(self.tabWidget)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.xmlFile_btn.setText(_translate("MainWindow", "Open File"))
        self.select_label.setText(_translate("MainWindow", "Select Dashboard XML:"))
        self.rub_btn.setText(_translate("MainWindow", "Create Added Names Report"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.AddedNamesReport), _translate("MainWindow", "Added Names Report"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.CheckFM), _translate("MainWindow", "Check names in FM"))
