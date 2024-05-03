# -*- coding: utf-8 -*-
import os
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon, QFont, QColor
from qgis.core import QgsMarkerSymbol, QgsSingleSymbolRenderer, QgsPalLayerSettings, QgsTextFormat, \
    QgsTextBufferSettings, QgsVectorLayerSimpleLabeling, Qgis
from qgis.gui import QgsMapCanvas, QgsMapToolPan, QgsMapToolZoom


## @brief With the TransformationDialogCanvas class a map canvas element is realized.
# It should be used in the transformation dialog
#
# Inherits from QgsMapCanvas
#
# @author Mario Uhlig, VisDat geodatentechnologie GmbH, mario.uhlig@visdat.de
# @date 2020-11-09
class TransformationDialogCanvas(QgsMapCanvas):

    ## The constructor.
    # @param dialogInstance pointer to the dialogInstance
    def __init__(self, dialogInstance):

        super(TransformationDialogCanvas, self).__init__()

        self.iconpath = os.path.join(os.path.dirname(__file__), 'Icons')

        self.dialogInstance = dialogInstance

        self.inputLayers = None
        self.sourceLayer = None

        self.setCanvasColor(Qt.white)

        self.createActionPan()
        self.createActionZoomIn()
        self.createActionZoomOut()
        self.createActionExtent()

        self.createConnects()

    ## \brief Event connections
    #
    def createConnects(self):
        # Koordinatenanzeige
        self.xyCoordinates.connect(self.canvasMoveEvent)

    ## \brief Create action to pan on the map
    #
    def createActionPan(self):

        iconPan = QIcon(os.path.join(self.iconpath, 'mActionPan.png'))
        self.actionPan = QAction(iconPan, "Pan", self)
        self.actionPan.setCheckable(True)

        self.actionPan.triggered.connect(self.pan)

        self.toolPan = QgsMapToolPan(self)
        self.toolPan.setAction(self.actionPan)

        self.pan()

    ## \brief Create action to zoom in on the map
    #
    def createActionZoomIn(self):

        iconZoomIn = QIcon(os.path.join(self.iconpath, 'mActionZoomIn.png'))
        self.actionZoomIn = QAction(iconZoomIn, "Zoom in", self)
        self.actionZoomIn.setCheckable(True)

        self.actionZoomIn.triggered.connect(self.zoomIn)

        self.toolZoomIn = QgsMapToolZoom(self, False)  # false = in
        self.toolZoomIn.setAction(self.actionZoomIn)

    ## \brief Create action to zoom out on the map
    #
    def createActionZoomOut(self):

        iconZoomOut = QIcon(os.path.join(self.iconpath, 'mActionZoomOut.png'))
        self.actionZoomOut = QAction(iconZoomOut, "Zoom out", self)
        self.actionZoomOut.setCheckable(True)

        self.actionZoomOut.triggered.connect(self.zoomOut)

        self.toolZoomOut = QgsMapToolZoom(self, True)  # true = out
        self.toolZoomOut.setAction(self.actionZoomOut)

    ## \brief Create action to zoom to the total extent of the source layer
    #
    def createActionExtent(self):

        iconExtent = QIcon(os.path.join(self.iconpath, 'mActionZoomToLayer.png'))
        self.actionExtent = QAction(iconExtent, "Zoom to layer", self)

        self.actionExtent.triggered.connect(self.setExtentBySourceLayer)

        self.toolZoomOut = QgsMapToolZoom(self, True)  # true = out
        self.toolZoomOut.setAction(self.actionZoomOut)

    ## \brief Set map tool pan
    #
    def pan(self):
        self.setMapTool(self.toolPan)

    ## \brief Set map tool zoom in
    #
    def zoomIn(self):
        self.setMapTool(self.toolZoomIn)

    ## \brief Set map tool zoom out
    #
    def zoomOut(self):
        self.setMapTool(self.toolZoomOut)

    ## \brief Set coordinates on the statusbar in dialog instance
    # TransformationDialog.setCoordinatesOnStatusBar().
    # Depends on mouse move on the map element
    #
    def canvasMoveEvent(self, event):
        x = event.x()
        y = event.y()
        self.dialogInstance.setCoordinatesOnStatusBar(x, y)

    ## \brief Set extent of the map by extent of the source layer
    #
    def setExtentBySourceLayer(self):

        self.setExtent(self.sourceLayer.extent())
        self.refresh()

    ## \brief Update canvas map element
    #
    # - Clear canvas element
    # - Validation of the source layer
    # - Show subset of the source layer - col obj_typ = TransformationDialog.colNameGcpSource
    # - Marker symbol
    # - Label lyer with Id of the feature
    # - Additional display other input layers
    #
    # \param sourceLayer
    # \param inputLayers
    def updateCanvas(self, sourceLayer, inputLayers):

        # canvas leeren
        self.clearCache()
        self.refresh()

        self.sourceLayer = sourceLayer
        self.inputLayers = inputLayers

        # check validation of Layers
        for layer in self.inputLayers:
            if not layer.isValid():
                self.messageBar.pushMessage(
                    "Error",
                    "Layer " + layer.name() + " failed to load!",
                    level=1,
                    duration=5
                )

        sourceCrs = self.sourceLayer.crs()

        self.sourceLayer.setSubsetString("obj_typ = '" + self.dialogInstance.colNameGcpSource + "'")

        # renderer = layer.renderer()

        symbol = QgsMarkerSymbol.createSimple({'name': 'circle', 'color': 'red', 'size': '2'})

        self.sourceLayer.setRenderer(QgsSingleSymbolRenderer(QgsMarkerSymbol()))
        self.sourceLayer.renderer().setSymbol(symbol)
        # show the change
        self.sourceLayer.triggerRepaint()

        # Sets canvas CRS
        # my_crs = QgsCoordinateReferenceSystem(31469, QgsCoordinateReferenceSystem.EpsgCrsId)
        self.setDestinationCrs(sourceCrs)

        # set extent to the extent of Layer E_Point
        self.setExtentBySourceLayer()

        # Label Source Layer
        sourcelayerSettings = QgsPalLayerSettings()
        textFormat = QgsTextFormat()

        textFormat.setFont(QFont("Arial", 12))
        textFormat.setSize(12)

        bufferSettings = QgsTextBufferSettings()
        bufferSettings.setEnabled(True)
        bufferSettings.setSize(0.10)
        bufferSettings.setColor(QColor("black"))

        textFormat.setBuffer(bufferSettings)
        sourcelayerSettings.setFormat(textFormat)

        sourcelayerSettings.fieldName = "pt_nr"
        sourcelayerSettings.placement = Qgis.LabelPlacement.AroundPoint
        sourcelayerSettings.enabled = True

        sourcelayerSettings = QgsVectorLayerSimpleLabeling(sourcelayerSettings)
        self.sourceLayer.setLabelsEnabled(True)
        self.sourceLayer.setLabeling(sourcelayerSettings)
        self.sourceLayer.triggerRepaint()

        # Falls in self.inputLayers auch self.sourceLayer vorhanden ist, wird dieser in Liste ersetzt
        listLayers = [self.sourceLayer]
        for layer in self.inputLayers:
            if layer.name != self.sourceLayer.name():
                listLayers.append(layer)

        self.setLayers(listLayers)

    ## \brief Short highlighting of a feature by obj_uuid
    #
    # \param uuidValue
    def highlightSourceLayer(self, uuidValue):

        for feature in self.sourceLayer.getFeatures():
            uuidFeat = feature.attribute("obj_uuid")
            if uuidFeat == uuidValue:
                self.flashFeatureIds(
                    self.sourceLayer,
                    [feature.id()],
                    startColor=QColor(Qt.green),
                    endColor=QColor(Qt.green),
                    flashes=5,
                    duration=500
                )
