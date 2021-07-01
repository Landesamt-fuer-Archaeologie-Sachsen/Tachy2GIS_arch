# -*- coding: utf-8 -*-
import os

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
                'usage': pointObj[6]
            })

        print('self.aarPoints', self.aarPoints)


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
                                        'aar_z': aarObj['z']
                                    })
        return georefData
