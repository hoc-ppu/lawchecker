# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'addedNames.ui'
##
## Created by: Qt User Interface Compiler version 6.5.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QDateEdit, QFrame,
    QGridLayout, QHBoxLayout, QLabel, QMainWindow,
    QPushButton, QSizePolicy, QSpacerItem, QTabWidget,
    QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(644, 750)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.horizontalLayout = QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.AddedNamesTab = QWidget()
        self.AddedNamesTab.setObjectName(u"AddedNamesTab")
        self.verticalLayout_3 = QVBoxLayout(self.AddedNamesTab)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.frame_2 = QFrame(self.AddedNamesTab)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setFrameShape(QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QFrame.Plain)
        self.gridLayout_3 = QGridLayout(self.frame_2)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.label_4 = QLabel(self.frame_2)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout_3.addWidget(self.label_4, 1, 0, 1, 1)

        self.createWorkingFolderBtn = QPushButton(self.frame_2)
        self.createWorkingFolderBtn.setObjectName(u"createWorkingFolderBtn")

        self.gridLayout_3.addWidget(self.createWorkingFolderBtn, 2, 1, 1, 1)

        self.workingFolderDateEdit = QDateEdit(self.frame_2)
        self.workingFolderDateEdit.setObjectName(u"workingFolderDateEdit")
        self.workingFolderDateEdit.setCalendarPopup(True)

        self.gridLayout_3.addWidget(self.workingFolderDateEdit, 1, 1, 1, 1)

        self.label_5 = QLabel(self.frame_2)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout_3.addWidget(self.label_5, 2, 0, 1, 1)

        self.label_3 = QLabel(self.frame_2)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setWordWrap(True)

        self.gridLayout_3.addWidget(self.label_3, 0, 0, 1, 2)

        self.label_6 = QLabel(self.frame_2)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setWordWrap(True)

        self.gridLayout_3.addWidget(self.label_6, 3, 0, 1, 2)


        self.verticalLayout_3.addWidget(self.frame_2)

        self.widget = QWidget(self.AddedNamesTab)
        self.widget.setObjectName(u"widget")
        self.verticalLayout_2 = QVBoxLayout(self.widget)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.get_label = QLabel(self.widget)
        self.get_label.setObjectName(u"get_label")
        self.get_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.get_label, 0, 0, 1, 1)

        self.select_label = QLabel(self.widget)
        self.select_label.setObjectName(u"select_label")
        self.select_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.select_label, 3, 0, 1, 1)

        self.openBrowser_btn = QPushButton(self.widget)
        self.openBrowser_btn.setObjectName(u"openBrowser_btn")

        self.gridLayout.addWidget(self.openBrowser_btn, 0, 1, 1, 1)

        self.xmlFile_btn = QPushButton(self.widget)
        self.xmlFile_btn.setObjectName(u"xmlFile_btn")

        self.gridLayout.addWidget(self.xmlFile_btn, 3, 1, 1, 1)

        self.instruction_label = QLabel(self.widget)
        self.instruction_label.setObjectName(u"instruction_label")
        self.instruction_label.setWordWrap(True)

        self.gridLayout.addWidget(self.instruction_label, 1, 0, 1, 2)

        self.gridLayout.setColumnStretch(0, 1)
        self.gridLayout.setColumnStretch(1, 1)

        self.verticalLayout_2.addLayout(self.gridLayout)


        self.verticalLayout_3.addWidget(self.widget)

        self.frame = QFrame(self.AddedNamesTab)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Plain)
        self.gridLayout_2 = QGridLayout(self.frame)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.fm_xml_btn = QPushButton(self.frame)
        self.fm_xml_btn.setObjectName(u"fm_xml_btn")

        self.gridLayout_2.addWidget(self.fm_xml_btn, 1, 1, 1, 1)

        self.label = QLabel(self.frame)
        self.label.setObjectName(u"label")
        self.label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout_2.addWidget(self.label, 1, 0, 1, 1)

        self.label_2 = QLabel(self.frame)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setWordWrap(True)
        self.label_2.setOpenExternalLinks(True)

        self.gridLayout_2.addWidget(self.label_2, 0, 0, 1, 2)


        self.verticalLayout_3.addWidget(self.frame)

        self.run_btn = QPushButton(self.AddedNamesTab)
        self.run_btn.setObjectName(u"run_btn")
        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.run_btn.sizePolicy().hasHeightForWidth())
        self.run_btn.setSizePolicy(sizePolicy)
        self.run_btn.setMaximumSize(QSize(264, 16777215))

        self.verticalLayout_3.addWidget(self.run_btn)

        self.tabWidget.addTab(self.AddedNamesTab, "")
        self.CheckAmendmentsTab = QWidget()
        self.CheckAmendmentsTab.setObjectName(u"CheckAmendmentsTab")
        self.verticalLayout = QVBoxLayout(self.CheckAmendmentsTab)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.widget_2 = QWidget(self.CheckAmendmentsTab)
        self.widget_2.setObjectName(u"widget_2")
        self.verticalLayout_4 = QVBoxLayout(self.widget_2)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.gridLayout_5 = QGridLayout()
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.label_9 = QLabel(self.widget_2)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout_5.addWidget(self.label_9, 1, 0, 1, 1)

        self.new_compare_XML_btn = QPushButton(self.widget_2)
        self.new_compare_XML_btn.setObjectName(u"new_compare_XML_btn")

        self.gridLayout_5.addWidget(self.new_compare_XML_btn, 2, 1, 1, 1)

        self.select_label_2 = QLabel(self.widget_2)
        self.select_label_2.setObjectName(u"select_label_2")
        self.select_label_2.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout_5.addWidget(self.select_label_2, 2, 0, 1, 1)

        self.old_compare_XML_btn = QPushButton(self.widget_2)
        self.old_compare_XML_btn.setObjectName(u"old_compare_XML_btn")

        self.gridLayout_5.addWidget(self.old_compare_XML_btn, 1, 1, 1, 1)

        self.instruction_label_2 = QLabel(self.widget_2)
        self.instruction_label_2.setObjectName(u"instruction_label_2")
        self.instruction_label_2.setWordWrap(True)

        self.gridLayout_5.addWidget(self.instruction_label_2, 0, 0, 1, 2)

        self.days_between_chk = QCheckBox(self.widget_2)
        self.days_between_chk.setObjectName(u"days_between_chk")

        self.gridLayout_5.addWidget(self.days_between_chk, 3, 1, 1, 1)

        self.gridLayout_5.setColumnStretch(0, 1)
        self.gridLayout_5.setColumnStretch(1, 1)

        self.verticalLayout_4.addLayout(self.gridLayout_5)

        self.create_compare_btn = QPushButton(self.widget_2)
        self.create_compare_btn.setObjectName(u"create_compare_btn")

        self.verticalLayout_4.addWidget(self.create_compare_btn)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_4.addItem(self.verticalSpacer)


        self.verticalLayout.addWidget(self.widget_2)

        self.tabWidget.addTab(self.CheckAmendmentsTab, "")

        self.horizontalLayout.addWidget(self.tabWidget)

        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)

        self.tabWidget.setCurrentIndex(0)
        self.run_btn.setDefault(False)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"SupCheck", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"Change date:", None))
        self.createWorkingFolderBtn.setText(QCoreApplication.translate("MainWindow", u"Create Folder", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"Create working folder:", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"<html><head/><body><p><span style=\" font-weight:700;\">Optional</span></p><p>Ideally you should create a dated folder in <span style=\" font-weight:700;\">PPU - Scripts &gt; added_names_report &gt; _Reports</span>. To do that click, 'Create Folder'.</p></body></html>", None))
        self.label_6.setText(QCoreApplication.translate("MainWindow", u"Note: This button will also create subfolders, Dashboard_Data and Amendment_Paper_XML. Ideally save data downloaded form Shaprepoint in Dashboard_Data and save Amendment paper XML in Amendment_Paper_XML (see below).", None))
        self.get_label.setText(QCoreApplication.translate("MainWindow", u"Get dashboard data:", None))
        self.select_label.setText(QCoreApplication.translate("MainWindow", u"Select dashboard data:", None))
        self.openBrowser_btn.setText(QCoreApplication.translate("MainWindow", u"Open in Browser", None))
        self.xmlFile_btn.setText(QCoreApplication.translate("MainWindow", u"Open File", None))
        self.instruction_label.setText(QCoreApplication.translate("MainWindow", u"The above button should open the added names dashboard data in a web browser.  Once opened,  you must download and save the XML to your computer (ideally within the folder created above). Then open that XML/text file using the button below.", None))
        self.fm_xml_btn.setText(QCoreApplication.translate("MainWindow", u"Select Folder", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"Select marshalling XML folder:", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"<html><head/><body><p><span style=\" font-weight:700;\">Optional</span></p><p>If you want the amendments in the report marshalling: save the XML file(s) for the paper(s) (downloaded from <a href=\"https://lawmaker.legislation.gov.uk/\"><span style=\" text-decoration: underline; color:#094fd1;\">LawMaker</span></a>, or saved from FrameMaker) into a folder (ideally within the folder created above). Select that folder with the button below.</p><p>Note: The marshalling feature works with <span style=\" font-weight:700;\">one</span> or <span style=\" font-weight:700;\">several</span> papers. In either case the XML file(s) need to be saved in a folder and you need to select that folder. Do not try to select a single XML file. Both LM and FM XML files can be used for marshalling.</p></body></html>", None))
        self.run_btn.setText(QCoreApplication.translate("MainWindow", u"Create Added Names Report", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.AddedNamesTab), QCoreApplication.translate("MainWindow", u"Added names report", None))
        self.label_9.setText(QCoreApplication.translate("MainWindow", u"Old XML file", None))
        self.new_compare_XML_btn.setText(QCoreApplication.translate("MainWindow", u"Select File", None))
        self.select_label_2.setText(QCoreApplication.translate("MainWindow", u"New XML file", None))
        self.old_compare_XML_btn.setText(QCoreApplication.translate("MainWindow", u"Select File", None))
        self.instruction_label_2.setText(QCoreApplication.translate("MainWindow", u"<html><head/><body><p>You can create a report compareing consecutive versions of the same amendment paper. This report will show you: Added and removed amendments, Added and removed names, Any stars that have not been changed correctly, and standing amendments with changes.</p><p>Below the <span style=\" font-weight:700;\">old XML file</span> is the XML downloaded from LawMaker for the <span style=\" font-weight:700;\">previously published version</span> of this paper. The <span style=\" font-weight:700;\">new XML file i</span>s the XML downloaded from Lawmaker for the <span style=\" font-weight:700;\">paper you are working on</span>.</p><p>Tick <span style=\" font-weight:700;\">Days between papers</span> if there are sitting days (or printing days) between the papers you are comparing. This is needed to get the star check right. </p></body></html>", None))
        self.days_between_chk.setText(QCoreApplication.translate("MainWindow", u"Days between papers", None))
        self.create_compare_btn.setText(QCoreApplication.translate("MainWindow", u"Create compare report", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.CheckAmendmentsTab), QCoreApplication.translate("MainWindow", u"Check Amendments", None))
    # retranslateUi

