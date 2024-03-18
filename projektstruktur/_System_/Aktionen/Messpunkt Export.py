"""
2018 by Daniel Timmel

Exportiert Punkte für Stationierung
"""
from qgis.core import *
from PyQt5.QtWidgets import QMessageBox, QFileDialog
import os
import operator

layer = qgis.utils.iface.activeLayer()

if layer.selectedFeatureCount() == 0:
    reply = QMessageBox.critical(None, "Meldung", u"Es sind keine Punkte selektiert!", QMessageBox.Abort)
else:
    output_file = QFileDialog.getSaveFileName(None, 'Speicherpfad',
        QgsProject.instance().readPath('./../Jobs'), 'Excel (*.csv);;Alle Dateien (*.*)')

    if output_file[0] != '':
        output_file = open(output_file[0], 'w')

        feats = []

        for feat in layer.selectedFeatures():
            msgout = '%s, %s, %s, %s\n' % (feat["ptnr"], feat["x"], feat["y"], feat["z"])
            unicode_message = msgout.encode('utf-8')
            feats.append(msgout)

        box = QMessageBox()
        box.setIcon(QMessageBox.Question)
        box.setWindowTitle('Frage')
        box.setText('Wie soll sortiert werden?')
        box.setStandardButtons(QMessageBox.Yes|QMessageBox.No)
        buttonY = box.button(QMessageBox.Yes)
        buttonY.setText('Punkt Nr')
        buttonN = box.button(QMessageBox.No)
        buttonN.setText('Datum')
        box.exec_()

        if box.clickedButton() == buttonY:
            s_feats = sorted(feats, key=operator.itemgetter(0))
        elif box.clickedButton() == buttonN:
            s_feats = sorted(feats, key=operator.itemgetter(1))

        #msgout = '%s, %s, %s, %s\n' % ('ptnr','x','y','z')
        #unicode_message = msgout.encode('utf-8')
        #s_feats.insert(0,msgout)
        for item in s_feats:
            output_file.write(item.replace(' ', ''))
        output_file.close()
        QMessageBox.information(None, "Meldung", u"Fertig!")
