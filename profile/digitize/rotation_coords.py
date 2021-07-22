from math import pi, cos, sin, tan, atan

class RotationCoords():

    def __init__(self, dataStore):

        print('init RotationCoords')

        #DataStore
        self.dataStore = dataStore


    def rotationReverse(self, x, y, z, zAdaption):

        print('startRotation')
        transformationParams = self.dataStore.getAarTransformationParams()

        slope_deg = transformationParams['slope_deg'] * (-1)
        center_x = transformationParams['center_x']
        center_y = transformationParams['center_y']
        z_slope = transformationParams['z_slope']
        #z_slope = tan((-90-(((atan(transformationParams['z_slope']) * 180) / pi))) * pi / 180)
        z_intercept = transformationParams['z_intercept']


        x_trans = center_x + (x - center_x) * cos(slope_deg / 180 * pi) - sin(slope_deg / 180 * pi) * (y - center_y)
        y_trans = center_y + (x - center_x) * sin(slope_deg / 180 * pi) + (y - center_y) * cos(slope_deg / 180 * pi)

        if zAdaption is True:
            print('z_slope', z_slope)
            print('z', z)
            print('z_intercept', z_intercept)
            z_trans = z_slope * z + z_intercept
        else:
            z_trans = z

        return {'x_trans': x_trans, 'y_trans': y_trans ,'z_trans': z_trans}
