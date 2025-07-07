# -*- coding: utf-8 -*-
import json
import os
import pathlib
import tempfile
import traceback
from glob import glob
from shutil import rmtree

import osgeo_utils.gdal_merge
from PIL import Image, ImageDraw
from osgeo import gdal
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import (
    QWidget,
    QMainWindow,
    QAction,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QMessageBox,
    QDesktopWidget,
)
from qgis.core import QgsGeometry
from qgis.gui import QgsMessageBar

from .data_store_georef import DataStoreGeoref
from .gcp_parambar import GcpParambar
from .image_georef import ImageGeoref
from .image_parambar import ImageParambar
from .profile_gcp_canvas import ProfileGcpCanvas
from .profile_georef_table import GeorefTable
from .profile_image_canvas import ProfileImageCanvas
from ..profileAAR.profileAAR import ProfileAAR
from ...Icons import ICON_PATHS


## @brief With the GeoreferencingDialog class a dialog window for the georeferencing of profiles is realized
#
# The class inherits form QMainWindow
#
# @author Mario Uhlig, VisDat geodatentechnologie GmbH, mario.uhlig@visdat.de
# @date 2021-25-05
class GeoreferencingDialog(QMainWindow):
    def __init__(self, t2GArchInstance, rotationCoords, iFace):
        print("Start GeoreferencingDialog")
        super().__init__()
        self.style_button_enabled = "background-color: green; width: 200px"
        self.style_button_disabled = "background-color: lightgrey; width: 200px"
        self.t2GArchInstance = t2GArchInstance
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.refData = None
        self.iface = iFace
        self.aarDirection = "horizontal"
        # DataStore
        self.dataStoreGeoref = DataStoreGeoref()
        self.rotationCoords = rotationCoords

        self.aarDirections_to_path_dict = {
            "horizontal": "dirPh",
            "original": "dirPo",
            "absolute height": "dirPa",
        }
        # for Kreuzprofil
        self.ref_data_pair = None
        self.profile_set = None
        self.clipping_polygon = QgsGeometry()

        self.createMenu()
        self.createComponents()
        self.createLayout()
        self.createConnects()

    def closeEvent(self, event):
        print("close")
        super().closeEvent(event)
        self.dataStoreGeoref.clearStore()
        # self.georefTable.cleanGeorefTable()

        # self.canvasImage
        self.destroyDialog()

    def set_for_kreuzprofil(self, ref_data_pair):
        self.ref_data_pair = ref_data_pair

    def polygon_drawn(self, geom: QgsGeometry):
        self.clipping_polygon = geom
        if self.ref_data_pair:
            self.check_for_enable_startBtn_kreuz()
        else:
            self.check_for_enable_startBtn()

    def check_for_enable_startBtn(self, _=None):
        if len(self.dataStoreGeoref.imagePoints) < 4:
            self.startGeorefBtn.setEnabled(False)
            self.startGeorefBtn.setStyleSheet(self.style_button_disabled)
        else:
            self.startGeorefBtn.setEnabled(True)
            self.startGeorefBtn.setStyleSheet(self.style_button_enabled)

    def check_for_enable_startBtn_kreuz(self, _=None):
        if self.clipping_polygon.isNull() or len(self.dataStoreGeoref.imagePoints) < 4:
            self.startGeorefBtn.setEnabled(False)
            self.startGeorefBtn.setStyleSheet(self.style_button_disabled)
        else:
            self.startGeorefBtn.setEnabled(True)
            self.startGeorefBtn.setStyleSheet(self.style_button_enabled)

    ## \brief Create different menus
    #
    #
    # creates the menuBar at upper part of the window and statusBar in the lower part
    #
    def createMenu(self):
        print("Start createMenu")
        self.statusBar()

        self.statusBar().reformat()
        self.statusBar().setStyleSheet("background-color: #FFF8DC;")
        self.statusBar().setStyleSheet("QStatusBar::item {border: none;}")

        exitAct = QAction(QIcon(ICON_PATHS["Ok_grau"]), "Exit", self)

        exitAct.setShortcut("Ctrl+Q")
        exitAct.setStatusTip("Anwendung schließen")
        exitAct.triggered.connect(self.destroyDialog)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu("&Datei")
        fileMenu.addAction(exitAct)

    ## \brief ECreates the components of the window
    #
    # - MessageBar to give hints
    # - Parameterbar to show the results of the transformation, instantiate class GeoreferencingDialogParambar()
    #   as self.transformationParamsBar
    # - Canvas component for layer display, instantiate class GeoreferencingDialogCanvas as self.canvasTransform
    # - Table with the GCPs, instantiate class GeoreferencingDialogTable() as self.georefTable
    # - Coordinates in statusBar
    # - instantiate class GeoreferencingCalculations as self.paramCalc
    # @returns
    def createComponents(self):
        # messageBar
        self.messageBar = QgsMessageBar()

        # Canvas Elemente
        self.canvasImage = ProfileImageCanvas(self)
        self.canvasGcp = ProfileGcpCanvas(self, self.rotationCoords)

        # paramsBar
        self.imageParambar = ImageParambar(self.canvasImage)
        self.gcpParambar = GcpParambar(self, self.canvasGcp, self.rotationCoords)

        # Actions
        self.createActions()

        # Toolbars
        self.createToolbars()

        # GcpTable
        self.georefTable = GeorefTable(self, self.dataStoreGeoref)

        # profileAAR
        self.profileAAR = ProfileAAR()

        # Bildgeoreferenzierung
        self.imageGeoref = ImageGeoref()

    ## \brief Event connections
    #
    def createConnects(self):
        self.imageParambar.toolDrawPolygon.finished_geometry.connect(self.polygon_drawn)

        self.georefTable.pup.register("activatePoint", self.canvasGcp.setActivePoint)
        self.georefTable.pup.register("activatePoint", self.canvasImage.setActivePoint)
        self.georefTable.pup.register("activatePoint", self.imageParambar.activateMapToolMove)

        self.canvasImage.pup.register("imagePointCoordinates", self.georefTable.updateImageCoordinates)
        self.canvasImage.pup.register("imagePointCoordinates", self.dataStoreGeoref.addImagePoint)
        self.canvasImage.pup.register("imagePointCoordinates", self.georefTable.updateErrorValues)

        self.startGeorefBtn.clicked.connect(self.startGeoreferencing)

        self.georefTable.pup.register("dataChanged", self.profileAAR.run)

        self.profileAAR.pup.register("aarPointsChanged", self.dataStoreGeoref.addAarPoints)

        self.dataStoreGeoref.pup.register("pushTransformationParams", self.rotationCoords.setAarTransformationParams)
        self.dataStoreGeoref.pup.register("pushAarPoints", self.canvasImage.updateAarPoints)

        self.canvasGcp.pup.register("moveCoordinate", self.gcpParambar.updateCoordinate)
        self.canvasImage.pup.register("moveCoordinate", self.imageParambar.updateCoordinate)

    ## \brief create actions
    #
    def createActions(self):
        # Export
        iconExport = QIcon(ICON_PATHS["mActionSaveGCPpointsAs"])
        self.actionExport = QAction(iconExport, "Export data", self)

        # Import
        iconImport = QIcon(ICON_PATHS["mActionLoadGCPpoints"])
        self.actionImport = QAction(iconImport, "Import data", self)

    ## \brief create toolbars
    #
    # - toolbarMap
    def createToolbars(self):
        # Toolbar Kartennavigation
        self.toolbarMap = self.addToolBar("Kartennavigation")

        self.startGeorefBtn = QPushButton("Profil entzerren", self)

        self.startGeorefBtn.setStyleSheet(self.style_button_enabled)

        self.toolbarMap.addWidget(self.startGeorefBtn)

    ## \brief Creates the layout for the window and assigns the created components
    #
    def createLayout(self):
        widgetCentral = QWidget(self)

        verticalLayout = QVBoxLayout()
        verticalLayout.setContentsMargins(0, 0, 0, 0)
        verticalLayout.setSpacing(0)
        widgetCentral.setLayout(verticalLayout)
        self.setCentralWidget(widgetCentral)

        verticalLayout.addWidget(self.messageBar)

        verticalImageLayout = QVBoxLayout()
        verticalImageLayout.addWidget(self.imageParambar)
        verticalImageLayout.addWidget(self.canvasImage)

        verticalGcpLayout = QVBoxLayout()
        verticalGcpLayout.addWidget(self.gcpParambar)
        verticalGcpLayout.addWidget(self.canvasGcp)

        horizontalLayout = QHBoxLayout()
        horizontalLayout.addLayout(verticalImageLayout)
        horizontalLayout.addLayout(verticalGcpLayout)

        verticalLayout.addLayout(horizontalLayout)
        verticalLayout.addWidget(self.georefTable)

    def createFolders(self, refData):
        print("Create missing folders ...")

        profileDirs = refData["profileDirs"].copy()

        if "original" not in refData["transform_methods"]:
            del profileDirs["dirPo"]
        if "horizontal" not in refData["transform_methods"]:
            del profileDirs["dirPh"]
        if "absolute height" not in refData["transform_methods"]:
            del profileDirs["dirPa"]
        del profileDirs["dir3d"]

        for key, value in profileDirs.items():
            if not os.path.exists(value):
                os.makedirs(value)

    def restore(self):
        self.georefTable.cleanGeorefTable()
        offset = 0

        if self.ref_data_pair and len(self.ref_data_pair) == 2:
            other_ref_data = (
                self.ref_data_pair[0] if self.ref_data_pair[0] is not self.refData else self.ref_data_pair[1]
            )
            self.georefTable.updateGeorefTable(
                self.refData,
                self.aarDirection,
                other_ref_data,
            )
            self.setWindowTitle(
                f"Georeferenzierung von Kreuzprofil: {self.refData['profileNumber']} "
                f"(im anderen Fenster {other_ref_data['profileNumber']})"
            )
            if self.profile_set == 0:
                offset = -10
            else:
                offset = 10
        else:
            self.georefTable.updateGeorefTable(self.refData, self.aarDirection)
            self.setWindowTitle(f"Georeferenzierung von Profil: {self.refData['profileNumber']}")

        self.georefTable.pointUsageChanged()

        validImageLayer = self.canvasImage.updateCanvas(self.refData["imagePath"])

        if validImageLayer:
            self.canvasGcp.updateCanvas(self.refData)

            self.dataStoreGeoref.addTargetPoints(self.refData)

            self.adjustSize()
            self.resize(1000, 750)
            sg = QDesktopWidget().availableGeometry()
            x = int((sg.width() - self.width()) / 2.0 + offset)
            y = int((sg.height() - self.height()) / 2.0 + offset)
            self.setGeometry(x, y, self.width(), self.height())
            self.show()
        else:
            self.iface.messageBar().pushMessage("Error", "Rasterlayer konnte nicht gelesen werden", level=1, duration=3)

    ## \brief Export GCP-Data in a textfile
    #
    def writeMetafile(self, aarDirection, metaFileOut):
        transformation_params = self.dataStoreGeoref.getAarTransformationParams(aarDirection)

        # Wenn die AAR-Berechnung aufgrund geringer Genauigkeit (O-W- oder N-S-Profile)
        # einen Fehler bringt (ns_error is True) wird in AAR der slope_deg Winkel um 45 Grad reduziert.
        # Die 45 Grad müssen hier wieder dazu addiert werden
        # damit die Digitalisierung von Objekten im Profil funktioniert

        if "ns_error" in transformation_params:
            if transformation_params["ns_error"] is True:
                transformation_params["slope_deg"] = transformation_params["slope_deg"] + 45

        data = {
            "profilnummer": self.refData["profileNumber"],
            "profil": self.refData["savePath"],
            "profilfoto": self.refData["imagePath"],
            "blickrichtung": self.refData["viewDirection"],
            "entzerrungsebene": "vertikal",
            "aar_direction": aarDirection,
            "gcps": self.dataStoreGeoref.getGeorefData(aarDirection),
            "transform_params": transformation_params,
        }

        with open(str(metaFileOut), "w") as outfile:
            json.dump(data, outfile)

        return metaFileOut

    ## \brief Open up the transformation dialog
    #
    # calls the funcion restore()
    #
    # \param refData
    def showGeoreferencingDialog(self, refData):
        self.refData = refData
        print(self.refData)

        self.startGeorefBtn.setEnabled(False)
        self.startGeorefBtn.setStyleSheet(self.style_button_disabled)
        if self.ref_data_pair:
            self.toolbarMap.addWidget(QLabel("   Benötigt Referenzierungspunkte und ein Beschneidungspolygon!"))
            self.canvasImage.pup.register("imagePointCoordinates", self.check_for_enable_startBtn_kreuz)
        else:
            self.toolbarMap.addWidget(QLabel("   Benötigt Referenzierungspunkte!"))
            self.canvasImage.pup.register("imagePointCoordinates", self.check_for_enable_startBtn)

        if self.ref_data_pair:
            if self.refData is self.ref_data_pair[0]:
                self.profile_set = 0
            elif self.refData is self.ref_data_pair[1]:
                self.profile_set = 1
            else:
                print("Fehler42")
                return

            if self.profile_set == 0:
                # later results will be copied there
                self.createFolders(refData)
                self.refData["profileDirs_backup"] = self.refData["profileDirs"].copy()

            # store all in temp dir:
            tmp_dir = tempfile.mkdtemp(prefix=f"georef_profile{self.refData['profileNumber']}_")
            self.refData["savePath"] = str(tmp_dir)

            for key, value in self.refData["profileDirs"].items():
                last_folder = os.path.basename(os.path.normpath(value))
                profile_dir = pathlib.Path(self.refData["savePath"]).joinpath(last_folder)
                self.refData["profileDirs"][key] = str(profile_dir)

            # load camera file:
            with Image.open(self.refData["imagePath"]) as imageObject:
                imageObject.load()

            file_name = "camera_copy.png"

            if self.profile_set == 1:
                # I am the second set and I need to flip my image
                opposite_direction = {
                    "S": "N",
                    "W": "E",
                    "N": "S",
                    "E": "W",
                }
                self.refData["viewDirection"] = opposite_direction[self.refData["viewDirection"]]
                imageObject = imageObject.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                file_name = "flipped_" + file_name

            # store file
            file_path = str(pathlib.Path(self.refData["savePath"]).joinpath(file_name))
            imageObject.save(file_path)
            imageObject.close()

            # make the (flipped) png image the default to work with
            self.refData["imagePath"] = file_path

        # create folders in tmp dir or original dir if not kreuzprofil
        self.createFolders(refData)

        self.restore()

    ## \brief Start georeferencing process
    #
    # Do georeferencing for every aarDirection
    # Write Metadatafile
    #
    def startGeoreferencing(self):
        try:
            if self.clipping_polygon:
                # clip image to polygon
                points_list = [(p[0], abs(p[1])) for p in self.clipping_polygon.asMultiPolygon()[0][0]]
                img = Image.open(self.refData["imagePath"])
                mask = Image.new("1", img.size, 0)
                draw_tool = ImageDraw.Draw(mask)
                draw_tool.polygon(points_list, fill=1, outline=1)
                background = Image.new(img.mode, img.size, "white")
                result = Image.composite(img, background, mask)
                if self.ref_data_pair:
                    clipped_image_path = str(pathlib.Path(self.refData["savePath"]).joinpath("clipped.png"))
                else:
                    # not kreuzprofil, but with clipping polygon:
                    # store clipped in temp dir:
                    tmp_dir = tempfile.mkdtemp(prefix=f"georef_profile{self.refData['profileNumber']}_")
                    clipped_image_path = str(pathlib.Path(tmp_dir).joinpath("clipped.png"))
                result.save(clipped_image_path)
                result.close()

                # make clipped image the default to work with
                self.refData["imagePath"] = clipped_image_path

            imageFileIn = self.refData["imagePath"]
            profileTargetName = self.refData["profileTargetName"]
            if not self.ref_data_pair:
                # not set for kreuzprofil
                file_extension = "jpg"
            else:
                file_extension = "png"

            for aarDirection in self.refData["transform_methods"]:
                base_path = pathlib.Path(self.refData["profileDirs"][self.aarDirections_to_path_dict[aarDirection]])
                imageFileOut = base_path.joinpath(f"{profileTargetName}.{file_extension}")
                metaFileOut = base_path.joinpath(f"{profileTargetName}.meta")

                georefData = self.dataStoreGeoref.getGeorefData(aarDirection)
                georefChecker = self.imageGeoref.run_georef(
                    georefData, self.refData["crs"], imageFileIn, str(imageFileOut)
                )

                if georefChecker != "ok":
                    self.iface.messageBar().pushMessage(
                        "Hinweis",
                        "Konnte Profil nicht georeferenzieren. Es müssen min. 4 GCP gesetzt sein!",
                        level=1,
                        duration=5,
                    )
                    continue

                _ = self.writeMetafile(aarDirection, metaFileOut)

                if not self.ref_data_pair:
                    # not set for kreuzprofil
                    self.iface.messageBar().pushMessage(
                        "Hinweis",
                        "Das Profil wurde unter " + str(imageFileOut) + " referenziert",
                        level=3,
                        duration=5,
                    )
                    continue

                self.refData[f"geo_ref_done_{aarDirection}"] = True

                if not (
                    self.ref_data_pair[0].get(f"geo_ref_done_{aarDirection}", False)
                    and self.ref_data_pair[1].get(f"geo_ref_done_{aarDirection}", False)
                ):
                    # other profil is not ready yet
                    continue

                save_path_0_original = pathlib.Path(
                    self.ref_data_pair[0]["profileDirs_backup"][self.aarDirections_to_path_dict[aarDirection]]
                )
                save_path_0 = pathlib.Path(
                    self.ref_data_pair[0]["profileDirs"][self.aarDirections_to_path_dict[aarDirection]]
                )
                save_path_1 = pathlib.Path(
                    self.ref_data_pair[1]["profileDirs"][self.aarDirections_to_path_dict[aarDirection]]
                )
                command = (
                    f"gdal_merge.py "
                    f"-n 255 "
                    f"-init 255 "
                    f"-of gtiff "
                    f"-o /vsimem/merged.tif "
                    f"{save_path_0.joinpath(f'{profileTargetName}.{file_extension}')} "
                    f"{save_path_1.joinpath(f'{profileTargetName}.{file_extension}')}"
                )
                osgeo_utils.gdal_merge.main(command.split(" "))

                imageFileOut = save_path_0_original.joinpath(f"{profileTargetName}.jpg")
                gdal.Translate(
                    f"{imageFileOut}",
                    "/vsimem/merged.tif",
                    options="-co WORLDFILE=YES -co QUALITY=100",
                )
                gdal.Unlink("/vsimem/merged.tif")

                with open(f"{save_path_0.joinpath(f'{profileTargetName}.meta')}", "r") as meta_file_0:
                    meta_0 = json.load(meta_file_0)
                with open(f"{save_path_1.joinpath(f'{profileTargetName}.meta')}", "r") as meta_file_1:
                    meta_1 = json.load(meta_file_1)
                meta_0["gcps"] += meta_1["gcps"]
                for item in meta_0["gcps"]:
                    # do not delete as they need to be there in plan export
                    # but they have to be 0 because half of them are not valid in kreuzprofil
                    item["input_x"] = 0.0
                    item["input_z"] = 0.0
                meta_0["profilnummer"] += "_" + meta_1["profilnummer"]
                out_path = f"{save_path_0_original.joinpath(f'{profileTargetName}.meta')}"
                with open(out_path, "w") as outfile:
                    json.dump(meta_0, outfile)

                self.iface.messageBar().pushMessage(
                    "Hinweis",
                    "Das Profil wurde unter " + str(imageFileOut) + " referenziert",
                    level=3,
                    duration=5,
                )

        except Exception as e:
            print(f"An exception occurred {type(e)} \n {traceback.format_exc()}")
            QMessageBox.critical(
                self,
                "Fehler bei der Profilentzerrung!",
                "Profil konnte nicht entzerrt werden. Vorgang wurde abgebrochen!",
                QMessageBox.Abort,
            )

        self.destroyDialog()

    def destroyDialog(self):
        self.refData["geo_ref_done_destroyed"] = True
        if (
            self.ref_data_pair
            and self.ref_data_pair[0].get("geo_ref_done_destroyed", False)
            and self.ref_data_pair[1].get("geo_ref_done_destroyed", False)
        ):
            # cleanup last sessions
            pattern = os.path.join(tempfile.gettempdir(), "georef_profile*")
            for item in glob(pattern):
                if os.path.isdir(item):
                    rmtree(item, ignore_errors=True)

        # mark that it was closed already:
        self.ref_data_pair = None
        self.close()
        self.destroy()
