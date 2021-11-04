# -*- coding: utf-8 -*-
import sys, os, shutil, os.path, time, csv, datetime
from datetime import *#date, datetime
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import *
from qgis.core import *
from qgis.gui import *
from qgis.utils import *#iface

class fileFunc():
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
    def makedirs(self,path):
        if os.path.exists(path):
            os.makedirs(path)

    def directory_copy(self, quelle, ziel):
        root_src_dir = unicode(quelle)
        root_dst_dir = unicode(ziel)
        for src_dir, dirs, files in os.walk(root_src_dir):
            dst_dir = src_dir.replace(root_src_dir, root_dst_dir, 1)
            if not os.path.exists(dst_dir):
                os.makedirs(dst_dir.replace('\\','/',1))
            for file_ in files:
                src_file = os.path.join(src_dir, file_)
                dst_file = os.path.join(dst_dir, file_)
                if os.path.exists(dst_file):
                    os.remove(dst_file)
                shutil.copy(src_file, dst_dir)

class projectSaveFunc():
    def project_save(self,quelle):
        try:
            datum = unicode(time.strftime("%Y.%m.%d"))
            zeit = unicode(time.strftime("%H-%M")) #"%H-%M-%S"
            ziel = os.path.join(quelle, r'_Sicherungen_', datum + '_' + zeit)

            fileFunc().directory_copy(os.path.join(quelle, 'Shape'), os.path.join(ziel, 'Shape'))
            fileFunc().directory_copy(os.path.join(quelle, 'Projekt'), os.path.join(ziel, 'Projekt'))

            os.remove(os.path.join(ziel, 'Projekt', 'intro.py'))
            fileFunc().directory_del(os.path.join(ziel, 'Projekt', '__pycache__'))
            return 'True'
        except:
            fileFunc().directory_del(ziel)
            return 'False'

    def dayproject_save(self,quelle):
        try:
            datum = unicode(time.strftime("%Y.%m.%d"))
            zeit = unicode(time.strftime("%H-%M")) #"%H-%M-%S"
            ziel = os.path.join(quelle, r'_Tagesdateien_', datum + '_' + zeit)

            fileFunc().directory_copy(os.path.join(quelle, 'Shape'), os.path.join(ziel, 'Shape'))
            fileFunc().directory_copy(os.path.join(quelle, 'Projekt'), os.path.join(ziel, 'Projekt'))

            os.remove(os.path.join(ziel, 'Projekt', 'intro.py'))
            fileFunc().directory_del(os.path.join(ziel, 'Projekt', '__pycache__'))
            return 'True'
        except:
            fileFunc().directory_del(ziel)
            return 'False'

    def shapesSave(self):
        for layer in iface.mapCanvas().layers():
            if layer.isEditable() and layer.isModified():
                layer.commitChanges()
                layer.startEditing()

class makerAndRubberbands():
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

    def setMarker(self, x, y):
        m = QgsVertexMarker(self.canvas)
        m.setCenter(QgsPointXY(float(x), float(y)))
        m.setColor(self.color)
        m.setIconSize(15)
        m.setIconType(self.makerTyp)
        m.setPenWidth(3)
        m.show()
        self.lMakers.append(m)

    def setRubberBandPoly(self, ptList):
        ptL = []
        for a in ptList:
            item = QgsPoint(float(a['x']), float(a['y']), float(a['z']))
            ptL.append(item)
        # ersten Punkt als letzten einfügen
        # ptList.append(ptList[0])
        r = QgsRubberBand(self.canvas, True)
        r.setToGeometry(QgsGeometry.fromPolyline(ptL), None)
        r.setColor(self.color)
        #r.fillColor()
        r.setWidth(5)
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
    correct = None
    try:
        a = float(str)
        correct = True
    except:
        correct = False
    return correct

def maxValue(layer, fieldname):
    QgsMessageLog.logMessage('Max Wert eritteln', 'T2G Archäologie', Qgis.Info)
    suchstr = fieldname + '!=' + '\'' + '' + '\''
    expr = QgsExpression(suchstr)
    it = layer.getFeatures(QgsFeatureRequest(expr))
    ids = [i.id() for i in it]
    layer.selectByIds(ids)

    values = []
    befnr = []
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
    #Scheint nicht zu gehen???
    #layer.removeSelection() eingefügt damit die Layer nicht zu Beginn alle selektiert sind
    #delSelectFeature()
    layer.removeSelection()
    return int(max(values))

def maxValueInt (layer, fieldname):
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


def setCustomProjectVariable(variableName, variableWert):
    project = QgsProject.instance()
    QgsExpressionContextUtils.setProjectVariable(project, variableName, variableWert)

def getCustomProjectVariable(variableName):
    project = QgsProject.instance()
    if str(QgsExpressionContextUtils.projectScope(project).variable(variableName)) == 'NULL':
        return str('')
    else:
        return QgsExpressionContextUtils.projectScope(project).variable(variableName)

def delCustomProjectVariable(variableName):
    project = QgsProject.instance()
    QgsExpressionContextUtils.removeProjectVariable(project, variableName)

def csvListfilter(pfad,spalte,suchspalte,suchwert,vergleich):
    path = os.path.join(pfad)
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f,delimiter=";")
        d = list(reader)
        w = Listfilter(d,spalte,suchspalte,suchwert,vergleich)
    f.close()
    return w

def csvToList(pfad):
    path = os.path.join(pfad)
    with open(path,'r') as f:
        reader = csv.reader(f, delimiter=";")
        d = list(reader)
    f.close()
    return d

def Listfilter(liste,spalte,suchspalte,suchwert,vergleich):
    w = []
    for i in range(len(liste)):
        if vergleich == 'genau':
            if suchwert == (liste[i][suchspalte]):
                w.append(liste[i][spalte])
        else:
            if suchwert in (liste[i][suchspalte]):
                w.append(liste[i][spalte])
    return w

def getListfilterIndex(liste,suchspalte,suchwert,vergleich):
    w = None
    for i in range(len(liste)):
        if vergleich == 'genau':
            if suchwert == (liste[i][suchspalte]):
                w = i
                return w
        else:
            if suchwert in (liste[i][suchspalte]):
                w = i
                return w
    return w

def csvWriter(pfad, list):
    output_file = open(pfad, 'w')
    row2 = ''
    for row in range(len(list)):
        for i in range(len(list[row])):
            row2 = row2 + list[row][i] + ';'
        row2 = row2[:-1] + '\n'
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
        #iface.mapCanvas().refresh()
        meldung = False
    else:
        meldung = True
    if meldung == True:
        QMessageBox.warning(None, "Meldung", 'Keine Objekte gefunden!')

def delSelectFeature():
    for a in iface.attributesToolBar().actions():
        if a.objectName() == 'mActionDeselectAll':
            a.trigger()
            break

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
    def __init__(self, objekt = QgsProject.instance().layerTreeRoot()):
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

    def allGroupsExpanded(self,value):
        self.setExpanded(value)
        for child in self.tree.children():
            self.layerGroupExpanded(child)

    def childVisible(self):
        pass

    def setVisible(self, value):
        self.visible = value

    def setExpanded(self, value):
        self.expanded = value
#---------------------------------------------------------------------------------------------------------------------

    def layerTreeVisible(self, child):
        child.setItemVisibilityChecked(self.visible)
        for child in child.children():
            #QgsMessageLog.logMessage(str(child.dump()), 'T2G Archäologie', Qgis.Info)
            if isinstance(child, QgsLayerTreeGroup):
                self.layerTreeVisible(child)
                pass
            elif isinstance(child, QgsLayerTreeLayer):
                child.setItemVisibilityChecked(self.visible)

    def layerGroupVisible(self, child):
        if isinstance(child, QgsLayerTreeGroup):
            child.setItemVisibilityChecked(self.visible)
        for child in child.children():
            #QgsMessageLog.logMessage(str(child.dump()), 'T2G Archäologie', Qgis.Info)
            if isinstance(child, QgsLayerTreeGroup):
                #child.setItemVisibilityChecked(self.visible)
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

def addPoint3D(layer, point, attListe):
    project = QgsProject.instance()
    # letzte id ermitteln
    idfeld = layer.dataProvider().fieldNameIndex('id')
    if layer.maximumValue(idfeld) == None:
        idmaxi = 0
    else:
        idmaxi = layer.maximumValue(idfeld)
    attListe.update({'id': str(idmaxi + 1)})

    aktcode = QgsExpressionContextUtils.projectScope(project).variable('aktcode')
    geoarch = QgsExpressionContextUtils.projectScope(project).variable('geo-arch')

    attListe.update({'messdatum': str(datetime.now()), 'aktcode' : aktcode,'geo-arch': geoarch})
    layer.startEditing()
    feature = QgsFeature()
    fields = layer.fields()
    feature.setFields(fields)
    feature.setGeometry(QgsGeometry(point))
    # Attribute
    layer.dataProvider().addFeatures([feature])
    layer.updateExtents()
    features = [feature for feature in layer.getFeatures()]
    lastfeature = features[-1]

    for item in attListe:
        #QgsMessageLog.logMessage(str(item), 'T2G', Qgis.Info)
        fIndex = layer.dataProvider().fieldNameIndex(item)
        layer.changeAttributeValue(lastfeature.id(), fIndex, attListe[item])
    layer.commitChanges()

def setAliasName() :
    # >Alias Namen erzeugen
    for layer in QgsProject.instance().mapLayers().values():
        if layer.type() == QgsMapLayer.VectorLayer:
            a = 0
            for field in layer.fields():
                if field.name() == 'messatum':
                    layer.setFieldAlias(a, 'Aufnamedatum')
                elif field.name() == 'aktcode':
                    layer.setFieldAlias(a, 'Grabung')
                elif field.name() == 'obj_type':
                    layer.setFieldAlias(a, 'Objekttyp')
                elif field.name() == 'obj_art':
                    layer.setFieldAlias(a, 'Objektart')
                elif field.name() == 'schnitt_nr':
                    layer.setFieldAlias(a, 'Schnitt-Nr')
                elif field.name() == 'planum':
                    layer.setFieldAlias(a, 'Planum')
                elif field.name() == 'material':
                    layer.setFieldAlias(a, 'Material')
                elif field.name() == 'bemerkung':
                    layer.setFieldAlias(a, 'Bemerkung')
                elif field.name() == 'bef_nr':
                    layer.setFieldAlias(a, 'Befund-Nr')
                elif field.name() == 'fund_nr':
                    layer.setFieldAlias(a, 'Fund-Nr')
                elif field.name() == 'geo-arch':
                    layer.setFieldAlias(a, 'Geo/Arch')
                elif field.name() == 'prob_nr':
                    layer.setFieldAlias(a, 'Probe-Nr')
                a = a + 1
    # <Alias Namen erzeugen


class progressBar(QtWidgets.QWidget):
    def __init__(self,titel):
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

    def setValue(self,value):
        self.progress.setValue(value)

    def setMaximum(self,value):
        self.progress.setMaximum(value)

    def setText(self, value):
        #self.lab.styleSheet("{Background-color : rgb(240, 240, 240) ; font: 75 7pt ;}")
        self.lab.setText(value)

    def closeEvent(self, event):
        #self.opacity = self.ui.mOpacityWidget.opacity
        self.close = True
        event.accept()

class PrintClickedPoint(QgsMapToolEmitPoint):
    geomPoint = pyqtSignal()
    def __init__(self,canvas,dlg):
        self.canvas = canvas
        QgsMapToolEmitPoint.__init__(self, self.canvas)
        self.dlg=dlg

    def canvasMoveEvent( self, e ):
        try:
            point = self.toMapCoordinates(self.canvas.mouseLastXY())
            point = e.originalMapPoint()
            point = e.snapPoint()
            self.dlg.activateWindow()
            self.dlg.txtPoint_2.setText(str(point.x())+','+str(point.y()))
        except:
            pass
    def canvasPressEvent( self, e ):
        #try:
        point = e.snapPoint()
        #point = self.asWkb(e.snapPoint())
        self.dlg.activateWindow()
        self.dlg.txtPointTemp.setText(str(point.x())+','+str(point.y()))
        #except:
        #    pass

class xml():
    def __init__(self, file):
        self.file = file

    def getValue(self,element,key):
        file = 'G:/settings.xml'
        import xml.etree.ElementTree as ElementTree
        tree = ElementTree.parse(self.file)
        root = tree.getroot()

        for elem in root:
            if elem.tag == element:
                for child in elem:
                    if child.attrib['name'] == key:
                        return child.text

    def setValue(self, element,key,wert):
        import xml.etree.ElementTree as ElementTree
        tree = ElementTree.parse(self.file)
        root = tree.getroot()

        for elem in root:
            if elem.tag == element:
                for child in elem:
                    if child.attrib['name'] == key:
                        child.text = wert
        tree.write(self.file)
