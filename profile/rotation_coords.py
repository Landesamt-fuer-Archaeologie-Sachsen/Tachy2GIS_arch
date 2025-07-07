from math import pi, cos, sin

import numpy as np
from qgis.core import QgsGeometry, QgsPoint, QgsMessageLog, Qgis, QgsWkbTypes


class RotationCoords:

    def __init__(self):

        self.transformationParamsHorizontal = None
        self.transformationParamsAbsolute = None
        self.transformationParamsOriginal = None

    # Transformationsparameter für jede AAR-Direction setzen
    def setAarTransformationParams(self, params):
        if params["aar_direction"] == "horizontal":
            self.transformationParamsHorizontal = params
        if params["aar_direction"] == "original":
            self.transformationParamsOriginal = params
        if params["aar_direction"] == "absolute height":
            self.transformationParamsAbsolute = params

    # Karte zu Profil
    # x,y,z sind reale Punkte bspw. im Gauss-Krüger System
    def rotation(self, x, y, z, zAdaption, aar_direction):

        if aar_direction == "horizontal":
            slope_deg = self.transformationParamsHorizontal["slope_deg"]
            center_x = self.transformationParamsHorizontal["center_x"]
            center_y = self.transformationParamsHorizontal["center_y"]
            center_z = self.transformationParamsHorizontal["center_z"]

            x_trans = center_x + (x - center_x) * cos(slope_deg / 180 * pi) - sin(slope_deg / 180 * pi) * (y - center_y)

            y_trans = center_y + (x - center_x) * sin(slope_deg / 180 * pi) + (y - center_y) * cos(slope_deg / 180 * pi)

            if zAdaption is True:
                z_trans = z + center_y - center_z
            else:
                z_trans = z

        elif aar_direction == "absolute height":

            slope_deg = self.transformationParamsAbsolute["slope_deg"]
            center_x = self.transformationParamsAbsolute["center_x"]
            center_y = self.transformationParamsAbsolute["center_y"]
            center_z = self.transformationParamsAbsolute["center_z"]
            min_x = self.transformationParamsAbsolute["min_x"]

            x_trans = center_x + (x - center_x) * cos(slope_deg / 180 * pi) - sin(slope_deg / 180 * pi) * (y - center_y)

            y_trans = center_y + (x - center_x) * sin(slope_deg / 180 * pi) + (y - center_y) * cos(slope_deg / 180 * pi)

            z_trans = z

            # Anpassung absolute height - verschieben nach x
            x_trans = x_trans - min_x

        elif aar_direction == "original":

            slope_deg = self.transformationParamsOriginal["slope_deg"]
            y_slope_deg = self.transformationParamsOriginal["y_slope_deg"]
            center_x = self.transformationParamsOriginal["center_x"]
            center_y = self.transformationParamsOriginal["center_y"]
            center_z = self.transformationParamsOriginal["center_z"]
            center_x_trans = self.transformationParamsOriginal["center_x_trans"]
            center_z_trans = self.transformationParamsOriginal["center_z_trans"]

            z = z + center_y - center_z

            y_trans = center_y + (x - center_x) * sin(slope_deg / 180 * pi) + (y - center_y) * cos(slope_deg / 180 * pi)

            x = center_x + (x - center_x) * cos(slope_deg / 180 * pi) - sin(slope_deg / 180 * pi) * (y - center_y)

            x_trans = (
                center_x_trans
                + (x - center_x_trans) * cos(y_slope_deg / 180 * pi)
                - (z - center_z_trans) * sin(y_slope_deg / 180 * pi)
            )

            z_trans = (
                center_z_trans
                + (x - center_x_trans) * sin(y_slope_deg / 180 * pi)
                + (z - center_z_trans) * cos(y_slope_deg / 180 * pi)
            )

        else:
            print("Wrong AAR-Direction")

        return {"x_trans": x_trans, "y_trans": y_trans, "z_trans": z_trans}

    # Profil zu Karte
    def rotationReverse(self, x, z, zAdaption, aar_direction):

        if aar_direction == "horizontal":

            slope_deg = self.transformationParamsHorizontal["slope_deg"] * (-1)
            center_x = self.transformationParamsHorizontal["center_x"]
            center_y = self.transformationParamsHorizontal["center_y"]
            z_slope = 1  # self.transformationParams['z_slope'] -- geht nicht mit dem Neigungswinkel
            z_intercept = self.transformationParamsHorizontal["z_intercept"]

            if zAdaption is True:
                z_trans = z_slope * z - z_intercept
            else:
                z_trans = z

            x_trans = center_x + (x - center_x) * cos(slope_deg / 180 * pi) - sin(slope_deg / 180 * pi) * 0
            y_trans = center_y + (x - center_x) * sin(slope_deg / 180 * pi) + 0 * cos(slope_deg / 180 * pi)

        elif aar_direction == "absolute height":

            slope_deg = self.transformationParamsAbsolute["slope_deg"] * (-1)
            center_x = self.transformationParamsAbsolute["center_x"]
            center_y = self.transformationParamsAbsolute["center_y"]
            z_slope = 1  # self.transformationParamsAbsolute['z_slope'] -- geht nicht mit dem Neigungswinkel
            z_intercept = self.transformationParamsAbsolute["z_intercept"]
            min_x = self.transformationParamsAbsolute["min_x"]

            # Anpassung absolute height - verschieben nach x
            x = x + min_x

            z_trans = z

            x_trans = center_x + (x - center_x) * cos(slope_deg / 180 * pi) - sin(slope_deg / 180 * pi) * 0
            y_trans = center_y + (x - center_x) * sin(slope_deg / 180 * pi) + 0 * cos(slope_deg / 180 * pi)

        elif aar_direction == "original":

            y_slope_deg = self.transformationParamsOriginal["y_slope_deg"] * (-1)
            slope_deg = self.transformationParamsOriginal["slope_deg"] * (-1)
            center_x = self.transformationParamsOriginal["center_x"]
            center_y = self.transformationParamsOriginal["center_y"]
            center_z = self.transformationParamsOriginal["center_z"]
            center_x_trans = self.transformationParamsOriginal["center_x_trans"]
            center_z_trans = self.transformationParamsOriginal["center_z_trans"]

            z1 = (
                center_z_trans
                + (x - center_x_trans) * sin(y_slope_deg / 180 * pi)
                + (z - center_z_trans) * cos(y_slope_deg / 180 * pi)
            )

            x1 = (
                center_x_trans
                + (x - center_x_trans) * cos(y_slope_deg / 180 * pi)
                - (z - center_z_trans) * sin(y_slope_deg / 180 * pi)
            )

            x2 = center_x + (x1 - center_x) * cos(slope_deg / 180 * pi)

            y1 = center_y + (x1 - center_x) * sin(slope_deg / 180 * pi)

            z2 = z1 - center_y + center_z

            x_trans = x2
            y_trans = y1
            z_trans = z2

        else:
            raise ValueError("Wrong AAR-Direction")

        return {"x_trans": x_trans, "y_trans": y_trans, "z_trans": z_trans}

    def rotatePointFeature(self, feature, aar_direction):

        geomFeat = feature.geometry()

        rotateGeom = self.rotationReverse(geomFeat.get().x(), geomFeat.get().y(), True, aar_direction)

        return rotateGeom

    def rotatePointFeatureFromOrg(self, feature, aar_direction):

        geomFeat = self.castMultiGeometry2Single(feature.geometry())

        rotateGeom = self.rotation(geomFeat.get().x(), geomFeat.get().y(), geomFeat.get().z(), True, aar_direction)

        return rotateGeom

    def rotateLineFeatureFromOrg(self, feature, aar_direction):

        geomFeat = feature.geometry()

        geomType = geomFeat.wkbType()

        mls = geomFeat.get()

        if (
            geomType == QgsWkbTypes.LineString
            or geomType == QgsWkbTypes.LineStringZ
            or geomType == QgsWkbTypes.LineString25D
        ):

            adjustGeom = QgsGeometry(mls.createEmptyWithSameType())

            pointList = []
            mls = geomFeat.get()

            for part in mls.vertices():
                try:
                    rotateGeom = self.rotation(part.x(), part.y(), part.z(), True, aar_direction)
                except:
                    rotateGeom = self.rotation(part.x(), part.y(), 0, True, aar_direction)

                zPoint = QgsPoint(rotateGeom["x_trans"], rotateGeom["z_trans"], rotateGeom["z_trans"])
                pointList.append(zPoint)

            adjustGeom.addPoints(pointList)

            retAdjustGeom = self.castMultiGeometry2Single(adjustGeom)

            return retAdjustGeom

        if (
            geomType == QgsWkbTypes.MultiLineString
            or geomType == QgsWkbTypes.MultiLineStringZ
            or geomType == QgsWkbTypes.MultiLineString25D
        ):

            QgsMessageLog.logMessage(
                "Achtung, Multi-Geometrien werden zu Single-Geometrien umgewandelt!", "T2G Archäologie", Qgis.Info
            )

            adjustGeom = QgsGeometry(mls.createEmptyWithSameType())

            for poly in geomFeat.parts():

                pointList = []

                # part ist QgsPoint
                for part in poly.vertices():

                    try:
                        rotateGeom = self.rotation(part.x(), part.y(), part.z(), True, aar_direction)
                    except:
                        rotateGeom = self.rotation(part.x(), part.y(), 0, True, aar_direction)

                    zPoint = QgsPoint(rotateGeom["x_trans"], rotateGeom["z_trans"], rotateGeom["z_trans"])
                    pointList.append(zPoint)

                adjustGeom.addPoints(pointList)

            retAdjustGeom = self.castMultiGeometry2Single(adjustGeom)

            return retAdjustGeom

    def rotatePolygonFeatureFromOrg(self, feature, aar_direction):

        geomFeat = feature.geometry()

        geomType = geomFeat.wkbType()

        mls = geomFeat.get()

        if geomType == QgsWkbTypes.Polygon or geomType == QgsWkbTypes.PolygonZ or geomType == QgsWkbTypes.Polygon25D:

            adjustGeom = QgsGeometry(mls.createEmptyWithSameType())

            pointList = []
            mls = geomFeat.get()
            for part in mls.vertices():
                try:
                    rotateGeom = self.rotation(part.x(), part.y(), part.z(), True, aar_direction)
                except:
                    rotateGeom = self.rotation(part.x(), part.y(), 0, True, aar_direction)

                zPoint = QgsPoint(rotateGeom["x_trans"], rotateGeom["z_trans"], rotateGeom["z_trans"])
                pointList.append(zPoint)

            adjustGeom.addPoints(pointList)

            retAdjustGeom = self.castMultiGeometry2Single(adjustGeom)

            return retAdjustGeom

        if (
            geomType == QgsWkbTypes.MultiPolygon
            or geomType == QgsWkbTypes.MultiPolygonZ
            or geomType == QgsWkbTypes.MultiPolygon25D
        ):

            QgsMessageLog.logMessage(
                "Achtung, Multi-Geometrien werden zu Single-Geometrien umgewandelt!", "T2G Archäologie", Qgis.Info
            )

            adjustGeom = QgsGeometry(mls.createEmptyWithSameType())

            for poly in geomFeat.parts():

                pointList = []

                # part ist QgsPoint
                for part in poly.vertices():
                    try:
                        rotateGeom = self.rotation(part.x(), part.y(), part.z(), True, aar_direction)
                    except:
                        rotateGeom = self.rotation(part.x(), part.y(), 0, True, aar_direction)

                    zPoint = QgsPoint(rotateGeom["x_trans"], rotateGeom["z_trans"], rotateGeom["z_trans"])
                    pointList.append(zPoint)

                adjustGeom.addPoints(pointList)

            retAdjustGeom = self.castMultiGeometry2Single(adjustGeom)

            return retAdjustGeom

    def rotateLineFeature(self, feature, emptyTargetGeometry, aar_direction):

        targetGeometry = emptyTargetGeometry

        geomFeat = feature.geometry()
        geomFeatWkbType = geomFeat.wkbType()

        if (
            geomFeatWkbType == QgsWkbTypes.LineString
            or geomFeatWkbType == QgsWkbTypes.LineStringZ
            or geomFeatWkbType == QgsWkbTypes.LineStringZM
        ):

            pointList = []

            mls = geomFeat.get()
            for part in mls.vertices():
                rotateGeom = self.rotationReverse(part.x(), part.y(), True, aar_direction)
                zPoint = QgsPoint(rotateGeom["x_trans"], rotateGeom["y_trans"], rotateGeom["z_trans"])
                pointList.append(zPoint)

            targetGeometry = QgsGeometry.fromPolyline(self.punkte_von_profillinie_abheben(pointList))

        else:
            QgsMessageLog.logMessage(
                "Achtung, die Geometrie ist keine Single-Line Geometrie!", "T2G Archäologie", Qgis.Info
            )

        return targetGeometry

    def rotatePolygonFeature(self, feature, emptyTargetGeometry, aar_direction):

        geomFeat = feature.geometry()
        geomFeatWkbType = geomFeat.wkbType()

        pointList = []

        if (
            geomFeatWkbType == QgsWkbTypes.Polygon
            or geomFeatWkbType == QgsWkbTypes.PolygonZ
            or geomFeatWkbType == QgsWkbTypes.PolygonZM
        ):

            mls = geomFeat.get()
            for part in mls.vertices():
                rotateGeom = self.rotationReverse(part.x(), part.y(), True, aar_direction)
                zPoint = QgsPoint(rotateGeom["x_trans"], rotateGeom["y_trans"], rotateGeom["z_trans"])
                pointList.append(zPoint)

        elif (
            geomFeatWkbType == QgsWkbTypes.MultiPolygon
            or geomFeatWkbType == QgsWkbTypes.MultiPolygon25D
            or geomFeatWkbType == QgsWkbTypes.MultiPolygonZ
            or geomFeatWkbType == QgsWkbTypes.MultiPolygonM
            or geomFeatWkbType == QgsWkbTypes.MultiPolygonZM
        ):

            for poly in geomFeat.parts():

                for part in poly.vertices():
                    rotateGeom = self.rotationReverse(part.x(), part.y(), True, aar_direction)
                    zPoint = QgsPoint(rotateGeom["x_trans"], rotateGeom["y_trans"], rotateGeom["z_trans"])
                    pointList.append(zPoint)

        else:
            QgsMessageLog.logMessage(
                "Achtung, die Geometrie kann nicht verarbeitet werden!", "T2G Archäologie", Qgis.Info
            )

        emptyTargetGeometry.addPoints(self.punkte_von_profillinie_abheben(pointList))

        retTargetGeometry = self.castMultiGeometry2Single(emptyTargetGeometry)

        return retTargetGeometry

    def profileBuffer(self, bufferSize, aar_direction):

        if aar_direction == "original":
            point1 = self.transformationParamsOriginal["cutting_line"][0][0]
            point2 = self.transformationParamsOriginal["cutting_line"][0][1]

        if aar_direction == "horizontal":
            point1 = self.transformationParamsHorizontal["cutting_line"][0][0]
            point2 = self.transformationParamsHorizontal["cutting_line"][0][1]

        if aar_direction == "absolute height":
            point1 = self.transformationParamsAbsolute["cutting_line"][0][0]
            point2 = self.transformationParamsAbsolute["cutting_line"][0][1]

        start_point = QgsPoint(point1[0], point1[1])
        end_point = QgsPoint(point2[0], point2[1])

        lineGeom = QgsGeometry.fromPolyline([start_point, end_point])
        bufferGeom = lineGeom.buffer(bufferSize, 5)

        return bufferGeom

    ## \brief cast multipoint geometries to single point geometries
    #
    #
    def castMultiGeometry2Single(self, geom):

        geoType = geom.wkbType()
        ret_geom = geom

        # Point25D or PointZ or LineString25D or LineStringZ or Polygon25D or PolygonZ
        if (
            geoType == QgsWkbTypes.Point25D
            or geoType == QgsWkbTypes.PointZ
            or geoType == QgsWkbTypes.LineString25D
            or geoType == QgsWkbTypes.LineStringZ
            or geoType == QgsWkbTypes.Polygon25D
            or geoType == QgsWkbTypes.PolygonZ
        ):
            return ret_geom

        # PointM or PointZM
        if geoType == QgsWkbTypes.PointM or geoType == QgsWkbTypes.PointZM:
            geom_total = geom.coerceToType(QgsWkbTypes.PointZ)

        # LineString or MultiLineString or MultiLineString25D or MultiLineStringZ or MultiLineStringM or MultiLineStringZM
        if (
            geoType == QgsWkbTypes.LineString
            or geoType == QgsWkbTypes.MultiLineString
            or geoType == QgsWkbTypes.MultiLineString25D
            or geoType == QgsWkbTypes.MultiLineStringZ
            or geoType == QgsWkbTypes.MultiLineStringM
            or geoType == QgsWkbTypes.MultiLineStringZM
        ):
            # LineString25D
            geom_total = geom.coerceToType(QgsWkbTypes.LineString25D)

        # Polygon or Multipolygon or MultiPolygon25D or MultiPolygonZ  or MultiPolygonM or MultiPolygonZM
        if (
            geoType == QgsWkbTypes.Polygon
            or geoType == QgsWkbTypes.MultiPolygon
            or geoType == QgsWkbTypes.MultiPolygon25D
            or geoType == QgsWkbTypes.MultiPolygonZ
            or geoType == QgsWkbTypes.MultiPolygonM
            or geoType == QgsWkbTypes.MultiPolygonZM
        ):
            # Polygon25D
            geom_total = geom.coerceToType(QgsWkbTypes.Polygon25D)

        if len(geom_total) >= 2:
            if geom_total[0].isEmpty() or geom_total[0].isGeosValid() == False:
                ret_geom = geom_total[1]
            elif geom_total[1].isEmpty() or geom_total[1].isGeosValid() == False:
                ret_geom = geom_total[0]
            else:
                print("Achtung, es wird der erste Teil der Multi-Geometrie verwendet!")
                ret_geom = geom_total[0]
        elif len(geom_total) == 1:
            ret_geom = geom_total[0]
        else:
            ret_geom = geom_total

        return ret_geom

    def calculate_normal_vector(self, list_of_qgspoints, gewuenschte_laenge):
        # Punkte in NumPy-Array umwandeln
        p1 = np.array([list_of_qgspoints[0].x(), list_of_qgspoints[0].y(), list_of_qgspoints[0].z()])
        p2 = np.array([list_of_qgspoints[1].x(), list_of_qgspoints[1].y(), list_of_qgspoints[1].z()])
        p3 = np.array([list_of_qgspoints[2].x(), list_of_qgspoints[2].y(), list_of_qgspoints[2].z()])

        # Vektoren zwischen den Punkten berechnen
        v1 = p2 - p1
        v2 = p3 - p1

        # Kreuzprodukt berechnen, um den Normalvektor zu erhalten
        normal_vector = np.cross(v1, v2)

        betrag = np.linalg.norm(normal_vector)

        # in Klammern kleine Zahl mit kleiner Zahl zuerst verrechnen (numerische Stabilität):
        return normal_vector * (gewuenschte_laenge / betrag)

    def punkte_von_profillinie_abheben(self, list_of_qgspoints):
        debugging_print = False

        if len(list_of_qgspoints) <= 2:
            return list_of_qgspoints

        is_polygon = False
        if list_of_qgspoints[0] == list_of_qgspoints[-1]:
            # wenn der erste und letzte Punkt gleich sind, dann ist es vermutlich ein Polygon
            is_polygon = True
            if debugging_print:
                for p in list_of_qgspoints:
                    print("original:", p.x(), p.y(), p.z())

        if not is_polygon:
            anzahl_der_abzuhebenden = len(list_of_qgspoints)
            index_stufen = [(i, i) for i in range(anzahl_der_abzuhebenden)]
        else:

            i = 0
            while i < len(list_of_qgspoints) - 1:
                # wenn Abstand kleiner, dann ist es vermutlich ein vormals eingefügter Punkt:
                if list_of_qgspoints[i].distance3D(list_of_qgspoints[i + 1]) < 0.000001:
                    if debugging_print:
                        print("pop", list_of_qgspoints[i], "distance", list_of_qgspoints[i].distance(list_of_qgspoints[i + 1]))
                    list_of_qgspoints.pop(i)
                else:
                    i += 1

            # da im Polygon der letzte Punkt gleich dem ersten ist, diesen weglassen und später extra hinzufügen:
            anzahl_der_abzuhebenden = len(list_of_qgspoints) - 1

            # INFO: Folgendes funktioniert nur, wenn die Profilebene nicht zufällig exakt nord-süd ausgerichtet ist.
            # Finde den Punkt mit dem kleinsten x-Wert:
            extremum_x_index = min(range(anzahl_der_abzuhebenden), key=lambda i: list_of_qgspoints[i].x())
            if extremum_x_index == 0:
                # Wenn der Punkt mit dem kleinsten x-Wert zugleich der Anfang des Polygons ist,
                # verwende Punkt mit dem größten x-Wert:
                extremum_x_index = max(range(anzahl_der_abzuhebenden), key=lambda i: list_of_qgspoints[i].x())

            index_stufen = []
            for i in range(anzahl_der_abzuhebenden):
                if i == extremum_x_index:
                    # Zum verschnittfreien Schließen des Polygons in der 2D-Kartenansicht
                    # zusätzlichen Punkt einfügen:
                    index_stufen.append((i, anzahl_der_abzuhebenden))
                # Stufen beginnen beim Extrem-Punkt (extremum_x_index) und enden beim eingefügten Punkt:
                abhebung_stufe = (i - extremum_x_index) % anzahl_der_abzuhebenden
                index_stufen.append((i, abhebung_stufe))

        if debugging_print:
            print("index_stufen", index_stufen)

        abhebung = 0.000001  # 1000stel mm
        # abhebung = 0.001  # zum Angucken
        shifted_points = []
        for index, abhebung_stufe in index_stufen:
            # Punkte laut Plan (index_stufen) fortlaufend von der Profilwand abheben ...

            vektor_abhebung = self.calculate_normal_vector(list_of_qgspoints, abhebung_stufe * abhebung)

            if debugging_print:
                print(f"{index:2d} Vektor der Abhebung: {vektor_abhebung}, Betrag {np.linalg.norm(vektor_abhebung)}")

            shifted_points.append(
                QgsPoint(
                    list_of_qgspoints[index].x() + vektor_abhebung[0],
                    list_of_qgspoints[index].y() + vektor_abhebung[1],
                    list_of_qgspoints[index].z() + vektor_abhebung[2]
                )
            )

        if is_polygon:
            # letzter Punkt wurde oben ausgelassen - muss aber gleich mit dem ersten sein:
            shifted_points.append(shifted_points[0])

            if debugging_print:
                for p in shifted_points:
                    print("shifted:", p.x(), p.y(), p.z())

        fehler = (abhebung * 1000) * max(index_stufen, key=lambda i: i[1])[1]
        print(
            f"Abhebung: {abhebung * 1000:.15f}mm\n"
            f"Fehler insgesamt: {fehler:.15f}mm"
        )
        if fehler > 0.5:
            QgsMessageLog.logMessage(
                f"Achtung, iterative Abhebung der Punkte von der Profillinie ergibt einen Fehler von "
                f"zuletzt {fehler:.15f}mm!", "T2G Archäologie", Qgis.Warning
            )

        return shifted_points
