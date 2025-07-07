## @package QGIS geoEdit extension..

from processing.gui import AlgorithmExecutor
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QMessageBox, QApplication, QPushButton
from qgis.core import QgsGeometry, QgsApplication, QgsWkbTypes, QgsMapLayer, QgsFeature, Qgis, QgsMessageLog, QgsPoint
from qgis.gui import QgsRubberBand

from ..utils.functions import delSelectFeature
from ..utils.identifygeometry import IdentifyGeometry


## @brief The class is used to implement functionalities for translate geometies within the geoEdit Module
#
# @author Mario Uhlig, VisDat geodatentechnologie GmbH, mario.uhlig@visdat.de
# @date 2021-01-22
class GeoEditCalculations:

    ## The constructor.
    #  Defines attributes for the GeoEditCalculations
    #
    #  @param geoEditInstance pointer to the geoEditInstance
    def __init__(self, geoEditInstance):
        self.selectedFeature = None
        self.abbruch = None
        self.geoEditInstance = geoEditInstance
        self.dockwidget = geoEditInstance.dockwidget
        self.iface = geoEditInstance.iface

        self.createMaptools()

    ## \brief Absolute translation of sourcelayer in z direction
    #
    # \param tranlationDirection - forward or reverse
    # \param sourceLayer - used layer for translation
    # \param translationZ - Value for translation in z direction
    # \param selectedFeatures - Array with selected features in the sourcelayer
    #
    # - Forward translation: The function uses the algorithm qgis:setvalue. The height of the feature geometry is set to the translationZ value, even if individual points of the geometry have different height values.
    # - Reverse translation: The current geometries are exchanged with the geometries saved before the transformation.
    def layerTranslationZAbsolute(self, tranlationDirection, sourceLayer, translationZ, selectedFeatures):

        layerName = sourceLayer.name()

        # Translation forward
        if tranlationDirection == "forward":
            tranlationZValue = translationZ

            print("Translation z - forward and absolute: ", layerName)

            sourceLayer.startEditing()
            translateAlg = QgsApplication.processingRegistry().createAlgorithmById("qgis:setzvalue")
            paramTranslate = {"Z_VALUE": tranlationZValue, "INPUT": sourceLayer}
            print(paramTranslate)
            AlgorithmExecutor.execute_in_place(translateAlg, paramTranslate)

            sourceLayer.commitChanges()

        # Translation reverse
        if tranlationDirection == "reverse":

            print("Translation z - reverse and absolute: ", layerName)
            sourceLayer.startEditing()

            for feat in sourceLayer.getFeatures():
                for selFeat in selectedFeatures:
                    if feat.id() == selFeat.id():
                        sourceLayer.dataProvider().changeGeometryValues({feat.id(): selFeat.geometry()})

            sourceLayer.commitChanges()

    ## \brief relative translation of sourcelayer in z direction
    #
    # \param tranlationDirection - forward or reverse
    # \param translationZ - Value for translation in z direction
    #
    # - Forward translation: The height of the individual points of the geometry is calculated by adding the translationZ to the current value.
    # - Reverse translation: The translationZ is subtracted from the individual points.
    def layerTranslationZ(self, tranlationDirection, sourceLayer, translationZ):

        layerName = sourceLayer.name()
        print("Transformation - Translation Z: ", layerName)

        # layer.startEditing()
        sourceLayer.beginEditCommand("Beginn edit Translation Z")
        for zFeat in sourceLayer.selectedFeatures():

            g = zFeat.geometry()  # QgsGeometry
            geomType = g.type()

            # line - 1, polygon - 2
            if geomType == 1 or geomType == 2:

                mls = g.get()  # QgsMultiPolygon

                adjustGeom = QgsGeometry(mls.createEmptyWithSameType())
                geomArray = []
                for v in mls.vertices():

                    if tranlationDirection == "forward":
                        newZVal = v.z() + translationZ
                    if tranlationDirection == "reverse":
                        newZVal = v.z() - translationZ

                    v.setZ(newZVal)
                    geomArray.append(v)

                adjustGeom.addPoints(geomArray)
                provGeom = sourceLayer.dataProvider().convertToProviderType(adjustGeom)
                fid = zFeat.id()

                if provGeom == None:
                    sourceLayer.dataProvider().changeGeometryValues({fid: adjustGeom})
                else:
                    sourceLayer.dataProvider().changeGeometryValues({fid: provGeom})

            # point - 0
            if geomType == 0:
                if tranlationDirection == "forward":
                    g.get().setZ(g.get().z() + translationZ)
                if tranlationDirection == "reverse":
                    g.get().setZ(g.get().z() - translationZ)

                fid = zFeat.id()
                sourceLayer.dataProvider().changeGeometryValues({fid: g})

        sourceLayer.dataProvider().createSpatialIndex()
        sourceLayer.endEditCommand()

    ## \brief Translation of the sourcelayer in x and y direction
    #
    # \param tranlationDirection - forward or reverse
    # \param sourceLayer - used layer for translation
    # \param translationX - Value for translation in x direction
    # \param translationY - Value for translation in y direction
    def layerTranslationXY(self, tranlationDirection, sourceLayer, translationX, translationY):

        layerName = sourceLayer.name()

        if tranlationDirection == "forward":
            tranlationXValue = translationX
            tranlationYValue = translationY
        if tranlationDirection == "reverse":
            tranlationXValue = translationX * -1
            tranlationYValue = translationY * -1

        print("Transformation - Translation X and Y: ", layerName)

        sourceLayer.startEditing()
        translateAlg = QgsApplication.processingRegistry().createAlgorithmById("native:translategeometry")
        paramTranslate = {"DELTA_Y": tranlationYValue, "DELTA_X": tranlationXValue, "INPUT": sourceLayer}
        print(paramTranslate)
        AlgorithmExecutor.execute_in_place(translateAlg, paramTranslate)

        sourceLayer.commitChanges()

    ## \brief Translation of the sourcelayer in x, y and z direction
    #
    # \param tranlationDirection - forward or reverse
    # \param sourceLayer - used layer for translation
    # \param translationX - Value for translation in x direction
    # \param translationY - Value for translation in y direction
    # \param translationZ - Value for translation in z direction
    def layerTranslationXYZ(self, tranlationDirection, sourceLayer, translationX, translationY, translationZ):

        layerName = sourceLayer.name()

        if tranlationDirection == "forward":
            tranlationXValue = translationX
            tranlationYValue = translationY
            tranlationZValue = translationZ
        if tranlationDirection == "reverse":
            tranlationXValue = translationX * -1
            tranlationYValue = translationY * -1
            tranlationZValue = translationZ * -1

        print("Transformation - Translation X, Y and Z: ", layerName)

        sourceLayer.startEditing()
        translateAlg = QgsApplication.processingRegistry().createAlgorithmById("native:translategeometry")

        layerType = sourceLayer.wkbType()
        print("layerType", layerType)

        # Abfrage nach Z und ZM Multi Layertypen
        if (
            layerType == QgsWkbTypes.PointZ
            or layerType == QgsWkbTypes.LineStringZ
            or layerType == QgsWkbTypes.PolygonZ
            or layerType == QgsWkbTypes.MultiPointZ
            or layerType == QgsWkbTypes.MultiLineZ
            or layerType == QgsWkbTypes.MultiPolygonZ
        ):

            paramTranslate = {
                "DELTA_Y": tranlationYValue,
                "DELTA_X": tranlationXValue,
                "DELTA_Z": tranlationZValue,
                "INPUT": sourceLayer,
            }

        elif (
            layerType == QgsWkbTypes.PointZM
            or layerType == QgsWkbTypes.LineStringZM
            or layerType == QgsWkbTypes.PolygonZM
            or layerType == QgsWkbTypes.MultiPointZM
            or layerType == QgsWkbTypes.MultiLineZM
            or layerType == QgsWkbTypes.MultiPolygonZM
        ):

            paramTranslate = {
                "DELTA_Y": tranlationYValue,
                "DELTA_X": tranlationXValue,
                "DELTA_Z": tranlationZValue,
                "DELTA_M": 0,
                "INPUT": sourceLayer,
            }

        else:
            QMessageBox.critical(
                self.geoEditInstance,
                "Invalider Layer",
                f"Kann Geometrietyp {layerType} nicht verarbeiten!",
                QMessageBox.Abort,
            )
            print("Kann Geometrietyp nicht verarbeiten ", layerType)

        print("paramTranslate ", paramTranslate)
        AlgorithmExecutor.execute_in_place(translateAlg, paramTranslate)
        sourceLayer.commitChanges()

    def createMaptools(self):
        self.mapToolSel = IdentifyGeometry(self.iface.mapCanvas())
        self.mapToolSel.geomIdentified.connect(self.featureSelect2)

    def insideClip(self):  # inside
        layer = self.iface.mapCanvas().currentLayer()
        if layer.type() == QgsMapLayer.VectorLayer:
            if layer.geometryType() == QgsWkbTypes.PolygonGeometry:
                selection = layer.selectedFeatures()
                if len(selection) != 0:
                    fsel = selection[0]
                    # set layer editable
                    layer.startEditing()
                    for g in layer.getFeatures():
                        if g.id() != fsel.id():
                            if g.geometry().intersects(fsel.geometry()):
                                # clipping non selected intersecting features
                                attributes = g.attributes()
                                diff = QgsFeature()
                                diff.setGeometry(g.geometry().difference(fsel.geometry()))
                                # copy attributes from original feature
                                diff.setAttributes(attributes)
                                # add modified feature to layer
                                layer.addFeature(diff)
                                # remove old feature
                                layer.deleteFeature(fsel.id())

                        # refresh the view and clear selection
                    self.iface.mapCanvas().refresh()
                    self.iface.mapCanvas().currentLayer().selectAll()
                    self.iface.mapCanvas().currentLayer().invertSelection()

    def outsideClip(self):  # outside
        layer = self.iface.mapCanvas().currentLayer()
        if layer.type() == QgsMapLayer.VectorLayer:
            if layer.geometryType() == QgsWkbTypes.PolygonGeometry:
                selection = layer.selectedFeatures()
                if len(selection) != 0:
                    fsel = selection[0]
                    # set layer editable
                    layer.startEditing()
                    for g in layer.getFeatures():
                        if g.id() != fsel.id():
                            if g.geometry().intersects(fsel.geometry()):
                                # clipping non selected intersecting features
                                attributes = g.attributes()
                                diff = QgsFeature()
                                diff.setGeometry(fsel.geometry().difference(g.geometry()))
                                # copy attributes from original feature
                                diff.setAttributes(attributes)
                                # add modified feature to layer
                                layer.addFeature(diff)
                                # remove old feature
                                layer.deleteFeature(fsel.id())

                        # refresh the view and clear selection
                    self.iface.mapCanvas().refresh()
                    self.iface.mapCanvas().currentLayer().selectAll()
                    self.iface.mapCanvas().currentLayer().invertSelection()

    def contactClip(self):
        self.iface.mapCanvas().setMapTool(self.mapToolSel)
        self.mapToolSel.geomIdentified.connect(self.featureSelect2)
        rubber_list = []
        feature_list = []
        self.abbruch = False
        self.selectedFeature = None
        layer = self.iface.mapCanvas().currentLayer()
        try:
            if layer.type() == QgsMapLayer.VectorLayer:
                if layer.geometryType() == QgsWkbTypes.PolygonGeometry:
                    self.createCancellationMessage("Schablone wählen.")
                    while self.selectedFeature is None:
                        if self.abbruch:
                            raise NameError
                        QApplication.processEvents()
                    while len(feature_list) < 1:
                        # Feature eins
                        while self.selectedFeature is None:
                            if self.abbruch:
                                raise NameError
                            QApplication.processEvents()

                        if self.selectedLayer.name() == "E_Polygon":
                            fsel = self.selectedFeature
                            r = QgsRubberBand(self.iface.mapCanvas())
                            r.setToGeometry(fsel.geometry(), None)
                            r.setColor(QColor(0, 0, 255, 180))
                            r.setWidth(5)
                            r.show()
                            rubber_list.append(r)
                            feature_list.append(self.selectedFeature)
                        layer.removeSelection()
                        self.selectedFeature = None
                        # Feature zwei
                        self.iface.messageBar().popWidget()
                        self.createCancellationMessage("Schnittobjekt wählen.")
                        while self.selectedFeature is None:
                            if self.abbruch:

                                for maker in rubber_list:
                                    self.iface.mapCanvas().scene().removeItem(maker)

                                raise NameError
                            QApplication.processEvents()
                        if self.selectedLayer.name() == "E_Polygon":
                            feature_list.append(self.selectedFeature)
                            selection = self.selectedFeature

                for g in feature_list:
                    if g.id() != feature_list[0].id():
                        if g.geometry().intersects(fsel.geometry()):
                            # clipping non selected intersecting features
                            attributes = g.attributes()
                            diff = QgsFeature()
                            diff.setGeometry(g.geometry().difference(fsel.geometry()))
                            # copy attributes from original feature
                            diff.setAttributes(attributes)
                            # add modified feature to layer
                            ptList = []
                            geo = diff.geometry().asPolygon()[0]
                            for i in range(len(geo)):
                                item = QgsPoint(diff.geometry().vertexAt(i).x(), diff.geometry().vertexAt(i).y())
                                ptList.append(item)
                            r = QgsRubberBand(self.iface.mapCanvas())
                            r.setToGeometry(QgsGeometry.fromPolyline(ptList), None)
                            r.setColor(QColor(255, 0, 0))
                            r.setWidth(5)
                            r.show()
                            rubber_list.append(r)
                            delSelectFeature()

                            box = QMessageBox()
                            box.setIcon(QMessageBox.Question)
                            box.setWindowTitle("Frage")
                            box.setText("Wollen Sie das Ergebnis übernehmen?")
                            box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                            ret = box.exec()
                            if ret == QMessageBox.Yes:
                                layer.startEditing()
                                layer.addFeature(diff)
                                layer.deleteFeature(g.id())
                                layer.commitChanges()
                                layer.endEditCommand()

                            elif ret == QMessageBox.No:
                                layer.deleteFeature(diff.id())
                                # layer.commitChanges()
                                # layer.endEditCommand()
        except NameError:
            QgsMessageLog.logMessage("Abbruch", "T2G Archäologie", Qgis.Info)
        for maker in rubber_list:
            self.iface.mapCanvas().scene().removeItem(maker)

        # layer.commitChanges()
        # layer.endEditCommand()
        layer.removeSelection()
        self.iface.actionSelect().trigger()
        self.iface.messageBar().clearWidgets()
        # self.selectedFeature == None
        self.mapToolSel.geomIdentified.disconnect()

    def featureSelect2(self, layer, feature):
        self.selectedLayer = layer
        self.selectedFeature = feature
        self.iface.setActiveLayer(self.selectedLayer)
        self.selectedLayer.select(int(self.selectedFeature.id()))
        # layer.select(int(feature.id()))
        QgsMessageLog.logMessage(str(layer.name()) + str(feature.id()), "aaa", Qgis.Info)

    def createCancellationMessage(self, text):
        self.iface.messageBar().clearWidgets()
        widgetMessage = self.iface.messageBar().createMessage(text)
        button = QPushButton(widgetMessage)
        button.setText("Abbruch")
        # TODO QGIS kann nicht beendet werden / Plugin kann nicht neu geladen werden
        # wenn button nicht gedrückt wird
        # wenn message bar mit x geschlossen wird, muss der Task-Manager benutzt werden
        button.pressed.connect(self.setAbbruch)
        widgetMessage.layout().addWidget(button)
        # button = QPushButton(widgetMessage)
        # button.setText("Weiter")
        # widgetMessage.layout().addWidget(button)
        self.iface.messageBar().pushWidget(widgetMessage, Qgis.Info)

    # ToDo: refactoring - befundlabel helper
    def setAbbruch(self):
        self.abbruch = True
        self.iface.messageBar().clearWidgets()
