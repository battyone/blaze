from __future__ import absolute_import, division, print_function

from .expressions import Expr, ndim, symbol
from datashape import DataShape
from collections import Iterable

__all__ = 'Transpose', 'TensorDot', 'dot', 'transpose', 'tensordot'

class Transpose(Expr):
    """ Transpose dimensions in an N-Dimensional array

    Examples
    --------

    >>> x = symbol('x', '10 * 20 * int32')
    >>> x.T
    transpose(x)
    >>> x.T.shape
    (20, 10)

    Specify axis ordering with axes keyword argument

    >>> x = symbol('x', '10 * 20 * 30 * int32')
    >>> x.transpose([2, 0, 1])
    transpose(x, axes=[2, 0, 1])
    >>> x.transpose([2, 0, 1]).shape
    (30, 10, 20)
    """

    __slots__ = '_hash', '_child', 'axes'

    @property
    def dshape(self):
        s = self._child.shape
        return DataShape(*(tuple([s[i] for i in self.axes]) +
                           (self._child.dshape.measure,)))

    def __str__(self):
        if self.axes == tuple(range(ndim(self)))[::-1]:
            return 'transpose(%s)' % self._child
        else:
            return 'transpose(%s, axes=%s)' % (self._child,
                    str(list(self.axes)))


def transpose(expr, axes=None):
    if axes is None:
        assert ndim(expr) == 2
        axes = (1, 0)
    if isinstance(axes, list):
        axes = tuple(axes)
    return Transpose(expr, axes)

transpose.__doc__ = Transpose.__doc__


def T(expr):
    return transpose(expr)


class TensorDot(Expr):
    """ Dot Product: Contract and sum dimensions of two arrays

    >>> x = symbol('x', '20 * 20 * int32')
    >>> y = symbol('y', '20 * 30 * int32')

    >>> x.dot(y)
    tensordot(x, y)

    >>> tensordot(x, y, axes=[0, 0])
    tensordot(x, y, axes=[0, 0])
    """

    __slots__ = '_hash', 'lhs', 'rhs', '_left_axes', '_right_axes'
    __inputs__ = 'lhs', 'rhs'

    @property
    def dshape(self):
        shape = tuple([d for i, d in enumerate(self.lhs.shape)
                         if i not in self._left_axes] +
                      [d for i, d in enumerate(self.rhs.shape)
                         if i not in self._right_axes])
        # TODO: handle type promotion
        return DataShape(*(shape + (self.lhs.dshape.measure,)))

    def __str__(self):
        if self.isidentical(tensordot(self.lhs, self.rhs)):
            return 'tensordot(%s, %s)' % (self.lhs, self.rhs)
        else:
            la = self._left_axes
            if len(la) == 1:
                la = la[0]
            ra = self._right_axes
            if len(ra) == 1:
                ra = ra[0]
            return 'tensordot(%s, %s, axes=[%s, %s])' % (
                    self.lhs, self.rhs, str(la), str(ra))


def tensordot(lhs, rhs, axes=None):
    if axes is None:
        left = ndim(lhs) - 1
        right = 0
    elif isinstance(axes, Iterable):
        left, right = axes
    else:
        left, right = axes, axes

    if isinstance(left, int):
        left = (left,)
    if isinstance(right, int):
        right = (right,)
    if isinstance(left, list):
        left = tuple(left)
    if isinstance(right, list):
        right = tuple(right)

    return TensorDot(lhs, rhs, left, right)

tensordot.__doc__ = TensorDot.__doc__

def dot(lhs, rhs):
    return tensordot(lhs, rhs)


from datashape.predicates import isnumeric, isboolean
from .expressions import dshape_method_list, method_properties

dshape_method_list.extend([
    (lambda ds: ndim(ds) > 1, set([transpose])),
    (lambda ds: ndim(ds) == 2, set([T])),
    (lambda ds: ndim(ds) >= 1 and (isnumeric(ds) or isboolean(ds)), set([dot]))
    ])

method_properties.add(T)
