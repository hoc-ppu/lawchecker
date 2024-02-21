# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'addedNames.ui'
##
## Created by: Qt User Interface Compiler version 6.6.2
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
        self.verticalLayout_5 = QVBoxLayout(self.centralwidget)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
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
        sizePolicy = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
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

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_4.addItem(self.verticalSpacer)


        self.verticalLayout.addWidget(self.widget_2)

        self.tabWidget.addTab(self.CheckAmendmentsTab, "")
        self.CompareBillsTab = QWidget()
        self.CompareBillsTab.setObjectName(u"CompareBillsTab")
        self.verticalLayout_7 = QVBoxLayout(self.CompareBillsTab)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.gridLayout_6 = QGridLayout()
        self.gridLayout_6.setObjectName(u"gridLayout_6")
        self.select_label_3 = QLabel(self.CompareBillsTab)
        self.select_label_3.setObjectName(u"select_label_3")
        self.select_label_3.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout_6.addWidget(self.select_label_3, 2, 0, 1, 1)

        self.widget_6 = QWidget(self.CompareBillsTab)
        self.widget_6.setObjectName(u"widget_6")
        self.widget_6.setMinimumSize(QSize(0, 15))
        self.horizontalLayout_2 = QHBoxLayout(self.widget_6)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.new_bill_XML_btn = QPushButton(self.widget_6)
        self.new_bill_XML_btn.setObjectName(u"new_bill_XML_btn")

        self.horizontalLayout_2.addWidget(self.new_bill_XML_btn)

        self.bill_new_xml_lbl = QLabel(self.widget_6)
        self.bill_new_xml_lbl.setObjectName(u"bill_new_xml_lbl")

        self.horizontalLayout_2.addWidget(self.bill_new_xml_lbl)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_4)


        self.gridLayout_6.addWidget(self.widget_6, 2, 1, 1, 1)

        self.widget_5 = QWidget(self.CompareBillsTab)
        self.widget_5.setObjectName(u"widget_5")
        self.widget_5.setMinimumSize(QSize(0, 15))
        self.widget_5.setMaximumSize(QSize(16777215, 16777215))
        self.horizontalLayout = QHBoxLayout(self.widget_5)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.old_bill_XML_btn = QPushButton(self.widget_5)
        self.old_bill_XML_btn.setObjectName(u"old_bill_XML_btn")

        self.horizontalLayout.addWidget(self.old_bill_XML_btn)

        self.bill_old_xml_lbl = QLabel(self.widget_5)
        self.bill_old_xml_lbl.setObjectName(u"bill_old_xml_lbl")

        self.horizontalLayout.addWidget(self.bill_old_xml_lbl)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_3)


        self.gridLayout_6.addWidget(self.widget_5, 1, 1, 1, 1)

        self.instruction_label_3 = QLabel(self.CompareBillsTab)
        self.instruction_label_3.setObjectName(u"instruction_label_3")
        self.instruction_label_3.setWordWrap(True)

        self.gridLayout_6.addWidget(self.instruction_label_3, 0, 0, 1, 2)

        self.label_10 = QLabel(self.CompareBillsTab)
        self.label_10.setObjectName(u"label_10")
        self.label_10.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout_6.addWidget(self.label_10, 1, 0, 1, 1)

        self.gridLayout_6.setColumnStretch(0, 1)
        self.gridLayout_6.setColumnStretch(1, 3)

        self.verticalLayout_7.addLayout(self.gridLayout_6)

        self.widget_3 = QWidget(self.CompareBillsTab)
        self.widget_3.setObjectName(u"widget_3")
        self.gridLayout_7 = QGridLayout(self.widget_3)
        self.gridLayout_7.setObjectName(u"gridLayout_7")
        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_7.addItem(self.horizontalSpacer_2, 1, 2, 1, 1)

        self.widget_4 = QWidget(self.widget_3)
        self.widget_4.setObjectName(u"widget_4")
        self.verticalLayout_6 = QVBoxLayout(self.widget_4)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.create_bill_compare_btn = QPushButton(self.widget_4)
        self.create_bill_compare_btn.setObjectName(u"create_bill_compare_btn")

        self.verticalLayout_6.addWidget(self.create_bill_compare_btn)

        self.compare_vs_code_btn = QPushButton(self.widget_4)
        self.compare_vs_code_btn.setObjectName(u"compare_vs_code_btn")

        self.verticalLayout_6.addWidget(self.compare_vs_code_btn)


        self.gridLayout_7.addWidget(self.widget_4, 1, 1, 1, 1)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_7.addItem(self.horizontalSpacer, 1, 0, 1, 1)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_7.addItem(self.verticalSpacer_3, 0, 1, 1, 1)


        self.verticalLayout_7.addWidget(self.widget_3)

        self.verticalSpacer1 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_7.addItem(self.verticalSpacer1)

        self.tabWidget.addTab(self.CompareBillsTab, "")
        self.Numbering = QWidget()
        self.Numbering.setObjectName(u"Numbering")
        self.verticalLayout_8 = QVBoxLayout(self.Numbering)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.gridLayout_4 = QGridLayout()
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.createCSVs = QPushButton(self.Numbering)
        self.createCSVs.setObjectName(u"createCSVs")

        self.gridLayout_4.addWidget(self.createCSVs, 3, 1, 1, 1)

        self.selectNumberingFolder = QPushButton(self.Numbering)
        self.selectNumberingFolder.setObjectName(u"selectNumberingFolder")

        self.gridLayout_4.addWidget(self.selectNumberingFolder, 1, 1, 1, 1)

        self.label_8 = QLabel(self.Numbering)
        self.label_8.setObjectName(u"label_8")
        self.label_8.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout_4.addWidget(self.label_8, 1, 0, 1, 1)

        self.label_7 = QLabel(self.Numbering)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setWordWrap(True)

        self.gridLayout_4.addWidget(self.label_7, 0, 0, 1, 2)

        self.label_12 = QLabel(self.Numbering)
        self.label_12.setObjectName(u"label_12")
        self.label_12.setWordWrap(True)

        self.gridLayout_4.addWidget(self.label_12, 2, 0, 1, 2)


        self.verticalLayout_8.addLayout(self.gridLayout_4)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_8.addItem(self.verticalSpacer_2)

        self.tabWidget.addTab(self.Numbering, "")

        self.verticalLayout_5.addWidget(self.tabWidget)

        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)

        self.tabWidget.setCurrentIndex(2)
        self.run_btn.setDefault(False)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"LawChecker", None))
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
        self.select_label_3.setText(QCoreApplication.translate("MainWindow", u"New XML file", None))
        self.new_bill_XML_btn.setText(QCoreApplication.translate("MainWindow", u"Select File", None))
        self.bill_new_xml_lbl.setText("")
        self.old_bill_XML_btn.setText(QCoreApplication.translate("MainWindow", u"Select File", None))
        self.bill_old_xml_lbl.setText("")
        self.instruction_label_3.setText(QCoreApplication.translate("MainWindow", u"<html><head/><body><p>You can create a report comparing different versions of a bill (e.g. the 2nd reading and as amended in committee). This report will show you: Added and removed clauses or schedule paragraphs, and standing clauses and schedule paragraphs with changes.</p><p>Below the old XML file is the XML downloaded from LawMaker for the older version of this bill. The new XML file is the XML downloaded from Lawmaker for the newer version of this bill.</p><p>Tick VS Code compare to create a comparison of the bills using the diff feature of <a href=\"https://code.visualstudio.com/\"><span style=\" text-decoration: underline; color:#094fd1;\">VS Code</span></a>. Note you must have VS Code installed to use this feature.</p><p><br/></p></body></html>", None))
        self.label_10.setText(QCoreApplication.translate("MainWindow", u"Old XML file", None))
        self.create_bill_compare_btn.setText(QCoreApplication.translate("MainWindow", u"Create HTML compare report", None))
        self.compare_vs_code_btn.setText(QCoreApplication.translate("MainWindow", u"Compare in VS Code", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.CompareBillsTab), QCoreApplication.translate("MainWindow", u"Compare Bills", None))
        self.createCSVs.setText(QCoreApplication.translate("MainWindow", u"Create CSV(s)", None))
        self.selectNumberingFolder.setText(QCoreApplication.translate("MainWindow", u"Select Folder", None))
        self.label_8.setText(QCoreApplication.translate("MainWindow", u"Select folder containing XML:", None))
        self.label_7.setText(QCoreApplication.translate("MainWindow", u"Compare the numbering of sections (a.k.a. clauses) and schedule paragraphs in two or more versions of a UK parliament bill. The bills must be provided as LawMaker XML. The output is CSV file(s) which indicate when sections or schedule paragraphs are insearted or removed. You can also process several different bills at once, e.g. bill A (with 3 versions) and bill B (with 2 versions).\n"
"\n"
"Use the button below to select a folder which contains Bill XML files. ", None))
        self.label_12.setText(QCoreApplication.translate("MainWindow", u"Use the button below to create CSV file(s) showing numbering changes between a versions of (a) bill(s).", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.Numbering), QCoreApplication.translate("MainWindow", u"Numbering", None))
    # retranslateUi

