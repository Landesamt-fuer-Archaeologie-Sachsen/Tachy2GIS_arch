## @package QGIS geoEdit extension..

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsLayerTreeGroup,
    QgsLayerTreeLayer,
    QgsRectangle,
)

from .geo_edit_calculations import GeoEditCalculations
from ..Icons import ICON_PATHS


## @brief The class is used to implement functionalities for edit geometies within the dock widget of the Tachy2GIS_arch plugin
#
# @author Mario Uhlig, VisDat geodatentechnologie GmbH, mario.uhlig@visdat.de
# @date 2021-01-22
class GeoEdit:

    ## The constructor.
    #  Defines attributes for the GeoEdit
    #
    #  @param dockWidget pointer to the dockwidget
    #  @param iFace pointer to the iface class
    def __init__(self, t2gArchInstance, iFace):
        self.t2gArchInstance = t2gArchInstance
        self.dockwidget = t2gArchInstance.dockwidget
        self.iface = iFace
        # FIDs of the selected features at the moment of starting forward translation
        self.selectedFids = []
        # Selected features at the moment of starting forward translation | used only in "absolute" transformation
        self.selectedFeatures = []
        # Selected layer at the moment of starting forward translation
        self.sourceLayer = None
        # X, Y, Z value at the moment of starting forward translation
        self.translationZ = 0
        self.translationY = 0
        self.translationX = 0
        # State of "relativ" (True) or "absolut" (False) radios
        self.relativeCheck = True
        # Allow reverse process
        self.allowReverse = False

    ## @brief Initializes the functionality for geoEdit modul
    # - Preselection of inputlayer, calls preselectionComboInputlayers()
    # - Connects elements in the geoEdit dockwidget to related functions
    def setup(self):

        # Setup "Verschieben"
        self.geoCalc = GeoEditCalculations(self)

        # Preselection of Inputlayers (only Layer below "Eingabelayer" are available)
        self.preselectionComboInputlayers()
        # Start process moving selected features
        self.dockwidget.btnGeometryMoveRun.clicked.connect(self.moveGeometryForward)
        # Start process moving selected features reverse
        self.dockwidget.btnGeometryMoveReverse.clicked.connect(self.moveGeometryReverse)
        # Signal connection of "relativ" and "absolut" radios
        self.dockwidget.radioGeometryMoveRelativ.toggled.connect(self.relativeAbsolutChanged)
        # Signal connection Infobutton
        self.dockwidget.btnGeometryMoveInfo.clicked.connect(self.openInfoMessageBox)
        # Get signal when active layer in layertree is changed
        self.iface.layerTreeView().currentLayerChanged.connect(self.activeLayerIsChanged)
        # Disable reverse button
        self.setAllowReverse(False)

        # Setup "Verschneiden"
        self.dockwidget.butContactClip.setToolTip("Berührend")
        self.dockwidget.butContactClip.setIcon(QIcon(ICON_PATHS["butContactClip"]))
        self.dockwidget.butContactClip.clicked.connect(self.geoCalc.contactClip)

        self.dockwidget.butOutsideClip.setToolTip("Außenliegend")
        self.dockwidget.butOutsideClip.setIcon(QIcon(ICON_PATHS["butOutsideClip"]))
        self.dockwidget.butOutsideClip.clicked.connect(self.geoCalc.outsideClip)

        self.dockwidget.butInsideClip.setToolTip("Innenliegend")
        self.dockwidget.butInsideClip.setIcon(QIcon(ICON_PATHS["butInsideClip"]))
        self.dockwidget.butInsideClip.clicked.connect(self.geoCalc.insideClip)

        # Setup Sonstiges
        self.dockwidget.butLineRes.setIcon(QIcon(ICON_PATHS["LineRe"]))
        self.dockwidget.butLineRes.setToolTip("Linie umdrehen")
        self.dockwidget.butLineRes.clicked.connect(self.t2gArchInstance.reverseLines)

    def disconnectSignals(self):
        # muss disconnected werden bei reload des Plugins
        self.iface.layerTreeView().currentLayerChanged.disconnect(self.activeLayerIsChanged)

    ## @brief Start process to move features forward
    # - Get input values
    # - Check validity of the sourcelayer
    # - Connects elements in the geoEdit dockwidget to related functions
    def moveGeometryForward(self):

        # Get input values
        self.sourceLayer = self.getInputLayer()

        # Check validity of the sourcelayer
        generalValid, validationText, detailedText = self.checkSourceLayerValidity()

        if generalValid == True:

            self.relativeCheck = self.getRelativeAbsolut()
            self.selectedFids = self.getSelectedFids()
            self.selectedFeatures = self.getSelectedFeatures()

            # Do translation only if features of the sourcelayer are selected
            if len(self.selectedFids) > 0:

                # Relative translation
                if self.relativeCheck == True:

                    self.translationZ = self.getZValue()
                    self.translationY = self.getYValue()
                    self.translationX = self.getXValue()
                    # Start process translate relative and forward
                    self.moveGeometryRelative("forward")
                    # Enable reverse translation
                    self.setAllowReverse(True)

                # Absolute translation
                else:
                    self.translationZ = self.getZValue()
                    self.translationY = 0
                    self.translationX = 0
                    # Start process translate absolute and forward
                    self.moveGeometryAbsolute("forward")
                    # Enable reverse translation
                    self.setAllowReverse(True)
            else:
                self.iface.messageBar().pushMessage("Hinweis", "Keine Features ausgewählt!", level=1, duration=5)

        else:
            self.iface.messageBar().pushMessage("Error", validationText, level=2, duration=5)

    ## @brief Start process to move features reverse
    # - Only when self.allowReverse is True
    # - Calls moveGeometryRelative() or moveGeometryAbsolute()
    # - Only one reverse step is passible
    def moveGeometryReverse(self):

        if self.allowReverse == True:
            if self.relativeCheck == True:
                self.moveGeometryRelative("reverse")
                self.setAllowReverse(False)
            else:
                self.moveGeometryAbsolute("reverse")
                self.setAllowReverse(False)

    ## @brief Start process to move features relative
    #
    #  @param tranlationDirection could be "forward" or "reverse"
    #
    # - Do translation only if features of the sourcelayer are selected
    # - Branch depending on wkb type - Query for Z and ZM single layer types - layerTranslationXYZ() does not output a correct Z value there (bug???).
    def moveGeometryRelative(self, tranlationDirection):

        # Create spatial index
        self.createLayerSpatialIndex()
        # Get wkb type of the sourcelayer
        layerType = self.sourceLayer.wkbType()
        print("layerType", layerType)

        self.geoCalc.layerTranslationXYZ(
            tranlationDirection, self.sourceLayer, self.translationX, self.translationY, self.translationZ
        )

        # Recalculate Extent
        self.recalculateLayerExtent()
        # Again create spatial index
        self.createLayerSpatialIndex()
        # Selection is lost so the features have to be reselected
        self.reselectFeatures()

        self.iface.messageBar().pushMessage(
            "Hinweis",
            "Die relative Verschiebung des Layers " + self.sourceLayer.name() + " ist fertig!",
            level=3,
            duration=5,
        )

    ## @brief Start process to move features absolute
    #
    #  @param tranlationDirection could be "forward" or "reverse"
    #
    # - Do translation only if features of the sourcelayer are selected
    # - Branch depending on wkb type - Query for Z and ZM single layer types - layerTranslationXYZ does not output a correct Z value there (bug???).
    def moveGeometryAbsolute(self, tranlationDirection):

        # Create spatial index
        self.createLayerSpatialIndex()
        # Absolute z-translation
        self.geoCalc.layerTranslationZAbsolute(
            tranlationDirection, self.sourceLayer, self.translationZ, self.selectedFeatures
        )
        # Recalculate Extent
        self.recalculateLayerExtent()
        # Create spatial index
        self.createLayerSpatialIndex()
        # Selection is lost so the features have to be reselected
        self.reselectFeatures()

        self.iface.messageBar().pushMessage(
            "Hinweis",
            "Die absolute Verschiebung des Layers " + self.sourceLayer.name() + " ist fertig!",
            level=3,
            duration=5,
        )

    ## @brief Set permission to start a reverse transformation
    #
    #  @param boolValue could be True or False
    #
    # - Enable or disable reverse button
    def setAllowReverse(self, boolValue: bool):
        self.allowReverse = boolValue
        self.dockwidget.btnGeometryMoveReverse.setEnabled(boolValue)

    ## @brief State change of "relativ" and "absolut" radios
    # Enable or disable input fields
    def relativeAbsolutChanged(self):

        checker = self.getRelativeAbsolut()

        if checker == True:
            self.dockwidget.spinBoxGeometryMoveX.setEnabled(True)
            self.dockwidget.spinBoxGeometryMoveY.setEnabled(True)
        else:
            self.dockwidget.spinBoxGeometryMoveX.setEnabled(False)
            self.dockwidget.spinBoxGeometryMoveY.setEnabled(False)

    ## @brief Get z value of the spinBoxGeometryMoveZ input
    #
    def getZValue(self):
        zVal = self.dockwidget.spinBoxGeometryMoveZ.value()
        return zVal

    ## @brief Get y value of the spinBoxGeometryMoveY input
    #
    def getYValue(self):
        yVal = self.dockwidget.spinBoxGeometryMoveY.value()
        return yVal

    ## @brief Get x value of the spinBoxGeometryMoveX input
    #
    def getXValue(self):
        xVal = self.dockwidget.spinBoxGeometryMoveX.value()
        return xVal

    ## @brief Get the current sourcelayer in the layerGeometryMove selection
    #
    def getInputLayer(self):
        sourceLayer = self.dockwidget.layerGeometryMove.currentLayer()
        return sourceLayer

    ## @brief Get the current state of "relative" and "absolute" radio
    #
    def getRelativeAbsolut(self):
        relativCheck = self.dockwidget.radioGeometryMoveRelativ.isChecked()
        return relativCheck

    ## @brief Get the selected features of the sourcelayer
    #
    def getSelectedFeatures(self):
        selectedFeatures = self.sourceLayer.selectedFeatures()
        return selectedFeatures

    ## @brief Get the fids of the selected features of the sourcelayer
    #
    def getSelectedFids(self):
        selectedFids = []
        selection = self.sourceLayer.selectedFeatures()
        for feature in selection:
            selectedFids.append(feature.id())
        return selectedFids

    ## @brief Reselect faetures of the sourcelayer
    #
    def reselectFeatures(self):
        self.sourceLayer.select(self.selectedFids)

    ## @brief Event handler is executed after active layer is changed
    #
    #  @param currentActiveLayer active layer object
    def activeLayerIsChanged(self, currentActiveLayer):

        inputLayers = self.getInputlayers(False)
        for layer in inputLayers:
            if layer == currentActiveLayer:
                self.dockwidget.layerGeometryMove.setLayer(currentActiveLayer)

    ## \brief Check the validity of the sourcelayer
    #
    # Uses QgsGeometry --> validateGeometry()
    def checkSourceLayerValidity(self):

        generalValid = False

        # is vector layer
        if isinstance(self.sourceLayer, QgsVectorLayer):
            generalValid = True

            layerSourceType = self.sourceLayer.dataProvider().storageType()

            print("layerSourceType", layerSourceType)

            if layerSourceType == "GPKG":

                validationText = "Ungültige Geometrien können zu Fehlern bei der Verschiebung führen! Bitte bereinigen Sie die Geometrien im Vorfeld einer Verschiebung! \n\n"

                detailedText = "\n" + self.sourceLayer.name() + "\n----------------------\n"

                validationFeatureText = ""

                for i, feat in enumerate(self.sourceLayer.selectedFeatures()):

                    validationError = feat.geometry().validateGeometry()

                    if not validationError:
                        pass
                    else:

                        for singleError in validationError:
                            validationFeatureText += "FeatureId " + str(feat.id()) + ": " + singleError.what() + "\n"

                if not validationFeatureText:
                    validationFeatureText = "Geometrien sind gültig!\n"
                else:
                    generalValid = False

                detailedText += validationFeatureText

            else:
                generalValid = False
                validationText = "Sourcelayer ist kein Geopackage"
                detailedText = ""
                self.iface.messageBar().pushMessage("Error", "Sourcelayer ist kein Geopackage", level=1, duration=5)

        else:
            generalValid = False
            validationText = "Sourcelayer ist kein Vektorlayer"
            detailedText = ""
            self.iface.messageBar().pushMessage("Error", "Sourcelayer ist kein Vektorlayer", level=1, duration=5)

        return generalValid, validationText, detailedText

    ## \brief This function creates a new spatial index for a layer
    #
    def createLayerSpatialIndex(self):
        self.sourceLayer.dataProvider().createSpatialIndex()

    ## \brief Preselection of comboEingabelayerTransform
    #
    # If layer E_Point exists then preselect this
    def preselectionComboInputlayers(self):

        notInputLayers = self.getNotInputlayers()
        inputLayers = self.getInputlayers(False)

        self.dockwidget.layerGeometryMove.setExceptedLayerList(notInputLayers)

        for layer in inputLayers:
            if layer.name() == "E_Polygon":
                self.dockwidget.layerGeometryMove.setLayer(layer)

        currentActiveLayer = self.iface.activeLayer()
        self.activeLayerIsChanged(currentActiveLayer)

    ## \brief Get all inputlayers from the folder "Eingabelayer" of the layertree
    #
    # Inputlayers must be of type vector
    #
    # \param isClone - should the return a copy of the layers or just a pointer to the layers
    # @returns Array of inputlayers

    def getInputlayers(self, isClone):

        inputLayers = []
        root = QgsProject.instance().layerTreeRoot()

        for group in root.children():
            if isinstance(group, QgsLayerTreeGroup) and group.name() == "Eingabelayer":
                for child in group.children():
                    if isinstance(child, QgsLayerTreeLayer):
                        if isClone == True:

                            if isinstance(child.layer(), QgsVectorLayer):
                                inputLayers.append(child.layer().clone())
                        else:
                            if isinstance(child.layer(), QgsVectorLayer):
                                inputLayers.append(child.layer())

        return inputLayers

    ## \brief Get all layers from the layertree exept those from the folder "Eingabelayer"
    #
    # layers must be of type vectorlayer
    def getNotInputlayers(self):

        allLayers = QgsProject.instance().mapLayers().values()

        inputLayer = []
        notInputLayer = []
        root = QgsProject.instance().layerTreeRoot()

        for group in root.children():
            if isinstance(group, QgsLayerTreeGroup) and group.name() == "Eingabelayer":
                for child in group.children():
                    if isinstance(child, QgsLayerTreeLayer):
                        if isinstance(child.layer(), QgsVectorLayer):
                            inputLayer.append(child.layer())

        for layerA in allLayers:
            check = False
            for layerIn in inputLayer:
                if layerA == layerIn:
                    check = True

            if check == False:
                notInputLayer.append(layerA)

        return notInputLayer

    ## \brief Calculates the current extent of a layer
    #
    def recalculateLayerExtent(self):

        targetExtent = QgsRectangle()
        targetExtent.setMinimal()
        for feat in self.sourceLayer.getFeatures():
            bbox = feat.geometry().boundingBox()
            targetExtent.combineExtentWith(bbox)

        self.sourceLayer.setExtent(targetExtent)

    ## \brief Opens a message box with background informations
    #

    def openInfoMessageBox(self):

        infoText = 'Der Nutzer kann hier einen Eingabelayer auswählen, in dem Features verschoben werden sollen. Es ist zu beachten, dass lediglich selektierte Features verschoben werden. Die Selektion erfolgt über die Selektionsfunktionen, die QGIS standardmäßig bereitstellt. \n \nEs kann festgelegt werden, welchen Typ die Verschiebung haben soll. "Relativ" bedeutet es erfolgt eine Verschiebung um den angegebenen Wert. Bspw. erfolgt bei der Z-Verschiebung um 10m die Verschiebung aller Stützpunkte einer Geometrie in Z-Richtung additiv um 10m. \n \n Bei der "absoluten" Verschiebung ist lediglich die Verschiebung in Z-Richtung möglich. Hier wird für alle Stützpunkte einer Geometrie der angegebene Wert festgelegt. Das Verschieben kann durch Klick auf den "Rückgängig" Button zurückgesetzt werden.'

        self.infoTranssformMsgBox = QMessageBox()
        self.infoTranssformMsgBox.setText(infoText)
        self.infoTranssformMsgBox.setWindowTitle("Hintergrundinformationen")
        self.infoTranssformMsgBox.setStandardButtons((QMessageBox.Ok))
        self.infoTranssformMsgBox.exec_()
