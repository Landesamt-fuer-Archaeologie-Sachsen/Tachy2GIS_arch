## @package QGIS geoEdit extension..
import os
import math
import numpy as np
from PIL import Image

from qgis.core import QgsProject, QgsPointXY, QgsVectorLayer, QgsLayerTreeGroup, QgsLayerTreeLayer, QgsWkbTypes
from qgis.analysis import QgsGcpTransformerInterface

from .data_store_georef import DataStoreGeoref
from .georeferencing_dialog import GeoreferencingDialog

## @brief The class is used to implement functionalities for work with profiles within the dock widget of the Tachy2GIS_arch plugin
#
# @author Mario Uhlig, VisDat geodatentechnologie GmbH, mario.uhlig@visdat.de
# @date 2021-05-07
class Georef():

    ## The constructor.
    #  Defines attributes for the Profile
    #
    #  @param dockWidget pointer to the dockwidget
    #  @param iFace pointer to the iface class
    def __init__(self, t2gArchInstance, iFace):

        self.__iconpath = os.path.join(os.path.dirname(__file__), 'Icons')
        self.__t2gArchInstance = t2gArchInstance
        self.__dockwidget = t2gArchInstance.dockwidget
        self.__iface = iFace

        self.dataStoreGeoref = DataStoreGeoref()

    ## @brief Initializes the functionality for profile modul
    #

    def setup(self):

        #Preselection of Inputlayers (only Layer below "Eingabelayer" are available)
        preselectedLineLayer = self.__preselectionProfileLayer()
        #Preselection profilenumber
        self.__preselectProfileNumbers(preselectedLineLayer)
        #Preselection of Inputlayers (only Layer below "Eingabelayer" are available)
        self.__preselectionGcpLayer()
        #set datatype filter to profileFotosComboGeoref
        self.__dockwidget.profileFotosComboGeoref.setFilter('Images (*.png *.JPG *.jpg *.jpeg *.tif)')
        #Preselection View direction
        self.__preselectViewDirection()
        #set datatype filter and save mode to profileSaveComboGeoref
        self.__dockwidget.profileSaveComboGeoref.setFilter('Images (*.jpg)')
        self.__dockwidget.profileSaveComboGeoref.setStorageMode(3)

        self.__dockwidget.startGeoreferencingBtn.clicked.connect(self.__startGeoreferencingDialog)

        self.__dockwidget.layerGcpGeoref.currentIndexChanged.connect(self.__calculateViewDirection)

        self.__dockwidget.profileIdsComboGeoref.currentIndexChanged.connect(self.__calculateViewDirection)

        self.__dockwidget.layerProfileGeoref.currentIndexChanged.connect(self.__calculateViewDirection)

        self.__dockwidget.profileInfoBtn.clicked.connect(self.__testProjective)

    ## \brief Start georeferencing dialog
    #
    #
    def __startGeoreferencingDialog(self):

        refData = self.__getSelectedValues()

        self.georeferencingDialog = GeoreferencingDialog(self, self.dataStoreGeoref, self.__iface)
        self.georeferencingDialog.showGeoreferencingDialog(refData)


    ## \brief get selected values
    #
    #
    def __getSelectedValues(self):

        #lineLayer
        lineLayer = self.__dockwidget.layerProfileGeoref.currentLayer().clone()

        #Profilnummer
        profileNumber = self.__dockwidget.profileIdsComboGeoref.currentText()

        #pointLayer
        pointLayer = self.__dockwidget.layerGcpGeoref.currentLayer().clone()
        pointLayer.setSubsetString("obj_type = 'Fotoentzerrpunkt' and obj_art = 'Profil' and prof_nr = '"+profileNumber+"'")

        #Zielkoordinaten
        targetGCP = {}
        targetGCP['points'] = []

        for feature in pointLayer.getFeatures():

            g = feature.geometry()

            pointObj = {'uuid': feature.attribute("uuid"), 'ptnr': feature.attribute("ptnr"), 'id': feature.attribute("id"), 'x': float(g.get().x()), 'y': float(g.get().y()), 'z': float(g.get().z())}

            targetGCP['points'].append(pointObj)

        #Foto
        imagePath = self.__dockwidget.profileFotosComboGeoref.filePath()
        #Blickrichtung
        viewDirLong = self.__dockwidget.profileViewDirectionComboGeoref.currentText()

        if viewDirLong == 'Nord':
            viewDirection = 'N'
        if viewDirLong == 'Ost':
            viewDirection = 'E'
        if viewDirLong == 'Süd':
            viewDirection = 'S'
        if viewDirLong == 'West':
            viewDirection = 'W'
        #horizontal true/false
        horizontalCheck = self.__dockwidget.radioDirectionHorizontal.isChecked()
        #Speichern unter
        savePath = self.__dockwidget.profileSaveComboGeoref.filePath()
        #Metadaten
        metadataCheck = self.__dockwidget.metaProfileCheckbox.isChecked()

        refData = {'lineLayer': lineLayer, 'pointLayer': pointLayer, 'crs': pointLayer.crs(), 'profileNumber': profileNumber, 'imagePath': imagePath, 'viewDirection': viewDirection, 'horizontal': horizontalCheck, 'savePath': savePath, 'saveMetadata': metadataCheck, 'targetGCP': targetGCP}

        return refData

    ## \brief Blickrichtung bestimmen
    #
    #
    def __calculateViewDirection(self):

        #lineLayer
        lineLayer = self.__dockwidget.layerProfileGeoref.currentLayer().clone()

        #Profilnummer
        profileNumber = self.__dockwidget.profileIdsComboGeoref.currentText()

        lineLayer.setSubsetString("prof_nr = '"+profileNumber+"'")

        view = None


        if lineLayer.geometryType() ==  QgsWkbTypes.LineGeometry:
            for feat in lineLayer.getFeatures():

                geom = feat.geometry()
                #Singlepart
                if QgsWkbTypes.isSingleType(geom.wkbType()):
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
                # Lösung von hier: https://stackoverflow.com/questions/14066933/direct-way-of-computing-clockwise-angle-between-2-vectors/16544330#16544330, angepasst auf Berechnung ohne numpy
                dot = v0[0] * vp[0] + v0[1] * vp[1]  # dot product: x1*x2 + y1*y2
                det = v0[0] * vp[1] - vp[0] * v0[1]  # determinant: x1*y2 - y1*x2

                radians = math.atan2(det, dot)
                angle = math.degrees(radians)
                # negative Winkelwerte (3. und 4. Quadrant, Laufrichtung entgegen Uhrzeigersinn) in fortlaufenden Wert (181 bis 360) umrechnen
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

                self.__dockwidget.profileViewDirectionComboGeoref.setCurrentText(view)


    ### Ende Blickrichtung bestimmen

    ## \brief Preselection of __preselectViewDirection
    #
    #
    def __preselectViewDirection(self):

        self.__dockwidget.profileViewDirectionComboGeoref.addItems(['Nord', 'Ost', 'Süd', 'West'])

    ## \brief Preselection of __preselectProfileNumbers
    #
    #  @param lineLayer
    def __preselectProfileNumbers(self, lineLayer):
        profileList = self.__getProfileNumbers(lineLayer)

        self.__dockwidget.profileIdsComboGeoref.addItems(profileList)

    ## \brief Preselection of __getProfileNumbers
    #
    #  @param lineLayer
    # @returns list of profile id's
    def __getProfileNumbers(self, lineLayer):

        profileList = []
        for feat in lineLayer.getFeatures():
            if feat.attribute('Objekttyp') == 'Profil':
                if feat.attribute('prof_nr'):
                    profileList.append(feat.attribute('prof_nr'))

        return sorted(profileList, key=str.lower)

    ## \brief Preselection of Inputlayers
    #
    # If layer E_Point exists then preselect this
    def __preselectionGcpLayer(self):

        notInputLayers = self.__getNotInputlayers(0)
        inputLayers = self.__getInputlayers(False)

        self.__dockwidget.layerGcpGeoref.setExceptedLayerList(notInputLayers)

        for layer in inputLayers:
            if layer.name() == 'E_Point':
                self.__dockwidget.layerGcpGeoref.setLayer(layer)


    ## \brief Preselection of Inputlayers
    #
    # If layer E_Line exists then preselect this
    def __preselectionProfileLayer(self):

        notInputLayers = self.__getNotInputlayers(1)
        inputLayers = self.__getInputlayers(False)

        self.__dockwidget.layerProfileGeoref.setExceptedLayerList(notInputLayers)

        for layer in inputLayers:
            if layer.name() == 'E_Line':
                self.__dockwidget.layerProfileGeoref.setLayer(layer)

        lineLayer = self.__dockwidget.layerProfileGeoref.currentLayer()

        return lineLayer

    ## \brief Get all layers from the layertree exept those from the folder "Eingabelayer"
    #
    # layers must be of type vectorlayer
    # geomType could be 0 - 'point', 1 - 'line', 2 - 'polygon', 'all'
    def __getNotInputlayers(self, geomType):

        allLayers = QgsProject.instance().mapLayers().values()

        inputLayer = []
        notInputLayer = []
        root = QgsProject.instance().layerTreeRoot()

        for group in root.children():
            if isinstance(group, QgsLayerTreeGroup) and group.name() == 'Eingabelayer':
                for child in group.children():
                    if isinstance(child, QgsLayerTreeLayer):
                        if isinstance(child.layer(), QgsVectorLayer):
                            if (geomType == 0 or geomType == 1 or geomType == 2):
                                if child.layer().geometryType() == geomType:
                                    inputLayer.append(child.layer())
                            if geomType == 'all':
                                 inputLayer.append(child.layer())

        for layerA in allLayers:
            check = False
            for layerIn in inputLayer:
                if layerA == layerIn:
                    check = True

            if check == False:
                notInputLayer.append(layerA)

        return notInputLayer

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

    ## \brief Start georeferencing dialog
    #
    #
    def __testProjective(self):
        print('projective - QgsGcpTransformerInterface')

        #source image
        imagePath = self.__dockwidget.profileFotosComboGeoref.filePath()
        imagePath = 'Y:/Projekte/2021/lfa_profil/beispieldaten/AZB-16/AZB-16/Entzerrungen/AZB-16_Pr65.JPG'
        imgOrg = Image.open(imagePath)
        src_w, src_h = imgOrg.size

        # vertices of source image (Ecken - Bildraum)
        src_ll = (0, -src_h)
        src_lr = (src_w, -src_h)
        src_ur = (src_w, 0)
        src_ul = (0, 0)

        ############ QgsGcpTransformerInterface ##########

        # GCP's
        src_cp  = [
            QgsPointXY(534.957, -1258.969), 
            QgsPointXY(2350.355, -1218.713), 
            QgsPointXY(4127.882, -1232.728), 
            QgsPointXY(3926.527, -2294.742), 
            QgsPointXY(2954.792, -2268.352), 
            QgsPointXY(2085.597, -2168.010),
            QgsPointXY(646.109, -1618.143)]
        geo_cp  = [
            QgsPointXY(4577323.165, 5709836.626), 
            QgsPointXY(4577324.778, 5709836.631), 
            QgsPointXY(4577326.313, 5709836.624), 
            QgsPointXY(4577326.256, 5709835.627), 
            QgsPointXY(4577325.333, 5709835.673), 
            QgsPointXY(4577324.520, 5709835.746), 
            QgsPointXY(4577323.229, 5709836.306)]

        #(1) get matrix for transformation T1 (src → geo) from 4...n control points
        transformMethod = QgsGcpTransformerInterface.TransformMethod(6) # 6 - projective
        qgisTransformer = QgsGcpTransformerInterface.createFromParameters(transformMethod, src_cp, geo_cp)

        print('qgisTransformer', qgisTransformer)

        # get extent of destination image in georeferenced area
        # transformation of source image vertices with transformation T1
        # Ecken in Geokoordinaten
        geo_vp_ul = qgisTransformer.transform(src_ul[0], src_ul[1], False)[1:3]
        geo_vp_ll = qgisTransformer.transform(src_ll[0], src_ll[1], False)[1:3]
        geo_vp_ur = qgisTransformer.transform(src_ur[0], src_ur[1], False)[1:3] 
        geo_vp_lr = qgisTransformer.transform(src_lr[0], src_lr[1], False)[1:3] 

        print('geo_vp_ul', geo_vp_ul)
        print('geo_vp_ll', geo_vp_ll)
        print('geo_vp_ur', geo_vp_ur)
        print('geo_vp_lr', geo_vp_lr)

        # calculation of destination image extent in georeferenced area
        #Ausdehnung Geo
        geo_left = min(geo_vp_ul[0], geo_vp_ll[0], geo_vp_ur[0], geo_vp_lr[0])
        geo_lower = min(geo_vp_ul[1], geo_vp_ll[1], geo_vp_ur[1], geo_vp_lr[1])
        geo_right = max(geo_vp_ul[0], geo_vp_ll[0], geo_vp_ur[0], geo_vp_lr[0])
        geo_upper = max(geo_vp_ul[1], geo_vp_ll[1], geo_vp_ur[1], geo_vp_lr[1])

        print('geo_left', geo_left)
        print('geo_lower', geo_lower)
        print('geo_right', geo_right)
        print('geo_upper', geo_upper)

        geo_ll = np.array([geo_left, geo_lower])
        geo_lr = np.array([geo_right, geo_lower])
        geo_ur = np.array([geo_right, geo_upper])
        geo_ul = np.array([geo_left, geo_upper])

        print('geo_ll', geo_ll)
        print('geo_lr', geo_lr)
        print('geo_ur', geo_ur)
        print('geo_ul', geo_ul)

        geo_w = geo_right - geo_left
        geo_h = geo_upper - geo_lower

        print('geo_w', geo_w)
        print('geo_h', geo_h)

        # (3) get transformation T2 from extent of destination image in local
        # (3a) shift upper left vertex to (0,0)
        t2_shift = np.array([-geo_left, -geo_upper])
        print('t2_shift', t2_shift)

        # (3b) resolution of destination image in pixel/m
        # calculated from image extent

        #Strecke oben-links zu unten-rechts

        dist_geo = math.dist(geo_vp_ul,geo_vp_lr)
        #dist_geo = math.dist(geo_ul,geo_lr)
        dist_img = math.dist(src_ul,src_lr)

        res_geo = dist_img / dist_geo
        res_img = dist_geo / dist_img

        print('dist_img', dist_img)
        print('dist_geo', dist_geo)

        print('res_geo', res_geo)
        print('res_img', res_img)

        dst_resolution = res_geo     

        # (3c) scaling with resolution of destination image
        # korrigiert
        dst_w = dst_resolution * geo_w #Anzahl Pixel im Bildraum
        dst_h = dst_resolution * geo_h

        print('dst_w', dst_w)
        print('dst_h', dst_h)

        # (as 2-dimensional vectors:)

        dst_ll = dst_resolution * (geo_ll + t2_shift)
        dst_lr = dst_resolution * (geo_lr + t2_shift)
        dst_ur = dst_resolution * (geo_ur + t2_shift)
        dst_ul = dst_resolution * (geo_ul + t2_shift)

        print('dst_ll', dst_ll)
        print('dst_lr', dst_lr)
        print('dst_ur', dst_ur)
        print('dst_ul', dst_ul)

        # (4) T2-transformation of the 4 T1-transformed vertices of source image
        # (taken from (2))
        dst_vp_ul = dst_resolution * (geo_vp_ul + t2_shift)
        dst_vp_ll = dst_resolution * (geo_vp_ll + t2_shift)
        dst_vp_ur = dst_resolution * (geo_vp_ur + t2_shift)
        dst_vp_lr = dst_resolution * (geo_vp_lr + t2_shift)

        print('geo_vp_ul', geo_vp_ul)
        print('t2_shift', t2_shift)
        print('sum', geo_vp_ul + t2_shift)
        print('dst_vp_ul', dst_vp_ul)
        print('dst_vp_ll', dst_vp_ll)
        print('dst_vp_ur', dst_vp_ur)
        print('dst_vp_lr', dst_vp_lr)

        ########### PIL ##########

        ###goe: hier spiegeln wir die Koordinaten von src und dst vom 4. in den 1. Quadranten, weil Pillow nur mit positiven Passpunkten arbeitet
        ###goe: anstatt 'abs' (das wäre nur bei positiven x-Werten richtig, die wir aber im Prinzip auch haben)
        ###goe: schlage ich aber die Multiplikation mit (1, -1) vor, d.h. alle y-Werte werden mit -1 multipliziert
		#imgCoordEdges = [src_ul, src_ur, src_lr, src_ll]
        ###goe: und 'edges' sind Kanten, reduzieren wir lieber auf imgCoords
        imgCoords = np.multiply([src_ul, src_ur, src_lr, src_ll], (1,-1))
        #projectiveCoordEdges = [tuple(dst_vp_ul), tuple(dst_vp_ur), tuple(dst_vp_lr), tuple(dst_vp_ll)]
        projectiveCoords = np.multiply([tuple(dst_vp_ul), tuple(dst_vp_ur), tuple(dst_vp_lr), tuple(dst_vp_ll)], (1,-1))
    
		#coeffs = self.__find_pill_coeffs(projectiveCoordEdges,imgCoordEdges)
        coeffs = self.__find_pill_coeffs(projectiveCoords,imgCoords) 

        print('imgCoordEdges', imgCoords)
        print('projectiveCoordEdges', imgCoords)
        coeffs = self.__find_pill_coeffs(projectiveCoords,imgCoords)

        print('coeffs', coeffs)
        imagePath = 'Y:/Projekte/2021/lfa_profil/beispieldaten/AZB-16/AZB-16/Entzerrungen/AZB-16_Pr65.JPG' #self.__dockwidget.profileFotosComboGeoref.filePath()
        savePath = self.__dockwidget.profileSaveComboGeoref.filePath()
        print('imagePath', imagePath)
        print('savePath', savePath)
        self.__imgTransform(imagePath, savePath, coeffs, dst_h, dst_w)
        print('finish pil')
        worldfilePath = savePath[:-3]+"wld"
        #imageGeoWidth = ur_geo[1] - ul_geo[1]
        #print('imageGeoWidth', imageGeoWidth)
        self.__writeWorldFile(worldfilePath, geo_ul, res_img)
        print('finish worldfile')


    #where pb is the four vertices in the current plane, and pa contains four vertices in the resulting plane.
    def __find_pill_coeffs(self, pa, pb):
        matrix = []
        for p1, p2 in zip(pa, pb):
            matrix.append([p1[0], p1[1], 1, 0, 0, 0, -p2[0]*p1[0], -p2[0]*p1[1]])
            matrix.append([0, 0, 0, p1[0], p1[1], 1, -p2[1]*p1[0], -p2[1]*p1[1]])

        A = np.matrix(matrix, dtype=np.float)
        B = np.array(pb).reshape(8)

        res = np.dot(np.linalg.inv(A.T * A) * A.T, B)
        return np.array(res).reshape(8)


    def __imgTransform(self, image_in, image_out, coeffs, heightDst, widthDst):

        img = Image.open(image_in)
        #m = -0.5
        #xshift = abs(m) * width
        #new_width = width + int(round(xshift))
        #img = img.transform((new_width, height), Image.AFFINE, (1, m, -xshift if m > 0 else 0, 0, 1, 0), Image.BICUBIC)

        img.transform((int(widthDst), int(heightDst)), Image.PERSPECTIVE, coeffs, Image.BICUBIC).save(image_out)

    def __writeWorldFile(self, worldfilePath, geo_ul, res_img):

        pixelwidth = res_img
        pixelheight = res_img * -1

        lines = [str(pixelwidth), str(0.0), str(0.0), str(pixelheight), str(geo_ul[0]), str(geo_ul[1])]
        with open(worldfilePath, 'w') as f:
            for line in lines:
                f.write(line)
                f.write('\n')