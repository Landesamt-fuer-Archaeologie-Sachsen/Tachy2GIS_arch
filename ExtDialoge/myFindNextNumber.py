
# -*- coding=utf-8 -*-


from utils.functions import *
from qgis.PyQt.QtCore import QObject, pyqtSignal, pyqtSlot


class FindNextNumber(QObject):
    nextNumberEmit = pyqtSignal()

    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent)
        #self.pollingTimer = QTimer()
        #self.pollingTimer.timeout.connect(self.poll)
        #self.ser = QSerialPort()
        #self.ser.setBaudRate(baudRate)
        #self.hasLogFile = False
        #self.logFileName = ''
        self.befNr = 0
        self.fundNr = 0
        self.profNr = 0
        self.probNr = 0

    def get(self):
        self.befNr = 0
        self.fundNr = 0
        self.profNr = 0
        self.probNr = 0
        self.nextNumberEmit.emit()
        self.getMaxValues()
        self.nextNumberEmit.emit()

    def getMaxValues(self):
        if getCustomProjectVariable('maxWerteAktualisieren') == True:
            layerLine = QgsProject.instance().mapLayersByName('E_Line')[0]
            layerPoly = QgsProject.instance().mapLayersByName('E_Polygon')[0]
            layerPoint = QgsProject.instance().mapLayersByName('E_Point')[0]
            layerlist = [layerLine, layerPoly, layerPoint]

            self.befNr = 0
            self.fundNr = 0
            self.profNr = 0
            self.probNr = 0

            for layer in layerlist:

                max1 = self.maxValue(layer, 'bef_nr')
                #QgsMessageLog.logMessage(str(max1), 'T2G Archäologie', Qgis.Info)
                if self.befNr < max1:
                    self.befNr = max1

                max2 = self.maxValue(layer, 'fund_nr')
                if self.fundNr < max2:
                    self.fundNr = max2

                max3 = self.maxValue(layer, 'prob_nr')
                if self.probNr < max3:
                    self.probNr = max3

                max4 = self.maxValue(layer, 'prof_nr')
                if self.profNr < max4:
                    self.profNr = max4

            self.befNr = self.befNr + 1
            self.fundNr = self.fundNr + 1
            self.profNr = self.profNr + 1
            self.probNr = self.probNr + 1

            QgsMessageLog.logMessage('1  '+str(self.befNr), 'T2G Archäologie', Qgis.Info)
            QgsMessageLog.logMessage('2  '+str(self.fundNr), 'T2G Archäologie', Qgis.Info)
            QgsMessageLog.logMessage('3  '+str(self.profNr), 'T2G Archäologie', Qgis.Info)
            QgsMessageLog.logMessage('4  '+str(self.probNr), 'T2G Archäologie', Qgis.Info)

    def maxValue(self, layer, fieldname):

        suchstr = fieldname + '!=' + '\'' + '' + '\''
        expr = QgsExpression(suchstr)
        it = layer.getFeatures(QgsFeatureRequest(expr))
        ids = [i.id() for i in it]
        layer.selectByIds(ids)

        values = []
        values.append(0)
        for field in layer.fields():
            if field.name() == fieldname:
                idField = layer.dataProvider().fieldNameIndex(fieldname)
                for feat in layer.selectedFeatures():
                    attrs = feat.attributes()
                    if attrs[idField] != None:
                        try:
                            values.append(int(attrs[idField]))
                        except ValueError:
                            # Zahl aus String extrahieren
                            index = 0
                            a = 0
                            zahl = ''
                            while index < len(attrs[idField]):
                                letter = attrs[idField][index]
                                if isNumber(letter):
                                    a = 1
                                    zahl = zahl + letter
                                else:
                                    if a == 1:
                                        break
                                index = index + 1
                            values.append(int(zahl))
                            pass
        delSelectFeature()

        return int(max(values))

    @pyqtSlot()
    def shutDown(self):
        pass
