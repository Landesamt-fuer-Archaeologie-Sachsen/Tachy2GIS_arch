# -*- coding: utf-8 -*-

## @brief With the TransformationDialogParambar class a bar based on QWidget is realized
#
# Inherits from QWidget
#
# @author Mario Uhlig, VisDat geodatentechnologie GmbH, mario.uhlig@visdat.de
# @date 2020-11-09

class DataStore():

    ## The constructor.
    # Creates labels with styles
    # @param dialogInstance pointer to the dialogInstance

    def __init__(self):

        print('init_dataStore')

        self.imagePoints = []

        self.targetPoints = []

        self.aarPoints = []

        self.aarTransformationParams = {}


    ## \brief Add image point
    #
    # @param pointObj is a dictionary e.G.:
    #  \code{.py}
    # {
    #   'uuid': '{ff4533b8-2e88-4f52-ac24-bb98c345c90b}',
    #   'x': 231.0,
    #   'z': -228.0
    # }
    #  \endcode
    #
    def addImagePoint(self, pointObj):

        print('pointObj', pointObj)

        if len(self.imagePoints) == 0:

            self.imagePoints.append({
            	'uuid': pointObj['uuid'],
            	'x': pointObj['x'],
                'z': pointObj['z']
            })
        else:
            checker = False
            for statePoint in self.imagePoints:
                print('statePoint', statePoint['uuid'])
                print('pointObj', pointObj['uuid'])
                if statePoint['uuid'] == pointObj['uuid']:
                    statePoint['x'] = pointObj['x']
                    statePoint['z'] = pointObj['z']
                    checker = True

            if checker == False:
                self.imagePoints.append({
                	'uuid': pointObj['uuid'],
                	'x': pointObj['x'],
                    'z': pointObj['z']
                })

        print('self.imagePoints', self.imagePoints)


    def addTargetPoints(self, refData):

        self.targetPoints = []

        for pointObj in refData['targetGCP']['points']:

            self.targetPoints.append({
            	'uuid': pointObj['uuid'],
            	'x': pointObj['x'],
                'y': pointObj['z'],
                'z': pointObj['z']
            })

        print('self.targetPoints', self.targetPoints)


    def addAarPoints(self, aarList):
        print('add_aar_points', aarList)
        self.aarPoints = []

        for pointObj in aarList['coord_trans']:

            self.aarPoints.append({
            	'uuid': pointObj[8],
            	'x': pointObj[0],
                'y': pointObj[1],
                'z': pointObj[2],
                'z_org': pointObj[3],
                'usage': pointObj[6]
            })

        print('self.aarPoints', self.aarPoints)
        transformationParams = aarList['transformationParams']

        z_slope = aarList['linegress'][0]

        z_intercept = aarList['linegress'][1]

        transformationParams['z_slope'] = z_slope
        transformationParams['z_intercept'] = z_intercept

        self.updateAarTransformationParams(transformationParams)

    def updateAarTransformationParams(self, params):

        self.aarTransformationParams = params

        print('self.aarTransformationParams', self.aarTransformationParams)

    def getAarTransformationParams(self):

        return self.aarTransformationParams

    def getGeorefData(self):

        georefData = []

        for aarObj in self.aarPoints:
            if(aarObj['usage'] == 1):
                for imageObj in self.imagePoints:
                    if aarObj['uuid'] == imageObj['uuid']:
                        georefData.append({
                                        'uuid': aarObj['uuid'],
                                        'input_x': imageObj['x'],
                                        'input_z': imageObj['z'],
                                        'aar_x': aarObj['x'],
                                        'aar_y': aarObj['y'],
                                        'aar_z': aarObj['z'],
                                        'aar_z_org': aarObj['z_org'],
                                    })
        return georefData
