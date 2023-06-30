from PIL import Image
import numpy as np
import math

from qgis.core import QgsPointXY
from qgis.analysis import QgsGcpTransformerInterface


class ImageGeoref:
    def __init__(self):
        self.image_file_in = ""
        self.image_file_out = ""
        self.gcp_points = ""
        self.crs = ""

    def run_georef(self, georefData, crs, imageFileIn, imageFileOut):
        self.image_file_in = imageFileIn
        self.image_file_out = imageFileOut
        self.gcp_points = georefData
        self.crs = crs

        if len(self.gcp_points) < 4:
            return "error"

        self._start_projective()
        return "ok"

    def _start_projective(self):
        # source image
        with Image.open(self.image_file_in) as imgOrg:
            imgOrg.load()
        src_w, src_h = imgOrg.size
        imgOrg.close()

        # vertices of source image (Ecken - Bildraum)
        src_ll = (0, -src_h)
        src_lr = (src_w, -src_h)
        src_ur = (src_w, 0)
        src_ul = (0, 0)

        ############ QgsGcpTransformerInterface ##########

        src_cp = []
        geo_cp = []
        for point in self.gcp_points:
            src_cp.append(QgsPointXY(float(point["input_x"]), float(point["input_z"]) * -1))
            geo_cp.append(QgsPointXY(float(point["aar_x"]), float(point["aar_z"])))

        # (1) get matrix for transformation T1 (src → geo) from 4...n control points
        transformMethod = QgsGcpTransformerInterface.TransformMethod(6)  # 6 - projective
        qgisTransformer = QgsGcpTransformerInterface.createFromParameters(transformMethod, src_cp, geo_cp)

        # get extent of destination image in georeferenced area
        # transformation of source image vertices with transformation T1
        # Ecken in Geokoordinaten
        geo_vp_ul = qgisTransformer.transform(src_ul[0], src_ul[1], False)[1:3]
        geo_vp_ll = qgisTransformer.transform(src_ll[0], src_ll[1], False)[1:3]
        geo_vp_ur = qgisTransformer.transform(src_ur[0], src_ur[1], False)[1:3]
        geo_vp_lr = qgisTransformer.transform(src_lr[0], src_lr[1], False)[1:3]

        # calculation of destination image extent in georeferenced area
        # Ausdehnung Geo
        geo_left = min(geo_vp_ul[0], geo_vp_ll[0], geo_vp_ur[0], geo_vp_lr[0])
        geo_lower = min(geo_vp_ul[1], geo_vp_ll[1], geo_vp_ur[1], geo_vp_lr[1])
        geo_right = max(geo_vp_ul[0], geo_vp_ll[0], geo_vp_ur[0], geo_vp_lr[0])
        geo_upper = max(geo_vp_ul[1], geo_vp_ll[1], geo_vp_ur[1], geo_vp_lr[1])

        geo_ll = np.array([geo_left, geo_lower])
        geo_lr = np.array([geo_right, geo_lower])
        geo_ur = np.array([geo_right, geo_upper])
        geo_ul = np.array([geo_left, geo_upper])

        geo_w = geo_right - geo_left
        geo_h = geo_upper - geo_lower

        # (3) get transformation T2 from extent of destination image in local
        # (3a) shift upper left vertex to (0,0)
        t2_shift = np.array([-geo_left, -geo_upper])

        # (3b) resolution of destination image in pixel/m
        # calculated from image extent

        # Strecke oben-links zu unten-rechts

        dist_geo = math.dist(geo_vp_ul, geo_vp_lr)
        dist_img = math.dist(src_ul, src_lr)

        res_geo = dist_img / dist_geo
        res_img = dist_geo / dist_img

        dst_resolution = res_geo

        # (3c) scaling with resolution of destination image
        # korrigiert
        dst_w = dst_resolution * geo_w  # Anzahl Pixel im Bildraum
        dst_h = dst_resolution * geo_h

        # (as 2-dimensional vectors:)

        dst_ll = dst_resolution * (geo_ll + t2_shift)
        dst_lr = dst_resolution * (geo_lr + t2_shift)
        dst_ur = dst_resolution * (geo_ur + t2_shift)
        dst_ul = dst_resolution * (geo_ul + t2_shift)

        # (4) T2-transformation of the 4 T1-transformed vertices of source image
        # (taken from (2))
        dst_vp_ul = dst_resolution * (geo_vp_ul + t2_shift)
        dst_vp_ll = dst_resolution * (geo_vp_ll + t2_shift)
        dst_vp_ur = dst_resolution * (geo_vp_ur + t2_shift)
        dst_vp_lr = dst_resolution * (geo_vp_lr + t2_shift)

        ########### PIL ##########

        ### goe: hier spiegeln wir die Koordinaten von src und dst vom 4. in den 1. Quadranten, weil Pillow nur mit
        # positiven Passpunkten arbeitet
        ### goe: anstatt 'abs' (das wäre nur bei positiven x-Werten richtig, die wir aber im Prinzip auch haben)
        ### goe: schlage ich aber die Multiplikation mit (1, -1) vor, d.h. alle y-Werte werden mit -1 multipliziert
        # imgCoordEdges = [src_ul, src_ur, src_lr, src_ll]
        ### goe: und 'edges' sind Kanten, reduzieren wir lieber auf imgCoords
        imgCoords = np.multiply([src_ul, src_ur, src_lr, src_ll], (1, -1))
        # projectiveCoordEdges = [tuple(dst_vp_ul), tuple(dst_vp_ur), tuple(dst_vp_lr), tuple(dst_vp_ll)]
        projectiveCoords = np.multiply(
            [tuple(dst_vp_ul), tuple(dst_vp_ur), tuple(dst_vp_lr), tuple(dst_vp_ll)],
            (1, -1),
        )
        coeffs = self._find_pill_coeffs(projectiveCoords, imgCoords)

        self._img_transform(self.image_file_in, self.image_file_out, coeffs, dst_h, dst_w)
        worldfilePath = self.image_file_out[:-3] + "wld"

        self._write_world_file(worldfilePath, geo_ul, res_img)

    def _find_pill_coeffs(self, pa, pb):
        # where pb is the four vertices in the current plane, and pa contains four vertices in the resulting plane.
        matrix = []
        for p1, p2 in zip(pa, pb):
            matrix.append([p1[0], p1[1], 1, 0, 0, 0, -p2[0] * p1[0], -p2[0] * p1[1]])
            matrix.append([0, 0, 0, p1[0], p1[1], 1, -p2[1] * p1[0], -p2[1] * p1[1]])

        A = np.matrix(matrix, dtype=np.float)
        B = np.array(pb).reshape(8)

        res = np.dot(np.linalg.inv(A.T * A) * A.T, B)
        return np.array(res).reshape(8)

    def _img_transform(self, image_in, image_out, coeffs, heightDst, widthDst):
        with Image.open(image_in) as img:
            img.load()

        img.transform(
            size=(int(widthDst), int(heightDst)),
            method=Image.PERSPECTIVE,
            data=coeffs,
            resample=Image.BICUBIC,
            fillcolor="white",
        ).save(image_out, quality=100)

        img.close()

    def _write_world_file(self, worldfilePath, geo_ul, res_img):
        pixelwidth = res_img
        pixelheight = res_img * -1

        lines = [
            str(pixelwidth),
            str(0.0),
            str(0.0),
            str(pixelheight),
            str(geo_ul[0]),
            str(geo_ul[1]),
        ]
        with open(worldfilePath, "w") as f:
            for line in lines:
                f.write(line)
                f.write("\n")
