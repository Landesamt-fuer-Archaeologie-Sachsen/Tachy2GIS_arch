
from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtGui import *

class Textadjustment(object):
    """docstring for ."""

    def __init__(self, t2gArchInstance, textScale):
        super(Textadjustment, self).__init__()
        self.__t2gArchInstance = t2gArchInstance
        self.__dockwidget = t2gArchInstance.dockwidget
        self.textScale = textScale


    def setText(self):
        f = float(self.textScale)
        w = self.__dockwidget
        w.label_2.setFont(QFont('MS Shell Dlg 2', 8*f))
        w.txtAkt.setFont(QFont('MS Shell Dlg 2', 11*f, weight=QFont.Bold))
        w.cboFigur.setFont(QFont('MS Shell Dlg 2', 8*f))
        w.label_3.setFont(QFont('MS Shell Dlg 2', 8*f))
        w.txtZKoord.setFont(QFont('MS Shell Dlg 2', 8*f))
        w.butCreateFeature.setFont(QFont('MS Shell Dlg 2', 8*f))
        w.butClear.setFont(QFont('MS Shell Dlg 2', 8*f))
        w.chbAutoAtt.setFont(QFont('MS Shell Dlg 2', 8*f))
        #w.chbAutoAtt.setStyleSheet("QCheckBox::indicator"
        #                       "{"
        #                       "width :10px;"
        #                       "height : 10px;"
        #                       "}")
        w.chbAttributtable.setFont(QFont('MS Shell Dlg 2', 7*f))
        w.labPointCount.setFont(QFont('MS Shell Dlg 2', 8*f))
        w.tabWidget.setFont(QFont('MS Shell Dlg 2', 8*f))
        w.tabWidget_2.setFont(QFont('MS Shell Dlg 2', 9*f))
        w.tabWidget.setStyleSheet("QTabBar::tab { height: 20px; width: 100px; }")
        w.tableWidget.horizontalHeader().setFixedHeight(20)
        w.tableWidget.setStyleSheet("QHeaderView { font-size: 5pt; }")
        w.tableWidget_2.horizontalHeader().setFixedHeight(20)
        w.tableWidget_2.setStyleSheet("QHeaderView { font-size: 5pt; }")
        w.tableWidget.setFont(QFont('MS Shell Dlg 2', 9*f))
        w.label_27.setFont(QFont('MS Shell Dlg 2', 8*f))
        w.label_9.setStyleSheet("QLabel {color: green}")
        w.label_34.setFont(QFont('MS Shell Dlg 2', 8*f))
        w.label_35.setFont(QFont('MS Shell Dlg 2', 8*f))

        w.label_28.setFont(QFont('MS Shell Dlg 2', 8*f))
        w.label_30.setFont(QFont('MS Shell Dlg 2', 8*f))
        w.label_29.setFont(QFont('MS Shell Dlg 2', 8*f))
        w.label_31.setFont(QFont('MS Shell Dlg 2', 8*f))
        w.label_32.setFont(QFont('MS Shell Dlg 2', 8*f))
        w.label_33.setFont(QFont('MS Shell Dlg 2', 8*f))

        w.label_5.setFont(QFont('MS Shell Dlg 2', 8*f))
        w.label_4.setFont(QFont('MS Shell Dlg 2', 8*f))
        w.label_8.setFont(QFont('MS Shell Dlg 2', 8*f))
        w.label_6.setFont(QFont('MS Shell Dlg 2', 8*f))
        w.label_7.setFont(QFont('MS Shell Dlg 2', 8*f))

        w.txtPoint_2.hide()
        w.txtPointTemp_2.hide()
        w.cboArchGeo.hide()
        w.butBefundLabel.hide()

        w.cboobjTyp.setStyleSheet("color:blue")
        w.cboobjArt.setStyleSheet("color:blue")
        w.txtSchnittNr.setStyleSheet("color:blue")
        w.txtPlanum.setStyleSheet("color:blue")
        w.txtBefNr.setStyleSheet("color:blue")
        w.txtProfilNr.setStyleSheet("color:blue")
        w.txtptnr.setStyleSheet("color:blue")
        w.txtFundNr.setStyleSheet("color:blue")
        w.txtProbeNr.setStyleSheet("color:blue")
        w.cboMaterial.setStyleSheet("color:blue")
