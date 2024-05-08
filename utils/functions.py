# -*- coding: utf-8 -*-
import csv
import datetime
import os
import os.path
import re
import shutil
import time
from datetime import *  # date, datetime

from qgis.PyQt import QtWidgets
from qgis.PyQt.QtCore import Qt, QUrl, pyqtSignal
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QDesktopWidget, QGridLayout, QMessageBox, QLabel, QProgressBar, QTextBrowser, QWidget
from qgis.core import (
    QgsExpressionContextUtils,
    QgsFeature,
    QgsFeatureRequest,
    QgsField,
    QgsGeometry,
    QgsLayerTreeGroup,
    QgsLayerTreeLayer,
    QgsMapLayer,
    QgsPoint,
    QgsPointXY,
    QgsProject,
    QgsVectorLayer,
    QgsWkbTypes,
)
from qgis.gui import QgsMapToolEmitPoint, QgsRubberBand, QgsVertexMarker
from qgis.utils import iface


def natural_sort_key(s, _nsre=re.compile("([0-9]+)")):
    return [int(text) if text.isdigit() else text.lower() for text in _nsre.split(s)]


def getLookupDict(layer, keyColumn, valueColumn, filterExpression=""):
    lookupDict = {}
    if layer.fields().indexOf(keyColumn) == -1 or layer.fields().indexOf(valueColumn) == -1:
        return lookupDict
    request = QgsFeatureRequest()
    if filterExpression:
        request.setFilterExpression(filterExpression)
    for feature in layer.getFeatures(request):
        lookupDict[feature.attribute(keyColumn)] = feature.attribute(valueColumn)
    return lookupDict


def setCustomProjectVariable(variableName, variableWert):
    project = QgsProject.instance()
    QgsExpressionContextUtils.setProjectVariable(project, variableName, variableWert)


def getCustomProjectVariable(variableName):
    project = QgsProject.instance()
    variable = QgsExpressionContextUtils.projectScope(project).variable(variableName)
    if not variable:
        return ""
    else:
        return variable


def delCustomProjectVariable(variableName):
    project = QgsProject.instance()
    QgsExpressionContextUtils.removeProjectVariable(project, variableName)


def showAndHideWidgets(widgetsToShow, widgetsToHide):
    for wg in widgetsToShow:
        wg.show()
    for wg in widgetsToHide:
        wg.hide()


def enableAndDisableWidgets(enableWidgets, disableWidgets):
    for wg in enableWidgets:
        wg.setEnabled(True)
    for wg in disableWidgets:
        wg.setEnabled(False)


def layerHasPendingChanges(layer: QgsVectorLayer):
    buffer = layer.editBuffer()
    if not buffer:
        return False
    return bool(len(buffer.changedGeometries()) + len(buffer.changedAttributeValues()))


def findLayerInProject(name):
    mapLayers = QgsProject.instance().mapLayers()
    for lyr in mapLayers.values():
        if lyr.name() == name:
            return lyr


class ProjectSaveFunc:
    # ToDo: Currently without use
    def projectSave(self, source):
        try:
            currentDate = time.strftime("%Y.%m.%d")
            currentTime = time.strftime("%H-%M")
            target = os.path.join(source, r"_Sicherungen_", currentDate + "_" + currentTime)

            fileFunc().directory_copy(os.path.join(source, "GPKG Files"), os.path.join(target, "GPKG Files"))
            fileFunc().directory_copy(os.path.join(source, "Shape"), os.path.join(target, "Shape"))
            fileFunc().directory_copy(os.path.join(source, "Projekt"), os.path.join(target, "Projekt"))

            os.remove(os.path.join(target, "Projekt", "intro.py"))
            fileFunc().directory_del(os.path.join(target, "Projekt", "__pycache__"))
            return True
        except:
            fileFunc().directory_del(target)
            return False

    def dayprojectSave(self, copyFrom):
        now = datetime.now()  # current date and time
        currentDate = now.strftime("%Y.%m.%d")
        currentTime = now.strftime("%H-%M")
        copyTo = os.path.join(copyFrom, r"_Tagesdateien_", currentDate + "_" + currentTime)

        try:
            fileFunc().directory_copy(os.path.join(copyFrom, "GPKG Files"), os.path.join(copyTo, "GPKG_Files"))
            fileFunc().directory_copy(os.path.join(copyFrom, "Shape"), os.path.join(copyTo, "Shape"))
            fileFunc().directory_copy(os.path.join(copyFrom, "Projekt"), os.path.join(copyTo, "Projekt"))

            os.remove(os.path.join(copyTo, "Projekt", "intro.py"))
            fileFunc().directory_del(os.path.join(copyTo, "Projekt", "__pycache__"))
            return True
        except:
            fileFunc().directory_del(copyTo)
            return False

    def shapesSave(self):
        for layer in iface.mapCanvas().layers():
            if layer.isEditable() and layer.isModified():
                layer.commitChanges()
                layer.startEditing()


def addPoint3D(layer, point, attListe):
    referenceNumber = getCustomProjectVariable("aktcode")
    # geoarch = getCustomProjectVariable('geo-arch')

    # ToDo: should geo-arch be included as a field?
    dateFieldIndex = layer.fields().indexFromName("erf_datum")
    referenceFieldIndex = layer.fields().indexFromName("aktcode")
    # geoArchFieldIndex = layer.fields().indexFromName('geo-arch')

    attListe.update(
        {
            dateFieldIndex: str(datetime.now()),
            referenceFieldIndex: referenceNumber,
            # geoArchFieldIndex: geoarch
        }
    )

    feature = QgsFeature()
    fields = layer.fields()
    feature.setFields(fields)
    feature.setGeometry(QgsGeometry(point))
    _, addedFeatures = layer.dataProvider().addFeatures([feature])
    layer.updateExtents()

    layer.dataProvider().changeAttributeValues({addedFeatures[-1].id(): attListe})


# -------------------- Refactoring ----------------------------


class fileFunc:
    def directory_del(self, path):
        # check if folder exists
        if os.path.exists(path):
            # remove if exists
            shutil.rmtree(path)

    def file_copy(self, quelle, ziel):
        # check if folder exists
        if os.path.exists(quelle):
            # remove if exists
            shutil.copy(quelle, ziel)

    def file_del(self, path):
        if os.path.exists(path):
            os.remove(path)

    def makedirs(self, path):
        if os.path.exists(path):
            os.makedirs(path)

    def directory_copy(self, quelle, ziel):
        for src_dir, dirs, files in os.walk(quelle):
            dst_dir = src_dir.replace(quelle, ziel, 1)
            if not os.path.exists(dst_dir):
                os.makedirs(dst_dir.replace("\\", "/", 1))
            for file_ in files:
                src_file = os.path.join(src_dir, file_)
                dst_file = os.path.join(dst_dir, file_)
                if os.path.exists(dst_file):
                    os.remove(dst_file)
                shutil.copy(src_file, dst_dir)


class makerAndRubberbands:
    def __init__(self):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.lMakers = []
        self.lRabberbands = []
        self.makerTyp = QgsVertexMarker.ICON_BOX
        self.color = QColor(255, 0, 0)

    def setMakerType(self, vertexMaker):
        self.makerTyp = vertexMaker

    def setColor(self, QColor):
        self.color = QColor

    def setMarker(self, x, y, size, penwidth):
        m = QgsVertexMarker(self.canvas)
        m.setCenter(QgsPointXY(float(x), float(y)))
        m.setColor(self.color)
        m.setIconSize(size)
        m.setIconType(self.makerTyp)
        m.setPenWidth(penwidth)
        m.show()
        self.lMakers.append(m)

    def setRubberBandPoly(self, ptList, penwidth):
        ptL = []
        for a in ptList:
            item = QgsPoint(float(a[0]), float(a[1]), float(a[2]))
            ptL.append(item)
        # ersten Punkt als letzten einfügen
        # ptList.append(ptList[0])
        r = QgsRubberBand(self.canvas, True)
        r.setToGeometry(QgsGeometry.fromPolyline(ptL), None)
        r.setColor(self.color)
        # r.fillColor()
        r.setWidth(penwidth)
        r.show()
        self.lRabberbands.append(r)

    def makerClean(self):
        for maker in self.lMakers:
            self.canvas.scene().removeItem(maker)

    def rubberBandClean(self):
        for maker in self.lRabberbands:
            self.canvas.scene().removeItem(maker)


def isDate(datum, spl):
    correctDate = None
    year = int(datum.split(spl)[0])
    month = int(datum.split(spl)[1])
    day = int(datum.split(spl)[2])
    try:
        newDate = datetime(year, month, day)
        correctDate = True
    except ValueError:
        correctDate = False
    return correctDate


def isNumber(str):
    try:
        float(str)
        correct = True
    except:
        correct = False
    return correct


def str2bool(v):
    if v is not None:
        return v.lower() in ("yes", "true", "on", "t", "1", "2")


def maxValue(layer, fieldname):
    values = []
    values.append(0)
    x = 0
    idField = layer.dataProvider().fieldNameIndex(fieldname)
    for feat in layer.getFeatures():
        attrs = feat.attributes()
        if attrs[idField] != None:
            x = x + 1
            try:
                if "_" in str(attrs[idField]):
                    continue
                # Attribute eine Zahl (bsp. 236)
                values.append(int(attrs[idField]))
            except ValueError:

                # list = [int(temp)for temp in str(attrs[idField]).split() if temp.isdigit()]
                # list = [int(s) for s in re.findall(r'-?\d+\.?\d*', str(attrs[idField]))]
                pattern = re.compile(r"\d+(?:;\.\d+)?")
                list = pattern.findall(str(attrs[idField]))
                for a in list:
                    values.append(int(a))
                pass
    return int(max(values))


def maxValueInt(layer, fieldname):
    idx = layer.dataProvider().fieldNameIndex(fieldname)
    if layer.maximumValue(idx) == None:
        max = 0
    else:
        max = layer.maximumValue(idx)
    return int(max)


def ValueList(layer, fieldname):
    befnr = []

    for field in layer.fields():
        if field.name() == fieldname:
            idField = layer.dataProvider().fieldNameIndex(fieldname)
            for feat in layer.selectedFeatures():
                attrs = feat.attributes()
                if attrs[idField] != None:
                    try:
                        befnr.append(int(attrs[idField]))
                    except ValueError:
                        pass
    try:
        return befnr
    except ValueError:
        befnr.append(0)
        return befnr


def mapCanvasRefresh():
    cachingEnabled = iface.mapCanvas().isCachingEnabled()
    for layer in iface.mapCanvas().layers():
        if cachingEnabled:
            layer.triggerRepaint()
    iface.mapCanvas().refresh()


def setColumnVisibility(layer, columnName, visible):
    config = layer.attributeTableConfig()
    columns = config.columns()
    for column in columns:
        if column.name == columnName:
            column.hidden = not visible
            break
    config.setColumns(columns)
    layer.setAttributeTableConfig(config)


def setColumnSort(layer, columnName, sort):
    config = layer.attributeTableConfig()


def csvListfilter(pfad, spalte, suchspalte, suchwert, vergleich):
    path = os.path.join(pfad)
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=";")
        d = list(reader)
        w = Listfilter(d, spalte, suchspalte, suchwert, vergleich)
    f.close()
    return w


def csvToList(pfad):
    path = os.path.join(pfad)
    with open(path, "r") as f:
        reader = csv.reader(f, delimiter=";")
        d = list(reader)
    f.close()
    return d


def Listfilter(liste, spalte, suchspalte, suchwert, vergleich):
    w = []
    for i in range(len(liste)):
        if vergleich == "genau":
            if suchwert == (liste[i][suchspalte]):
                w.append(liste[i][spalte])
        else:
            if suchwert in (liste[i][suchspalte]):
                w.append(liste[i][spalte])
    return w


def getListfilterIndex(liste, suchspalte, suchwert, vergleich):
    w = None
    for i in range(len(liste)):
        if vergleich == "genau":
            if suchwert == (liste[i][suchspalte]):
                w = i
                return w
        else:
            if suchwert in (liste[i][suchspalte]):
                w = i
                return w
    return w


def csvWriter(pfad, list):
    output_file = open(pfad, "w")
    row2 = ""
    for row in range(len(list)):
        for i in range(len(list[row])):
            row2 = row2 + list[row][i] + ";"
        row2 = row2[:-1] + "\n"
    output_file.write(row2.strip())
    output_file.close()


def featureAttributEdit(layer, feature, attList):
    for item in attList:
        fIndex = layer.dataProvider().fieldNameIndex(item)
        layer.changeAttributeValue(feature.id(), fIndex, attList[item])


def addAttributField(layer, fieldname, typ, length):
    layer.startEditing()
    if layer.dataProvider().fieldNameIndex(fieldname) == -1:
        layer.dataProvider().addAttributes([QgsField(fieldname, typ, len=length)])
        layer.updateFields()


def setSelectAllFeatures(layer):
    meldung = True
    it = layer.getFeatures()
    ids = [i.id() for i in it]
    layer.selectByIds(ids)

    if layer.selectedFeatureCount() > 0:
        iface.mapCanvas().zoomToSelected(layer)
        if not layer.geometryType() == QgsWkbTypes.PointGeometry:
            iface.mapCanvas().zoomByFactor(5)
        # iface.mapCanvas().refresh()
        meldung = False
    else:
        meldung = True
    if meldung == True:
        QMessageBox.warning(None, "Meldung", "Keine Objekte gefunden!")


def delSelectFeature():
    for layer in QgsProject.instance().mapLayers().values():
        if layer.type() == QgsMapLayer.VectorLayer:
            layer.removeSelection()


def fileLineCount(file):
    file = open(file)
    linecount = 0
    for line in file:
        linecount = linecount + 1
    file.close()
    return linecount


def getlayerSelectedFeatures():
    for layer in QgsProject.instance().mapLayers().values():
        if layer.type() == QgsMapLayer.VectorLayer:
            if layer.selectedFeatureCount() > 0:
                layer
                break
    return layer


def delLayer(layername):
    if len([lyr for lyr in QgsProject.instance().mapLayers().values() if lyr.name() == layername]) != 0:
        templayer = QgsProject.instance().mapLayersByName(layername)[0]
        QgsProject.instance().removeMapLayers([templayer.id()])


def tableWidgetRemoveRows(widget):
    for row in reversed(range(widget.rowCount())):
        widget.removeRow(row)


class LayerTree:
    def __init__(self, objekt=QgsProject.instance().layerTreeRoot()):
        self.tree = objekt
        self.visible = True
        self.expanded = True

    def allChildsVisible(self, value):
        self.setVisible(value)
        for child in self.tree.children():
            self.layerTreeVisible(child)

    def allGroupsVisible(self, value):
        self.setVisible(value)
        for child in self.tree.children():
            self.layerGroupVisible(child)

    def allGroupsExpanded(self, value):
        self.setExpanded(value)
        for child in self.tree.children():
            self.layerGroupExpanded(child)

    def childVisible(self):
        pass

    def setVisible(self, value):
        self.visible = value

    def setExpanded(self, value):
        self.expanded = value

    # ---------------------------------------------------------------------------------------------------------------------

    def layerTreeVisible(self, child):
        child.setItemVisibilityChecked(self.visible)
        for child in child.children():
            # QgsMessageLog.logMessage(str(child.dump()), 'T2G Archäologie', Qgis.Info)
            if isinstance(child, QgsLayerTreeGroup):
                self.layerTreeVisible(child)
                pass
            elif isinstance(child, QgsLayerTreeLayer):
                child.setItemVisibilityChecked(self.visible)

    def layerGroupVisible(self, child):
        if isinstance(child, QgsLayerTreeGroup):
            child.setItemVisibilityChecked(self.visible)
        for child in child.children():
            # QgsMessageLog.logMessage(str(child.dump()), 'T2G Archäologie', Qgis.Info)
            if isinstance(child, QgsLayerTreeGroup):
                # child.setItemVisibilityChecked(self.visible)
                self.layerGroupVisible(child)

    def layerGroupExpanded(self, child):
        if isinstance(child, QgsLayerTreeGroup):
            child.setExpanded(self.expanded)
        elif isinstance(child, QgsLayerTreeLayer):
            child.setExpanded(False)
        for child in child.children():
            if isinstance(child, QgsLayerTreeGroup):
                child.setExpanded(self.expanded)
                self.layerGroupExpanded(child)
            elif isinstance(child, QgsLayerTreeLayer):
                child.setExpanded(False)

    def layerExpanded(self, child):
        if isinstance(child, QgsLayerTreeLayer):
            child.setExpanded(self.expanded)
        for child in child.children():
            if isinstance(child, QgsLayerTreeLayer):
                child.setExpanded(self.expanded)
        pass


def setAliasName():
    # >Alias Namen erzeugen
    for layer in QgsProject.instance().mapLayers().values():
        if layer.type() == QgsMapLayer.VectorLayer:
            a = 0
            for field in layer.fields():
                if field.name() == "messatum":
                    layer.setFieldAlias(a, "Aufnamedatum")
                elif field.name() == "aktcode":
                    layer.setFieldAlias(a, "Grabung")
                elif field.name() == "obj_typ":
                    layer.setFieldAlias(a, "Objekttyp")
                elif field.name() == "obj_art":
                    layer.setFieldAlias(a, "Objektart")
                elif field.name() == "schnitt_nr":
                    layer.setFieldAlias(a, "Schnitt-Nr")
                elif field.name() == "planum":
                    layer.setFieldAlias(a, "Planum")
                elif field.name() == "material":
                    layer.setFieldAlias(a, "Material")
                elif field.name() == "bemerkung":
                    layer.setFieldAlias(a, "Bemerkung")
                elif field.name() == "bef_nr":
                    layer.setFieldAlias(a, "Befund-Nr")
                elif field.name() == "fund_nr":
                    layer.setFieldAlias(a, "Fund-Nr")
                elif field.name() == "geo-arch":
                    layer.setFieldAlias(a, "Geo/Arch")
                elif field.name() == "prob_nr":
                    layer.setFieldAlias(a, "Probe-Nr")
                a = a + 1
    # <Alias Namen erzeugen


class progressBar(QtWidgets.QWidget):
    def __init__(self, titel):
        super().__init__()
        self.setWindowTitle(titel)
        self.move(QDesktopWidget().availableGeometry().center())
        self.progress = QProgressBar(self)
        self.progress.setGeometry(0, 0, 300, 25)
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)
        self.value = 0
        self.close = False
        self.lab = QLabel(self)
        self.lab.setGeometry(0, 25, 300, 25)
        self.lab.setAlignment(Qt.AlignCenter)
        self.show()

    def setValue(self, value):
        self.progress.setValue(value)

    def setMaximum(self, value):
        self.progress.setMaximum(value)

    def setText(self, value):
        # self.lab.styleSheet("{Background-color : rgb(240, 240, 240) ; font: 75 7pt ;}")
        self.lab.setText(value)

    def closeEvent(self, event):
        # self.opacity = self.ui.mOpacityWidget.opacity
        self.close = True
        event.accept()


class PrintClickedPoint(QgsMapToolEmitPoint):
    geomPoint = pyqtSignal()

    def __init__(self, canvas, dlg):
        self.canvas = canvas
        QgsMapToolEmitPoint.__init__(self, self.canvas)
        self.dlg = dlg

    def canvasMoveEvent(self, e):
        try:
            # point = self.toMapCoordinates(self.canvas.mouseLastXY())
            # point = e.originalMapPoint()
            # point = e.snapPoint()
            # self.dlg.activateWindow()
            # self.dlg.txtPoint_2.setText(str(point.x())+','+str(point.y()))
            pass
        except:
            pass

    def canvasPressEvent(self, e):
        # try:
        point = e.snapPoint()
        # point = self.asWkb(e.snapPoint())
        self.dlg.activateWindow()
        self.dlg.txtPointTemp.setText(str(point.x()) + "," + str(point.y()))
        # except:
        #    pass


class ClickedPoint(QgsMapToolEmitPoint):
    geomPoint = pyqtSignal()
    tempPoint = pyqtSignal()

    def __init__(self, canvas, dlg):
        self.canvas = canvas
        QgsMapToolEmitPoint.__init__(self, self.canvas)
        self.dlg = dlg

    def canvasMoveEvent(self, e):
        try:
            point = self.toMapCoordinates(self.canvas.mouseLastXY())
            point = e.originalMapPoint()
            point = e.snapPoint()
            self.geomPoint.emit()
            self.dlg.activateWindow()
        except:
            pass

    def canvasPressEvent(self, e):
        # try:
        point = e.snapPoint()

        # point = self.asWkb(e.snapPoint())
        self.dlg.activateWindow()
        self.tempPoint.emit()


class xml:
    def __init__(self, file):
        self.file = file

    def getValue(self, element, key):
        import xml.etree.ElementTree as ElementTree

        tree = ElementTree.parse(self.file)
        root = tree.getroot()

        for elem in root:
            if elem.tag == element:
                for child in elem:
                    if child.attrib["name"] == key:
                        return child.text

    def setValue(self, element, key, wert):
        import xml.etree.ElementTree as ElementTree

        tree = ElementTree.parse(self.file)
        root = tree.getroot()

        for elem in root:
            if elem.tag == element:
                for child in elem:
                    if child.attrib["name"] == key:
                        child.text = wert
        tree.write(self.file)


class HelpWindow(QWidget):

    def __init__(self, parent=None):
        super(HelpWindow, self).__init__(parent, Qt.WindowStaysOnTopHint)
        self.setLayout(QGridLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.meldung = QTextBrowser()
        self.text = None
        self.pfad = None
        self.layout().addWidget(self.meldung)  # ,0,0,1,2)

    def run(self, pfad, text, width, height):
        if pfad == None:
            self.meldung.setHtml(text)
        elif text == None:
            self.meldung.setSource(QUrl.fromLocalFile(pfad))
        self.resize(width, height)
        self.show()

    def setText(self, text):
        self.text = text

    def setPfad(self, pfad):
        self.pfad = pfad
