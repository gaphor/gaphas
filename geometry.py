"""
Geometry functions
"""
import operator

def matrix_identity():
    """
    >>> len(matrix_identity())
    6
    """
    return (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)

def matrix_multiply(m1, m2):
    """Multiply two transformation matrices.
    """
    d0 = m1[0] * m2[0] + m1[1] * m2[2];
    d1 = m1[0] * m2[1] + m1[1] * m2[3];
    d2 = m1[2] * m2[0] + m1[3] * m2[2];
    d3 = m1[2] * m2[1] + m1[3] * m2[3];
    d4 = m1[4] * m2[0] + m1[5] * m2[2] + m2[4];
    d5 = m1[4] * m2[1] + m1[5] * m2[3] + m2[5];
    return (d0, d1, d2, d3, d4, d5)


def matrix_invert(m):
    """
    """
    r_det = 1.0 / (m[0] * m[3] - m[1] * m[2]);
    dst0 = m[3] * r_det;
    dst1 = -m[1] * r_det;
    dst2 = -m[2] * r_det;
    dst3 = m[0] * r_det;
    dst4 = -m[4] * dst[0] - m[5] * dst[2];
    dst5 = -m[4] * dst[1] - m[5] * dst[3];
    return (dst0, dst1, dst2, dst3, dst4, dst5)

def matrix_scale(m, sx, sy):
    """
    """
    m2 = (float(sx), 0.0, 0.0, float(sy), 0.0, 0.0)
    return matrix_multiply(m, m2)

def matrix_rotate(m, radians):
    """
    """
    s = math.sin(radians)
    c = math.cos(radians)
    m2 = (c, s, -s, c, 0.0, 0.0)
    return matrix_multiply(m, m2)
    
def matrix_shear(m, radians):
    """
    """
    t = math.tan(radians)
    m2 = (1.0, 0.0, t, 1.0, 0.0, 0.0)
    return matrix_multiply(m, m2)

if __name__ = '__main__':
    import doctest
    doctest.testmod()

