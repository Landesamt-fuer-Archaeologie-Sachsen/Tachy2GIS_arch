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
from builtins import str
from builtins import range
from builtins import object
from .transformation import sectionCalc
#errorhandling is managed here
from .errorhandling import ErrorHandler
# the magic happens here
from .transformation import Magic_Box
#the export to a shapefile happens here
from .export import Export

from ..publisher import Publisher

class profileAAR(object):

    """QGIS Plugin Implementation."""

    def __init__(self):

        """
        Constructor
        """

        self.pup = Publisher()

    def run(self, data):
        """Run method that performs all the real work"""

        # initialize the Errorhandler
        errorhandler = ErrorHandler()
        magicbox = Magic_Box()
        export = Export()

        '''DEFINE OUTPUT PATH'''

        '''TODO check input data'''

        result = data[0]
        transform_param = data[1]
        if result:

            '''GET INPUT FROM GUI TO VARIABLES/PREPARE LIST OF DATA'''

            # GET TEXT FROM METHOD AND DIRECTION
            # Read the method that is selected
            method = transform_param['method']

            # read the direction, that is selected
            direction = transform_param['direction']

            # PREPARE DATA LIST
            # Go thought all data rows in the selected layer

            iter = result

            # list for the data
            coord = []

            # list for the different profile names
            profile_names = []

            point_id = 0

            for feature in iter:

                # retrieve every feature with its geometry and attributes
                view = feature[3]
                profileName = feature[4]

                # fetch geometry
                #for p in feature:
                # getting x and y coordinate
                x = round(feature[0], 3)
                y = round(feature[1], 3)
                z = round(feature[2], 3)
                use = feature[5]
                obj_uuid = feature[6]

                # write coordinates and attributes (view, profile and z) in a list
                # add an ID to each point

                point_id += 1

                coord.append([x,y,z,view, profileName, use, point_id, obj_uuid])

                # write a list of profilenames (unique entries)
                if profileName not in profile_names:
                    profile_names.append(profileName)

            '''WORK ON EVERY PROFILE IN LOOP'''

            # CREATE A LIST OF DATA FOR EVERY PROFILE
            # select every single profile in a loop
            coord_trans = []
            height_points = []
            cutting_line = []

            for i in range(len(profile_names)):
                # instantiate a temporary list for a single profile
                coord_proc = []

                # instantiate list for the view to check if all entries in one profile are the same
                view_check = []

                # instantiate list for the selection to check if all entries in one profile are the same
                selection_check = []

                # iterate through the features in coord, if the profilename matches store the features
                # datalist in templist

                for x in range(len(coord)):
                    coord_proc.append(coord[x])

                    # write the unique view values in the checklist
                    if coord[x][1] not in view_check:
                        view_check.append(coord[x][1])

                    # write the unique selection values in the checklist
                    if coord[x][4] not in selection_check:
                        selection_check.append(coord[x][3])

                # Handle Errors depending on the attributes in the fields

                # Errorhandling: Checking the single Profiles for inconsestency

                # Therefore we need the data of the actual profile, the view_check with the view values
                # and actual profile name, selection is 0 or 1

                # TODO checks
                profileCheck, fieldCheck, inputCheck = False, False, False

                if fieldCheck is False and inputCheck is False:

                    profileCheck = False

                if profileCheck is False and fieldCheck is False and inputCheck is False:

                    # Calculating the profile and add it to the list

                    transform_return = magicbox.transformation(coord_proc, method, direction)

                    coord_height_list = transform_return['coord_trans']

                    coord_trans.append(coord_height_list)

                    # If checked, the upper right point has to be exportet as point
                    height_points.append(magicbox.height_points(coord_height_list))

                    cutting_line.append(sectionCalc(self,
                        coord_proc,
                        transform_return['cutting_start'],
                        transform_return['linegress'],
                        transform_return['ns_error']), )

                    #return transform_return
                    transform_return['transformationParams']['cutting_line'] = cutting_line
                    transform_return['transformationParams']['aar_direction'] = direction
                    self.pup.publish('aarPointsChanged', transform_return)
