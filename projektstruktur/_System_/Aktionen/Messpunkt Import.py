"""
2018 by Daniel Timmel

Importiert Punkte aus csv datei
"""
from qgis.core import *
from PyQt5.QtWidgets import QMessageBox, QFileDialog
import os, csv, datetime

result = QMessageBox.information(None,'WICHTIG','Dateiformat csv'+'\n'+'ptnr,x,y,z'+'\n'+'Möchten Sie fortfahren?            ',QMessageBox.Ok|QMessageBox.Cancel)
if result == QMessageBox.Ok:
    layer = qgis.utils.iface.activeLayer()

    input_file = QFileDialog.getOpenFileName(None, 'Quellpfad',
        QgsProject.instance().readPath('./../Jobs'), 'Excel (*.csv);;Alle Dateien (*.*)')

    with open(str(input_file [0])) as csvfile:
        readerCSV = csv.reader(csvfile,delimiter=',')
        for row in readerCSV:
            attL = {'ptnr': str(row[0]), 'x': str(row[1]), 'y': str(row[2]), 'z': str(row[3])}
            point = QgsPoint(float(row[1]), float(row[2]), float(row[3]))
            layer.startEditing()
            feature = QgsFeature()
            fields = layer.fields()
            feature.setFields(fields)
            feature.setGeometry(QgsGeometry(point))
            # Attribute
            layer.dataProvider().addFeatures([feature])
            layer.updateExtents()
            layer.commitChanges()
            features = [feature for feature in layer.getFeatures()]
            lastfeature = features[-1]
            layer.startEditing()

            idfeld = layer.dataProvider().fieldNameIndex('id')
            if layer.maximumValue(idfeld) == None:
                nextid = 0
            else:
                nextid = layer.maximumValue(idfeld) + 1
            layer.changeAttributeValue(lastfeature.id(), idfeld, int(nextid))
            # Projektvariablen holen
            project = QgsProject.instance()
            aktcode = QgsExpressionContextUtils.projectScope(project).variable('aktcode')
            # weitere automatische Attribute
            idMesDatum = layer.dataProvider().fieldNameIndex('messdatum')
            idAktCode = layer.dataProvider().fieldNameIndex('aktCode')
            layer.changeAttributeValue(lastfeature.id(), idMesDatum, str(datetime.datetime.now()))
            layer.changeAttributeValue(lastfeature.id(), idAktCode, aktcode)
            QgsMessageLog.logMessage(str(nextid), 'Attribute', Qgis.Info)

            for item in attL:
                #QgsMessageLog.logMessage(str(item), 'Attribute', Qgis.Info)
                fIndex = layer.dataProvider().fieldNameIndex(item)
                layer.changeAttributeValue(lastfeature.id(), fIndex, attL[item])

            layer.commitChanges()
        QMessageBox.information(None, "Meldung", u"Fertig!")
