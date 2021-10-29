from math import pi, cos, sin, tan, atan

from qgis.core import QgsWkbTypes, QgsGeometry, QgsPoint, QgsPointXY



class RotationCoords():

    def __init__(self):

        self.transformationParams = None

    def setAarTransformationParams(self, params):

        print('setAarTransformationParams', params)

        self.transformationParams = params

    def rotation(self, x, y, z, zAdaption):

        slope_deg = self.transformationParams['slope_deg']
        center_x = self.transformationParams['center_x']
        center_y = self.transformationParams['center_y']
        center_z = self.transformationParams['center_z']
        z_slope = self.transformationParams['z_slope']
        z_intercept = self.transformationParams['z_intercept']

        x_trans = center_x + (x - center_x) * cos(slope_deg / 180 * pi) - sin(slope_deg / 180 * pi) * (y - center_y)

        y_trans = center_y + (x - center_x) * sin(slope_deg / 180 * pi) + (y - center_y) * cos(slope_deg / 180 * pi)

        if zAdaption is True:
            z_trans = z + center_y - center_z
        else:
            z_trans = z

        return {'x_trans': x_trans, 'y_trans': y_trans ,'z_trans': z_trans}

    def rotationReverse(self, x, z, zAdaption):

        slope_deg = self.transformationParams['slope_deg'] * (-1)
        center_x = self.transformationParams['center_x']
        center_y = self.transformationParams['center_y']
        z_slope = self.transformationParams['z_slope']
        z_intercept = self.transformationParams['z_intercept']

        x_trans = center_x + (x - center_x) * cos(slope_deg / 180 * pi) - sin(slope_deg / 180 * pi) * 0

        y_trans = center_y + (x - center_x) * sin(slope_deg / 180 * pi) + 0 * cos(slope_deg / 180 * pi)

        if zAdaption is True:
            z_trans = z_slope * z - z_intercept
        else:
            z_trans = z

        return {'x_trans': x_trans, 'y_trans': y_trans ,'z_trans': z_trans}

    def rotatePointFeature(self, feature):
        #print(type(feature))

        geomFeat = feature.geometry()

        rotateGeom = self.rotationReverse(geomFeat.get().x(), geomFeat.get().y(), True)

        return rotateGeom

    def rotatePointFeatureFromOrg(self, feature):

        geomFeat = feature.geometry()

        rotateGeom = self.rotation(geomFeat.get().x(), geomFeat.get().y(), geomFeat.get().z(), True)

        return rotateGeom

    def rotateLineFeatureFromOrg(self, feature):

        print('rotateLineFeature', type(feature))

        geomFeat = feature.geometry()
        print('geomType', geomFeat.wkbType())
        geomFeat.convertToSingleType()
        geomFeatPoly = geomFeat.asPolyline()

        pointList = []

        for part in geomFeatPoly:
            try:
                rotateGeom = self.rotation(part.x(), part.y(), part.z(), True)
            except:
                rotateGeom = self.rotation(part.x(), part.y(), 0, True)

            zPoint = QgsPoint(rotateGeom['x_trans'], rotateGeom['z_trans'], rotateGeom['z_trans'])
            pointList.append(zPoint)

        polyline = QgsGeometry.fromPolyline(pointList)
        return polyline

    def rotateLineFeature(self, feature):
        print('rotateLineFeature', type(feature))

        geomFeat = feature.geometry()
        geomFeatPoly = geomFeat.asPolyline()

        pointList = []

        for part in geomFeatPoly:
            rotateGeom = self.rotationReverse(part.x(), part.y(), True)

            zPoint = QgsPoint(rotateGeom['x_trans'], rotateGeom['y_trans'], rotateGeom['z_trans'])
            pointList.append(zPoint)

        polyline = QgsGeometry.fromPolyline(pointList)
        return polyline

    def rotatePolygonFeatureFromOrg(self, feature):

        print('rotatePolygonFeature', type(feature))

        geomFeat = feature.geometry()
        print('geomType', geomFeat.wkbType())
        geomFeat.convertToSingleType()

        mls = geomFeat.get()
        print('geomFeat', type(geomFeat))
        print('mls', type(mls))

        adjustGeom = QgsGeometry(mls.createEmptyWithSameType())

        pointList = []

        for part in mls.vertices():
            try:
                rotateGeom = self.rotation(part.x(), part.y(), part.z(), True)
            except:
                rotateGeom = self.rotation(part.x(), part.y(), 0, True)

            zPoint = QgsPoint(rotateGeom['x_trans'], rotateGeom['z_trans'], rotateGeom['z_trans'])
            pointList.append(zPoint)

        print('pointList', pointList)

        adjustGeom.addPoints(pointList)
        #provGeom = layer.dataProvider().convertToProviderType(adjustGeom)

        #polyline = QgsGeometry.fromPolyline(pointList)
        #retGeom = polyline.asPolygon()
        #print('adjustGeom', adjustGeom)
        return adjustGeom

    def rotatePolygonFeature(self, feature):
        print('rotatePolygonFeature', type(feature))

        geomFeat = feature.geometry()

        print('asMultiPolygon', geomFeat.asMultiPolygon())
        geomFeatPoly = geomFeat.asMultiPolygon()

        pointList = []
        for singlePoly in geomFeatPoly[0]:
            for part in singlePoly:
                rotateGeom = self.rotationReverse(part.x(), part.y(), True)

                zPoint = QgsPoint(rotateGeom['x_trans'], rotateGeom['y_trans'], rotateGeom['z_trans'])
                pointList.append(zPoint)

        polyline = QgsGeometry.fromPolyline(pointList)

        return polyline

    def profileBuffer(self, bufferSize):
        print('profileBuffer')

        point1 = self.transformationParams['cutting_line'][0][0]
        point2 = self.transformationParams['cutting_line'][0][1]

        start_point = QgsPoint(point1[0], point1[1])
        end_point = QgsPoint(point2[0], point2[1])

        lineGeom = QgsGeometry.fromPolyline([start_point, end_point])
        bufferGeom = lineGeom.buffer(bufferSize, 5)

        return bufferGeom
