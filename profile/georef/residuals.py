import numpy as np
import math

class Residuals:
    def __init__(self):
        pass

    def testFunc(self):
        print('funzt')

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

        return V_X, V_Y, V_XY, V_XY_uuid, mo, mox, moy, [a, b, c, d]

    #POLYNOMIAL TRANSFORMATIONS
    def polynomial(self, order, points_arr, Ax_row, Ay_row, LX_row, LY_row): #( {1, 2 or 3}, np.array, x-row, y-row, X-row, Y-row)
        n = len(points_arr)
        points = np.zeros((len(points_arr), 4), dtype=np.float)
        points[:, 0] = points_arr[:, Ax_row]
        points[:, 1] = points_arr[:, Ay_row]
        points[:, 2] = points_arr[:, LX_row]
        points[:, 3] = points_arr[:, LY_row]
        if order == 1:
            #X = a0 + a1x + a2y
            #Y = b0 + b1x + b2y
            Axy = np.zeros((len(points_arr), 3), dtype=np.float)
            Axy[:, 0] = 1
            Axy[:,1:3] = points[:, 0:2]
        elif order == 2:
            #X = a0 + a1x + a2y + a3xy + a4x^2 + a5y^2
            #Y = b0 + b1x + b2y + b3xy + b4x^2 + b5y^2
            Axy = np.zeros((len(points_arr), 6), dtype=np.float)
            Axy[:, 0] = 1 #a0
            Axy[:, 1] = points[ : , 0] # a1
            Axy[:, 2] = points[ : , 1] # a2
            Axy[:, 3] = points[ : , 0] * points[ : , 1] # ...
            Axy[:, 4] = points[ : , 0] * points[ : , 0]
            Axy[:, 5] = points[ : , 1] * points[ : , 1]
        elif order == 3:
            #X = a0 + a1x + a2y + a3xy + a4x^2 + a5y^2 + a6x^3 + a7x^2y + a8xy^2 + a9y^3
            #Y = b0 + b1x + b2y + b3xy + b4x^2 + b5y^2 + b6x^3 + b7x^2y + b8xy^2 + b9y^3
            Axy = np.zeros((len(points_arr), 10), dtype=np.float)
            Axy[:, 0] = 1 #a0
            Axy[:, 1] = points[ : , 0] # a1
            Axy[:, 2] = points[ : , 1] # a2
            Axy[:, 3] = points[ : , 0] * points[ : , 1] # ...
            Axy[:, 4] = points[ : , 0] * points[ : , 0]
            Axy[:, 5] = points[ : , 1] * points[ : , 1] #
            Axy[:, 6] = points[ : , 0] * points[ : , 0] * points[ : , 0]
            Axy[:, 7] = points[ : , 0] * points[ : , 0] * points[ : , 1]
            Axy[:, 8] = points[ : , 0] * points[ : , 1] * points[ : , 1]
            Axy[:, 9] = points[ : , 1] * points[ : , 1] * points[ : , 1]

        BX = points[ : , 2]
        BY = points[ : , 3]

        aaa_X = np.linalg.lstsq(Axy,BX) #transf parameters calculation using least square method
        bbb_Y = np.linalg.lstsq(Axy,BY)

        predXs = Axy.dot(aaa_X[0])
        predYs = Axy.dot(bbb_Y[0])

        V_X = points[ : , 2] - np.array(predXs)
        V_Y = points[ : , 3] - np.array(predYs)
        V_XY = np.sqrt(V_X*V_X + V_Y*V_Y)

        V_XY_sum_sq, V_X_sum_sq, V_Y_sum_sq = 0, 0, 0
        for i in range(n):
            V_XY_sum_sq += V_XY[i]*V_XY[i]
            V_X_sum_sq += V_X[i]*V_X[i]
            V_Y_sum_sq += V_Y[i]*V_Y[i]

        mo = math.sqrt(V_XY_sum_sq/(n)) #avarage error
        mox = math.sqrt(V_X_sum_sq/(n)) #avarage x error
        moy = math.sqrt(V_Y_sum_sq/(n)) #avarage y error

        return V_X, V_Y, V_XY, mo, mox, moy, aaa_X[0], bbb_Y[0]
