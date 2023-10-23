from math import pi, cos, sin
from qgis.core import QgsGeometry, QgsPoint

class RotationCoords():

    def __init__(self):

        self.transformationParamsHorizontal = None
        self.transformationParamsAbsolute = None
        self.transformationParamsOriginal = None

    #Transformationsparameter für jede AAR-Direction setzen
    def setAarTransformationParams(self, params):

        if params['aar_direction'] == 'horizontal':
            self.transformationParamsHorizontal = params
        if params['aar_direction'] == 'original':
            self.transformationParamsOriginal = params
        if params['aar_direction'] == 'absolute height':
            self.transformationParamsAbsolute = params

    #Karte zu Profil
    #x,y,z sind reale Punkte bspw. im Gauss-Krüger System
    def rotation(self, x, y, z, zAdaption, aar_direction):

        if aar_direction == 'horizontal':

            slope_deg = self.transformationParamsHorizontal['slope_deg']
            center_x = self.transformationParamsHorizontal['center_x']
            center_y = self.transformationParamsHorizontal['center_y']
            center_z = self.transformationParamsHorizontal['center_z']

            x_trans = center_x + (x - center_x) * cos(slope_deg / 180 * pi) - sin(slope_deg / 180 * pi) * (y - center_y)

            y_trans = center_y + (x - center_x) * sin(slope_deg / 180 * pi) + (y - center_y) * cos(slope_deg / 180 * pi)

            if zAdaption is True:
                z_trans = z + center_y - center_z
            else:
                z_trans = z

        elif aar_direction == 'absolute height':

            slope_deg = self.transformationParamsAbsolute['slope_deg']
            center_x = self.transformationParamsAbsolute['center_x']
            center_y = self.transformationParamsAbsolute['center_y']
            center_z = self.transformationParamsAbsolute['center_z']
            min_x = self.transformationParamsAbsolute['min_x']

            x_trans = center_x + (x - center_x) * cos(slope_deg / 180 * pi) - sin(slope_deg / 180 * pi) * (y - center_y)

            y_trans = center_y + (x - center_x) * sin(slope_deg / 180 * pi) + (y - center_y) * cos(slope_deg / 180 * pi)

            z_trans = z

            #Anpassung absolute height - verschieben nach x
            x_trans = x_trans - min_x

        elif aar_direction == 'original':

            slope_deg = self.transformationParamsOriginal['slope_deg']
            y_slope_deg = self.transformationParamsOriginal['y_slope_deg']
            center_x = self.transformationParamsOriginal['center_x']
            center_y = self.transformationParamsOriginal['center_y']
            center_z = self.transformationParamsOriginal['center_z']
            center_x_trans = self.transformationParamsOriginal['center_x_trans']
            center_z_trans = self.transformationParamsOriginal['center_z_trans']
            
            z = z + center_y - center_z   

            y_trans = center_y + (x - center_x) * sin(slope_deg / 180 * pi) + (y - center_y) * cos(slope_deg / 180 * pi)

            x = center_x + (x - center_x) * cos(slope_deg / 180 * pi) - sin(slope_deg / 180 * pi) * (y - center_y)

            x_trans = center_x_trans + (x - center_x_trans) * cos(y_slope_deg / 180 * pi) - (z - center_z_trans) * sin(y_slope_deg / 180 * pi)

            z_trans = center_z_trans + (x - center_x_trans) * sin(y_slope_deg / 180 * pi) + (z - center_z_trans) * cos(y_slope_deg / 180 * pi)

        else:
            print('Wrong AAR-Direction')

        return {'x_trans': x_trans, 'y_trans': y_trans ,'z_trans': z_trans}


    #Profil zu Karte
    def rotationReverse(self, x, z, zAdaption, aar_direction):

        if aar_direction == 'horizontal':

            slope_deg = self.transformationParamsHorizontal['slope_deg'] * (-1)
            center_x = self.transformationParamsHorizontal['center_x']
            center_y = self.transformationParamsHorizontal['center_y']
            z_slope = 1 #self.transformationParams['z_slope'] -- geht nicht mit dem Neigungswinkel
            z_intercept = self.transformationParamsHorizontal['z_intercept']

            if zAdaption is True:
                z_trans = z_slope * z - z_intercept
            else:
                z_trans = z         

            x_trans = center_x + (x - center_x) * cos(slope_deg / 180 * pi) - sin(slope_deg / 180 * pi) * 0
            y_trans = center_y + (x - center_x) * sin(slope_deg / 180 * pi) + 0 * cos(slope_deg / 180 * pi)   

        elif aar_direction == 'absolute height':

            slope_deg = self.transformationParamsAbsolute['slope_deg'] * (-1)
            center_x = self.transformationParamsAbsolute['center_x']
            center_y = self.transformationParamsAbsolute['center_y']
            z_slope = 1 #self.transformationParamsAbsolute['z_slope'] -- geht nicht mit dem Neigungswinkel
            z_intercept = self.transformationParamsAbsolute['z_intercept']
            min_x = self.transformationParamsAbsolute['min_x']

            #Anpassung absolute height - verschieben nach x
            x = x + min_x

            z_trans = z

            x_trans = center_x + (x - center_x) * cos(slope_deg / 180 * pi) - sin(slope_deg / 180 * pi) * 0
            y_trans = center_y + (x - center_x) * sin(slope_deg / 180 * pi) + 0 * cos(slope_deg / 180 * pi)

        elif aar_direction == 'original':

            y_slope_deg = self.transformationParamsOriginal['y_slope_deg'] * (-1)
            slope_deg = self.transformationParamsOriginal['slope_deg'] * (-1)
            center_x = self.transformationParamsOriginal['center_x']
            center_y = self.transformationParamsOriginal['center_y']
            center_z = self.transformationParamsOriginal['center_z']
            center_x_trans = self.transformationParamsOriginal['center_x_trans']
            center_z_trans = self.transformationParamsOriginal['center_z_trans']

            z1 = center_z_trans + (x - center_x_trans) * sin(y_slope_deg / 180 * pi) + (z - center_z_trans) * cos(y_slope_deg / 180 * pi)

            x1 = center_x_trans + (x - center_x_trans) * cos(y_slope_deg / 180 * pi) - (z - center_z_trans) * sin(y_slope_deg / 180 * pi)

            x2 = center_x + (x1 - center_x) * cos(slope_deg / 180 * pi)

            y1 = center_y + (x1 - center_x) * sin(slope_deg / 180 * pi)

            z2 = z1 - center_y + center_z   

            x_trans = x2
            y_trans = y1
            z_trans = z2

        else:
            raise ValueError('Wrong AAR-Direction')


        return {'x_trans': x_trans, 'y_trans': y_trans ,'z_trans': z_trans}

    def rotatePointFeature(self, feature, aar_direction):

        geomFeat = feature.geometry()

        rotateGeom = self.rotationReverse(geomFeat.get().x(), geomFeat.get().y(), True, aar_direction)

        return rotateGeom

    def rotatePointFeatureFromOrg(self, feature, aar_direction):

        geomFeat = self.castMultipointGeometry(feature.geometry())

        rotateGeom = self.rotation(geomFeat.get().x(), geomFeat.get().y(), geomFeat.get().z(), True, aar_direction)

        return rotateGeom


    def rotateLineFeatureFromOrg(self, feature, aar_direction):

        geomFeat = feature.geometry()
        geomType = str(geomFeat.wkbType())[-1]

        mls = geomFeat.get()

        if geomType == '2':

            adjustGeom = QgsGeometry(mls.createEmptyWithSameType())

            pointList = []
            mls = geomFeat.get()

            for part in mls.vertices():
                try:
                    rotateGeom = self.rotation(part.x(), part.y(), part.z(), True, aar_direction)
                except:
                    rotateGeom = self.rotation(part.x(), part.y(), 0, True, aar_direction)

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
                        rotateGeom = self.rotation(part.x(), part.y(), part.z(), True, aar_direction)
                    except:
                        rotateGeom = self.rotation(part.x(), part.y(), 0, True, aar_direction)

                    zPoint = QgsPoint(rotateGeom['x_trans'], rotateGeom['z_trans'], rotateGeom['z_trans'])
                    pointList.append(zPoint)

                adjustGeom.addPoints(pointList)

            return adjustGeom

    def rotatePolygonFeatureFromOrg(self, feature, aar_direction):

        geomFeat = feature.geometry()

        geomType = str(geomFeat.wkbType())[-1]

        mls = geomFeat.get()

        if geomType == '3':

            adjustGeom = QgsGeometry(mls.createEmptyWithSameType())

            pointList = []
            mls = geomFeat.get()
            for part in mls.vertices():
                try:
                    rotateGeom = self.rotation(part.x(), part.y(), part.z(), True, aar_direction)
                except:
                    rotateGeom = self.rotation(part.x(), part.y(), 0, True, aar_direction)

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
                        rotateGeom = self.rotation(part.x(), part.y(), part.z(), True, aar_direction)
                    except:
                        rotateGeom = self.rotation(part.x(), part.y(), 0, True, aar_direction)

                    zPoint = QgsPoint(rotateGeom['x_trans'], rotateGeom['z_trans'], rotateGeom['z_trans'])
                    pointList.append(zPoint)

                adjustGeom.addPoints(pointList)

            return adjustGeom

    def rotateLineFeature(self, feature, emptyTargetGeometry, aar_direction):

        geomFeat = feature.geometry()
        if geomFeat.wkbType() == 2 or geomFeat.wkbType() == 1002 or geomFeat.wkbType() == 3002 or geomFeat.wkbType() == 1005 or geomFeat.wkbType() == 3005:

            #1 point, 2 line, 3 polygon, 5 MultiLineString,6 Multipolygon
            geomType = str(geomFeat.wkbType())[-1]
            pointList = []
            if geomType == '2':
                mls = geomFeat.get()
                for part in mls.vertices():
                    rotateGeom = self.rotationReverse(part.x(), part.y(), True, aar_direction)
                    if emptyTargetGeometry.wkbType() == 1002:
                        zPoint = QgsPoint(rotateGeom['x_trans'], rotateGeom['y_trans'], rotateGeom['z_trans'])
                    else:
                        zPoint = QgsPoint(rotateGeom['x_trans'], rotateGeom['y_trans'], rotateGeom['z_trans'], rotateGeom['z_trans'])

                    pointList.append(zPoint)

            if geomType == '5':

                for poly in geomFeat.parts():

                    for part in poly.vertices():

                        rotateGeom = self.rotationReverse(part.x(), part.y(), True, aar_direction)
                        if emptyTargetGeometry.wkbType() == 1005:
                            zPoint = QgsPoint(rotateGeom['x_trans'], rotateGeom['y_trans'], rotateGeom['z_trans'])
                        else:
                            zPoint = QgsPoint(rotateGeom['x_trans'], rotateGeom['y_trans'], rotateGeom['z_trans'], rotateGeom['z_trans'])

                        pointList.append(zPoint)

            emptyTargetGeometry = QgsGeometry.fromPolyline(pointList)

        return emptyTargetGeometry


    def rotatePolygonFeature(self, feature, emptyTargetGeometry, aar_direction):

        geomFeat = feature.geometry()
        #1 point, 2 line, 3 polygon, 6 Multipolygon
        geomType = str(geomFeat.wkbType())[-1]

        pointList = []
        if geomType == '3':
            mls = geomFeat.get()
            for part in mls.vertices():
                rotateGeom = self.rotationReverse(part.x(), part.y(), True, aar_direction)
                zPoint = QgsPoint(rotateGeom['x_trans'], rotateGeom['y_trans'], rotateGeom['z_trans'])
                pointList.append(zPoint)

        if geomType == '6':

            for poly in geomFeat.parts():

                for part in poly.vertices():
                    rotateGeom = self.rotationReverse(part.x(), part.y(), True, aar_direction)
                    zPoint = QgsPoint(rotateGeom['x_trans'], rotateGeom['y_trans'], rotateGeom['z_trans'])
                    pointList.append(zPoint)

        emptyTargetGeometry.addPoints(pointList)

        return emptyTargetGeometry


    def profileBuffer(self, bufferSize, aar_direction):

        if aar_direction == 'original':
            point1 = self.transformationParamsOriginal['cutting_line'][0][0]
            point2 = self.transformationParamsOriginal['cutting_line'][0][1]
        
        if aar_direction == 'horizontal':
            point1 = self.transformationParamsHorizontal['cutting_line'][0][0]
            point2 = self.transformationParamsHorizontal['cutting_line'][0][1]

        if aar_direction == 'absolute height':
            point1 = self.transformationParamsAbsolute['cutting_line'][0][0]
            point2 = self.transformationParamsAbsolute['cutting_line'][0][1]

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

from math import pi, cos, sin
from qgis.core import QgsGeometry, QgsPoint

class RotationCoords():

    def __init__(self):

        self.transformationParamsHorizontal = None
        self.transformationParamsAbsolute = None
        self.transformationParamsOriginal = None

    #Transformationsparameter für jede AAR-Direction setzen
    def setAarTransformationParams(self, params):

        if params['aar_direction'] == 'horizontal':
            self.transformationParamsHorizontal = params
        if params['aar_direction'] == 'original':
            self.transformationParamsOriginal = params
        if params['aar_direction'] == 'absolute height':
            self.transformationParamsAbsolute = params

    #Karte zu Profil
    #x,y,z sind reale Punkte bspw. im Gauss-Krüger System
    def rotation(self, x, y, z, zAdaption, aar_direction):

        if aar_direction == 'horizontal':

            slope_deg = self.transformationParamsHorizontal['slope_deg']
            center_x = self.transformationParamsHorizontal['center_x']
            center_y = self.transformationParamsHorizontal['center_y']
            center_z = self.transformationParamsHorizontal['center_z']

            x_trans = center_x + (x - center_x) * cos(slope_deg / 180 * pi) - sin(slope_deg / 180 * pi) * (y - center_y)

            y_trans = center_y + (x - center_x) * sin(slope_deg / 180 * pi) + (y - center_y) * cos(slope_deg / 180 * pi)

            if zAdaption is True:
                z_trans = z + center_y - center_z
            else:
                z_trans = z

        elif aar_direction == 'absolute height':

            slope_deg = self.transformationParamsAbsolute['slope_deg']
            center_x = self.transformationParamsAbsolute['center_x']
            center_y = self.transformationParamsAbsolute['center_y']
            center_z = self.transformationParamsAbsolute['center_z']
            min_x = self.transformationParamsAbsolute['min_x']

            x_trans = center_x + (x - center_x) * cos(slope_deg / 180 * pi) - sin(slope_deg / 180 * pi) * (y - center_y)

            y_trans = center_y + (x - center_x) * sin(slope_deg / 180 * pi) + (y - center_y) * cos(slope_deg / 180 * pi)

            z_trans = z

            #Anpassung absolute height - verschieben nach x
            x_trans = x_trans - min_x

        elif aar_direction == 'original':

            slope_deg = self.transformationParamsOriginal['slope_deg']
            y_slope_deg = self.transformationParamsOriginal['y_slope_deg']
            center_x = self.transformationParamsOriginal['center_x']
            center_y = self.transformationParamsOriginal['center_y']
            center_z = self.transformationParamsOriginal['center_z']
            center_x_trans = self.transformationParamsOriginal['center_x_trans']
            center_z_trans = self.transformationParamsOriginal['center_z_trans']
            
            z = z + center_y - center_z   

            y_trans = center_y + (x - center_x) * sin(slope_deg / 180 * pi) + (y - center_y) * cos(slope_deg / 180 * pi)

            x = center_x + (x - center_x) * cos(slope_deg / 180 * pi) - sin(slope_deg / 180 * pi) * (y - center_y)

            x_trans = center_x_trans + (x - center_x_trans) * cos(y_slope_deg / 180 * pi) - (z - center_z_trans) * sin(y_slope_deg / 180 * pi)

            z_trans = center_z_trans + (x - center_x_trans) * sin(y_slope_deg / 180 * pi) + (z - center_z_trans) * cos(y_slope_deg / 180 * pi)

        else:
            print('Wrong AAR-Direction')

        return {'x_trans': x_trans, 'y_trans': y_trans ,'z_trans': z_trans}


    #Profil zu Karte
    def rotationReverse(self, x, z, zAdaption, aar_direction):

        if aar_direction == 'horizontal':

            slope_deg = self.transformationParamsHorizontal['slope_deg'] * (-1)
            center_x = self.transformationParamsHorizontal['center_x']
            center_y = self.transformationParamsHorizontal['center_y']
            z_slope = 1 #self.transformationParams['z_slope'] -- geht nicht mit dem Neigungswinkel
            z_intercept = self.transformationParamsHorizontal['z_intercept']

            if zAdaption is True:
                z_trans = z_slope * z - z_intercept
            else:
                z_trans = z         

            x_trans = center_x + (x - center_x) * cos(slope_deg / 180 * pi) - sin(slope_deg / 180 * pi) * 0
            y_trans = center_y + (x - center_x) * sin(slope_deg / 180 * pi) + 0 * cos(slope_deg / 180 * pi)   

        elif aar_direction == 'absolute height':

            slope_deg = self.transformationParamsAbsolute['slope_deg'] * (-1)
            center_x = self.transformationParamsAbsolute['center_x']
            center_y = self.transformationParamsAbsolute['center_y']
            z_slope = 1 #self.transformationParamsAbsolute['z_slope'] -- geht nicht mit dem Neigungswinkel
            z_intercept = self.transformationParamsAbsolute['z_intercept']
            min_x = self.transformationParamsAbsolute['min_x']

            #Anpassung absolute height - verschieben nach x
            x = x + min_x

            z_trans = z

            x_trans = center_x + (x - center_x) * cos(slope_deg / 180 * pi) - sin(slope_deg / 180 * pi) * 0
            y_trans = center_y + (x - center_x) * sin(slope_deg / 180 * pi) + 0 * cos(slope_deg / 180 * pi)

        elif aar_direction == 'original':

            y_slope_deg = self.transformationParamsOriginal['y_slope_deg'] * (-1)
            slope_deg = self.transformationParamsOriginal['slope_deg'] * (-1)
            center_x = self.transformationParamsOriginal['center_x']
            center_y = self.transformationParamsOriginal['center_y']
            center_z = self.transformationParamsOriginal['center_z']
            center_x_trans = self.transformationParamsOriginal['center_x_trans']
            center_z_trans = self.transformationParamsOriginal['center_z_trans']

            z1 = center_z_trans + (x - center_x_trans) * sin(y_slope_deg / 180 * pi) + (z - center_z_trans) * cos(y_slope_deg / 180 * pi)

            x1 = center_x_trans + (x - center_x_trans) * cos(y_slope_deg / 180 * pi) - (z - center_z_trans) * sin(y_slope_deg / 180 * pi)

            x2 = center_x + (x1 - center_x) * cos(slope_deg / 180 * pi)

            y1 = center_y + (x1 - center_x) * sin(slope_deg / 180 * pi)

            z2 = z1 - center_y + center_z   

            x_trans = x2
            y_trans = y1
            z_trans = z2

        else:
            raise ValueError('Wrong AAR-Direction')


        return {'x_trans': x_trans, 'y_trans': y_trans ,'z_trans': z_trans}

    def rotatePointFeature(self, feature, aar_direction):

        geomFeat = feature.geometry()

        rotateGeom = self.rotationReverse(geomFeat.get().x(), geomFeat.get().y(), True, aar_direction)

        return rotateGeom

    def rotatePointFeatureFromOrg(self, feature, aar_direction):

        geomFeat = self.castMultipointGeometry(feature.geometry())

        rotateGeom = self.rotation(geomFeat.get().x(), geomFeat.get().y(), geomFeat.get().z(), True, aar_direction)

        return rotateGeom


    def rotateLineFeatureFromOrg(self, feature, aar_direction):

        geomFeat = feature.geometry()
        geomType = str(geomFeat.wkbType())[-1]

        mls = geomFeat.get()

        if geomType == '2':

            adjustGeom = QgsGeometry(mls.createEmptyWithSameType())

            pointList = []
            mls = geomFeat.get()

            for part in mls.vertices():
                try:
                    rotateGeom = self.rotation(part.x(), part.y(), part.z(), True, aar_direction)
                except:
                    rotateGeom = self.rotation(part.x(), part.y(), 0, True, aar_direction)

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
                        rotateGeom = self.rotation(part.x(), part.y(), part.z(), True, aar_direction)
                    except:
                        rotateGeom = self.rotation(part.x(), part.y(), 0, True, aar_direction)

                    zPoint = QgsPoint(rotateGeom['x_trans'], rotateGeom['z_trans'], rotateGeom['z_trans'])
                    pointList.append(zPoint)

                adjustGeom.addPoints(pointList)

            return adjustGeom

    def rotatePolygonFeatureFromOrg(self, feature, aar_direction):

        geomFeat = feature.geometry()

        geomType = str(geomFeat.wkbType())[-1]

        mls = geomFeat.get()

        if geomType == '3':

            adjustGeom = QgsGeometry(mls.createEmptyWithSameType())

            pointList = []
            mls = geomFeat.get()
            for part in mls.vertices():
                try:
                    rotateGeom = self.rotation(part.x(), part.y(), part.z(), True, aar_direction)
                except:
                    rotateGeom = self.rotation(part.x(), part.y(), 0, True, aar_direction)

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
                        rotateGeom = self.rotation(part.x(), part.y(), part.z(), True, aar_direction)
                    except:
                        rotateGeom = self.rotation(part.x(), part.y(), 0, True, aar_direction)

                    zPoint = QgsPoint(rotateGeom['x_trans'], rotateGeom['z_trans'], rotateGeom['z_trans'])
                    pointList.append(zPoint)

                adjustGeom.addPoints(pointList)

            return adjustGeom

    def rotateLineFeature(self, feature, emptyTargetGeometry, aar_direction):

        geomFeat = feature.geometry()
        if geomFeat.wkbType() == 2 or geomFeat.wkbType() == 1002 or geomFeat.wkbType() == 3002 or geomFeat.wkbType() == 1005 or geomFeat.wkbType() == 3005:

            #1 point, 2 line, 3 polygon, 5 MultiLineString,6 Multipolygon
            geomType = str(geomFeat.wkbType())[-1]
            pointList = []
            if geomType == '2':
                mls = geomFeat.get()
                for part in mls.vertices():
                    rotateGeom = self.rotationReverse(part.x(), part.y(), True, aar_direction)
                    if emptyTargetGeometry.wkbType() == 1002:
                        zPoint = QgsPoint(rotateGeom['x_trans'], rotateGeom['y_trans'], rotateGeom['z_trans'])
                    else:
                        zPoint = QgsPoint(rotateGeom['x_trans'], rotateGeom['y_trans'], rotateGeom['z_trans'], rotateGeom['z_trans'])

                    pointList.append(zPoint)

            if geomType == '5':

                for poly in geomFeat.parts():

                    for part in poly.vertices():

                        rotateGeom = self.rotationReverse(part.x(), part.y(), True, aar_direction)
                        if emptyTargetGeometry.wkbType() == 1005:
                            zPoint = QgsPoint(rotateGeom['x_trans'], rotateGeom['y_trans'], rotateGeom['z_trans'])
                        else:
                            zPoint = QgsPoint(rotateGeom['x_trans'], rotateGeom['y_trans'], rotateGeom['z_trans'], rotateGeom['z_trans'])

                        pointList.append(zPoint)

            emptyTargetGeometry = QgsGeometry.fromPolyline(pointList)

        return emptyTargetGeometry


    def rotatePolygonFeature(self, feature, emptyTargetGeometry, aar_direction):

        geomFeat = feature.geometry()
        #1 point, 2 line, 3 polygon, 6 Multipolygon
        geomType = str(geomFeat.wkbType())[-1]

        pointList = []
        if geomType == '3':
            mls = geomFeat.get()
            for part in mls.vertices():
                rotateGeom = self.rotationReverse(part.x(), part.y(), True, aar_direction)
                zPoint = QgsPoint(rotateGeom['x_trans'], rotateGeom['y_trans'], rotateGeom['z_trans'])
                pointList.append(zPoint)

        if geomType == '6':

            for poly in geomFeat.parts():

                for part in poly.vertices():
                    rotateGeom = self.rotationReverse(part.x(), part.y(), True, aar_direction)
                    zPoint = QgsPoint(rotateGeom['x_trans'], rotateGeom['y_trans'], rotateGeom['z_trans'])
                    pointList.append(zPoint)

        emptyTargetGeometry.addPoints(pointList)

        return emptyTargetGeometry


    def profileBuffer(self, bufferSize, aar_direction):

        if aar_direction == 'original':
            point1 = self.transformationParamsOriginal['cutting_line'][0][0]
            point2 = self.transformationParamsOriginal['cutting_line'][0][1]
        
        if aar_direction == 'horizontal':
            point1 = self.transformationParamsHorizontal['cutting_line'][0][0]
            point2 = self.transformationParamsHorizontal['cutting_line'][0][1]

        if aar_direction == 'absolute height':
            point1 = self.transformationParamsAbsolute['cutting_line'][0][0]
            point2 = self.transformationParamsAbsolute['cutting_line'][0][1]

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
