from math import pi, cos, sin, tan, atan

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
        center_x = self.transformationParams['center_x']
        center_y = self.transformationParams['center_y']
        center_z = self.transformationParams['center_z']

        x_trans = center_x + (x - center_x) * cos(slope_deg / 180 * pi) - sin(slope_deg / 180 * pi) * (y - center_y)

        y_trans = center_y + (x - center_x) * sin(slope_deg / 180 * pi) + (y - center_y) * cos(slope_deg / 180 * pi)


        if zAdaption is True:
            z_trans = z + center_y - center_z
        else:
            z_trans = z

        return {'x_trans': x_trans, 'y_trans': y_trans ,'z_trans': z_trans}

    #Profil zu Karte
    def rotationReverse(self, x, z, zAdaption):

        slope_deg = self.transformationParams['slope_deg'] * (-1)
        center_x = self.transformationParams['center_x']
        center_y = self.transformationParams['center_y']
        z_slope = 1 #self.transformationParams['z_slope'] -- geht nicht mit dem Neigungswinkel
        z_intercept = self.transformationParams['z_intercept']

        x_trans = center_x + (x - center_x) * cos(slope_deg / 180 * pi) - sin(slope_deg / 180 * pi) * 0

        y_trans = center_y + (x - center_x) * sin(slope_deg / 180 * pi) + 0 * cos(slope_deg / 180 * pi)

        if zAdaption is True:
            z_trans = z_slope * z - z_intercept
        else:
            z_trans = z

        return {'x_trans': x_trans, 'y_trans': y_trans ,'z_trans': z_trans}


    def rotatePointFeature(self, feature):

        geomFeat = feature.geometry()

        rotateGeom = self.rotationReverse(geomFeat.get().x(), geomFeat.get().y(), True)

        return rotateGeom

    def rotatePointFeatureFromOrg(self, feature):

        geomFeat = feature.geometry()

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
        #geomFeat.convertToSingleType()

        mls = geomFeat.get()
        #print('geomFeat', type(geomFeat))
        #print('mls', type(mls))

        if geomType == '3':

            adjustGeom = QgsGeometry(mls.createEmptyWithSameType())

            pointList = []
            mls = geomFeat.get()
            #print('test', mls.vertices())
            for part in mls.vertices():
                try:
                    rotateGeom = self.rotation(part.x(), part.y(), part.z(), True)
                except:
                    rotateGeom = self.rotation(part.x(), part.y(), 0, True)

                zPoint = QgsPoint(rotateGeom['x_trans'], rotateGeom['z_trans'], rotateGeom['z_trans'])
                pointList.append(zPoint)

            print('pointList', pointList)

            adjustGeom.addPoints(pointList)
            print('adjustGeom', adjustGeom)
            #provGeom = layer.dataProvider().convertToProviderType(adjustGeom)

            return adjustGeom

        if geomType == '6':
            print('hier ist 6')
            print('geomType', geomType)

            #adjustGeom = geomFeat.get().clone()

            adjustGeom = QgsGeometry(mls.createEmptyWithSameType())
            print('adjustGeom_org', adjustGeom)

            #print('poly getConst', poly.getConst())
            #print('poly getConst type', type(poly.getConst()))
            for poly in geomFeat.parts():
                print('poly', poly)
                print('poly type', type(poly))

                pointList = []

                #part ist QgsPoint
                for part in poly.vertices():
                    print('part', part)
                    print('part type', type(part))
                    try:
                        rotateGeom = self.rotation(part.x(), part.y(), part.z(), True)
                    except:
                        rotateGeom = self.rotation(part.x(), part.y(), 0, True)

                    print('part_neu', part)
                    print('part type neu', type(part))
                    zPoint = QgsPoint(rotateGeom['x_trans'], rotateGeom['z_trans'], rotateGeom['z_trans'])
                    pointList.append(zPoint)


                print('pointList', pointList)

                adjustGeom.addPoints(pointList)

                print('adjustGeom', adjustGeom)

            #adjustGeom.addPart(adjustPart)
            print('adjustGeom', adjustGeom)
            #provGeom = layer.dataProvider().convertToProviderType(adjustGeom)

            return adjustGeom

    def rotateLineFeature(self, feature, emptyTargetGeometry):
        print('rotateLineFeature', type(feature))

        geomFeat = feature.geometry()
        print('geomFeat.wkbType()', geomFeat.wkbType())
        if geomFeat.wkbType() == 2 or geomFeat.wkbType() == 1002 or geomFeat.wkbType() == 3002 or geomFeat.wkbType() == 1005 or geomFeat.wkbType() == 3005:

            #1 point, 2 line, 3 polygon, 5 MultiLineString,6 Multipolygon
            geomType = str(geomFeat.wkbType())[-1]
            print('geomType', geomFeat.wkbType())
            print('geomType', geomFeat.wkbType())
            print('emptyTargetGeometry', emptyTargetGeometry.wkbType())
            #emptyTargetGeometry.convertToSingleType()
            print('emptyTargetGeometry_singlle', emptyTargetGeometry.wkbType())

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
                    print('poly', poly)
                    print('poly type', type(poly))

                    for part in poly.vertices():
                        print('part', part)
                        print('part type', type(part))
                        rotateGeom = self.rotationReverse(part.x(), part.y(), True)
                        if emptyTargetGeometry.wkbType() == 1005:
                            zPoint = QgsPoint(rotateGeom['x_trans'], rotateGeom['y_trans'], rotateGeom['z_trans'])
                        else:
                            zPoint = QgsPoint(rotateGeom['x_trans'], rotateGeom['y_trans'], rotateGeom['z_trans'], rotateGeom['z_trans'])

                        pointList.append(zPoint)

            print('pointList', pointList)

            #emptyTargetGeometry.addPoints(pointList)

            emptyTargetGeometry = QgsGeometry.fromPolyline(pointList)

            print('emptyTargetGeometry', emptyTargetGeometry)

        else:
            pass
            #self.dialogInstance.messageBar.pushMessage("Error", "Geometrietypen(ist: "+str(geomFeat.wkbType())+") müssen Z oder ZM sein", level=1, duration=3)


        return emptyTargetGeometry


    def rotatePolygonFeature(self, feature, emptyTargetGeometry):
        print('rotatePolygonFeature', type(feature))

        geomFeat = feature.geometry()
        #geomFeat.convertToSingleType()

        #1 point, 2 line, 3 polygon, 6 Multipolygon
        geomType = str(geomFeat.wkbType())[-1]
        print('geomType', geomFeat.wkbType())
        print('geomType', geomFeat.wkbType())
        print('emptyTargetGeometry', emptyTargetGeometry.wkbType())
        #emptyTargetGeometry.convertToSingleType()
        print('emptyTargetGeometry_singlle', emptyTargetGeometry.wkbType())

        pointList = []
        if geomType == '3':
            mls = geomFeat.get()
            #print('test', mls.vertices())
            for part in mls.vertices():
                rotateGeom = self.rotationReverse(part.x(), part.y(), True)
                zPoint = QgsPoint(rotateGeom['x_trans'], rotateGeom['y_trans'], rotateGeom['z_trans'])
                pointList.append(zPoint)

        if geomType == '6':

            print('geomType', geomType)
            #print('poly getConst', poly.getConst())
            #print('poly getConst type', type(poly.getConst()))
            for poly in geomFeat.parts():
                print('poly', poly)
                print('poly type', type(poly))

                #mls = poly.get()
                #print('mls', mls)
                #print('mls type', type(mls))
                for part in poly.vertices():
                    print('part', part)
                    print('part type', type(part))
                    rotateGeom = self.rotationReverse(part.x(), part.y(), True)
                    zPoint = QgsPoint(rotateGeom['x_trans'], rotateGeom['y_trans'], rotateGeom['z_trans'])
                    pointList.append(zPoint)

        print('pointList', pointList)

        emptyTargetGeometry.addPoints(pointList)

        print('emptyTargetGeometry', emptyTargetGeometry)

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
