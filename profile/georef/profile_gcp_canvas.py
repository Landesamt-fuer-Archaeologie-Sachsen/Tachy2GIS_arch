# -*- coding: utf-8 -*-
import os
import processing
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QFont, QColor
from qgis.core import (
    Qgis,
    QgsPoint,
    QgsFeature,
    QgsGeometry,
    QgsMarkerSymbol,
    QgsSingleSymbolRenderer,
    QgsPalLayerSettings,
    QgsTextFormat,
    QgsTextBufferSettings,
    QgsVectorLayerSimpleLabeling,
)
from qgis.gui import QgsMapCanvas, QgsMapToolPan, QgsMapToolZoom

from ..publisher import Publisher


## @brief With the ProfileGcpCanvas class a map canvas element is realized. It should be used in the profile dialog
#
# Inherits from QgsMapCanvas
#
# @author Mario Uhlig, VisDat Geodatentechnologie GmbH, mario.uhlig@visdat.de
# @date 2021-26-05
class ProfileGcpCanvas(QgsMapCanvas):
    ## The constructor.
    #
    def __init__(self, dialogInstance, rotationCoords):
        super().__init__()

        self.pup = Publisher()

        self.iconpath = os.path.join(os.path.dirname(__file__), "Icons")

        self.activePoint = None

        self.gcpLayer = None

        self.rotationCoords = rotationCoords

        self.setCanvasColor(Qt.white)

        self.createMapToolPan()
        self.createMapToolZoomIn()
        self.createMapToolZoomOut()

        self.createConnects()

    ## \brief Event connections
    #
    def createConnects(self):
        # Koordinatenanzeige
        self.xyCoordinates.connect(self.canvasMoveEvent)

    ## \brief Set coordinates on the statusbar in dialog instance TransformationDialog.setCoordinatesOnStatusBar().
    # Depends on mouse move on the map element
    #
    def canvasMoveEvent(self, event):
        x = event.x()
        y = event.y()
        self.pup.publish("moveCoordinate", {"x": x, "y": y})
        # self.dialogInstance.setCoordinatesOnStatusBar(x, y)

    ## \brief Create action to pan on the map
    #
    def createMapToolPan(self):
        self.toolPan = QgsMapToolPan(self)

    ## \brief Create action to zoom in on the map
    #
    def createMapToolZoomIn(self):
        self.toolZoomIn = QgsMapToolZoom(self, False)

    ## \brief Create action to zoom out on the map
    #
    def createMapToolZoomOut(self):
        self.toolZoomOut = QgsMapToolZoom(self, True)  # true = out

    ## \brief Set extent of the map by extent of the source layer
    #
    def setExtentByGcpLayer(self):
        self.setExtent(self.gcpLayer.extent().buffered(0.2))
        self.refresh()

    def setActivePoint(self, linkObj):
        self.activePoint = linkObj["obj_uuid"]

    ## \brief Update canvas map element
    #
    # - Clear canvas element
    # - Validation of the source layer
    # - Show subset of the source layer - col obj_type = TransformationDialog.colNameGcpSource
    # - Marker symbol
    # - Label lyer with Id of the feature
    # - Additional display other input layers
    #
    # \param gcpLayer

    def updateCanvas(self, refData):
        # canvas leeren

        self.clearCache()
        self.refresh()

        self.setupGcpLayer(refData)

        self.styleLayer()

        # Sets canvas CRS
        sourceCrs = self.gcpLayer.crs()
        self.setDestinationCrs(sourceCrs)

        # set extent to the extent of Layer E_Point
        self.setExtentByGcpLayer()

        listLayers = [self.gcpLayer]

        self.setLayers(listLayers)

    ## \brief Short highlighting of a feature by obj_uuid
    #
    # \param uuidValue

    def highlightSourceLayer(self, uuidValue):
        for feature in self.gcpLayer.getFeatures():
            uuidFeat = feature.attribute("obj_uuid")
            if uuidFeat == uuidValue:
                self.flashFeatureIds(
                    self.gcpLayer,
                    [feature.id()],
                    startColor=QColor(Qt.green),
                    endColor=QColor(Qt.green),
                    flashes=5,
                    duration=500,
                )

    def styleLayer(self):
        # Label Layer
        sourcelayerSettings = QgsPalLayerSettings()
        textFormat = QgsTextFormat()

        textFormat.setFont(QFont("Arial", 13))

        bufferSettings = QgsTextBufferSettings()
        bufferSettings.setEnabled(True)
        bufferSettings.setSize(0.20)
        bufferSettings.setColor(QColor("black"))

        textFormat.setBuffer(bufferSettings)
        sourcelayerSettings.setFormat(textFormat)

        sourcelayerSettings.fieldName = "pt_nr"
        sourcelayerSettings.placement = Qgis.LabelPlacement.Horizontal
        sourcelayerSettings.enabled = True

        sourcelayerSettings = QgsVectorLayerSimpleLabeling(sourcelayerSettings)
        self.gcpLayer.setLabelsEnabled(True)
        self.gcpLayer.setLabeling(sourcelayerSettings)

        # Styling
        symbol = QgsMarkerSymbol.createSimple({"name": "circle", "color": "green", "size": "2"})
        self.gcpLayer.setRenderer(QgsSingleSymbolRenderer(symbol))

        self.gcpLayer.triggerRepaint()

    def setupGcpLayer(self, refData):
        refData["pointLayer"].selectAll()
        self.gcpLayer = processing.run(
            "native:saveselectedfeatures", {"INPUT": refData["pointLayer"], "OUTPUT": "memory:"}
        )["OUTPUT"]
        refData["pointLayer"].removeSelection()

        # check validation of Layers
        if not self.gcpLayer.isValid():
            self.messageBar.pushMessage(
                "Error", "Layer " + self.gcpLayer.name() + " failed to load!", level=1, duration=5
            )

        # gcpLayer leeren
        features = self.gcpLayer.getFeatures()

        self.gcpLayer.startEditing()

        for feature in features:
            self.gcpLayer.deleteFeature(feature.id())

        self.gcpLayer.commitChanges()

        # aus Eingabelayer holen und in Profilsystem (x, z) konvertieren
        self.gcpLayer.startEditing()
        pr = self.gcpLayer.dataProvider()

        featsSel = refData["pointLayer"].getFeatures()

        selFeatures = []
        for feature in featsSel:
            rotFeature = QgsFeature(self.gcpLayer.fields())

            rotateGeom = self.rotationCoords.rotatePointFeatureFromOrg(feature, "horizontal")

            zPoint = QgsPoint(rotateGeom["x_trans"], rotateGeom["z_trans"], rotateGeom["z_trans"])

            gZPoint = QgsGeometry(zPoint)
            rotFeature.setGeometry(gZPoint)
            rotFeature.setAttributes(feature.attributes())
            selFeatures.append(rotFeature)

        pr.addFeatures(selFeatures)

        self.gcpLayer.commitChanges()
        self.gcpLayer.updateExtents()
        self.gcpLayer.endEditCommand()

        # show the change
        self.gcpLayer.triggerRepaint()
