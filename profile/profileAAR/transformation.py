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

from __future__ import division, print_function

from __future__ import absolute_import
from builtins import str
from builtins import range

import scipy

from scipy import stats

import sys

from math import atan, fabs, pi, cos, sin, tan, isnan, sqrt

from numpy import mean

import itertools

from .errorhandling import ErrorHandler


def rotation (self, coord_proc, slope_deg, zAdaption):
    print('rotation_coord_proc', coord_proc)
    #coord_proc = listToList(coord_proc, 0)
    x_coord_proc = listToList(coord_proc, 0)

    y_coord_proc = listToList(coord_proc, 1)

    z_coord_proc = listToList(coord_proc, 2)

    # calculate the point of rotation

    center_x = mean(x_coord_proc)

    center_y = mean(y_coord_proc)

    # instantiate lists for the transformed coordinates

    x_trans = []

    y_trans = []

    z_trans = []

    for i in range(len(coord_proc)):

        x_trans.append(

            center_x + (coord_proc[i][0] - center_x) * cos(slope_deg / 180 * pi) - sin(slope_deg / 180 * pi) * (

                        coord_proc[i][1] - center_y))

        y_trans.append(

            center_y + (coord_proc[i][0] - center_x) * sin(slope_deg / 180 * pi) + (coord_proc[i][1] - center_y) * cos(

                slope_deg / 180 * pi))

        if zAdaption is True:

            z_trans.append(coord_proc[i][2] + center_y - mean(z_coord_proc))

        else:

            z_trans.append(coord_proc[i][2])

    return {'x_trans': x_trans, 'y_trans': y_trans ,'z_trans': z_trans }


def listToList(coord_proc, position):

    newList = []

    for i in range(len(coord_proc)):

        newList.append(coord_proc[i][position])

    return newList


def ns_error_determination(self, coord_proc):
    #print('coord_proc_trans', coord_proc)
    #coord_proc = listToList(coord_proc, 0)
    xw = listToList(coord_proc, 0)

    yw = listToList(coord_proc, 1)

    ymin = min(yw)
    ymax = max(yw)

    # Due to mathematical problems with exactly north-south orientated profiles it is nessecary to determine them

    # Therefore a linear regression has to be calculated "by hand"
    # and the slope between the the most northern und southern

    # points has to be compared with the slope of the linegress (the results of the lingress function are not sufficent)

    # The calculation is after https://www.crashkurs-statistik.de/einfache-lineare-regression/

    xStrich = mean(xw)

    yStrich = mean(yw)

    abzugX = []

    abzugY = []

    for i in range(len(xw)):

        abzugX.append(xw[i] - xStrich)

        if i > 0 and xw[i] < xw[i-1]:

            x1Gerade = xw[i]

        elif i > 0 and xw[i] > xw[i-1]:

            x2Gerade = xw[i]

        elif i == 0:

            x1Gerade = xw[i]

            x2Gerade = xw[i]

    for i in range(len(yw)):

        if i > 0 and yw[i] < ymin:

            ymin = yw[i]

            ymin_postition = i

        elif i > 0 and yw[i] > ymax:

            ymax = yw[i]

            ymax_postition = i

        elif i == 0:

            ymin = yw[i]

            ymin_postition = i

            ymax = yw[i]

            ymax_postition = i

        abzugY.append(yw[i] - yStrich)

    abzugXsum = 0

    abzugXsum2 = 0

    for i in range(len(abzugX)):

        abzugXsum = abzugXsum + abzugX[i] * abzugY[i]

        abzugXsum2 = abzugXsum2 + abzugX[i] * abzugX[i]

    b = abzugXsum / abzugXsum2

    a = yStrich - b * xStrich

    y1Gerade = a + b * x1Gerade

    y2Gerade = a + b * x2Gerade

    steigung_neu = atan((y2Gerade - y1Gerade) / (x2Gerade - x1Gerade)) * 180 / pi

    # If the profile is perfectly E-W orentated there is no problem, the new slope can be the old one

    try:

        steigung_alt = atan((ymax - ymin) / (xw[ymax_postition] - xw[ymin_postition])) * 180 / pi

    except ZeroDivisionError:

        steigung_alt = steigung_neu

    # If the slope of the regression and the original points differs more than 10%, the Profile has to be considered separately

    pluszehn = abs(steigung_alt) + (abs(steigung_alt) * 10 / 100)

    minuszehn = abs(steigung_alt) - (abs(steigung_alt) * 10 / 100)

    if abs(steigung_neu) > pluszehn and abs(round(steigung_alt, 0)) != 45 \
            or abs(steigung_neu) < minuszehn and abs(round(steigung_alt, 0)) != 45:

        return bool(True)

    else:

        return bool(False)


def sectionPoint(coord_proc, side, slope):

    slope_deg = (atan(slope) * 180) / pi

    if slope_deg >= 45 or slope_deg <= -45:

        if side == 'East':

            coord_sort = sorted(coord_proc, key = lambda  x: ( -x[0]))

        elif side == 'West':

            coord_sort = sorted(coord_proc, key=lambda x: (x[0]))

    elif slope_deg < 45 and slope_deg > -45:

        if side == 'East':

            coord_sort = sorted(coord_proc, key=lambda x: (-x[1]))

        elif side == 'West':

            coord_sort = sorted(coord_proc, key=lambda x: (x[1]))

    coord_sort_xy = []

    for i in range(0, 2):

        coord_sort_xy.append(coord_sort[i])

    coords_sort_z = sorted(coord_sort_xy, key = lambda x: (-x[2]))

    return {'x': coords_sort_z[0][0], 'y': coords_sort_z[0][1]}


def sectionCalc(self, coord_proc, cutting_start, linegress, ns_error):
    # Calculation the section of the profile
    # getting the most easter or western and highest point
    # this is nearly the sectionline

    eastpoint = sectionPoint(coord_proc, 'East', linegress[0])

    westpoint = sectionPoint(coord_proc, 'West', linegress[0])

    # getting the single coordinates to rotate them if they are affected by the north - south problem

    eastx = eastpoint['x']

    easty = eastpoint['y']

    westx = westpoint['x']

    westy = westpoint['y']

    if ns_error:

        # Rotate the line by - 45 degree

        # list of two coordinates

        rotlist = []

        rotlist.append([eastpoint['x'],eastpoint['y'], 0])

        rotlist.append([westpoint['x'], westpoint['y'], 0])

        rot_result = rotation(self, rotlist, -45, False)

        eastx = rot_result['x_trans'][0]

        westx = rot_result['x_trans'][1]

        easty = rot_result['y_trans'][0]

        westy = rot_result['y_trans'][1]

    # Convert the coorinates to Qgis Vector Points

    print(eastx, easty, westx, westy)

    #QgisEastPoint = QgsPointXY(eastx, easty)

    #QgisWestPoint = QgsPointXY(westx, westy)

    # write a list with the coordinates from left to right in direction of view

    # This is necessary for the correct mapping in qgis

    points_of_line = []

    if cutting_start == 'W':

        points_of_line.append([eastx, easty])

        points_of_line.append([westx, westy])

    elif cutting_start == 'E':

        points_of_line.append([westx, westy])

        points_of_line.append([eastx, easty])

    return (points_of_line)

class Magic_Box():

    def __init__(self):
        """magic box"""

    def transformation(self, coord_proc, method, direction):
        #initialize the Errorhandler
        print('coord_proc_transformation',coord_proc)
        errorhandler = ErrorHandler()

        profilnr_proc = listToList(coord_proc, 4)

        fehler_check = False

        ns_fehler_vorhanden = ns_error_determination(self, coord_proc)
        print('ns_fehler_vorhanden check', ns_fehler_vorhanden)
        if ns_fehler_vorhanden:
            print('ns_fehler_vorhanden', ns_fehler_vorhanden)
            # Profil um 45 Grad drehen

            rotationresult = rotation(self, coord_proc, 45, False)

            fehler_check = True

            print('coord_proc[0]', coord_proc[0])
            print('rotationresult',  rotationresult['x_trans'])

            for i in range(len(coord_proc)):

                coord_proc[i][0] = rotationresult['x_trans'][i]

                coord_proc[i][1] = rotationresult['y_trans'][i]

                coord_proc[i][2] = rotationresult['z_trans'][i]

        # write the x and v values in the corresponding lists
        # instantiate an empty list for the transformed coordinates and other values

        print('coord_proc',coord_proc)
        # instantiate lists for the x and y values
        #coordList = listToList(coord_proc, 0)
        x_coord_proc = listToList(coord_proc, 0)
        print('x_coord_proc',x_coord_proc)

        y_coord_proc = listToList(coord_proc, 1)
        print('y_coord_proc',y_coord_proc)

        selection_proc = listToList(coord_proc, 5)
        print('selection_proc',selection_proc)

        id_proc = listToList(coord_proc, 6)
        print('id_proc',id_proc)

        uuid_proc = listToList(coord_proc, 7)
        print('uuid_proc',uuid_proc)

        rangcheck_orginal = []

        for i in range(len(coord_proc)):

            tmplist = []

            for k in range(len(coord_proc[i])):

                tmplist.append(coord_proc[i][k])

            rangcheck_orginal.append(tmplist)

        '''
        print('###',rangcheck_orginal)
        for coords in range(len(rangcheck_orginal)):

            del rangcheck_orginal[coords][1]

            del rangcheck_orginal[coords][2]

            del rangcheck_orginal[coords][3]

        print('###',rangcheck_orginal)
        '''

        # distanz zwischen den beiden Punkten oben CHANGE
        # create the valuelists that are used

        xw = []

        yw = []

        xw_check = []

        yw_check = []

        print('selection_proc ',selection_proc)
        for x in range(len(x_coord_proc)):

            # Nur Auswahl zum berechnen der Steigung verwenden

            if(selection_proc[x] == 1):

                xw.append(x_coord_proc[x] - min(x_coord_proc))

                yw.append(y_coord_proc[x] - min(y_coord_proc))

            xw_check.append(x_coord_proc[x] - min(x_coord_proc))

            yw_check.append(y_coord_proc[x] - min(y_coord_proc))

        #There is a problem with lingress if the points are nearly N-S oriented

        # To solve this, it is nessecary to change the input values of the regression

        # Calculate the regression for both directions
        #print(' xw,yw', xw,yw)

        linegress_x = scipy.stats.linregress(scipy.array(xw), scipy.array(yw))

        linegress_y = scipy.stats.linregress(scipy.array(yw), scipy.array(xw))

        print('xw', xw)
        print('yw', yw)

        print('x_coord_proc', x_coord_proc)
        print('y_coord_proc', y_coord_proc)
        print('linegress_y', linegress_y)
        print('linegress_x', linegress_x)

        linegress_profil = scipy.stats.linregress(x_coord_proc, y_coord_proc)
        print('linegress_profil', linegress_profil)
        # get the sum of residuals for both direction

        # We like to use the regression with less sum of the residuals

        res_x = self.calculateResidual(linegress_x, scipy.array(xw), scipy.array(yw))

        res_y = self.calculateResidual(linegress_y, scipy.array(yw), scipy.array(xw))

        if isnan(res_y) or res_x >= res_y:

            linegress = linegress_x

            slope = linegress[0]

        elif isnan(res_x) or res_x < res_y:

             linegress = linegress_y

             # if the linear regression with the changed values was used, the angle of the slope is rotated by 90°

             slope = tan((-90-(((atan(linegress[0]) * 180) / pi))) * pi / 180)

        else:

            sys.exit(' ERROR: Calculation failed! Corrupt data!')

        print('linregress, slope', linegress, slope)


        # Check the distance with all points

        distance = errorhandler.calculateError( linegress, xw_check, yw_check)

        # calculate the degree of the slope

        # Defining the starting point for the export of the section

        slope_deg = 0.0

        # Variable for determining the paint direction of the cutting line

        cutting_start = ''

        if slope < 0 and coord_proc[0][3] in ["N", "E"]:

            slope_deg = 180 - fabs((atan(slope)*180)/pi) * -1

            cutting_start = 'E'

        elif slope < 0 and coord_proc[0][3] in ["S", "W"]:

            slope_deg = fabs((atan(slope) * 180) / pi)

            cutting_start = 'W'

        elif slope > 0 and coord_proc[0][3] in ["S", "E"]:

            slope_deg = ((atan(slope) * 180) / pi) * -1

            cutting_start = 'W'

        elif slope > 0 and coord_proc[0][3] in ["N", "W"]:

            slope_deg = 180 - ((atan(slope) * 180) / pi)

            cutting_start = 'E'

        elif slope == 0 and coord_proc[0][3] == "N":

            slope_deg = 180

            cutting_start = 'E'

        print('cutting start, slope_deg', cutting_start, slope_deg)
        # instantiate lists for the transformed coordinates

        x_trans = []

        y_trans = []

        z_trans = []

        print('coord_proc', coord_proc)
        # rotation with z as y: zAdpation == True, z is adapted to mean y value
        first_rotationresult = rotation(self, coord_proc, slope_deg, True)

        print('first_rotationresult', first_rotationresult)

        for i in range(len(coord_proc)):

            x_trans.append(first_rotationresult['x_trans'][i])

            y_trans.append(first_rotationresult['y_trans'][i])

            z_trans.append(first_rotationresult['z_trans'][i])

        if direction == "absolute height":

            # To get an export for the absolute height it is necessary to rotate the profile like the horizontal way

            # and move it on the y-axis

            x_coord_proc = listToList(coord_proc, 0)

            y_coord_proc = listToList(coord_proc, 1)

            z_coord_proc = listToList(coord_proc, 2)

            # calculate the minimal x

            mean_x = mean(x_coord_proc)

            mean_y = mean(y_coord_proc)

            mean_z = mean(z_coord_proc)

            for i in range(len(x_trans)):

                x_trans[i]  = x_trans[i] - mean_x

                z_trans[i] = z_trans[i] - mean_y + mean_z

            new_min_x = min(x_trans)

            for i in range(len(x_trans)):

                x_trans[i] = x_trans[i] + abs(new_min_x)

        # instantiate a list for the transformed coordinates

        coord_trans = []

        rangcheck_trans = []

        # build the finished list

        for i in range(len(coord_proc)):

            coord_trans.append([x_trans[i], y_trans[i], z_trans[i], coord_proc[i][4], coord_proc[i][2],
                                distance[i], selection_proc[i], id_proc[i]])

            rangcheck_trans.append([x_trans[i], z_trans[i], y_trans[i]])

        # If the aim is to get the view of the surface, the x-axis has to be rotated aswell

        if method == "surface":

            # calculating the slope, therefore preparing lists

            z_yw = []

            z_zw = []

            for i in range(len(coord_proc)):

                z_yw.append(y_trans[i] - min(y_trans + z_trans))

                z_zw.append(z_trans[i] - min(y_trans + z_trans))

            # actual calculation of the slope using the linear regression again

            z_slope = scipy.stats.linregress(scipy.array(z_yw), scipy.array(z_zw))[0]

            # transform the radians of the slope into degrees

            z_slope_deg = 0.0

            if z_slope < 0:

                z_slope_deg = -(90 -fabs(((atan(z_slope) * 180) / pi)))

            elif z_slope > 0:

                z_slope_deg = 90 - ((atan(z_slope) * 180)/pi)

            elif z_slope == 0:

                z_slope_deg = 0.0

            # calculate the centerpoint

            z_center_y = mean(y_trans)

            z_center_z = mean(z_trans)

            # rewrite the lists for the y and z values

            y_trans = []

            z_trans = []

            for i in range(len(coord_trans)):

                y_trans.append(z_center_y + (coord_trans[i][1] - z_center_y)
                               * cos(z_slope_deg / 180 * pi) - (coord_trans[i][2] - z_center_z)
                               * sin(z_slope_deg / 180 * pi))

                z_trans.append(z_center_z + (coord_trans[i][1] - z_center_y)
                               * sin(z_slope_deg / 180 * pi) + (coord_trans[i][2] - z_center_z)
                               * cos(z_slope_deg / 180 * pi))

            # empty and rewrite the output list

            coord_trans = []

            rangcheck_trans = []

            for i in range(len(coord_proc)):

                coord_trans.append([x_trans[i], y_trans[i], z_trans[i], coord_proc[i][4], coord_proc[i][2],
                                    distance[i], selection_proc[i],id_proc[i], uuid_proc[i]])

                rangcheck_trans.append([x_trans[i], z_trans[i], y_trans[i]])

        # If the direction is in the "original" setting, the points have
        # to be rotated back to their original orientation
        print('coord_trans_hor', coord_trans)
        if direction == "original":

            # the rotation angle is the negative angle of the first rotation

            if fehler_check is True:

                y_slope_deg = -slope_deg - 45

            else:

                y_slope_deg = -slope_deg

            # get the centerpoint

            y_center_x = mean(x_trans)

            y_center_z = mean(z_trans)

            # rewrite the lists for the x and z values

            x_trans = []

            z_trans = []

            for i in range(len(coord_trans)):

                x_trans.append(y_center_x + (coord_trans[i][0] - y_center_x) * cos(y_slope_deg / 180 * pi)
                               - (coord_trans[i][2] - y_center_z)
                               * sin(y_slope_deg / 180 * pi))

                z_trans.append(y_center_z + (coord_trans[i][0] - y_center_x) * sin(y_slope_deg / 180 * pi)
                               + (coord_trans[i][2] - y_center_z)
                               * cos(y_slope_deg / 180 * pi))

            # empty and rewrite the output list

            coord_trans = []

            rangcheck_trans = []

            for i in range(len(coord_proc)):

                # CHANGE

                coord_trans.append([x_trans[i], y_trans[i], z_trans[i], coord_proc[i][4],
                                    coord_proc[i][2], distance[i], selection_proc[i], id_proc[i], uuid_proc[i]])

                rangcheck_trans.append([x_trans[i], z_trans[i], y_trans[i]])

        print('coord_trans_org', coord_trans)
         # check the distances of the outter points from the old points and the converted ones
        original_outer_points = self.outer_profile_points(coord_proc)

        original_distance = self.calculate_distance_from_outer_profile_points_orgiginal(original_outer_points)

        new_outer_points = []

        for point in coord_trans:

            if point[7] == original_outer_points[0][6] or point[7] == original_outer_points[1][6]:

                new_outer_points.append(point)

        new_distance = self.calculate_distance_from_outer_profile_points_proc(new_outer_points)
        print(new_distance)

        print( 'PR:' + str(coord_proc[0][4]), 'Distance')

        print( 'Original Distance: ' + str(original_distance), 'Distance')

        print( 'New Distance: ' + str(new_distance), 'Distance')

        print( 'Diff. Distance: ' + str(abs(original_distance-new_distance)), 'Distance')

        if abs(original_distance - new_distance) > 0.01:

            print('Error', 'Profile was calculated incorrect (1cm acc.) See Log-Window: '
                                 + str(str(coord_proc[0][4])))

            print( 'DISTANCE WARNING!', 'Distance')

        print('########################')
        print('coord_proc', coord_proc)
        #print({'coord_trans': coord_trans, 'cutting_start': cutting_start, 'linegress': linegress, 'ns_error': ns_fehler_vorhanden})
        print('########################')
        print(rotation(self, coord_trans, -slope_deg, True))
        print('########################')
        return {'coord_trans': coord_trans, 'cutting_start': cutting_start, 'linegress': linegress,
                'ns_error': ns_fehler_vorhanden}


    def height_points (self, coord_trans):

        #Getting the top right point and export it to a pointshape

        height_point = []

        upperright_last = 0

        for i in range(len(coord_trans)):

            upperright_check = coord_trans[i][0] + coord_trans[i][2]

            if upperright_check > upperright_last:

                upperright_last = upperright_check

                height_point = coord_trans[i]

        return height_point

    def outer_profile_points(self, coords):

        # get the two points with the highest and lowest xvalue

        coords_sorted = sorted(coords, key=lambda x: (x[0]))

        two_lowest = coords_sorted[:2]

        two_highest = coords_sorted[-2:]

        if two_lowest[1][2] > two_lowest[0][2]:

            lowestx = two_lowest[1]

        else:

            lowestx = two_lowest[0]

        if two_highest[1][2] > two_highest[0][2]:

            highestx = two_highest[1]

        else:

            highestx = two_highest[0]

        return [lowestx, highestx]

    def calculate_distance_from_outer_profile_points_orgiginal(self, outer_points):

        distance = sqrt((outer_points[1][0]-outer_points[0][0])**2 + (outer_points[1][1]-outer_points[0][1])**2)

        return distance

    def calculate_distance_from_outer_profile_points_proc(self, outer_points):

        distance = sqrt((outer_points[1][0]-outer_points[0][0])**2 + (outer_points[1][2]-outer_points[0][2])**2)

        return distance

    def calculateResidual(self, linegress, array1, array2):

        # This calculates the predicted value for each observed value

        obs_values = array2

        pred_values = linegress[0] * array1 + linegress[1]

        # This prints the residual for each pair of observations

        Residual = obs_values - pred_values

        return sum(Residual)
