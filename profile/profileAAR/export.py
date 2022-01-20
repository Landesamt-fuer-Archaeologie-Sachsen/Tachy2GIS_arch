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

class Export(): 

    def __init__(self):
        """export"""

    def export(self, coord_trans, filename, corrdinate_system):

            '''Create Vector Layer'''

            export_fields = QgsFields()

            export_fields.append(QgsField("x", QVariant.Double))

            export_fields.append(QgsField("y", QVariant.Double))

            export_fields.append(QgsField("z", QVariant.Double))

            export_fields.append(QgsField("prnumber", QVariant.String))

            export_fields.append(QgsField("org_z", QVariant.String))

            export_fields.append(QgsField("distance", QVariant.String))

            export_fields.append(QgsField("was_used", QVariant.String))

            writer = QgsVectorFileWriter(filename,
                                         "utf-8",
                                         export_fields,
                                         QgsWkbTypes.Point,
                                         corrdinate_system,
                                         "ESRI Shapefile")

            if writer.hasError() != QgsVectorFileWriter.NoError:

                exportError(self)

            export_feature = QgsFeature()

            for x in range(len(coord_trans)):

                for i in range(len(coord_trans[x])):

                    export_feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(coord_trans[x][i][0],
                                                                                  coord_trans[x][i][2])))

                    export_feature.setAttributes([float(coord_trans[x][i][0]), float(coord_trans[x][i][1]),
                                                  float(coord_trans[x][i][2]), str(coord_trans[x][i][3]),
                                                  str(coord_trans[x][i][4]), str(coord_trans[x][i][5]),
                                                  str(coord_trans[x][i][6])])

                    writer.addFeature(export_feature)

            del writer

    def export_height(self, coord_trans, filename, corrdinate_system):

            '''Create Vector Layer'''

            export_fields = QgsFields()

            export_fields.append(QgsField("prnumber", QVariant.String))

            export_fields.append(QgsField("org_z", QVariant.String))

            filename = filename.split(".shp")[0]

            filename = filename + "_height.shp"

            writer = QgsVectorFileWriter(filename, "utf-8", export_fields,
                                         QgsWkbTypes.Point, corrdinate_system,
                                         "ESRI Shapefile")

            if writer.hasError() != QgsVectorFileWriter.NoError:

                exportError(self)

            export_feature = QgsFeature()

            for x in range(len(coord_trans)):

                # QgsMessageLog.logMessage(str(coord_trans[x]), 'MyPlugin')

                export_feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(coord_trans[x][0], coord_trans[x][2])))

                export_feature.setAttributes([str(coord_trans[x][3]), str(coord_trans[x][4])])

                writer.addFeature(export_feature)

            del writer

    def export_section(self, cutting_line, prnumber, filename, corrdinate_system):

            '''Create Vector Layer'''

            export_fields = QgsFields()

            export_fields.append(QgsField("prnumber", QVariant.String))

            filename = filename.split(".shp")[0]

            filename = filename + "_section.shp"

            writer = QgsVectorFileWriter(filename, "utf-8",
                                         export_fields,
                                         QgsWkbTypes.LineString,
                                         corrdinate_system,
                                         "ESRI Shapefile")

            if writer.hasError() != QgsVectorFileWriter.NoError:

                exportError(self)

            export_feature = QgsFeature()

            for x in range(len(cutting_line)):

                export_feature.setGeometry(QgsGeometry.fromPolylineXY(cutting_line[x]))

                export_feature.setAttributes([str(prnumber)])

                writer.addFeature(export_feature)

            del writer
