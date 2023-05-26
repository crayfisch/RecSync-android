# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'remote_control.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.

import sys

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox
import websocket
import rel
import threading
CONNECTION_URL = "ws://192.168.5.3:7867/remotecon"
class RemoteController(object):

    def __init__(self, MainWindow ) -> None:
        self.setupUi(MainWindow)

    def show_popup(self):
    		msg = QMessageBox()
    		msg.setWindowTitle("Connection Error")
    		msg.setText("Seems like your websocket connection is closed")
    		msg.setIcon(QMessageBox.Critical)
    		msg.exec_()

    def startBtn(self):
        session_prefix = self.download_prefix_text.toPlainText()
        if self.isPrefix(session_prefix):
            try:
                self.ws.send("START_REC@@"+session_prefix)
                self.label.setText('Recording Started')
                self.label.adjustSize()
            except Exception as e:
                self.show_popup()
                with open('last_prefix.txt','w+') as file:
                    file.writelines(session_prefix)
                sys.exit()

    def stopBtn(self):
        self.label.setText('Recording Stopped')
        try:
            self.ws.send("STOP_REC")
        except Exception as e:
            self.show_popup()
            with open('last_prefix.txt','w+') as file:
                file.writelines(self.download_prefix_text.toPlainText())
            sys.exit()

    def statusBtn(self):
        try:
            self.ws.send("STATUS")
            message = self.ws.recv()
            self.status_label.setPlainText(message)
        except Exception as e:
            self.show_popup()
            with open('last_prefix.txt','w+') as file:
                file.writelines(self.download_prefix_text.toPlainText())
            sys.exit()

    def delete_all_btn(self):
        msgBox = QMessageBox()
        msgBox.setText("Are you sure you want to delete all the recordings and related files ?")
        msgBox.setInformativeText("This action cannot be reversed !!!")
        msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msgBox.setDefaultButton(QMessageBox.Cancel)
        ret = msgBox.exec()
        if ret == QMessageBox.Ok:
            try:
                self.ws.send("DELETE_ALL")
            except Exception as e:
                self.show_popup()
                with open('last_prefix.txt','w+') as file:
                    file.writelines(self.download_prefix_text.toPlainText())
                sys.exit()

    def clearStatusBtn(self):
        self.status_label.setPlainText("")

    def prefixList(self):
        try:
            self.ws.send("PREFIX_LIST")
        except Exception as e:
            self.show_popup()
            with open('last_prefix.txt','w+') as file:
                file.writelines(self.download_prefix_text.toPlainText())
            sys.exit()

    def downloadBtn(self):
        endpoint = self.api_input.toPlainText()
        download_prefix = self.download_prefix_text.toPlainText()
        if self.isPrefix(download_prefix):
            self.ws.send("UPLOAD@@"+endpoint+","+download_prefix)

    def isPrefix(self, prefix_text):
        if prefix_text is None or len(prefix_text) == 0:
           self.label.setText('Prefix Text Missing')
           self.label.adjustSize()
           self.label.setStyleSheet("background-color: red")
           return False
        return True

    def phaseAlign(self):
        try:
            self.ws.send("PHASE_ALIGN")
        except Exception as e:
            self.show_popup()
            with open('last_prefix.txt','w+') as file:
                file.writelines(self.download_prefix_text.toPlainText())
            sys.exit()



#     def asyncTask(self, f_stop):
#         self.ws.send("PING")
#         self.ws.recv()
#         if not f_stop.is_set():
#                 # call f() again in 60 seconds
#                 threading.Timer(5, self.asyncTask, [f_stop]).start()

    def setupUi(self, MainWindow):
        # Setup the WEB SOCKET
        #self.ws = websocket.WebSocketApp("ws://192.168.5.2:7867/remotecon")
        self.ws = websocket.WebSocket()
        self.ws.connect(CONNECTION_URL)
#         f_stop = threading.Event()
#         self.asyncTask(f_stop)
        # Setup the GUI
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 800)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(290, 10, 161, 61))
        font = QtGui.QFont()
        #font.setFamily("Source Code Pro")
        font.setPointSize(19)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.start_btn = QtWidgets.QPushButton(self.centralwidget)
        self.start_btn.setGeometry(QtCore.QRect(130, 120, 161, 61))
        self.start_btn.setFont(font)
        self.start_btn.setObjectName("pushButton")
        self.start_btn.clicked.connect(self.startBtn)
        self.stop_btn = QtWidgets.QPushButton(self.centralwidget)
        self.stop_btn.setGeometry(QtCore.QRect(430, 120, 161, 61))
        self.stop_btn.setFont(font)
        self.stop_btn.setObjectName("pushButton_2")
        self.stop_btn.clicked.connect(self.stopBtn)
        self.status_btn = QtWidgets.QPushButton(self.centralwidget)
        self.status_btn.setGeometry(QtCore.QRect(280, 200,  161, 61))
        self.status_btn.setFont(font)
        self.status_btn.setObjectName("pushButton_3")
        self.status_btn.clicked.connect(self.statusBtn)
        self.api_input = QtWidgets.QTextEdit(self.centralwidget)
        self.api_input.setGeometry(QtCore.QRect(143, 450, 451, 31))
        self.api_input.setObjectName("textEdit")
        self.download_prefix_text = QtWidgets.QTextEdit(self.centralwidget)
        self.download_prefix_text.setGeometry(QtCore.QRect(180, 80, 380, 31))
        self.download_prefix_text.setObjectName("prefix_text")
        try:
            with open('last_prefix.txt','r+') as file:
                data = file.readlines()
            if len(data) > 0:
                self.download_prefix_text.setText(data[0])
        except:
            pass

        self.prefix_list_btn = QtWidgets.QPushButton(self.centralwidget)
        self.prefix_list_btn.setGeometry(QtCore.QRect(120, 380, 241, 61))
        self.prefix_list_btn.setFont(font)
        self.prefix_list_btn.setObjectName("prefix_list_button")
        self.prefix_list_btn.clicked.connect(self.prefixList)

        self.download_btn = QtWidgets.QPushButton(self.centralwidget)
        self.download_btn.setGeometry(QtCore.QRect(380, 380, 241, 61))
        self.download_btn.setFont(font)
        self.download_btn.setObjectName("pushButton_4")
        self.download_btn.clicked.connect(self.downloadBtn)

        self.delete_btn = QtWidgets.QPushButton(self.centralwidget)
        self.delete_btn.setGeometry(QtCore.QRect(450, 520, 161, 50))
        self.delete_btn.setFont(font)
        self.delete_btn.setObjectName("pushButton_6")
        self.delete_btn.clicked.connect(self.delete_all_btn)

        self.phase_align_btn = QtWidgets.QPushButton(self.centralwidget)
        self.phase_align_btn.setGeometry(QtCore.QRect(120,520, 161, 50))
        self.phase_align_btn.setFont(font)
        self.phase_align_btn.setObjectName("pushButton_phase")
        self.phase_align_btn.clicked.connect(self.phaseAlign)


        self.status_label = QtWidgets.QPlainTextEdit(self.centralwidget)
        self.status_label.setGeometry(QtCore.QRect(173, 280, 381, 91))
        self.status_label.setObjectName("plainTextEdit")
        self.status_clear_btn = QtWidgets.QPushButton(self.centralwidget)
        self.status_clear_btn.setGeometry(QtCore.QRect(560, 341, 31, 31))
        self.status_clear_btn.setFont(font)
        self.status_clear_btn.setObjectName("pushButton_5")
        self.status_clear_btn.clicked.connect(self.clearStatusBtn)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 21))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Remote Control App"))
        self.label.setText(_translate("MainWindow", "RC APP"))
        self.start_btn.setText(_translate("MainWindow", "Start"))
        self.stop_btn.setText(_translate("MainWindow", "Stop"))
        self.status_btn.setText(_translate("MainWindow", "Status"))
        self.status_clear_btn.setText(_translate("MainWindow", "X"))
        self.status_clear_btn.setStyleSheet('QPushButton {;color: red;}')
        self.delete_btn.setText(_translate("MainWindow", "Empty Device"))
        self.delete_btn.setStyleSheet('QPushButton {;background-color: red;}')
        self.api_input.setPlaceholderText(_translate("MainWindow", "Please enter the api endpoint where you want the files to be uploaded."))
        self.download_prefix_text.setPlaceholderText(_translate("MainWindow", " Enter Session Prefix"))
        self.download_btn.setText(_translate("MainWindow", "Download"))
        self.prefix_list_btn.setText(_translate("MainWindow", "Prefix List"))
        self.phase_align_btn.setText(_translate("MainWindow", "Phase Align"))
        self.status_label.setPlaceholderText(_translate("MainWindow", "No status "))


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    rc = RemoteController(MainWindow)
    rc.setupUi(MainWindow)

    MainWindow.show()
    sys.exit(app.exec_())
