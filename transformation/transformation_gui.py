## @package QGIS transformation extension..
import csv
import os
import shutil
import time

from qgis.PyQt.QtWidgets import QMessageBox
from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsLayerTreeGroup,
    QgsLayerTreeLayer,
    QgsCoordinateReferenceSystem,
    QgsWkbTypes,
)

from .transformation_calculations import TransformationCalculations
from .transformation_dialog import TransformationDialog


## @brief The class is used to implement GUI functionalities for transformation within the dock widget of the Tachy2GIS_arch plugin
#
# @author Mario Uhlig, VisDat geodatentechnologie GmbH, mario.uhlig@visdat.de
# @date 2020-10-19
class TransformationGui:

    ## The constructor.
    #  Defines attributes for the transformation
    #
    #  Initialize class TransformationCalculations as self.paramCalc
    #
    #  Initialize class TransformationDialog as self.transformationDialog
    #
    #  @param dockWidget pointer to the dockwidget
    #  @param iFace pointer to the iface class
    def __init__(self, dockWidget, iFace):

        self.iface = iFace
        self.dockwidget = dockWidget
        self.colNameGcpSource = "11"  # enspricht 'Festpunkt'
        self.transformationDialog = TransformationDialog(self)
        self.paramCalc = TransformationCalculations(self)
        self.transformationParametersDone = False
        self.zAngle = float("NAN")
        self.translationX = float("NAN")
        self.translationY = float("NAN")
        self.translationZ = float("NAN")
        self.defaultEpsg = QgsCoordinateReferenceSystem("EPSG:31469")

    ## @brief Initializes the functionality for transformation modul
    # - Reads the transformation status and any transformation parameters from the QGIS project file
    # - Preselection of inputlayer, calls preselectionComboInputlayers()
    # - Connects elements in the transformation dockwidget to related functions
    def setup(self):

        transformationStateId, transformationStatelong = self.getTransformationStateFromProject()
        # 1 - Vektordaten wurden transformiert oder 2 - Transformation wurde zurückgesetzt.
        if transformationStateId == 1 or transformationStateId == 2:
            self.transformationParametersDone = True
        else:
            self.transformationParametersDone = False

        self.getTransformationParametersFromProject()
        self.setTransformationStateGUI(transformationStateId, transformationStatelong)
        self.setTransformationParametersGUI(self.translationX, self.translationY, self.translationZ, self.zAngle)

        # Preselection Inputlayer
        self.preselectionComboInputlayers()

        self.dockwidget.projectionSelectionTransform.setCrs(self.defaultEpsg)
        self.dockwidget.btnOpenTransformDlg.clicked.connect(self.transformationDialogShow)
        self.dockwidget.transformResetBtn.clicked.connect(self.resetTransformationMessageBox)
        self.dockwidget.btnTransformInputLayers.clicked.connect(self.startTransformation)
        self.dockwidget.transformValidityBtn.clicked.connect(self.openValidityMessageBox)
        self.dockwidget.transformInfoBtn.clicked.connect(self.openInfoMessageBox)

    ## \brief Save the current QGIS-Project
    #

    def saveProject(self):

        projectFile = QgsProject.instance().fileName()
        print("Save projectfile: ", projectFile)
        if projectFile != "":
            QgsProject.instance().write(projectFile)

    ## \brief Preselection of comboEingabelayerTransform
    #
    # If layer E_Point exists then preselect this
    #

    def preselectionComboInputlayers(self):

        inputLayers = self.getInputlayers(False)
        for layer in inputLayers:
            if layer.name() == "E_Point":
                self.dockwidget.comboEingabelayerTransform.setLayer(layer)

    ## \brief Set transformation state of the current Project in GUI
    #
    # Set text to transformationStateText element (QLineEdit)
    #
    # @param stateId 0 - no transformation yet; 1 - Vector data were transformed; 2 - Transformation was reset
    # @param textValue The text value of the transformation state
    def setTransformationStateGUI(self, stateId, textValue):

        # 0 - noch keine Transformation 1 - Vektordaten wurden transformiert oder 2 - Transformation wurde zurückgesetzt.
        if stateId == 0:
            styleText = "QLabel {color : grey;}"
        if stateId == 1:
            styleText = "QLabel {color : green;}"
        if stateId == 2:
            styleText = "QLabel {color : grey;}"

        self.dockwidget.transformationStateText.setStyleSheet(styleText)
        self.dockwidget.transformationStateText.setText(textValue)

    ## \brief Get tranformation state of the current project
    #
    # @returns transformationStateId (e.g. transformationStateId - 0)
    # @returns transformationStatelong (e.g. transformationStatelong - No transformation has been executed yet)
    def getTransformationStateFromProject(self):

        projectSettings = QgsProject.instance()
        transformationStateId = projectSettings.readNumEntry("transformation_state_id", "int", 0)[0]
        transformationStatelong = projectSettings.readEntry(
            "transformation_state_long", "text", "Es wurde bisher keine Transformation ausgeführt."
        )[0]

        return transformationStateId, transformationStatelong

    ## \brief Set tranformation state of the current project
    # Save it to project file - saveProject()
    # \param stateId 0 - no transformation yet; 1 - Vector data were transformed; 2 - Transformation was reset
    def setTransformationState2Project(self, stateId):

        projectSettings = QgsProject.instance()
        # stateId 0 - Es wurde bisher keine Transformation ausgeführt.
        if stateId == 0:
            projectSettings.writeEntry("transformation_state_id", "int", stateId)
            projectSettings.writeEntry(
                "transformation_state_long", "text", str("Es wurde bisher keine Transformation ausgeführt.")
            )
        # stateId 1 - Vektordaten wurden transformiert.
        if stateId == 1:
            projectSettings.writeEntry("transformation_state_id", "int", stateId)
            projectSettings.writeEntry("transformation_state_long", "text", str("Vektordaten wurden transformiert."))
        # stateId 2 - Transformation wurde zurückgesetzt.
        if stateId == 2:
            projectSettings.writeEntry("transformation_state_id", "int", stateId)
            projectSettings.writeEntry("transformation_state_long", "text", str("Transformation wurde zurückgesetzt."))

        self.saveProject()

    ## \brief Set transformation parameters to attributes
    #
    # calls setTransformationParametersGUI() to set transformationsparameter in GUI elements
    #
    # \param translationX Translation in x direction
    # \param translationY Translation in y direction
    # \param translationZ Translation in z direction
    # \param zAngle Rotation around z axis
    # \param targetCrs Coordinate system
    # \param sourceCrs Coordinate system

    def setTransformationParameters(self, translationX, translationY, translationZ, zAngle, targetCrs):

        self.transformationParametersDone = True
        self.zAngle = zAngle
        self.translationX = translationX
        self.translationY = translationY
        self.translationZ = translationZ
        self.targetCrs = targetCrs.authid()

        self.setTransformationParameters2Project()

        self.setTransformationParametersGUI(translationX, translationY, translationZ, zAngle)

    ## \brief Set transformationsparameter in GUI elements
    #
    # \param translationX Translation in x direction
    # \param translationY Translation in y direction
    # \param translationZ Translation in z direction
    # \param zAngle Rotation around z axis

    def setTransformationParametersGUI(self, translationX, translationY, translationZ, zAngle):

        self.dockwidget.xTranslationText.setText(str(round(translationX, 3)))
        self.dockwidget.yTranslationText.setText(str(round(translationY, 3)))
        self.dockwidget.zTranslationText.setText(str(round(translationZ, 3)))
        self.dockwidget.rotationText.setText(str(round(zAngle, 3)))

    ## \brief Get transformationsparameter from project file
    #
    # Write theese parameters to attributes
    #
    def getTransformationParametersFromProject(self):

        projectSettings = QgsProject.instance()
        self.zAngle = projectSettings.readDoubleEntry("transformation_z_angle", "float", float("NAN"))[0]
        self.translationX = projectSettings.readDoubleEntry("transformation_x_translation", "float", float("NAN"))[0]
        self.translationY = projectSettings.readDoubleEntry("transformation_y_translation", "float", float("NAN"))[0]
        self.translationZ = projectSettings.readDoubleEntry("transformation_z_translation", "float", float("NAN"))[0]
        self.targetCrs = projectSettings.readEntry("transformation_target_crs", "text", None)[0]
        self.sourceCrs = projectSettings.readEntry("transformation_source_crs", "text", None)[0]

    ## \brief Set transformationsparameter to project file
    #

    def setTransformationParameters2Project(self):

        projectSettings = QgsProject.instance()
        projectSettings.writeEntryDouble("transformation_z_angle", "float", self.zAngle)
        projectSettings.writeEntryDouble("transformation_x_translation", "float", self.translationX)
        projectSettings.writeEntryDouble("transformation_y_translation", "float", self.translationY)
        projectSettings.writeEntryDouble("transformation_z_translation", "float", self.translationZ)
        projectSettings.writeEntry("transformation_target_crs", "text", self.targetCrs)
        projectSettings.writeEntry("transformation_source_crs", "text", self.sourceCrs)

    """
    ## \brief Enable transformation of the current project
    # \brief It enables or disables elements in the dockWidget
    # \brief currently not used, maybe to restrictive. If some errors occurs there could be a disabled and not usable GUI
    # \param state could be True or False

    def enableTransformation(self, state):

        if state == True:
            self.dockwidget.calcParametersGroupBox.setEnabled(True)
            self.dockwidget.layerTransformGroupBox.setEnabled(True)
            self.dockwidget.transformResetBtn.setEnabled(False)

        else:
            self.dockwidget.calcParametersGroupBox.setEnabled(False)
            self.dockwidget.layerTransformGroupBox.setEnabled(False)
            self.dockwidget.transformResetBtn.setEnabled(True)

    """

    ## \brief Open Transformationdialog
    # - previously reads out a copy of the inputlayers (Eingabelayer) of the current project (getInputlayers())
    # - and the point layer (sourceLayer) that holds the local measured GCP data (getLocalGCPs())
    # - and the target coordinate system
    # - and a textfile with the reference point information (getTargetCoordinates())
    # - and validate this file (validateGCPFile())
    # - starts validation of the sourceLayer (validateSourceLayer())
    # - finally opens transformation dialog (TransformationDialog.showTransformationDialog())

    def transformationDialogShow(self):

        inputLayers = self.getInputlayers(True)
        sourceLayer = self.dockwidget.comboEingabelayerTransform.currentLayer().clone()

        isValidSourceLayer = self.validateSourceLayer(sourceLayer)

        self.sourceCrs = sourceLayer.crs().authid()
        self.targetCrs = self.dockwidget.projectionSelectionTransform.crs().authid()
        targetGCPFile = self.dockwidget.fileWidgetTargetCoordinates.filePath()

        isValidGCPFile = self.validateGCPFile(targetGCPFile)
        if isValidGCPFile == True and isValidSourceLayer == True:
            gcpSource = self.getLocalGCPs(sourceLayer)
            success, targetGCP = self.getTargetCoordinates(targetGCPFile)
            if success == True:
                self.transformationDialog.showTransformationDialog(
                    sourceLayer, inputLayers, QgsCoordinateReferenceSystem(self.targetCrs), gcpSource, targetGCP
                )
        else:
            print("Validation", False)

    ## \brief Open messagebox before reverse calculation of the transformation starts
    #

    def resetTransformationMessageBox(self):
        self.transformMsgBox = QMessageBox()
        self.transformMsgBox.setIcon(QMessageBox.Warning)
        self.transformMsgBox.setWindowTitle("Transformation zurücksetzen")
        self.transformMsgBox.setText(
            "Es werden alle Eingabelayer mit ihrem aktuellen Inhalt entsprechend der Transformationsparameter zurücktransformiert."
        )
        self.transformMsgBox.setStandardButtons((QMessageBox.Ok | QMessageBox.Cancel))
        self.transformMsgBox.buttonClicked.connect(self.resetTransformation)
        self.transformMsgBox.exec_()

    ## \brief Open messagebox with respect to the validation of the Eingabelayer (inputlayers)
    #
    # \param validationText
    # \param detailedText

    def validityMessageBox(self, validationText, detailedText):

        self.validityMsgBox = QMessageBox()
        self.validityMsgBox.setText(validationText)

        self.validityMsgBox.setDetailedText(detailedText)
        # self.validityMsgBox.setWidget(scroll)
        # self.validityMsgBox.setStyleSheet("QScrollArea{min-width:300 px; min-height: 400px}")
        self.validityMsgBox.setIcon(QMessageBox.Warning)
        self.validityMsgBox.setWindowTitle("Gültigkeitsprüfung der Eingabelayer")
        self.validityMsgBox.setStandardButtons((QMessageBox.Cancel))
        self.validityMsgBox.exec_()

    ## \brief Opens a message box with background informations
    #

    def openInfoMessageBox(self):

        infoText = "Bei der hier durchgeführten Vektordatentransformation von einem lokalen in ein übergeordnetes Koordinatensystem, erfolgt keine Verformung der Features. Die Daten verbleiben winkel-, strecken- und flächentreu (keine Skalierung oder Verzerrung!). Es handelt sich genaugenommen also nicht um eine „echte“ geodätische Transformation, vielmehr wird die Messung in das übergeordnete System „eingehangen“. Dies erfolgt auf Basis von Passpunkt-Paaren im Quell- und Zielsystem (homologe Punkte) als Kombination von: \n \n 1. 2D Translation und Rotation in der XY-Ebene (Rigide 2D-Transformation oder Euklidische Transformation ohne Skalierung) mit Fehlerausgleich (Least Squares) \n \n 2. 1D Translation in Z-Richtung (Verschiebung um Mittelwert der dZ / Ausgleichung über Least Squares). Ziel der Anpassung der Höhenwerte ist es die gemessenen Höhenzusammenhänge nicht zu verändern. Die gemessenen Features der Layer sollen lediglich über einen Translationswert in der Höhe verändert werden können. \n \nEs erfolgt explizit keine 3D-Transformation, da dies evtl. eine Kippung der Daten zur Folge hätte!"
        self.infoTranssformMsgBox = QMessageBox()
        self.infoTranssformMsgBox.setText(infoText)

        # self.validityMsgBox.setWidget(scroll)
        # self.validityMsgBox.setStyleSheet("QScrollArea{min-width:300 px; min-height: 400px}")
        self.infoTranssformMsgBox.setWindowTitle("Hintergrundinformationen")
        self.infoTranssformMsgBox.setStandardButtons((QMessageBox.Ok))
        self.infoTranssformMsgBox.exec_()

    ## \brief Check the validity of the inputlayers and open validity message box
    #
    # calls checkInputlayersValidity()
    #
    # after validation it opens validityMessageBox()

    def openValidityMessageBox(self):

        generalValid, validationText, detailedText = self.checkInputlayersValidity()

        self.validityMessageBox(validationText, detailedText)

    ## \brief Check the validity of the inputlayers
    #
    # Uses QgsGeometry --> validateGeometry()
    #
    # after validation it opens validityMessageBox()

    def checkInputlayersValidity(self):
        generalValid = True
        inputLayers = self.getInputlayers(True)

        validationText = "Ungültige Geometrien können zu Transformationsfehlern führen! Bitte bereinigen Sie die Geometrien im Vorfeld einer Transformation! \n\n"
        detailedText = ""
        for layer in inputLayers:

            detailedText += "\n" + layer.name() + "\n----------------------\n"

            validationFeatureText = ""

            for i, feat in enumerate(layer.getFeatures()):

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

        return generalValid, validationText, detailedText

    ## \brief After resetBtn was clicked this function is executed
    # starts the reverse transformation (startReverseTransformation())

    def resetTransformation(self, btn):

        if btn.text() == "OK":
            self.startReverseTransformation()
            # self.enableTransformation(True)

    ## \brief check valid sourcelayer
    # prueft auf Spalten Anzahl (4)
    # prueft auf Spaltennamen NUMMER, Position X, Position Y, Position Z
    # prueft auf Zeilenanzahl Anzahl (> 1)
    # \param filePath
    # @returns true / false

    def validateSourceLayer(self, sourceLayer):

        isValid = False

        # is vector layer
        if isinstance(sourceLayer, QgsVectorLayer):
            isValid = True

            # is 3d Point layer
            # feature.attribute('obj_typ') == 'Georeferenzierung':
            layerType = sourceLayer.wkbType()
            # 1001 PointZ, 3001 PointZM, 1004 MultiPointZ, 3004 MultipointZM
            if (
                layerType == QgsWkbTypes.PointZ
                or layerType == QgsWkbTypes.PointZM
                or layerType == QgsWkbTypes.MultiPointZ
                or layerType == QgsWkbTypes.MultiPointZM
            ):
                isValid = True

                # Check that column obj_type is in attributtable
                field_index = sourceLayer.fields().indexFromName("obj_typ")

                if field_index == -1:
                    self.iface.messageBar().pushMessage(
                        "Error", "Im Eingabelayer fehlt die Spalte 'obj_typ'", level=1, duration=5
                    )
                    isValid = False
                else:
                    isValid = True

                    counterGeoref = 0
                    for feature in sourceLayer.getFeatures():
                        # Alt war Georeferenzierung

                        if feature.attribute("obj_typ") == self.colNameGcpSource:
                            counterGeoref += 1

                    if counterGeoref < 2:
                        isValid = False
                        self.iface.messageBar().pushMessage(
                            "Error",
                            "Min. zwei Einträge 'Festpunkt' in Spalte 'obj_typ' sind notwendig",
                            level=1,
                            duration=5,
                        )
                    else:
                        isValid = True

            else:
                isValid = False
                self.iface.messageBar().pushMessage(
                    "Error", "Sourcelayer muss PointZ, PointZM, MultiPointZ oder MultipointZM sein", level=1, duration=5
                )

        else:
            isValid = False
            self.iface.messageBar().pushMessage("Error", "Sourcelayer ist kein Vektorlayer", level=1, duration=5)

        return isValid

    ## \brief Check Valid GCP File
    # - checks for number of columns (4)
    # - checks for number of rows (> 1)
    #
    # \param filePath
    # @returns true / false

    def validateGCPFile(self, filePath):

        isValid = False
        checkCountRows = 2
        checkCountColumns = 4

        if os.path.isfile(filePath) == True:
            isValid = True

            with open(filePath, newline="") as csvfile:
                reader = csv.DictReader(csvfile, delimiter="\t")

                # check Anzahl Zeilen > 1
                if len(list(reader)) >= checkCountRows:
                    isValid = True

                    # check Anzahl Spalten == 4
                    for row in reader:
                        if len(row) == checkCountColumns:
                            isValid = True
                        else:
                            isValid = False
                            self.iface.messageBar().pushMessage(
                                "Error",
                                "GCP Datei ist ungültig: Anzahl Spalten ungleich " + str(checkCountColumns),
                                level=1,
                                duration=5,
                            )

                else:
                    isValid = False
                    self.iface.messageBar().pushMessage(
                        "Error",
                        "GCP Datei ist ungültig: min. " + str(checkCountRows) + " Zeilen notwendig",
                        level=1,
                        duration=5,
                    )

        else:

            isValid = False
            self.iface.messageBar().pushMessage("Error", "Keine GCP Datei ausgewählt!", level=1, duration=5)

        return isValid

    ## \brief Extract measured georeferencing points from pointlayer
    #
    # \param sourceLayer
    # @returns dictionary of the source GCPs e.G.:
    #  \code{.py}
    #    [{
    #    	'uuid': '{c81ce552-9466-417a-a1fd-2305f81c3051}',
    #    	'fid': 0,
    #    	'pt_nr': 'ALT_01',
    #    	'geometry': < QgsGeometry: PointZ(451.15690000000000737 956.48540000000002692 102.51779999999999404) > ,
    #    	'x': 451.1569,
    #    	'y': 956.4854,
    #    	'z': 102.5178
    #    }, {
    #    	'uuid': '{0689dab2-f5fa-4db7-a3ff-6c5e343054d9}',
    #    	'fid': 1,
    #    	'pt_nr': 'ALT_12',
    #    	'geometry': < QgsGeometry: PointZ(483.94339999999999691 1002.8064000000000533 102.33379999999999654) > ,
    #    	'x': 483.9434,
    #    	'y': 1002.8064,
    #    	'z': 102.3338
    #    }, {
    #    	'uuid': '{23934b9c-9ddc-4098-8d61-352c818e32db}',
    #    	'fid': 2,
    #    	'pt_nr': 'ALT_03',
    #    	'geometry': < QgsGeometry: PointZ(526.23810000000003129 979.89469999999994343 102.5023000000000053) > ,
    #    	'x': 526.2381,
    #    	'y': 979.8947,
    #    	'z': 102.5023
    #    }]
    #  \endcode

    def getLocalGCPs(self, sourceLayer):

        gcpSource = []

        for feature in sourceLayer.getFeatures():
            if feature.attribute("obj_typ") == self.colNameGcpSource:
                point = feature.geometry().constGet()
                geomType = point.wkbType()
                # 1001 PointZ, 3001 PointZM, -2147483647 Point2.5D
                if (
                    geomType == QgsWkbTypes.PointZ
                    or geomType == QgsWkbTypes.PointZM
                    or geomType == QgsWkbTypes.Point25D
                ):
                    try:
                        zVal = point.z()
                    except:
                        zVal = 0
                    gcpSource.append(
                        {
                            "uuid": feature.attribute("uuid"),
                            "fid": feature.attribute("fid"),
                            "pt_nr": feature.attribute("pt_nr"),
                            "geometry": feature.geometry(),
                            "x": point.x(),
                            "y": point.y(),
                            "z": zVal,
                        }
                    )
                else:
                    # 1004 MultiPointZ, 3004 MultipointZM
                    # Workaround um aus Multipointdaten GCP-Punktinfos zu bekommen
                    # Geometrie darf keine wirkliche Multigeometrie sein (mehrere Punkte in einem Feature)
                    childPoint = point.childGeometry(0)

                    try:
                        zVal = childPoint.z()
                    except:
                        zVal = 0
                    gcpSource.append(
                        {
                            "uuid": feature.attribute("uuid"),
                            "fid": feature.attribute("fid"),
                            "pt_nr": feature.attribute("pt_nr"),
                            "geometry": feature.geometry(),
                            "x": childPoint.x(),
                            "y": childPoint.y(),
                            "z": zVal,
                        }
                    )

        return gcpSource

    ## \brief Read out target coordinates
    #
    # \param filePath
    # @returns success could be True or False (Error in read out the data)
    # @returns dictionary of the target GCPs e.G.:
    #  \code{.py}
    #    {
    #    	'points': [{
    #    		'pt_nr': 'ALT_01',
    #    		'x': 5460004.380048368,
    #    		'y': 5700036.800403067,
    #    		'z': 50.0
    #    	}, {
    #    		'pt_nr': 'ALT_12',
    #    		'x': 5460046.428512702,
    #    		'y': 5700901.997960591,
    #    		'z': 80.0
    #    	}]
    #    }
    #  \endcode

    def getTargetCoordinates(self, filePath):
        targetGCP = {}
        targetGCP["points"] = []

        try:
            with open(filePath, newline="") as csvfile:
                reader = csv.reader(csvfile, delimiter="\t")
                for row in reader:
                    if row:
                        # 0-NUMMER	1-Position X	2-Position Y	3-Position Z
                        pointObj = {"pt_nr": row[0], "x": float(row[1]), "y": float(row[2]), "z": float(row[3])}
                        targetGCP["points"].append(pointObj)
                    else:
                        print("Leerzeile")
            return True, targetGCP
        except:
            self.iface.messageBar().pushMessage("GCP-File", "Datei kann nicht eingelesen werden!", level=1, duration=5)

            return False, targetGCP

    ## \brief Backup of the folders Shape and Projekt to the folder Backup Transformation
    #
    # Just before the transformation takes place, the data is backuped

    def backupBeforeTransformation(self):

        # Backuppfad finden und gfl. erzeugen
        projectPath = QgsProject.instance().readPath("../")
        sourceProjectPath = projectPath + "/Projekt/"
        sourceShapePath = projectPath + "/Shape/"
        folderName = str(time.strftime("%Y-%m-%d_%H-%M-%S"))
        backupPath = projectPath + "/Backup Transformation/backup_" + folderName + "/"
        targetShapePath = backupPath + "Shape/"
        targetProjectPath = backupPath + "Projekt/"

        shutil.copytree(sourceShapePath, targetShapePath)
        shutil.copytree(sourceProjectPath, targetProjectPath)

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

    ## \brief Starts the process of the transformation of the inputLayers
    #
    # - check if transformation paramters are available
    # - check validity of the inputlayers checkInputlayersValidity()
    # - Backup of the folders Shape and Projekt to the folder Backup Transformation backupBeforeTransformation()
    # - set target CRS to the layer
    # - create spatial index for the layer TransformationCalculations.createLayerSpatialIndex()
    # - do the rotation of the layer TransformationCalculations.layerRotation()
    # - calculate translation in z direction TransformationCalculations.layerTranslationZ()
    # - calculate translation in xy direction TransformationCalculations.layerTranslationXY
    # - recalculate the extent of the layer TransformationCalculations.recalculateLayerExtent()
    # - do some GUI updates
    # - save the current project saveProject()

    def startTransformation(self):

        if self.transformationParametersDone == True:

            # generalValid = True
            generalValid, validationText, detailedText = self.checkInputlayersValidity()

            if generalValid == True:

                # Workaround - unklar warum die Parameter aus Projekt aufgerufen werden muessen um das die XYZ Transformation (Z wird sonst nicht richtig gesetzt) richtig funktioniert???
                # Eigentlich muss der Aufruf hier nicht stehen
                self.getTransformationParametersFromProject()

                inputLayers = self.getInputlayers(False)
                self.backupBeforeTransformation()

                for layer in inputLayers:

                    print("layer_name: ", layer.name())

                    layer.removeSelection()

                    layer.setCrs(QgsCoordinateReferenceSystem(self.targetCrs))

                    self.paramCalc.createLayerSpatialIndex(layer)

                    layerType = layer.wkbType()

                    print("layerType: ", layerType)
                    # Abfrage nach Z und ZM Single Layertypen - layerTranslationXYZ gibt dort keinen korrekten Z Wert aus
                    # 3002 LineStringZM , 3001 PointZM, 3003 PolygonZM
                    if (
                        layerType == QgsWkbTypes.PointZM
                        or layerType == QgsWkbTypes.LineStringZM
                        or layerType == QgsWkbTypes.PolygonZM
                    ):

                        print("Translation XY")

                        # Rotation
                        self.paramCalc.layerRotation(layer, "forward", self.zAngle)

                        # Z-Translation - unbedingt zuerst ausführen sonst Fehler bei Extentberechnung
                        self.paramCalc.layerTranslationZ(layer, "forward", self.translationZ)

                        # Translation in X und Y
                        self.paramCalc.layerTranslationXY(layer, "forward", self.translationX, self.translationY)
                    else:
                        print("Translation XYZ")
                        # Rotation
                        self.paramCalc.layerRotation(layer, "forward", self.zAngle)
                        # Translation in X, Y und Z
                        self.paramCalc.layerTranslationXYZ(
                            layer, "forward", self.translationX, self.translationY, self.translationZ
                        )

                    # Recalculate Extent
                    self.paramCalc.recalculateLayerExtent(layer)

                    self.paramCalc.createLayerSpatialIndex(layer)

                    layer.removeSelection()

                    print("Finish Transform of Layer " + layer.name() + " !")

                self.setTransformationState2Project(1)

                self.setTransformationParameters2Project()

                transformationStateId, transformationStatelong = self.getTransformationStateFromProject()

                self.setTransformationStateGUI(transformationStateId, transformationStatelong)

                # self.enableTransformation(False)

                self.iface.mapCanvas().refresh()

                self.saveProject()

            else:

                self.validityMessageBox(validationText, detailedText)

        else:
            self.iface.messageBar().pushMessage(
                "Tranformationsparameter", "Berechnen Sie zuerst die Transformationsparameter!", level=1, duration=5
            )

    ## \brief Starts the reverse process of the transformation of inputLayers
    #
    # - check if transformation paramters are available
    # - check validity of the inputlayers checkInputlayersValidity()
    # - set target CRS to the layer
    # - create spatial index for the layer TransformationCalculations.createLayerSpatialIndex()
    # - calculate translation in z direction TransformationCalculations.layerTranslationZ()
    # - calculate translation in xy direction TransformationCalculations.layerTranslationXY
    # - do the rotation of the layer TransformationCalculations.layerRotation()
    # - recalculate the extent of the layer TransformationCalculations.recalculateLayerExtent()
    # - do some GUI updates

    def startReverseTransformation(self):

        if self.transformationParametersDone == True:

            # generalValid = True
            generalValid, validationText, detailedText = self.checkInputlayersValidity()

            if generalValid == True:

                # Workaround - unklar warum die Parameter aus Projekt aufgerufen werden muessen um das die XYZ Transformation (Z wird sonst nicht richtig gesetzt) richtig funktioniert???
                # Eigentlich muss der Aufruf hier nicht stehen
                self.getTransformationParametersFromProject()

                inputLayers = self.getInputlayers(False)

                for layer in inputLayers:

                    print("layer_name", layer.name())

                    layer.removeSelection()

                    layer.setCrs(QgsCoordinateReferenceSystem(self.sourceCrs))

                    self.paramCalc.createLayerSpatialIndex(layer)

                    layerType = layer.wkbType()

                    print("layerType", layerType)

                    # Abfrage nach Z und ZM Single Layertypen - layerTranslationXYZ gibt dort keinen korrekten Z Wert aus
                    if (
                        layerType == QgsWkbTypes.PointZM
                        or layerType == QgsWkbTypes.LineStringZM
                        or layerType == QgsWkbTypes.PolygonZM
                    ):  # Z-Translation - unbedingt zuerst ausführen sonst Fehler bei Extentberechnung
                        self.paramCalc.layerTranslationZ(layer, "reverse", self.translationZ)

                        # Translation in X und Y
                        self.paramCalc.layerTranslationXY(layer, "reverse", self.translationX, self.translationY)

                        # Rotation
                        self.paramCalc.layerRotation(layer, "reverse", self.zAngle)

                    else:
                        # Translation in X, Y und Z
                        self.paramCalc.layerTranslationXYZ(
                            layer, "reverse", self.translationX, self.translationY, self.translationZ
                        )

                        # Rotation
                        self.paramCalc.layerRotation(layer, "reverse", self.zAngle)

                    # Recalculate Extent
                    self.paramCalc.recalculateLayerExtent(layer)

                    self.paramCalc.createLayerSpatialIndex(layer)

                    layer.removeSelection()

                    print("Finish Reversetransform of Layer " + layer.name() + " !")

                self.setTransformationState2Project(2)

                self.setTransformationParameters2Project()

                transformationStateId, transformationStatelong = self.getTransformationStateFromProject()

                self.setTransformationStateGUI(transformationStateId, transformationStatelong)

                self.setTransformationParametersGUI(
                    self.translationX, self.translationY, self.translationZ, self.zAngle
                )

                # self.enableTransformation(True)

                self.iface.mapCanvas().refresh()

            else:
                self.validityMessageBox(validationText, detailedText)

        else:
            self.iface.messageBar().pushMessage(
                "Tranformationsparameter",
                "Zurücksetzen der Transformation nicht möglich - keine Transformationsparameter vorhanden!",
                level=1,
                duration=5,
            )
