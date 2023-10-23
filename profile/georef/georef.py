## @package QGIS geoEdit extension..
import math
import pathlib
from functools import partial

from qgis.PyQt.QtWidgets import QMessageBox, QComboBox, QLabel
from qgis.PyQt.QtCore import Qt, pyqtSlot, QObject
from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsLayerTreeGroup,
    QgsLayerTreeLayer,
    QgsWkbTypes,
)
from qgis.gui import QgsFileWidget

from .georeferencing_dialog import GeoreferencingDialog


## @brief The class is used to implement functionalities for work with profiles
# within the dock widget of the Tachy2GIS_arch plugin
#
# @author Mario Uhlig, VisDat geodatentechnologie GmbH, mario.uhlig@visdat.de
# @date 2021-05-07
class Georef:
    ## The constructor.
    #  Defines attributes for the Profile
    #
    #  @param dockWidget pointer to the dockwidget
    #  @param iFace pointer to the iface class
    def __init__(self, t2gArchInstance, iFace, rotationCoords):
        self.dockwidget = t2gArchInstance.dockwidget
        self.iface = iFace

        self.rotationCoords = rotationCoords

        self.ref_data_pair = []
        self.geo_referencing_dialogues_list = []
        self.draw_polygon_window_list = []
        self.polygon_list = []

    ## @brief Initializes the functionality for profile modul
    #
    def setup(self):
        # Preselection of Inputlayers (only Layer below "Eingabelayer" are available)
        preselectedLineLayer = self.preselectionProfileLayer()
        # Tooltip
        self.dockwidget.profileTargetName.setToolTip(
            "Die Ergebnisdateien werden in Unterverzeichnissen vom Profilfoto abgelegt, "
            "die Dateinamen beginnen so wie hier angegeben."
        )
        # Preselection profilenumber
        if isinstance(preselectedLineLayer, QgsVectorLayer):
            self.preselectProfileNumbers(preselectedLineLayer)
            # Preselection of Inputlayers (only Layer below "Eingabelayer" are available)
            self.preselectionGcpLayer()
            # set datatype filter to profileFotosComboGeoref
            self.dockwidget.profileFotosComboGeoref.setFilter("Images (*.png *.JPG *.jpg *.jpeg *.tif)")
            self.dockwidget.profileFotosComboGeoref.fileChanged.connect(self.changedProfileImage)
            # Preselection View direction
            self.preselectViewDirection()

            self.dockwidget.startGeoreferencingBtn.clicked.connect(self.startGeoreferencingBtn_clicked)

            self.dockwidget.layerGcpGeoref.currentIndexChanged.connect(self.calculateViewDirection)
            self.dockwidget.layerProfileGeoref.currentIndexChanged.connect(self.calculateViewDirection)
            self.dockwidget.profileIdsComboGeoref.currentIndexChanged.connect(self.calculateViewDirection)

            profil_start_idx = self.dockwidget.profileIdsComboGeoref.currentIndex()

            # Connection to info messagebox
            self.dockwidget.profileInfoBtn.clicked.connect(self.openInfoMessageBox)

            # Calculate initial profile view
            self.calculateViewDirection(profil_start_idx)

            # Initial hide Kreuzprofilselection
            # self.__showKreuzprofilSelection(False)

            self.dockwidget.checkboxKreuzprofil.stateChanged.connect(self.handleKreuzprofil)

        else:
            print("preselectedLineLayer is kein QgsVectorLayer")

    def startGeoreferencingBtn_clicked(self):
        # reset old dialogues, windows and ref data:
        self.geo_referencing_dialogues_list = []
        self.draw_polygon_window_list = []
        self.polygon_list = []
        self.ref_data_pair = []
        self.ref_data_pair.append(self.getSelectedValues())

        if not (
            self.dockwidget.check_transform_original.isChecked()
            or self.dockwidget.check_transform_horizontal.isChecked()
            or self.dockwidget.check_transform_absolut.isChecked()
        ):
            QMessageBox.critical(
                self.dockwidget,
                "Invalide Einstellung",
                "Mindestens eine Transformationsmethode muss ausgewählt sein!",
                QMessageBox.Abort,
            )
            return

        transform_methods = []
        if self.dockwidget.check_transform_original.isChecked():
            transform_methods.append("original")
        if self.dockwidget.check_transform_horizontal.isChecked():
            transform_methods.append("horizontal")
        if self.dockwidget.check_transform_absolut.isChecked():
            transform_methods.append("absolute height")

        self.ref_data_pair[0]["transform_methods"] = transform_methods

        # case no kreuzprofil:
        if not self.dockwidget.checkboxKreuzprofil.isChecked():
            self.startGeoreferencingDialog(self.ref_data_pair[0])
            return

        # case kreuzprofil:
        if (
            self.dockwidget.profileIdsComboGeoref.currentIndex()
            == self.dockwidget.profileIdsComboGeoref_2.currentIndex()
        ):
            QMessageBox.critical(
                self.dockwidget,
                "Invalide Einstellung",
                "Die eingestellten Profilnummern müssen verschieden sein!",
                QMessageBox.Abort,
            )
            return

        self.ref_data_pair.append(self.getSelectedValues(second_set=True))
        self.ref_data_pair[1]["transform_methods"] = transform_methods

        view_direction_set = {self.ref_data_pair[0]["viewDirection"], self.ref_data_pair[1]["viewDirection"]}
        if view_direction_set != {"S", "N"} and view_direction_set != {"E", "W"}:
            QMessageBox.critical(
                self.dockwidget,
                "Invalide Einstellung",
                "Die eingestellten Profile müssen in entgegengesetzten Blickrichtungen aufgenommen worden sein!",
                QMessageBox.Abort,
            )
            return
        self.startGeoreferencingDialog(self.ref_data_pair[0], True)
        self.startGeoreferencingDialog(self.ref_data_pair[1], True)

    ## \brief Start georeferencing dialog
    #
    #
    def startGeoreferencingDialog(self, refData, set_for_kreuzprofil=False):
        georeferencingDialog = GeoreferencingDialog(self, self.rotationCoords, self.iface)
        if set_for_kreuzprofil:
            georeferencingDialog.set_for_kreuzprofil(self.ref_data_pair)
            georeferencingDialog.destroyed.connect(partial(self.on_dialog_closed, self))
        georeferencingDialog.showGeoreferencingDialog(refData)
        self.geo_referencing_dialogues_list.append(georeferencingDialog)

    @pyqtSlot(QObject)
    def on_dialog_closed(self, _):
        successful = 0
        for dialog in self.geo_referencing_dialogues_list:
            ready = [
                dialog.refData.get(f"geo_ref_done_{aarDirection}", False)
                for aarDirection in dialog.refData["transform_methods"]
            ]
            if all(ready):
                successful += 1

        # if one window was closed but no successful:
        if successful == 0:
            for dialog in self.geo_referencing_dialogues_list:
                # detect if it was closed already:
                if dialog.ref_data_pair:
                    dialog.destroyDialog()
            self.geo_referencing_dialogues_list = []
            self.draw_polygon_window_list = []
            self.ref_data_pair = []
            self.polygon_list = []

    ## \brief SaveComboBox is clicked
    #
    # suggest profileTargetName
    def changedProfileImage(self):
        imageFilePath = self.dockwidget.profileFotosComboGeoref.filePath()
        shortFileName = pathlib.Path(imageFilePath).stem
        second_profile_name = ""
        if self.dockwidget.checkboxKreuzprofil.isChecked():
            second_profile_name = "_" + self.dockwidget.profileIdsComboGeoref_2.currentText()
        suggestTargetName = shortFileName + f"{second_profile_name}_entz"
        self.dockwidget.profileTargetName.setText(suggestTargetName)

    ## \brief Handler Checkbox Kreuzprofile is clicked
    #
    #
    def handleKreuzprofil(self, state):
        if state == Qt.Checked:
            self.show_kreuzprofil_selection(True)
        else:
            self.show_kreuzprofil_selection(False)

    ## \brief Show or hide Selection of Kreuzprofile
    # siehe https://stackoverflow.com/questions/70859955/some-blank-space-remains-in-qvboxlayout-after-hiding-widgets-qt
    # @param vis
    def show_kreuzprofil_selection(self, vis):
        if not vis:
            self.dockwidget.layerGcpGeoref.currentIndexChanged.disconnect(self.calculateViewDirection2)
            self.dockwidget.layerProfileGeoref.currentIndexChanged.disconnect(self.calculateViewDirection2)
            self.dockwidget.profileIdsComboGeoref_2.currentIndexChanged.disconnect(self.calculateViewDirection2)
            self.dockwidget.profileIdsComboGeoref_2.currentIndexChanged.disconnect(self.changedProfileImage)
            self.changedProfileImage()

            self.dockwidget.kreuzLabelProfilnummer.deleteLater()
            self.dockwidget.kreuzLabelProfilfoto.deleteLater()
            self.dockwidget.kreuzLabelRichtung.deleteLater()
            self.dockwidget.profileIdsComboGeoref_2.deleteLater()
            self.dockwidget.profileFotosComboGeoref_2.deleteLater()
            self.dockwidget.profileViewDirectionComboGeoref_2.deleteLater()
        else:
            self.dockwidget.layerGcpGeoref.currentIndexChanged.connect(self.calculateViewDirection2)
            self.dockwidget.layerProfileGeoref.currentIndexChanged.connect(self.calculateViewDirection2)

            self.dockwidget.kreuzLabelRichtung = QLabel("2. Blickrichtung auf das Profil")
            self.dockwidget.profileViewDirectionComboGeoref_2 = QComboBox()
            self.dockwidget.profileViewDirectionComboGeoref_2.addItems(
                [
                    self.dockwidget.profileViewDirectionComboGeoref.itemText(i)
                    for i in range(self.dockwidget.profileViewDirectionComboGeoref.count())
                ]
            )

            self.dockwidget.kreuzLabelProfilnummer = QLabel("2. Profilnummer")
            self.dockwidget.profileIdsComboGeoref_2 = QComboBox()
            self.dockwidget.profileIdsComboGeoref_2.currentIndexChanged.connect(self.calculateViewDirection2)
            self.dockwidget.profileIdsComboGeoref_2.currentIndexChanged.connect(self.changedProfileImage)
            self.dockwidget.profileIdsComboGeoref_2.addItems(
                [
                    self.dockwidget.profileIdsComboGeoref.itemText(i)
                    for i in range(self.dockwidget.profileIdsComboGeoref.count())
                ]
            )

            self.dockwidget.kreuzLabelProfilfoto = QLabel("2. Profilfoto")
            self.dockwidget.profileFotosComboGeoref_2 = QgsFileWidget()
            self.dockwidget.profileFotosComboGeoref_2.setFilter(self.dockwidget.profileFotosComboGeoref.filter())

            row, col = self.dockwidget.profileGeoreferencing.layout().getWidgetPosition(
                self.dockwidget.checkboxKreuzprofil
            )
            self.dockwidget.profileGeoreferencing.layout().insertRow(
                row + 1,
                self.dockwidget.kreuzLabelProfilnummer,
                self.dockwidget.profileIdsComboGeoref_2,
            )
            self.dockwidget.profileGeoreferencing.layout().insertRow(
                row + 2,
                self.dockwidget.kreuzLabelProfilfoto,
                self.dockwidget.profileFotosComboGeoref_2,
            )
            self.dockwidget.profileGeoreferencing.layout().insertRow(
                row + 3,
                self.dockwidget.kreuzLabelRichtung,
                self.dockwidget.profileViewDirectionComboGeoref_2,
            )

    ## \brief get selected values
    #
    # refData
    # {
    #    'lineLayer': < QgsVectorLayer: 'E_Line'(ogr) > ,
    #    'pointLayer': < QgsVectorLayer: 'E_Point'(ogr) > ,
    #    'crs': < QgsCoordinateReferenceSystem: EPSG: 31468 > ,
    #    'profileNumber': '131',
    #    'imagePath': 'path\\to\\AZB-16_Pr_132.jpg',
    #    'viewDirection': 'E',
    #    'horizontal': True,
    #    'profileTargetName': 'AZB-16_Pr_132_entz',
    #    'savePath': 'path\\to\\Profil_132',
    #    'profileDirs': {
    #        'dirPa': 'path\\to\\pa',
    #        'dirPo': 'path\\to\\po',
    #        'dirPh': 'path\\to\\ph',
    #        'dir3d': 'path\\to\\3d'
    #    },
    #    'saveMetadata': True,
    #    'targetGCP': {
    #        'points': [{
    #            'uuid': '{f9a241b4-1a9b-4695-a493-5262efa1857c}',
    #            'ptnr': '1',
    #            'id': 745,
    #            'x': 4577275.697,
    #            'y': 5710099.149,
    #            'z': 84.729
    #        }, {...}]
    #    }
    # }
    #
    # @return refData

    def getSelectedValues(self, second_set=False):
        lineLayer = self.dockwidget.layerProfileGeoref.currentLayer().clone()

        if second_set:
            profileNumber = self.dockwidget.profileIdsComboGeoref_2.currentText()
        else:
            profileNumber = self.dockwidget.profileIdsComboGeoref.currentText()

        pointLayer = self.dockwidget.layerGcpGeoref.currentLayer().clone()
        pointLayer.setSubsetString(
            "obj_type = 'Fotoentzerrpunkt' and " "obj_art = 'Profil' and " "prof_nr = '" + profileNumber + "'"
        )

        # Zielkoordinaten
        targetGCP = {"points": []}

        validGeomCheck = True
        orgGeomType = ""

        for feature in pointLayer.getFeatures():
            org_geom = feature.geometry()
            orgGeomType = org_geom.wkbType()

            g = self.rotationCoords.castMultipointGeometry(org_geom)

            geoType = g.wkbType()

            if geoType == 1001 or geoType == 3001:
                pointObj = {
                    "uuid": feature.attribute("obj_uuid"),
                    "ptnr": feature.attribute("pt_nr"),
                    "id": feature.attribute("id"),
                    "x": float(g.get().x()),
                    "y": float(g.get().y()),
                    "z": float(g.get().z()),
                }
                targetGCP["points"].append(pointObj)

            else:
                validGeomCheck = False

        if validGeomCheck is False:
            errorMsg = f"Kann Geometrietyp nicht verarbeiten {orgGeomType}"
            self.iface.messageBar().pushMessage("Error", errorMsg, level=1, duration=3)

        if second_set:
            imagePath = self.dockwidget.profileFotosComboGeoref_2.filePath()
            viewDirLong = self.dockwidget.profileViewDirectionComboGeoref_2.currentText()
        else:
            imagePath = self.dockwidget.profileFotosComboGeoref.filePath()
            viewDirLong = self.dockwidget.profileViewDirectionComboGeoref.currentText()

        translate_direction = {
            "Nord": "N",
            "Ost": "E",
            "Süd": "S",
            "West": "W",
        }
        viewDirection = translate_direction[viewDirLong]

        # horizontal true/false
        # horizontalCheck = self.dockwidget.radioDirectionHorizontal.isChecked()

        # profileTargetName
        profileTargetName = self.dockwidget.profileTargetName.text()
        # Speicherpfad
        p_path = pathlib.Path(imagePath)
        savePath = p_path.parent

        profileDirs = {
            "dirPa": str(savePath / "pa"),
            "dirPo": str(savePath / "po"),
            "dirPh": str(savePath / "ph"),
            "dir3d": str(savePath / "3d"),
        }

        # Metadaten
        metadataCheck = True  # self.dockwidget.metaProfileCheckbox.isChecked()

        refData = {
            "lineLayer": lineLayer,
            "pointLayer": pointLayer,
            "crs": pointLayer.crs(),
            "profileNumber": profileNumber,
            "imagePath": imagePath,
            "viewDirection": viewDirection,
            "horizontal": True,
            "profileTargetName": profileTargetName,
            "savePath": str(savePath),
            "profileDirs": profileDirs,
            "saveMetadata": metadataCheck,
            "targetGCP": targetGCP,
        }

        return refData

    ## \brief Blickrichtung bestimmen
    #
    #
    def calculateViewDirection(self, idx):
        if not (isinstance(idx, int) and idx >= 0):
            return

        profile_number = self.dockwidget.profileIdsComboGeoref.currentText()
        view_direction = self.calc_view_direction(profile_number)
        self.dockwidget.profileViewDirectionComboGeoref.setCurrentText(view_direction)

    ## \brief Blickrichtung bestimmen
    #
    #
    def calculateViewDirection2(self, idx):
        if not (isinstance(idx, int) and idx >= 0):
            return

        profile_number = self.dockwidget.profileIdsComboGeoref_2.currentText()
        view_direction = self.calc_view_direction(profile_number)
        self.dockwidget.profileViewDirectionComboGeoref_2.setCurrentText(view_direction)

    def calc_view_direction(self, profile_number):
        """!
        \brief Blickrichtung bestimmen
        """

        # lineLayer
        lineLayer = self.dockwidget.layerProfileGeoref.currentLayer().clone()
        lineLayer.setSubsetString("prof_nr = '" + profile_number + "'")

        if lineLayer.geometryType() != QgsWkbTypes.LineGeometry:
            return

        view = None
        for feat in lineLayer.getFeatures():
            geom = feat.geometry()
            if QgsWkbTypes.isSingleType(geom.wkbType()):
                # Singlepart
                line = geom.asPolyline()
            else:
                # Multipart
                line = geom.asMultiPolyline()[0]

            pointA = line[0]
            pointB = line[-1]

            pointAx = pointA.x()
            pointAy = pointA.y()
            pointBx = pointB.x()
            pointBy = pointB.y()

            dx = pointBx - pointAx
            dy = pointBy - pointAy
            vp = [dx, dy]
            v0 = [-1, 1]

            # Lösung von hier:
            # https://stackoverflow.com/
            # questions/14066933/direct-way-of-computing-clockwise-angle-between-2-vectors/16544330#16544330
            # angepasst auf Berechnung ohne numpy
            dot = v0[0] * vp[0] + v0[1] * vp[1]  # dot product: x1*x2 + y1*y2
            det = v0[0] * vp[1] - vp[0] * v0[1]  # determinant: x1*y2 - y1*x2

            radians = math.atan2(det, dot)
            angle = math.degrees(radians)

            # negative Winkelwerte
            # (3. und 4. Quadrant, Laufrichtung entgegen Uhrzeigersinn)
            # in fortlaufenden Wert (181 bis 360) umrechnen
            if angle < 0:
                angle *= -1
                angle = 180 - angle + 180

            if angle <= 90:
                view = "Nord"
            elif angle <= 180:
                view = "West"
            elif angle <= 270:
                view = "Süd"
            elif angle > 270:
                view = "Ost"
        return view

    ## \brief Preselection of preselectViewDirection
    #
    #
    def preselectViewDirection(self):
        self.dockwidget.profileViewDirectionComboGeoref.addItems(["Nord", "Ost", "Süd", "West"])

    ## \brief Preselection of preselectProfileNumbers
    #
    #  @param lineLayer
    def preselectProfileNumbers(self, lineLayer):
        profileList = self.getProfileNumbers(lineLayer)

        self.dockwidget.profileIdsComboGeoref.addItems(profileList)

    ## \brief Preselection of getProfileNumbers
    #
    #  @param lineLayer
    # @returns list of profile id's
    def getProfileNumbers(self, lineLayer):
        profileList = []
        for feat in lineLayer.getFeatures():
            if feat.attribute('obj_typ') == 'Profil':
                if feat.attribute('prof_nr'):
                    profileList.append(feat.attribute('prof_nr'))

        return sorted(profileList, key=str.lower)

    ## \brief Preselection of Inputlayers
    #
    # If layer E_Point exists then preselect this
    def preselectionGcpLayer(self):
        notInputLayers = self.getNonInputLayers(0)
        inputLayers = self.getInputlayers(False)

        self.dockwidget.layerGcpGeoref.setExceptedLayerList(notInputLayers)

        for layer in inputLayers:
            if layer.name() == "E_Point":
                self.dockwidget.layerGcpGeoref.setLayer(layer)

    ## \brief Preselection of Inputlayers
    #
    # If layer E_Line exists then preselect this
    def preselectionProfileLayer(self):
        notInputLayers = self.getNonInputLayers(1)
        inputLayers = self.getInputlayers(False)

        self.dockwidget.layerProfileGeoref.setExceptedLayerList(notInputLayers)

        for layer in inputLayers:
            if layer.name() == "E_Line":
                self.dockwidget.layerProfileGeoref.setLayer(layer)

        lineLayer = self.dockwidget.layerProfileGeoref.currentLayer()

        return lineLayer

    ## \brief Get all layers from the layer tree except those from the folder "Eingabelayer"
    #
    # layers must be of type vector layer
    # geomType could be 0 - 'point', 1 - 'line', 2 - 'polygon', 'all'
    def getNonInputLayers(self, geomType):
        allLayers = QgsProject.instance().mapLayers().values()

        inputLayer = []
        nonInputLayer = []
        root = QgsProject.instance().layerTreeRoot()

        for group in root.children():
            if isinstance(group, QgsLayerTreeGroup) and group.name() == "Eingabelayer":
                for child in group.children():
                    if isinstance(child, QgsLayerTreeLayer):
                        if isinstance(child.layer(), QgsVectorLayer):
                            if geomType == 0 or geomType == 1 or geomType == 2:
                                if child.layer().geometryType() == geomType:
                                    inputLayer.append(child.layer())
                            if geomType == "all":
                                inputLayer.append(child.layer())

        for layerA in allLayers:
            check = False
            for layerIn in inputLayer:
                if layerA == layerIn:
                    check = True

            if not check:
                nonInputLayer.append(layerA)

        return nonInputLayer

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

    ## \brief Opens a message box with background information
    #
    def openInfoMessageBox(self):
        infoText = (
            "Ein archäologisches Profil ist ein (nahezu) vertikaler Schnitt durch einen oder mehrere archäologische "
            "Befunde und bietet daher gute Voraussetzungen zur dreidimensionalen Dokumentation von Grabungsszenen. "
            "\n\nDas Profiltool bietet die Möglichkeit Profilfotos anhand von Messpunkten zu georeferenzieren. "
            "Weiterhin können im erstellten Profil geometische Strukturen digitalisiert werden und die Daten für "
            "Profilpläne erzeugt werden."
        )
        self.infoTranssformMsgBox = QMessageBox()
        self.infoTranssformMsgBox.setText(infoText)

        self.infoTranssformMsgBox.setWindowTitle("Hintergrundinformationen")
        self.infoTranssformMsgBox.setStandardButtons(QMessageBox.Ok)
        self.infoTranssformMsgBox.exec_()
