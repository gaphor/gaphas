from gaphas.matrix import Matrix


def test_multiply_equals_should_result_in_same_matrix():
    m1 = Matrix()
    m2 = m1
    m2 *= Matrix(20, 20)

    assert m1 is m2
