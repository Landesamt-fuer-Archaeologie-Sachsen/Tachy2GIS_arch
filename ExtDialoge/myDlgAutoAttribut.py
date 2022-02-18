# -*- coding: utf-8 -*-
from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets, QtCore, QtGui, uic
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from qgis.core import *
from qgis.gui import *
from ..functions import *
from ..t2g_arch_dockwidget import T2G_ArchDockWidget


class dlgAutoAttribut(QtWidgets.QDialog):
    def __init__(self, iface, dialog, parent=None):
        super(dlgAutoAttribut, self).__init__(parent)
        pfad = os.path.abspath(os.path.join(os.path.join(os.path.dirname(__file__), "./..")))
        iconpfad = os.path.join(os.path.join(pfad,'Icons'))
        self.ui = uic.loadUi(os.path.join(pfad, 'ExtDialoge/myDlgAutoAttribut.ui'), self)
        #self.ui.setWindowIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), 'Icons/Ptneu.jpg')))
        self.iface = iface
        self.dialog = dialog
        self.ui.txtReflH.textChanged.connect(self.setStatAttribute)
        self.ui.butRefHDel.setIcon(QIcon(os.path.join(iconpfad, 'del.gif')))
        self.ui.butRefHDel.clicked.connect(self.delReflH)
        self.ui.butRefHDel.setToolTip('Reflektorhöhe löschen')
        self.ui.butAttDel.clicked.connect(self.delAutoAttribut)
        self.ui.butAttDel.setIcon(QtGui.QIcon(os.path.join(pfad, 'Icons/del.gif')))
        self.ui.cboobjTyp.currentIndexChanged.connect(self.fillcboobjArt)
        self.ui.groupBox_3.clicked.connect(self.autoAttEinAus)
        self.ui.groupBox_2.clicked.connect(self.zaehlenEinAus)
        self.ui.chkBefZahl.stateChanged.connect(self.nextValue)
        self.ui.chkProfZahl.stateChanged.connect(self.nextValue)
        self.ui.chkFundZahl.stateChanged.connect(self.nextValue)
        self.ui.chkProbZahl.stateChanged.connect(self.nextValue)
        self.ui.chkptnrZahl.stateChanged.connect(self.nextValue)
        self.ui.txtptnr.textChanged.connect(self.setNextptnr)
        self.ui.setup()

    def setup(self):
        self.ui.groupBox_2.hide()

        self.QgisDateiPfad = QgsProject.instance().readPath('./')
        self.ProjPfad = os.path.abspath(os.path.join(self.QgisDateiPfad, "./.."))

        if self.iface.activeLayer():
            self.ui.labActLayer.setText('akt. Layer:    ' + self.iface.activeLayer().name())
        else:
            self.ui.labActLayer.setText('akt. Layer:    ')


        self.getStatAttribute()
        self.getAutoAttribute()

    def delAutoAttribut(self):
        self.ui.cboobjTyp.setCurrentText('')
        self.ui.cboobjArt.setCurrentText('')
        self.ui.txtSchnittNr.setText('')
        self.ui.txtBefNr.setText('')
        self.ui.txtPlanum.setText('')
        self.ui.txtFundNr.setText('')
        self.ui.txtProbeNr.setText('')
        self.ui.txtProfilNr.setText('')
        self.ui.cboMaterial.setCurrentText('')

    def autoAttEinAus(self):
        if self.ui.groupBox_3.isChecked() == True:
            setCustomProjectVariable('autoAttribute', 'True')
        else:
            self.ui.groupBox_2.setChecked(False)
            setCustomProjectVariable('autoAttribute', 'False')

    def zaehlenEinAus(self):
        if self.ui.groupBox_2.isChecked() == True:
            self.ui.groupBox_3.setChecked(True)
            setCustomProjectVariable('autoAttribute', 'True')
            setCustomProjectVariable('autoZahl', 'True')
        else:
            self.ui.groupBox_3.setChecked(False)
            setCustomProjectVariable('autoAttribute', 'False')
            setCustomProjectVariable('autoZahl', 'False')
            self.nextValue()

    def nextValue(self):
        if self.ui.chkBefZahl.isChecked() == True:
            #setCustomProjectVariable('nextBefNr','True')
            self.ui.txtBefNr.setText(self.dialog.txtNextBef.text())
        else:
            #setCustomProjectVariable('nextBefNr', 'False')
            self.ui.txtBefNr.setText('')

        if self.ui.chkProfZahl.isChecked() == True:
            #setCustomProjectVariable('nextProfNr','True')
            self.ui.txtProfilNr.setText(self.dialog.txtNextProf.text())
        else:
            #setCustomProjectVariable('nextProfNr', 'False')
            self.ui.txtProfilNr.setText('')

        if self.ui.chkFundZahl.isChecked() == True:
            #setCustomProjectVariable('nextFundNr','True')
            self.ui.txtFundNr.setText(self.dialog.txtNextFund.text())
        else:
            setCustomProjectVariable('nextFundNr', 'False')
            self.ui.txtFundNr.setText('')

        if self.ui.chkProbZahl.isChecked() == True:
            #setCustomProjectVariable('nextProbNr','True')
            self.ui.txtProbeNr.setText(self.dialog.txtNextProb.text())
        else:
            #setCustomProjectVariable('nextProbNr', 'False')
            self.ui.txtProbeNr.setText('')

        if self.ui.chkptnrZahl.isChecked() == True:
            self.ui.txtptnr.setText('Bitte Nummer eingeben')
        else:
            #setCustomProjectVariable('nextptnrNr','False')
            self.ui.txtptnr.setText('')

    def setNextptnr(self):
        setCustomProjectVariable('ptnr', self.ui.txtptnr.text())

    def closeEvent(self, QCloseEvent):
        self.setStatAttribute()
        self.setAutoAttribute()

    def setStatAttribute(self):
        setCustomProjectVariable('aktcode', self.ui.txtAkt.text())
        self.ui.txtReflH.setText(self.ui.txtReflH.text().replace(',', '.'))
        if len(self.ui.txtReflH.text()) == 0:
            setCustomProjectVariable('reflH', '')
        if isNumber(self.ui.txtReflH.text()):
            setCustomProjectVariable('reflH', str(self.ui.txtReflH.text()))
        else:
            if self.ui.txtReflH.text() != '':
                QMessageBox.warning(None, "Achtung", 'Reflektorhöhe ist keine Zahl!')
        setCustomProjectVariable('geo-arch', str(self.ui.cboArchGeo.currentText()))

    def delReflH(self):
        setCustomProjectVariable('reflH', '')
        self.ui.txtReflH.setText('')

    def delReflHUpdate(self):
        if self.ui.txtReflH.text == '':
            setCustomProjectVariable('reflH', '')

    def setAutoAttribute(self):
        setCustomProjectVariable('obj_type', self.ui.cboobjTyp.currentText())
        setCustomProjectVariable('obj_art', self.ui.cboobjArt.currentText())
        setCustomProjectVariable('schnitt_nr', self.ui.txtSchnittNr.text())
        setCustomProjectVariable('bef_nr', self.ui.txtBefNr.text())
        setCustomProjectVariable('planum', self.ui.txtPlanum.text())
        setCustomProjectVariable('fund_nr', self.ui.txtFundNr.text())
        setCustomProjectVariable('prob_nr', self.ui.txtProbeNr.text())
        setCustomProjectVariable('prof_nr', self.ui.txtProfilNr.text())
        setCustomProjectVariable('ptnr', self.ui.txtptnr.text())
        setCustomProjectVariable('material', self.ui.cboMaterial.currentText())

    def getStatAttribute(self):
        self.ui.txtAkt.setText(getCustomProjectVariable('aktcode'))
        self.ui.txtReflH.setText(getCustomProjectVariable('reflH'))
        self.ui.cboArchGeo.setCurrentText(getCustomProjectVariable('geo-arch'))

    def getAutoAttribute(self):
        if getCustomProjectVariable('autoAttribute') == 'True':
            self.ui.groupBox_3.setChecked(True)
        else:
            self.ui.groupBox_3.setChecked(False)
        if getCustomProjectVariable('autoZahl') == 'True':
            self.ui.groupBox_2.setChecked(True)
        else:
            self.ui.groupBox_2.setChecked(False)

        self.ui.cboobjTyp.clear()
        if self.iface.activeLayer():
            if self.iface.activeLayer().name() == 'E_Point':
                swert='Punkt'
            else:
                swert='Linie'
            self.ui.cboobjTyp.addItem('')
            self.ui.cboobjTyp.addItems(csvListfilter(os.path.join(self.ProjPfad, 'Listen\Objekttypen.csv'), 0, 4, swert,''))

        self.ui.cboobjTyp.setCurrentText(getCustomProjectVariable('obj_type'))
        self.ui.cboobjArt.setCurrentText(getCustomProjectVariable('obj_art'))
        self.ui.txtSchnittNr.setText(getCustomProjectVariable('schnitt_nr'))
        self.ui.txtBefNr.setText(getCustomProjectVariable('bef_nr'))
        self.ui.txtPlanum.setText(getCustomProjectVariable('planum'))
        self.ui.txtFundNr.setText(getCustomProjectVariable('fund_nr'))
        self.ui.txtProbeNr.setText(getCustomProjectVariable('prob_nr'))
        self.ui.txtProfilNr.setText(getCustomProjectVariable('prof_nr'))
        self.ui.txtptnr.setText(getCustomProjectVariable('ptnr'))
        self.ui.cboMaterial.setCurrentText(getCustomProjectVariable('material'))

    def fillcboobjArt(self):
        swert = '|' + self.ui.cboobjTyp.currentText() + '|'
        self.ui.cboobjArt.clear()
        self.ui.cboMaterial.clear()
        self.ui.cboobjArt.addItem('')
        self.ui.cboMaterial.addItem('')
        if self.iface.activeLayer().name() == 'E_Point':
            self.ui.cboobjArt.addItems(csvListfilter(os.path.join(self.ProjPfad ,'Listen\Objektarten.csv'), 0, 1, swert,''))
        else:
            self.ui.cboobjArt.addItems(csvListfilter(os.path.join(self.ProjPfad, 'Listen\Objektarten.csv'), 0, 1, swert,''))

        self.ui.cboMaterial.addItems(csvListfilter(os.path.join(self.ProjPfad, 'Listen\Material.csv'), 0, 1, swert,''))
