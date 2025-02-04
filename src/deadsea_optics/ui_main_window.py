# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
##
## Created by: Qt User Interface Compiler version 6.8.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import QCoreApplication, QMetaObject, QRect
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMenu,
    QMenuBar,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from pyqtgraph import PlotWidget


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        self.actionAbout_DeadSea_Optics = QAction(MainWindow)
        self.actionAbout_DeadSea_Optics.setObjectName("actionAbout_DeadSea_Optics")
        self.actionQuit = QAction(MainWindow)
        self.actionQuit.setObjectName("actionQuit")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.plot_widget = PlotWidget(self.centralwidget)
        self.plot_widget.setObjectName("plot_widget")

        self.horizontalLayout.addWidget(self.plot_widget)

        self.formLayout = QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.integrationTimeSLabel = QLabel(self.centralwidget)
        self.integrationTimeSLabel.setObjectName("integrationTimeSLabel")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.integrationTimeSLabel)

        self.integration_time = QSpinBox(self.centralwidget)
        self.integration_time.setObjectName("integration_time")
        self.integration_time.setMinimum(10000)
        self.integration_time.setMaximum(100000000)
        self.integration_time.setSingleStep(1000)
        self.integration_time.setValue(100000)

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.integration_time)

        self.integrationsLabel = QLabel(self.centralwidget)
        self.integrationsLabel.setObjectName("integrationsLabel")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.integrationsLabel)

        self.num_integrations = QSpinBox(self.centralwidget)
        self.num_integrations.setObjectName("num_integrations")
        self.num_integrations.setMinimum(1)
        self.num_integrations.setMaximum(1000)
        self.num_integrations.setValue(20)

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.num_integrations)

        self.horizontalLayout.addLayout(self.formLayout)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.single_button = QPushButton(self.centralwidget)
        self.single_button.setObjectName("single_button")

        self.horizontalLayout_2.addWidget(self.single_button)

        self.continuous_button = QPushButton(self.centralwidget)
        self.continuous_button.setObjectName("continuous_button")

        self.horizontalLayout_2.addWidget(self.continuous_button)

        self.integrate_button = QPushButton(self.centralwidget)
        self.integrate_button.setObjectName("integrate_button")

        self.horizontalLayout_2.addWidget(self.integrate_button)

        self.stop_button = QPushButton(self.centralwidget)
        self.stop_button.setObjectName("stop_button")

        self.horizontalLayout_2.addWidget(self.stop_button)

        self.toggle_lines_button = QPushButton(self.centralwidget)
        self.toggle_lines_button.setObjectName("toggle_lines_button")

        self.horizontalLayout_2.addWidget(self.toggle_lines_button)

        self.save_button = QPushButton(self.centralwidget)
        self.save_button.setObjectName("save_button")

        self.horizontalLayout_2.addWidget(self.save_button)

        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.progress_bar = QProgressBar(self.centralwidget)
        self.progress_bar.setObjectName("progress_bar")
        self.progress_bar.setValue(0)

        self.verticalLayout.addWidget(self.progress_bar)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName("menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 37))
        self.menuHelp = QMenu(self.menubar)
        self.menuHelp.setObjectName("menuHelp")
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())
        self.menuHelp.addAction(self.actionAbout_DeadSea_Optics)
        self.menuFile.addAction(self.actionQuit)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)

    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(
            QCoreApplication.translate("MainWindow", "DeadSea Optics", None)
        )
        self.actionAbout_DeadSea_Optics.setText(
            QCoreApplication.translate("MainWindow", "About DeadSea Optics", None)
        )
        self.actionQuit.setText(QCoreApplication.translate("MainWindow", "Quit", None))
        self.integrationTimeSLabel.setText(
            QCoreApplication.translate("MainWindow", "Integration time (\u00b5s)", None)
        )
        self.integrationsLabel.setText(
            QCoreApplication.translate("MainWindow", "# integrations", None)
        )
        self.single_button.setText(
            QCoreApplication.translate("MainWindow", "Single", None)
        )
        self.continuous_button.setText(
            QCoreApplication.translate("MainWindow", "Continuous", None)
        )
        self.integrate_button.setText(
            QCoreApplication.translate("MainWindow", "Integrate", None)
        )
        self.stop_button.setText(QCoreApplication.translate("MainWindow", "Stop", None))
        self.toggle_lines_button.setText(
            QCoreApplication.translate("MainWindow", "Toggle lines/markers", None)
        )
        self.save_button.setText(
            QCoreApplication.translate("MainWindow", "Save data", None)
        )
        self.menuHelp.setTitle(QCoreApplication.translate("MainWindow", "Help", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", "File", None))

    # retranslateUi
