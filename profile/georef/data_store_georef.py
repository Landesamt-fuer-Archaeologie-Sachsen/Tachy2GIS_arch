# -*- coding: utf-8 -*-

## @brief With the TransformationDialogParambar class a bar based on QWidget is realized
#
# Inherits from QWidget
#
# @author Mario Uhlig, VisDat geodatentechnologie GmbH, mario.uhlig@visdat.de
# @date 2020-11-09

from ..publisher import Publisher

class DataStoreGeoref():

    ## The constructor.
    # Creates labels with styles
    # @param dialogInstance pointer to the dialogInstance

    def __init__(self):

        print('init_dataStore_georef')

        self.pup = Publisher()

        self.imagePoints = []

        self.targetPoints = []

        self.aarPointsHorizontal = []

        self.aarPointsOriginal = []

        self.aarPointsAbsolute = []

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


    def addTargetPoints(self, refData):

        self.targetPoints = []

        for pointObj in refData['targetGCP']['points']:

            self.targetPoints.append({
            	'uuid': pointObj['uuid'],
            	'x': pointObj['x'],
                'y': pointObj['z'],
                'z': pointObj['z']
            })


    def addAarPoints(self, aarList):
        print('jetzt_addAarPoints', aarList)

        aarDirection = aarList['aar_direction']

        if aarDirection == 'horizontal':

            self.aarPointsHorizontal = []

            #Punkte
            for pointObj in aarList['coord_trans']:

                self.aarPointsHorizontal.append({
                    'uuid': pointObj[8],
                    'ptnr': str(pointObj[7]),
                    'x': pointObj[0],
                    'y': pointObj[1],
                    'z': pointObj[2],
                    'z_org': pointObj[4],
                    'distance': pointObj[5],
                    'usage': pointObj[6]
                })

            #Transformationsparameter
            transformationParams = aarList['transformationParams']
            z_slope = aarList['linegress'][0]
            z_intercept = aarList['linegress'][1]
            transformationParams['z_slope'] = z_slope
            transformationParams['z_intercept'] = z_intercept
            transformationParams['ns_error'] = aarList['ns_error']

            self.updateAarTransformationParams(transformationParams)

        if aarDirection == 'original':
        
            self.aarPointsOriginal = []

            for pointObj in aarList['coord_trans']:

                self.aarPointsOriginal.append({
                    'uuid': pointObj[8],
                    'ptnr': str(pointObj[7]),
                    'x': pointObj[0],
                    'y': pointObj[1],
                    'z': pointObj[2],
                    'z_org': pointObj[4],
                    'distance': pointObj[5],
                    'usage': pointObj[6]
                })

        if aarDirection == 'absolute height':
        
            self.aarPointsAbsolute = []

            for pointObj in aarList['coord_trans']:

                self.aarPointsAbsolute.append({
                    'uuid': pointObj[8],
                    'ptnr': str(pointObj[7]),
                    'x': pointObj[0],
                    'y': pointObj[1],
                    'z': pointObj[2],
                    'z_org': pointObj[4],
                    'distance': pointObj[5],
                    'usage': pointObj[6]
                })


    def updateAarTransformationParams(self, params):
        self.aarTransformationParams = params

        self.pup.publish('pushTransformationParams', self.getAarTransformationParams())

    def getAarTransformationParams(self):

        return self.aarTransformationParams

    def getGeorefData(self, aarDirection):

        if aarDirection == 'horizontal':
            retPoints = self.aarPointsHorizontal

        if aarDirection == 'original':
            retPoints = self.aarPointsOriginal

        if aarDirection == 'absolute height':
            retPoints = self.aarPointsAbsolute

        georefData = []

        for aarObj in retPoints:
            if(aarObj['usage'] == 1):
                for imageObj in self.imagePoints:
                    if aarObj['uuid'] == imageObj['uuid']:
                        georefData.append({
                                        'uuid': aarObj['uuid'],
                                        'ptnr': aarObj['ptnr'],
                                        'input_x': imageObj['x'],
                                        'input_z': imageObj['z'],
                                        'aar_x': aarObj['x'],
                                        'aar_y': aarObj['y'],
                                        'aar_z': aarObj['z'],
                                        'aar_z_org': aarObj['z_org'],
                                        'aar_distance': aarObj['distance'],
                                        'aar_direction': aarDirection,
                                    })
        return georefData

    def clearStore(self):
        
        self.imagePoints = []
        self.targetPoints = []
        self.aarPointsHorizontal = []
        self.aarPointsOriginal = []
        self.aarPointsAbsolute = []
        self.aarTransformationParams = {}
