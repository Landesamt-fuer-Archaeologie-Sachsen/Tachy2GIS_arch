# -*- coding: utf-8 -*-

"""

/***************************************************************************

 profileAARDialog

                                 A QGIS plugin

 profileAAR des

                             -------------------

        begin                : 2019-02-06

        git sha              : $Format:%H$

        copyright            : (C) 2019 by Moritz Mennenga / Kay Schmuetz

        email                : mennenga@nihk.de

 ***************************************************************************/



/***************************************************************************

 *                                                                         *

 *                                                                         '

 ' A QGIS-Plugin by members of                                             '

 '          ISAAK (https://isaakiel.github.io/)                            '

 '           Lower Saxony Institute for Historical Coastal Research        '

 '           University of Kiel                                            '

 '   This program is free software; you can redistribute it and/or modify  *

 *   it under the terms of the GNU General Public License as published by  *

 *   the Free Software Foundation; either version 2 of the License, or     *

 *   (at your option) any later version.                                   *

 *                                                                         *

 ***************************************************************************/

"""

from __future__ import absolute_import




from builtins import chr
from builtins import str
from builtins import range
from builtins import object
#from qgis.core import *

#from numpy import std, mean, cross

from numpy import *

import sys

from math import pi, fabs, atan

import scipy

# columreader in a "table" (list of lists)


def columnreader(list_in_list_object, columnindex):

    columnvalues = []

    for i in range(len(list_in_list_object)):

        columnvalues.append(list_in_list_object[i][columnindex])

    return columnvalues


class ErrorHandler(object):

    def __init__(self):
        """init"""

# Checks that have to do on every single Profile

    def singleprofile(self, coord_proc, view_check, profile_name, selection_check):

        errorCheck = False

        # check if actual profile has less then 4 points

        if len(coord_proc) <= 3:

            # if it is less, print error message

            criticalMessageToBar(self,
                                 'Error',
                                 'A profile needs min. 4 points. Error on profile: '
                                 +str(profile_name))

            printLogMessage(self,
                            'A profile needs min. 4 points. Error on profile: '
                            +str(profile_name),
                            'Error_LOG')

            # cancel execution of the script

            errorCheck = True

        # check if the view value is the same in all features

        if len(view_check) != 1:

            # if it is not the same, print error message

            criticalMessageToBar(self,
                                 'Error',
                                 'The view column of your data is inconsistant '
                                 '(either non or two different views are present). Error on profile: '
                                 + str(profile_name))

            printLogMessage(self,
                            'The view column of your data is inconsistant '
                            '(either non or two different views are present). Error on profile: '
                            + str(profile_name), 'Error_LOG')

            # cancel execution of the script

            errorCheck = True

        # check if the view is one of the four cardinal directions

        if view_check[0].upper() not in ["N", "E", "S", "W"]:

            # if it is not the same, print error message

            criticalMessageToBar(self,
                                 'Error',
                                 'The view value is not one of the four cardinal directions. '
                                 'Error on profile: ' + str(profile_name))

            printLogMessage(self,
                            'The view value is not one of the four cardinal directions. '
                            'Error on profile: ' + str(profile_name), 'Error_LOG')

            # cancel execution of the script

            errorCheck = True

        # check if the selection/use is 0 or 1

        for i in range(len(selection_check)):

            if str(selection_check[i]) not in ["1", "0"]:

                # if it is not the same, print error message

                criticalMessageToBar(self, 'Error',
                                     'Only 0 or 1 are allowed in the selection/use. Error on profile: '
                                     + str(profile_name))

                printLogMessage(self,

                                'Only 0 or 1 are allowed in the selection/use. Error on profile: : '
                                + str(profile_name),
                                'Error_LOG')

                # cancel execution of the script

                errorCheck = True

        # check if the coordinates x, y, z fall into 2 sigma range

        # instance a table like list of lists with i rows and j columns

        for i in range(3):

            xyz = []

            xyz_lower = []

            xyz_upper = []

            xyz = columnreader(coord_proc, i)

            xyz_lower = mean(xyz) - (2 * std(xyz))

            xyz_upper = mean(xyz) + (2 * std(xyz))

            for j in range(len(xyz)):

                if xyz[j] < xyz_lower or xyz[j] > xyz_upper:

                    criticalMessageToBar(self,
                                         'Warning',
                                         'Warning: Profile ' + str(profile_name) +': '
                                         + chr(120+i) + 'Pt '
                                         + str(j+1) + ' exceeds the 2std interval of '
                                         + chr(120+i))
                    printLogMessage(self,
                                    'Warning: Profile '
                                    + str(profile_name)
                                    +': '+ chr(120+i) + 'Pt '
                                    + str(j+1) + ' exceeds the 2std interval of '
                                    + chr(120+i),
                                    'Error_LOG')
        return errorCheck

    # general checks for the fields of the layer after the import

    def field_check (self, layer, z_field):

        errorCheck = False

        # Check if the vectorlayer is projected

        if layer.crs().isGeographic() is True:

            criticalMessageToBar(self, 'Error',
                                 "Layer "+layer.name()+
                                 " is not projected. Please choose an projected reference system.")

            printLogMessage(self, "Layer "+layer.name()+
                            " is not projected. Please choose an projected reference system.",
                            'Error_LOG')

            # cancel execution of the script

            errorCheck = True



        # check the z-field

        for field in layer.fields():

            # Take a look for the z Field

            if str(field.name()) == str(z_field):

                # if the z value is not a float

                if field.typeName() != "Real" and field.typeName() != "double":

                    # Give a message

                    criticalMessageToBar(self, 'Error',
                                         'The z-Value needs to be a float. Check the field type of the z-Value')

                    printLogMessage(self,
                                    'The z-Value needs to be a float. Check the field type of the z-Value', 'Error_LOG')

                    # cancel execution of the script
                    errorCheck = True

        return errorCheck

    # checks if the inputfields are filled correct

    def input_check(self, value):

        errorCheck = False

        if str(value) == "":

            criticalMessageToBar(self, 'Error',
                                 'Please choose an output file!')
            # cancel execution of the script
            errorCheck = True
        return errorCheck

    def calculateError(self, linegress, xw, yw):

        intercept = linegress[1]

        slope = linegress[0]

        # predict points on line

        for i in range(len(xw)):

            # Predict the value for the minmal x

            if xw[i] == min(xw):

                x1pred = xw[i]

                y1pred = intercept + slope*xw[i]

                p1 = scipy.array([x1pred, y1pred])

            # Predict the value for the maximal x

            if xw[i] == max(xw):

                x2pred = xw[i]

                y2pred = intercept + slope*xw[i]

                p2 =  scipy.array([x2pred, y2pred])

        # Calculate the distance from every point to the line.

        distance = []		

        # Export this value to every point, and give a sum of all distances indicator: sum = 0, fine; sum = max point (this is the bad one) ; sum > max point (maybe more than one are bad)

        for i in range(len(xw)):

            p3 = scipy.array([xw[i],yw[i]])

            distance.append(linalg.norm(cross(p2 - p1, p1 - p3)) / linalg.norm(p2 - p1))

        return distance
