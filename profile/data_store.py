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
            for statePoint in self.imagePoints:
                if statePoint['uuid'] == pointObj['uuid']:
                    statePoint['x'] = pointObj['x']
                    statePoint['z'] = pointObj['z']
                else:
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


    def addAarPoints(self, pointList):
        print('add_aar_points')
