"""
MIT License

Copyright (c) 2020 Gabriel De Luca

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import numpy as np


class Simil:
    def __init__(self):
        """ """

    # =================
    # Private functions
    # =================

    @staticmethod
    def _get_scalar(alpha_0, q_coords=None):
        if q_coords is None:
            scalar = np.einsum("i->", alpha_0)
        else:
            scalar = np.einsum("i,i->", alpha_0, (q_coords * q_coords).sum(0))
        return scalar

    @staticmethod
    def _get_q_matrix(quaternions):
        q_matrix = [
            [
                [q[3], -q[2], q[1], q[0]],
                [q[2], q[3], -q[0], q[1]],
                [-q[1], q[0], q[3], q[2]],
                [-q[0], -q[1], -q[2], q[3]],
            ]
            for q in quaternions
        ]
        return np.array(q_matrix)

    @staticmethod
    def _get_w_matrix(quaternions):
        w_matrix = [
            [
                [q[3], q[2], -q[1], q[0]],
                [-q[2], q[3], q[0], q[1]],
                [q[1], -q[0], q[3], q[2]],
                [-q[0], -q[1], -q[2], q[3]],
            ]
            for q in quaternions
        ]
        return np.array(w_matrix)

    @staticmethod
    def _get_abc_matrices(alpha_0, m1, m2=None):
        if m2 is None:
            matrix = np.einsum("i,ijk->jk", alpha_0, m1)
        else:
            matrix = np.einsum("i,ijk->jk", alpha_0, np.transpose(m1, (0, 2, 1)) @ m2)
        return matrix

    @staticmethod
    def _get_blc_matrix(b_matrix, lambda_i, c_matrix):
        blc_matrix = b_matrix - lambda_i * c_matrix
        return blc_matrix

    @staticmethod
    def _get_d_matrix(li, cs, am, blcm):
        d_matrix = 2 * li * am + (1 / cs) * (blcm.T @ blcm)
        return d_matrix

    @staticmethod
    def _get_r_quat(d_matrix):
        eigvals, eigvects = np.linalg.eig(d_matrix)
        beta_1 = np.argmax(eigvals)
        r_quat = eigvects[:, beta_1]
        return beta_1, r_quat

    @staticmethod
    def _get_lambda_next(am, bs, bm, cs, cm, rq):
        expr_1 = rq.T @ am @ rq
        expr_2 = (1 / cs) * (rq.T @ bm.T @ cm @ rq)
        expr_3 = (1 / cs) * (rq.T @ cm.T @ cm @ rq)
        lambda_next = (expr_1 - expr_2) / (bs - expr_3)
        return lambda_next

    @staticmethod
    def _get_solution(am, bs, bm, cs, cm, scale, li, i):
        blc_matrix = Simil._get_blc_matrix(bm, li, cm)
        d_matrix = Simil._get_d_matrix(li, cs, am, blc_matrix)
        beta_1, r_quat = Simil._get_r_quat(d_matrix)
        if scale is False:
            return blc_matrix, d_matrix, beta_1, r_quat, li, i
        else:
            lambda_next = Simil._get_lambda_next(am, bs, bm, cs, cm, r_quat)
            if abs(li - lambda_next) < 0.000001:
                return blc_matrix, d_matrix, beta_1, r_quat, li, i
            else:
                li, i = lambda_next, i + 1
                return Simil._get_solution(am, bs, bm, cs, cm, scale, li, i)

    @staticmethod
    def _get_r_matrix(r_quat):
        r_w_matrix = Simil._get_w_matrix([r_quat])[0]
        r_q_matrix = Simil._get_q_matrix([r_quat])[0]
        r_matrix = (r_w_matrix.T @ r_q_matrix)[:3, :3]
        return r_matrix

    @staticmethod
    def _get_s_quat(c_scalar, blcm, r_quat):
        s_quat = 1 / (2 * c_scalar) * (blcm @ r_quat)
        return s_quat

    @staticmethod
    def _get_t_vector(r_quat, s_quat):
        r_w_matrix = Simil._get_w_matrix([r_quat])[0]
        t_vector = [2 * (r_w_matrix.T @ s_quat)[:3]]
        return t_vector

    # ================
    # Process function
    # ================

    @staticmethod
    def process(source_points, target_points, alpha_0=None, scale=True, lambda_0=1.0):
        """
        Find similarity transformation parameters given a set of control points

        Parameters
        ----------
        source_points : array_like
            The function will try to cast it to a numpy array with shape:
            ``(n, 3)``, where ``n`` is the number of points.
            Two points is the minimum requeriment (in that case, the solution
            will map well all points that belong in the rect that passes
            through both control points).
        target_points : array_like
            The function will try to cast it to a numpy array with shape:
            ``(n, 3)``, where ``n`` is the number of points.
            The function will check that there are as many target points
            as source points.
        alpha_0 : array_like, optional
            Per point weights.
            If provided, the function will try to cast to a numpy array with
            shape: ``(n,)``.
        scale : boolean, optional
            Allow to find a multiplier factor different from lambda_0.
            Default is True.
        lambda_0 : float, optional
            Multiplier factor to find the first solution. Default is 1.0.
            If `scale=True`, a recursion is implemented to find a better
            value. If it is negative, forces mirroring. Can't be zero.

        Returns
        -------
        lambda_i : float
            Multiplier factor.
        r_matrix : numpy.ndarray
            Rotation matrix.
        t_vector : numpy.ndarray
            Translation (column) vector.
        """

        # declarations and checkups

        source_coords = np.array(source_points, dtype=float).T

        if source_coords.ndim != 2:
            err_msg = "source_points array must have dimension = 2."
            raise ValueError(err_msg)

        if source_coords.shape[0] != 3:
            err_msg = "There are not three coordinates in source points."
            raise ValueError(err_msg)

        n = source_coords.shape[1]

        if n == 1 or (source_coords[None, 0] == source_coords).all():
            err_msg = "There are not two distinct source points."
            raise ValueError(err_msg)

        target_coords = np.array(target_points, dtype=float).T

        if target_coords.ndim != 2:
            err_msg = "target_points array must have dimension = 2."
            raise ValueError(err_msg)

        if target_coords.shape[0] != 3:
            err_msg = "There are not three coordinates in target points."
            raise ValueError(err_msg)

        if target_coords.shape[1] != n:
            err_msg = "There are not as many target points as source points."
            raise ValueError(err_msg)

        if alpha_0 is None:
            alpha_0 = np.ones(n)
        else:
            alpha_0 = np.array(alpha_0, dtype=float)

        if alpha_0.ndim != 1:
            err_msg = "alpha_0 array must have dimension = 1."
            raise ValueError(err_msg)

        if alpha_0.shape != (n,):
            err_msg = "There are not as many alpha_0 coefficients as " "control points."
            raise ValueError(err_msg)

        lambda_0 = float(lambda_0)

        if lambda_0 == 0:
            err_msg = "lambda_0 cannot be zero."
            raise ValueError(err_msg)

        # processes

        source_q_coords = np.concatenate((source_coords, np.zeros((1, n))))

        target_q_coords = np.concatenate((target_coords, np.zeros((1, n))))

        b_scalar = Simil._get_scalar(alpha_0, source_q_coords)

        c_scalar = np.einsum("i->", alpha_0)

        q0_w_matrix = Simil._get_w_matrix(source_q_coords.T)

        qt_q_matrix = Simil._get_q_matrix(target_q_coords.T)

        a_matrix = Simil._get_abc_matrices(alpha_0, q0_w_matrix, qt_q_matrix)

        b_matrix = Simil._get_abc_matrices(alpha_0, qt_q_matrix)

        c_matrix = Simil._get_abc_matrices(alpha_0, q0_w_matrix)

        lambda_i, i = lambda_0, 1

        blc_matrix, d_matrix, beta_1, r_quat, lambda_i, i = Simil._get_solution(
            a_matrix, b_scalar, b_matrix, c_scalar, c_matrix, scale, lambda_i, i
        )

        r_matrix = Simil._get_r_matrix(r_quat)

        s_quat = Simil._get_s_quat(c_scalar, blc_matrix, r_quat)

        t_vector = np.array(Simil._get_t_vector(r_quat, s_quat)).reshape(3, 1)

        return lambda_i, r_matrix, t_vector
