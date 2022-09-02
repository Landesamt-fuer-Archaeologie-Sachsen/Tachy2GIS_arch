from math import pi, cos, sin

from qgis.core import QgsGeometry, QgsPoint


class RotationCoords():

    def __init__(self):

        #self.dialogInstance = dialogInstance

        self.transformationParams = None

    def setAarTransformationParams(self, params):

        print('setAarTransformationParams', params)

        self.transformationParams = params

    #Karte zu Profil
    def rotation(self, x, y, z, zAdaption):

        slope_deg = self.transformationParams['slope_deg']
        slope_deg_rev = self.transformationParams['slope_deg'] * (-1)
        center_x = self.transformationParams['center_x']
        center_y = self.transformationParams['center_y']
        center_z = self.transformationParams['center_z']
        min_x = self.transformationParams['min_x']
        center_x_trans = self.transformationParams['center_x_trans']
        center_z_trans = self.transformationParams['center_z_trans']

        x_trans = center_x + (x - center_x) * cos(slope_deg / 180 * pi) - sin(slope_deg / 180 * pi) * (y - center_y)

        y_trans = center_y + (x - center_x) * sin(slope_deg / 180 * pi) + (y - center_y) * cos(slope_deg / 180 * pi)
        
        if self.transformationParams['aar_direction'] == 'horizontal':

            if zAdaption is True:
                z_trans = z + center_y - center_z
            else:
                z_trans = z

        elif self.transformationParams['aar_direction'] == 'absolute height':
       
            z_trans = z

            #Anpassung absolute height - verschieben nach x
            x_trans = x_trans - min_x

        elif self.transformationParams['aar_direction'] == 'original':

            x_trans = center_x_trans + (x - center_x_trans) * cos(slope_deg_rev / 180 * pi) - (z - center_z_trans) * sin(slope_deg_rev / 180 * pi)

            z_trans = center_z_trans + (x - center_x_trans) * sin(slope_deg_rev / 180 * pi) + (z - center_z_trans) * cos(slope_deg_rev / 180 * pi)

            y_trans = y

        else:
            print('Wrong AAR-Direction')

        
        return {'x_trans': x_trans, 'y_trans': y_trans ,'z_trans': z_trans}


    #Profil zu Karte
    def rotationReverse(self, x, z, zAdaption):

        slope_deg = self.transformationParams['slope_deg'] * (-1)
        center_x = self.transformationParams['center_x']
        center_y = self.transformationParams['center_y']
        z_slope = 1 #self.transformationParams['z_slope'] -- geht nicht mit dem Neigungswinkel
        z_intercept = self.transformationParams['z_intercept']
        min_x = self.transformationParams['min_x']
        center_x_trans = self.transformationParams['center_x_trans']
        center_z_trans = self.transformationParams['center_z_trans']

        if self.transformationParams['aar_direction'] == 'horizontal':

            if zAdaption is True:
                z_trans = z_slope * z - z_intercept
            else:
                z_trans = z         

            x_trans = center_x + (x - center_x) * cos(slope_deg / 180 * pi) - sin(slope_deg / 180 * pi) * 0
            y_trans = center_y + (x - center_x) * sin(slope_deg / 180 * pi) + 0 * cos(slope_deg / 180 * pi)   

        elif self.transformationParams['aar_direction'] == 'absolute height':

            #Anpassung absolute height - verschieben nach x
            x = x + min_x

            z_trans = z

            x_trans = center_x + (x - center_x) * cos(slope_deg / 180 * pi) - sin(slope_deg / 180 * pi) * 0
            y_trans = center_y + (x - center_x) * sin(slope_deg / 180 * pi) + 0 * cos(slope_deg / 180 * pi)

        elif self.transformationParams['aar_direction'] == 'original':

            x_trans_test = center_x_trans + (x - center_x_trans) * cos(slope_deg / 180 * pi) * sin(slope_deg / 180 * pi)
            z_trans_test = center_z_trans + (x - center_x_trans) * sin(slope_deg / 180 * pi) * cos(slope_deg / 180 * pi)

            y_trans_test = z

            print('x', x)
            print('y', z)
            print('x_trans_test', x_trans_test)
            print('z_trans_test', z_trans_test)
            print('y_trans_test', y_trans_test)

            x_trans = 1
            y_trans = 1
            z_trans = 1
        else:
            raise ValueError('Wrong AAR-Direction')


        return {'x_trans': x_trans, 'y_trans': y_trans ,'z_trans': z_trans}

    def rotatePointFeature(self, feature):

        geomFeat = feature.geometry()

        rotateGeom = self.rotationReverse(geomFeat.get().x(), geomFeat.get().y(), True)

        return rotateGeom

    def rotatePointFeatureFromOrg(self, feature):

        geomFeat = self.castMultipointGeometry(feature.geometry())

        rotateGeom = self.rotation(geomFeat.get().x(), geomFeat.get().y(), geomFeat.get().z(), True)

        return rotateGeom


    def rotateLineFeatureFromOrg(self, feature):

        geomFeat = feature.geometry()
        geomType = str(geomFeat.wkbType())[-1]

        mls = geomFeat.get()

        if geomType == '2':

            adjustGeom = QgsGeometry(mls.createEmptyWithSameType())

            pointList = []
            mls = geomFeat.get()

            for part in mls.vertices():
                try:
                    rotateGeom = self.rotation(part.x(), part.y(), part.z(), True)
                except:
                    rotateGeom = self.rotation(part.x(), part.y(), 0, True)

                zPoint = QgsPoint(rotateGeom['x_trans'], rotateGeom['z_trans'], rotateGeom['z_trans'])
                pointList.append(zPoint)

            adjustGeom.addPoints(pointList)

            return adjustGeom

        if geomType == '5':

            adjustGeom = QgsGeometry(mls.createEmptyWithSameType())

            for poly in geomFeat.parts():

                pointList = []

                #part ist QgsPoint
                for part in poly.vertices():

                    try:
                        rotateGeom = self.rotation(part.x(), part.y(), part.z(), True)
                    except:
                        rotateGeom = self.rotation(part.x(), part.y(), 0, True)

                    zPoint = QgsPoint(rotateGeom['x_trans'], rotateGeom['z_trans'], rotateGeom['z_trans'])
                    pointList.append(zPoint)

                adjustGeom.addPoints(pointList)

            return adjustGeom

    def rotatePolygonFeatureFromOrg(self, feature):

        print('rotatePolygonFeatureFromOrg', type(feature))
        geomFeat = feature.geometry()
        print('geomType', geomFeat.wkbType())

        geomType = str(geomFeat.wkbType())[-1]

        mls = geomFeat.get()

        if geomType == '3':

            adjustGeom = QgsGeometry(mls.createEmptyWithSameType())

            pointList = []
            mls = geomFeat.get()
            for part in mls.vertices():
                try:
                    rotateGeom = self.rotation(part.x(), part.y(), part.z(), True)
                except:
                    rotateGeom = self.rotation(part.x(), part.y(), 0, True)

                zPoint = QgsPoint(rotateGeom['x_trans'], rotateGeom['z_trans'], rotateGeom['z_trans'])
                pointList.append(zPoint)

            adjustGeom.addPoints(pointList)

            return adjustGeom

        if geomType == '6':

            adjustGeom = QgsGeometry(mls.createEmptyWithSameType())

            for poly in geomFeat.parts():

                pointList = []

                #part ist QgsPoint
                for part in poly.vertices():
                    try:
                        rotateGeom = self.rotation(part.x(), part.y(), part.z(), True)
                    except:
                        rotateGeom = self.rotation(part.x(), part.y(), 0, True)

                    zPoint = QgsPoint(rotateGeom['x_trans'], rotateGeom['z_trans'], rotateGeom['z_trans'])
                    pointList.append(zPoint)

                adjustGeom.addPoints(pointList)

            return adjustGeom

    def rotateLineFeature(self, feature, emptyTargetGeometry):
        print('rotateLineFeature', type(feature))

        geomFeat = feature.geometry()
        print('geomFeat.wkbType()', geomFeat.wkbType())
        if geomFeat.wkbType() == 2 or geomFeat.wkbType() == 1002 or geomFeat.wkbType() == 3002 or geomFeat.wkbType() == 1005 or geomFeat.wkbType() == 3005:

            #1 point, 2 line, 3 polygon, 5 MultiLineString,6 Multipolygon
            geomType = str(geomFeat.wkbType())[-1]
            pointList = []
            if geomType == '2':
                mls = geomFeat.get()
                for part in mls.vertices():
                    rotateGeom = self.rotationReverse(part.x(), part.y(), True)
                    if emptyTargetGeometry.wkbType() == 1002:
                        zPoint = QgsPoint(rotateGeom['x_trans'], rotateGeom['y_trans'], rotateGeom['z_trans'])
                    else:
                        zPoint = QgsPoint(rotateGeom['x_trans'], rotateGeom['y_trans'], rotateGeom['z_trans'], rotateGeom['z_trans'])

                    pointList.append(zPoint)

            if geomType == '5':

                print('geomType', geomType)

                for poly in geomFeat.parts():

                    for part in poly.vertices():

                        rotateGeom = self.rotationReverse(part.x(), part.y(), True)
                        if emptyTargetGeometry.wkbType() == 1005:
                            zPoint = QgsPoint(rotateGeom['x_trans'], rotateGeom['y_trans'], rotateGeom['z_trans'])
                        else:
                            zPoint = QgsPoint(rotateGeom['x_trans'], rotateGeom['y_trans'], rotateGeom['z_trans'], rotateGeom['z_trans'])

                        pointList.append(zPoint)

            emptyTargetGeometry = QgsGeometry.fromPolyline(pointList)

        return emptyTargetGeometry


    def rotatePolygonFeature(self, feature, emptyTargetGeometry):
        print('rotatePolygonFeature', type(feature))

        geomFeat = feature.geometry()
        #1 point, 2 line, 3 polygon, 6 Multipolygon
        geomType = str(geomFeat.wkbType())[-1]

        pointList = []
        if geomType == '3':
            mls = geomFeat.get()
            for part in mls.vertices():
                rotateGeom = self.rotationReverse(part.x(), part.y(), True)
                zPoint = QgsPoint(rotateGeom['x_trans'], rotateGeom['y_trans'], rotateGeom['z_trans'])
                pointList.append(zPoint)

        if geomType == '6':

            for poly in geomFeat.parts():

                for part in poly.vertices():
                    rotateGeom = self.rotationReverse(part.x(), part.y(), True)
                    zPoint = QgsPoint(rotateGeom['x_trans'], rotateGeom['y_trans'], rotateGeom['z_trans'])
                    pointList.append(zPoint)

        emptyTargetGeometry.addPoints(pointList)

        return emptyTargetGeometry


    def profileBuffer(self, bufferSize):
        print('profileBuffer')

        point1 = self.transformationParams['cutting_line'][0][0]
        point2 = self.transformationParams['cutting_line'][0][1]

        start_point = QgsPoint(point1[0], point1[1])
        end_point = QgsPoint(point2[0], point2[1])

        lineGeom = QgsGeometry.fromPolyline([start_point, end_point])
        bufferGeom = lineGeom.buffer(bufferSize, 5)

        return bufferGeom


    ## \brief cast multipoint geometries to single point geometries
    #
    #
    def castMultipointGeometry(self, geom):

        geoType = geom.wkbType()

        #PointZ or PointZM
        if geoType == 1001 or geoType == 3001:
            return geom
        else:
            ret_geom = geom.coerceToType(3001)
            return ret_geom[0]
