import numpy as np
import math
from qgis.analysis import QgsGcpTransformerInterface
from qgis.core import QgsPointXY


class Residuals:
    def __init__(self):
        pass

    #HELMERT  TRANSFORMATIONS
    def projective_trans(self, gcps_uuid): #cgps is numpy.array [x, y, Xmap, Ymap]

        gcps = gcps_uuid[:,0:4].astype(np.float32)
        n = len(gcps)

        src_cp = []
        geo_cp = []
        for point in gcps:
            src_cp.append(QgsPointXY(float(point[0]), float(point[1]) * -1 ))
            geo_cp.append(QgsPointXY(float(point[2]), float(point[3])))

        transformMethod = QgsGcpTransformerInterface.TransformMethod(6) # 6 - projective
        qgisTransformer = QgsGcpTransformerInterface.createFromParameters(transformMethod, src_cp, geo_cp)

        Xi = []
        Yi = []
        for point in gcps:
            checkPoint = qgisTransformer.transform(float(point[0]), float(point[1]) * -1, False)[1:3]
            Xi.append(checkPoint[0])
            Yi.append(checkPoint[1])

        #JANEK compare calculated values to "clicked" ones
        V_X = Xi - gcps[:,2]
        V_Y = Yi - gcps[:,3]
        V_XY = np.sqrt(V_X*V_X + V_Y*V_Y)
        
        V_XY_uuid = []
        V_XY_sum_sq, V_X_sum_sq, V_Y_sum_sq = 0, 0, 0
        for i in range(n):
            V_XY_sum_sq += V_XY[i]*V_XY[i]
            V_X_sum_sq += V_X[i]*V_X[i]
            V_Y_sum_sq += V_Y[i]*V_Y[i]

            V_XY_uuid.append({'v_xy': V_XY[i], 'uuid': gcps_uuid[i,4]})

        mo = math.sqrt(V_XY_sum_sq/(n)) #avarage error
        mox = math.sqrt(V_X_sum_sq/(n)) #avarage x error
        moy = math.sqrt(V_Y_sum_sq/(n)) #avarage y error

        return V_X, V_Y, V_XY, V_XY_uuid, mo, mox, moy

    #HELMERT  TRANSFORMATIONS
    def helm_trans(self, gcps_uuid): #cgps is numpy.array [x, y, Xmap, Ymap]
        print('gcps_uuid',gcps_uuid)
        gcps = gcps_uuid[:,0:4].astype(np.float32)
        print('gcps',gcps)
        n = len(gcps)
        print('n',n)
        xo, yo, Xo, Yo = 0.0, 0.0, 0.0, 0.0

        #JANEK calculate center of gravity
        for i in range(n):
            xo, yo, Xo, Yo = xo + gcps[i,0], yo + gcps[i,1], Xo + gcps[i,2], Yo + gcps[i,3]

        xo, yo, Xo, Yo = xo/n, yo/n, Xo/n, Yo/n

        del_x, del_y, del_X, del_Y = gcps[:,0] - xo, gcps[:,1] - yo, gcps[:,2] - Xo, gcps[:,3] - Yo

        #JANEK calculation of unknowns
        a_up, a_down, b_up, b_down= 0, 0, 0, 0
        for i in range(n):
            a_up += del_x[i]*del_Y[i] - del_y[i]*del_X[i]
            a_down += del_x[i]*del_x[i] + del_y[i]*del_y[i]
            b_up += del_x[i]*del_X[i] + del_y[i]*del_Y[i]

        b_down = a_down
        a = a_up/a_down
        b= b_up/b_down
        c = yo*a - xo*b + Xo
        d = -xo*a - yo*b + Yo # a,b,c,d are transformation parameters X = c + b*x - a*y / Y = d + a*x + b*y

        #JANEK calculate new coordinates for points based on transformation values
        Xi = (gcps[:,0] - xo)*b - (gcps[:,1] - yo)*a + Xo
        Yi = (gcps[:,0] - xo)*a + (gcps[:,1] - yo)*b + Yo

        print('Xi', Xi)

        #JANEK compare calculated values to "clicked" ones
        V_X = Xi - gcps[:,2]
        V_Y = Yi - gcps[:,3]
        V_XY = np.sqrt(V_X*V_X + V_Y*V_Y)

        print('V_XY', V_XY)

        V_XY_uuid = []
        V_XY_sum_sq, V_X_sum_sq, V_Y_sum_sq = 0, 0, 0
        for i in range(n):
            V_XY_sum_sq += V_XY[i]*V_XY[i]
            V_X_sum_sq += V_X[i]*V_X[i]
            V_Y_sum_sq += V_Y[i]*V_Y[i]

            V_XY_uuid.append({'v_xy': V_XY[i], 'uuid': gcps_uuid[i,4]})

        mo = math.sqrt(V_XY_sum_sq/(n)) #avarage error
        mox = math.sqrt(V_X_sum_sq/(n)) #avarage x error
        moy = math.sqrt(V_Y_sum_sq/(n)) #avarage y error

        return V_X, V_Y, V_XY, V_XY_uuid, mo, mox, moy, [a, b, c, d]

