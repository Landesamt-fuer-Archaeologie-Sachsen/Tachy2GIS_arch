## @package QGIS geoEdit extension..
import shutil
import os

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMessageBox
from qgis.core import QgsProject, QgsGeometry, QgsVectorLayer, QgsApplication, QgsLayerTreeGroup, QgsLayerTreeLayer, QgsRectangle, QgsVectorFileWriter
from processing.gui import AlgorithmExecutor
from qgis import processing

from .geo_edit_calculations import GeoEditCalculations

## @brief The class is used to implement functionalities for edit geometies within the dock widget of the Tachy2GIS_arch plugin
#
# @author Mario Uhlig, VisDat geodatentechnologie GmbH, mario.uhlig@visdat.de
# @date 2021-01-22
class GeoEdit():

    ## The constructor.
    #  Defines attributes for the GeoEdit
    #
    #  @param dockWidget pointer to the dockwidget
    #  @param iFace pointer to the iface class
    def __init__(self, t2gArchInstance, iFace):

        self.__iconpath = os.path.join(os.path.dirname(__file__), 'Icons')
        self.__t2gArchInstance = t2gArchInstance
        self.__dockwidget = t2gArchInstance.dockwidget
        self.__iface = iFace
        #FIDs of the selected features at the moment of starting forward translation
        self.__selectedFids = []
        #Selected features at the moment of starting forward translation | used only in "absolute" transformation
        self.__selectedFeatures = []
        #Selected layer at the moment of starting forward translation
        self.__sourceLayer = None
        #X, Y, Z value at the moment of starting forward translation
        self.__translationZ = 0
        self.__translationY = 0
        self.__translationX = 0
        #State of "relativ" (True) or "absolut" (False) radios
        self.__relativeCheck = True
        #Allow reverse process
        self.__allowReverse = False

    ## @brief Initializes the functionality for geoEdit modul
    # - Preselection of inputlayer, calls __preselectionComboInputlayers()
    # - Connects elements in the geoEdit dockwidget to related functions
    def setup(self):

        #Setup "Verschieben"
        self.geoCalc = GeoEditCalculations(self)

        #Preselection of Inputlayers (only Layer below "Eingabelayer" are available)
        self.__preselectionComboInputlayers()
        #Start process moving selected features
        self.__dockwidget.btnGeometryMoveRun.clicked.connect(self.__moveGeometryForward)
        #Start process moving selected features reverse
        self.__dockwidget.btnGeometryMoveReverse.clicked.connect(self.__moveGeometryReverse)
        #Signal connection of "relativ" and "absolut" radios
        self.__dockwidget.radioGeometryMoveRelativ.toggled.connect(self.__relativeAbsolutChanged)
        #Signal connection Infobutton
        self.__dockwidget.btnGeometryMoveInfo.clicked.connect(self.__openInfoMessageBox)
        #Get signal when active layer in layertree is changed
        self.__iface.layerTreeView().currentLayerChanged.connect(self.__activeLayerIsChanged)
        #Disable reverse button
        self.__setAllowReverse(False)

        #Setup "Verschneiden"
        self.__dockwidget.butContactClip.setToolTip('Berührend')
        self.__dockwidget.butContactClip.setIcon(QIcon(os.path.join(self.__iconpath, 'butContactClip.gif')))
        self.__dockwidget.butContactClip.clicked.connect(self.__t2gArchInstance.contactClip)

        self.__dockwidget.butOutsideClip.setToolTip('Außenliegend')
        self.__dockwidget.butOutsideClip.setIcon(QIcon(os.path.join(self.__iconpath, 'butOutsideClip.gif')))
        self.__dockwidget.butOutsideClip.clicked.connect(self.__t2gArchInstance.outsideClip)

        self.__dockwidget.butInsideClip.setToolTip('Innenliegend')
        self.__dockwidget.butInsideClip.setIcon(QIcon(os.path.join(self.__iconpath, 'butInsideClip.gif')))
        self.__dockwidget.butInsideClip.clicked.connect(self.__t2gArchInstance.insideClip)

        #Setup Sonstiges
        self.__dockwidget.butLineRes.setIcon(QIcon(os.path.join(self.__iconpath, 'LineRe.gif')))
        self.__dockwidget.butLineRes.setToolTip('Linie umdrehen')
        self.__dockwidget.butLineRes.clicked.connect(self.__t2gArchInstance.lineFeatureReverse)

    ## @brief Start process to move features forward
    # - Get input values
    # - Check validity of the sourcelayer
    # - Connects elements in the geoEdit dockwidget to related functions
    def __moveGeometryForward(self):

        #Get input values
        self.__sourceLayer = self.__getInputLayer()

        #Check validity of the sourcelayer
        generalValid, validationText, detailedText = self.__checkSourceLayerValidity()

        if generalValid == True:

            self.__relativeCheck = self.__getRelativeAbsolut()
            self.__selectedFids = self.__getSelectedFids()
            self.__selectedFeatures = self.__getSelectedFeatures()

            #Do translation only if features of the sourcelayer are selected
            if len(self.__selectedFids) > 0:

                #Relative translation
                if self.__relativeCheck == True:

                    self.__translationZ = self.__getZValue()
                    self.__translationY = self.__getYValue()
                    self.__translationX = self.__getXValue()
                    #Start process translate relative and forward
                    self.__moveGeometryRelative('forward')
                    #Enable reverse translation
                    self.__setAllowReverse(True)

                #Absolute translation
                else:
                    self.__translationZ = self.__getZValue()
                    self.__translationY = 0
                    self.__translationX = 0
                    #Start process translate absolute and forward
                    self.__moveGeometryAbsolute('forward')
                    #Enable reverse translation
                    self.__setAllowReverse(True)
            else:
                self.__iface.messageBar().pushMessage("Hinweis", "Keine Features ausgewählt!", level=1, duration=5)

        else:
            self.__iface.messageBar().pushMessage("Error", validationText, level=2, duration=5)


    ## @brief Start process to move features reverse
    # - Only when self.__allowReverse is True
    # - Calls __moveGeometryRelative() or __moveGeometryAbsolute()
    # - Only one reverse step is passible
    def __moveGeometryReverse(self):

        if self.__allowReverse == True:
            if self.__relativeCheck == True:
                self.__moveGeometryRelative('reverse')
                self.__setAllowReverse(False)
            else:
                self.__moveGeometryAbsolute('reverse')
                self.__setAllowReverse(False)

    ## @brief Start process to move features relative
    #
    #  @param tranlationDirection could be "forward" or "reverse"
    #
    # - Do translation only if features of the sourcelayer are selected
    # - Branch depending on wkb type - Query for Z and ZM single layer types - __layerTranslationXYZ() does not output a correct Z value there (bug???).
    def __moveGeometryRelative(self, tranlationDirection):

        #Create spatial index
        self.__createLayerSpatialIndex()
        #Get wkb type of the sourcelayer
        layerType = self.__sourceLayer.wkbType()
        print('layerType', layerType)

        self.geoCalc.layerTranslationXYZ(tranlationDirection, self.__sourceLayer, self.__translationX, self.__translationY, self.__translationZ)

        #Recalculate Extent
        self.__recalculateLayerExtent()
        #Again create spatial index
        self.__createLayerSpatialIndex()
        #Cache layer and thus overwrite .shp and .idx so that the extent of the layer is correct.
        self.__saveLayerAfterTransformation()
        #Selection is lost so the features have to be reselected
        self.__reselectFeatures()

        self.__iface.messageBar().pushMessage("Hinweis", 'Die relative Verschiebung des Layers '+self.__sourceLayer.name()+' ist fertig!', level=3, duration=5)

    ## @brief Start process to move features absolute
    #
    #  @param tranlationDirection could be "forward" or "reverse"
    #
    # - Do translation only if features of the sourcelayer are selected
    # - Branch depending on wkb type - Query for Z and ZM single layer types - __layerTranslationXYZ does not output a correct Z value there (bug???).
    def __moveGeometryAbsolute(self, tranlationDirection):

        #Create spatial index
        self.__createLayerSpatialIndex()
        #Absolute z-translation
        self.geoCalc.layerTranslationZAbsolute(tranlationDirection, self.__sourceLayer, self.__translationZ, self.__selectedFeatures)
        #Recalculate Extent
        self.__recalculateLayerExtent()
        #Create spatial index
        self.__createLayerSpatialIndex()
        #Selection is lost so the features have to be reselected
        self.__reselectFeatures()

        self.__iface.messageBar().pushMessage("Hinweis", 'Die absolute Verschiebung des Layers '+self.__sourceLayer.name()+' ist fertig!', level=3, duration=5)


    ## @brief Set permission to start a reverse transformation
    #
    #  @param boolValue could be True or False
    #
    # - Enable or disable reverse button
    def __setAllowReverse(self, boolValue: bool):
        self.__allowReverse = boolValue
        self.__dockwidget.btnGeometryMoveReverse.setEnabled(boolValue)

    ## @brief State change of "relativ" and "absolut" radios
    # Enable or disable input fields
    def __relativeAbsolutChanged(self):

        checker = self.__getRelativeAbsolut()

        if checker == True:
            self.__dockwidget.spinBoxGeometryMoveX.setEnabled(True)
            self.__dockwidget.spinBoxGeometryMoveY.setEnabled(True)
        else:
            self.__dockwidget.spinBoxGeometryMoveX.setEnabled(False)
            self.__dockwidget.spinBoxGeometryMoveY.setEnabled(False)

    ## @brief Get z value of the spinBoxGeometryMoveZ input
    #
    def __getZValue(self):
        zVal = self.__dockwidget.spinBoxGeometryMoveZ.value()
        return zVal
    ## @brief Get y value of the spinBoxGeometryMoveY input
    #
    def __getYValue(self):
        yVal = self.__dockwidget.spinBoxGeometryMoveY.value()
        return yVal
    ## @brief Get x value of the spinBoxGeometryMoveX input
    #
    def __getXValue(self):
        xVal = self.__dockwidget.spinBoxGeometryMoveX.value()
        return xVal
    ## @brief Get the current sourcelayer in the layerGeometryMove selection
    #
    def __getInputLayer(self):
        sourceLayer = self.__dockwidget.layerGeometryMove.currentLayer()
        return sourceLayer
    ## @brief Get the current state of "relative" and "absolute" radio
    #
    def __getRelativeAbsolut(self):
        relativCheck = self.__dockwidget.radioGeometryMoveRelativ.isChecked()
        return relativCheck
    ## @brief Get the selected features of the sourcelayer
    #
    def __getSelectedFeatures(self):
        selectedFeatures = self.__sourceLayer.selectedFeatures()
        return selectedFeatures
    ## @brief Get the fids of the selected features of the sourcelayer
    #
    def __getSelectedFids(self):
        selectedFids = []
        selection = self.__sourceLayer.selectedFeatures()
        for feature in selection:
            selectedFids.append(feature.id())
        return selectedFids

    ## @brief Reselect faetures of the sourcelayer
    #
    def __reselectFeatures(self):
        self.__sourceLayer.select(self.__selectedFids)

    ## @brief Event handler is executed after active layer is changed
    #
    #  @param currentActiveLayer active layer object
    def __activeLayerIsChanged(self, currentActiveLayer):

        inputLayers = self.__getInputlayers(False)
        for layer in inputLayers:
            if layer == currentActiveLayer:
                self.__dockwidget.layerGeometryMove.setLayer(currentActiveLayer)

    ## \brief Check the validity of the sourcelayer
    #
    # Uses QgsGeometry --> validateGeometry()
    def __checkSourceLayerValidity(self):

        generalValid = False

        # is vector layer
        if isinstance(self.__sourceLayer, QgsVectorLayer):
            generalValid = True

            layerSourceType = self.__sourceLayer.source()[-3:]

            if layerSourceType == 'shp':

                validationText = 'Ungültige Geometrien können zu Fehlern bei der Verschiebung führen! Bitte bereinigen Sie die Geometrien im Vorfeld einer Verschiebung! \n\n'

                detailedText = '\n'+self.__sourceLayer.name()+'\n----------------------\n'

                validationFeatureText = ''

                #for i, feat in enumerate(self.__sourceLayer.getFeatures()):
                for i, feat in enumerate(self.__sourceLayer.selectedFeatures()):

                    validationError = feat.geometry().validateGeometry()

                    if not validationError:
                        pass
                    else:

                        for singleError in validationError:
                            validationFeatureText += 'FeatureId '+str(feat.id())+': '+singleError.what()+'\n'

                if not validationFeatureText:
                    validationFeatureText = 'Geometrien sind gültig!\n'
                else:
                    generalValid = False

                detailedText += validationFeatureText

            else:
                generalValid = False
                validationText = "Sourcelayer ist kein Esri Shapefile"
                detailedText = ""
                self.__iface.messageBar().pushMessage("Error", "Sourcelayer ist kein Esri Shapefile", level=1, duration=5)

        else:
            generalValid = False
            validationText = "Sourcelayer ist kein Vektorlayer"
            detailedText = ""
            self.__iface.messageBar().pushMessage("Error", "Sourcelayer ist kein Vektorlayer", level=1, duration=5)

        return generalValid, validationText, detailedText

    ## \brief This function creates a new spatial index for a layer
    #
    def __createLayerSpatialIndex(self):
        self.__sourceLayer.dataProvider().createSpatialIndex()

    ## \brief Save sourcelayer after transformation and overwrite original data
    #
    # A correct "resave" is necessary to ensure that the extent of the layers is correct after the transformations.
    # - The extent of the layer is stored in the .shp file
    # - Problem: you cannot overwrite the shapefile directly while the project is open.
    # - Workaround: Layer will be saved temporarily, then only the shp and shx file will be copied from there and the files can be overwritten
    def __saveLayerAfterTransformation(self):

        sourceUri = self.__sourceLayer.dataProvider().dataSourceUri().split('.shp|')[0]
        #Backuppfad finden und gfl. erzeugen
        projectPath = QgsProject.instance().readPath("../")
        backupPath = projectPath+"/Shape/after_transform/"
        completePath = backupPath+self.__sourceLayer.name()+".shp"
        if not os.path.exists(backupPath):
            os.makedirs(backupPath)

        #layer in Backuppfad schreiben
        QgsVectorFileWriter.writeAsVectorFormat(self.__sourceLayer, completePath, "UTF-8", self.__sourceLayer.crs(), "ESRI Shapefile")

        #.shx und .shp Dateien im Orginal überschreiben
        #shx
        source = backupPath+self.__sourceLayer.name()+'.shx'
        target = sourceUri+'.shx'
        shutil.copy(source, target)

        #shp
        source = backupPath+self.__sourceLayer.name()+'.shp'
        target = sourceUri+'.shp'
        shutil.copy(source, target)

        # temporären backupPath Pfad wieder löschen
        shutil.rmtree(backupPath)

    ## \brief Preselection of comboEingabelayerTransform
    #
    # If layer E_Point exists then preselect this
    def __preselectionComboInputlayers(self):

        notInputLayers = self.__getNotInputlayers()
        inputLayers = self.__getInputlayers(False)

        self.__dockwidget.layerGeometryMove.setExceptedLayerList(notInputLayers)

        for layer in inputLayers:
            if layer.name() == 'E_Polygon':
                self.__dockwidget.layerGeometryMove.setLayer(layer)

        currentActiveLayer = self.__iface.activeLayer()
        self.__activeLayerIsChanged(currentActiveLayer)

    ## \brief Get all inputlayers from the folder "Eingabelayer" of the layertree
    #
    # Inputlayers must be of type vector
    #
    # \param isClone - should the return a copy of the layers or just a pointer to the layers
    # @returns Array of inputlayers

    def __getInputlayers(self, isClone):

        inputLayers = []
        root = QgsProject.instance().layerTreeRoot()

        for group in root.children():
            if isinstance(group, QgsLayerTreeGroup) and group.name() == 'Eingabelayer':
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
    def __getNotInputlayers(self):

        allLayers = QgsProject.instance().mapLayers().values()

        inputLayer = []
        notInputLayer = []
        root = QgsProject.instance().layerTreeRoot()

        for group in root.children():
            if isinstance(group, QgsLayerTreeGroup) and group.name() == 'Eingabelayer':
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
    def __recalculateLayerExtent(self):

        targetExtent = QgsRectangle()
        targetExtent.setMinimal()
        for feat in self.__sourceLayer.getFeatures():

            bbox = feat.geometry().boundingBox()
            targetExtent.combineExtentWith(bbox)

        self.__sourceLayer.setExtent(targetExtent)


    ## \brief Opens a message box with background informations
    #

    def __openInfoMessageBox(self):

        infoText = "Der Nutzer kann hier einen Eingabelayer auswählen, in dem Features verschoben werden sollen. Es ist zu beachten, dass lediglich selektierte Features verschoben werden. Die Selektion erfolgt über die Selektionsfunktionen, die QGIS standardmäßig bereitstellt. \n \nEs kann festgelegt werden, welchen Typ die Verschiebung haben soll. \"Relativ\" bedeutet es erfolgt eine Verschiebung um den angegebenen Wert. Bspw. erfolgt bei der Z-Verschiebung um 10m die Verschiebung aller Stützpunkte einer Geometrie in Z-Richtung additiv um 10m. \n \n Bei der \"absoluten\" Verschiebung ist lediglich die Verschiebung in Z-Richtung möglich. Hier wird für alle Stützpunkte einer Geometrie der angegebene Wert festgelegt. Das Verschieben kann durch Klick auf den \"Rückgängig\" Button zurückgesetzt werden."

        self.__infoTranssformMsgBox = QMessageBox()
        self.__infoTranssformMsgBox.setText(infoText)
        self.__infoTranssformMsgBox.setWindowTitle("Hintergrundinformationen")
        self.__infoTranssformMsgBox.setStandardButtons((QMessageBox.Ok))
        self.__infoTranssformMsgBox.exec_()
