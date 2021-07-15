import numpy as np

class Transformation(object):

    def __init__(self):
        '''
        Create transformation which allows you to do forward and inverse
        transformation and view the transformation parameters.
        :param ttype: similarity, bilinear, projective, polynomial, affine
            transformation type
        :param params: :class:`numpy.array`
            transformation parameters
        :param params: :class:`numpy.array`
            explicit transformation parameters as
        '''

        self.params = None


    def make_tform(self, src, dst):
        '''
        Create spatial transformation.
        You can determine the over-, well- and under-determined parameters
        with the least-squares method.
        The following transformation types are supported:
            NAME / TTYPE            DIM     NUM POINTS FOR EXACT SOLUTION
            similarity:              2D      2
            bilinear:               2D      4
            projective:             2D      4
            polynomial (order n):  2D      (n+1)*(n+2)/2
            affine:                 2D      3
            affine:                 3D      4
        Number of source must match number of destination coordinates.
        :param ttype: similarity, bilinear, projective, polynomial, affine
            transformation type
        :param src: :class:`numpy.array`
            Nx2 or Nx3 coordinate matrix of source coordinate system
        :param src: :class:`numpy.array`
            Nx2 or Nx3 coordinate matrix of destination coordinate system
        :returns: :class:`Transformation`
        '''

        self.params = self.make_projective(src, dst)
        #return Transformation(ttype, params, params_explicit)

    def fwd(self, coords):
        '''
        Apply forward transformation.
        :param coords: :class:`numpy.array`
            Nx2 or Nx3 coordinate matrix
        '''

        single = False
        if coords.ndim == 1:
            coords = np.array([coords])
            single = True
        result = self.projective_transform(coords, self.params, inverse=False)
        if single:
            return result[0]
        return result

    def inv(self, coords):
        '''
        Apply inverse transformation.
        :param coords: :class:`numpy.array`
            Nx2 or Nx3 coordinate matrix
        '''

        single = False
        if coords.ndim == 1:
            coords = np.array([coords])
            single = True
        result = self.projective_transform(coords, self.params, inverse=True)
        if single:
            return result[0]
        return result

    def make_projective(self, src, dst):
        '''
        Determine parameters of 2D projective transformation in the order:
            a0, a1, a2, b0, b1, b2, c0, c1
        where the transformation is defined as:
            X = (a0+a1*x+a2*y) / (1+c0*x+c1*y)
            Y = (b0+b1*x+b2*y) / (1+c0*x+c1*y)
        You can determine the over-, well- and under-determined parameters
        with the least-squares method.
        :param src: :class:`numpy.array`
            Nx2 coordinate matrix of source coordinate system
        :param src: :class:`numpy.array`
            Nx2 coordinate matrix of destination coordinate system
        :returns: params, None
        '''

        xs = src[:,0]
        ys = src[:,1]
        rows = src.shape[0]
        A = np.zeros((rows*2, 8))
        A[:rows,0] = 1
        A[:rows,1] = xs
        A[:rows,2] = ys
        A[rows:,3] = 1
        A[rows:,4] = xs
        A[rows:,5] = ys
        A[:rows,6] = - dst[:,0] * xs
        A[:rows,7] = - dst[:,0] * ys
        A[rows:,6] = - dst[:,1] * xs
        A[rows:,7] = - dst[:,1] * ys
        b = np.zeros((rows*2,))
        b[:rows] = dst[:,0]
        b[rows:] = dst[:,1]
        params = np.linalg.lstsq(A, b)[0]
        return params

    def projective_transform(self, coords, params, inverse=False):
        '''
        Apply projective transformation.

        :param coords: :class:`numpy.array`
            Nx2 coordinate matrix of source coordinate system
        :param params: :class:`numpy.array`
            parameters returned by `make_tform`
        :param inverse: bool
            apply inverse transformation, default is False

        :returns: :class:`numpy.array`
            transformed coordinates
        '''

        a0, a1, a2, b0, b1, b2, c0, c1 = params
        x = coords[:,0]
        y = coords[:,1]
        out = np.zeros(coords.shape)
        if inverse:
            out[:,0] = (a2*b0-a0*b2+(b2-b0*c1)*x+(a0*c1-a2)*y) \
                / (a1*b2-a2*b1+(b1*c1-b2*c0)*x+(a2*c0-a1*c1)*y)
            out[:,1] = (a0*b1-a1*b0+(b0*c0-b1)*x+(a1-a0*c0)*y) \
                / (a1*b2-a2*b1+(b1*c1-b2*c0)*x+(a2*c0-a1*c1)*y)
        else:
            out[:,0] = (a0+a1*x+a2*y) / (1+c0*x+c1*y)
            out[:,1] = (b0+b1*x+b2*y) / (1+c0*x+c1*y)
        return out
