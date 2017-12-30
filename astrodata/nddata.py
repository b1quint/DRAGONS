"""
This module implements a derivative class based on NDData with some Mixins,
implementing windowing and on-the-fly data scaling.
"""

from __future__ import (absolute_import, division, print_function)

from copy import deepcopy

from astropy.nddata import NDData
from astropy.nddata import StdDevUncertainty
from astropy.nddata.mixins.ndslicing import NDSlicingMixin
from astropy.nddata.mixins.ndarithmetic import NDArithmeticMixin
from astropy.io.fits import ImageHDU
import numpy as np

__all__ = ['NDAstroData']

class StdDevAsVariance(object):
    def as_variance(self):
        if self.array is not None:
            return self.array ** 2
        else:
            return None

def new_variance_uncertainty_instance(array):
    obj = StdDevUncertainty(np.sqrt(array))
    cls = obj.__class__
    obj.__class__ = cls.__class__(cls.__name__ + "WithAsVariance", (cls, StdDevAsVariance), {})
    return obj

class FakeArray(object):
    def __init__(self, very_faked):
        self.data = very_faked
        self.shape = (100, 100) # Won't matter. This is just to fool NDData
        self.dtype = np.float32 # Same here

    def __getitem__(self, index):
        # FAKE NEWS!
        return None

    def __array__(self):
        return self.data

class NDWindowing(object):
    def __init__(self, target):
        self._target = target

    def __getitem__(self, slice):
        return NDWindowingAstroData(self._target, window=slice)

class NDWindowingAstroData(NDArithmeticMixin, NDSlicingMixin, NDData):
    """
    """
    def __init__(self, target, window):
        self._target = target
        self._window = window

    @property
    def unit(self):
        return self._target.unit

    @property
    def wcs(self):
        return self._target.wcs

    @property
    def data(self):
        return self._target._get_simple('_data', section=self._window)

    @property
    def uncertainty(self):
        return self._target._get_uncertainty(section=self._window)

    @property
    def variance(self):
        un = self.uncertainty
        if un is not None:
            return un.array**2

    @property
    def mask(self):
        return self._target._get_simple('_mask', section=self._window)

def is_lazy(item):
    return isinstance(item, ImageHDU) or (hasattr(item, 'lazy') and item.lazy)

class NDAstroData(NDArithmeticMixin, NDSlicingMixin, NDData):
    """Implements `NDData` with all Mixins.

    This class implements a `NDData`-like container that supports reading and
    writing as implemented in the ``astropy.io.registry`` and also slicing
    (indexing) and simple arithmetics (add, subtract, divide and multiply).

    Notes
    -----
    A key distinction from `NDDataArray` is that this class does not attempt
    to provide anything that was not defined in any of the parent classes.

    See also
    --------
    NDData
    NDArithmeticMixin
    NDSlicingMixin

    Examples
    --------
    The mixins allow operation that are not possible with `NDData` or
    `NDDataBase`, i.e. simple arithmetics::

        >>> from astropy.nddata import NDAstroData, StdDevUncertainty
        >>> import numpy as np

        >>> data = np.ones((3,3), dtype=np.float)
        >>> ndd1 = NDAstroData(data, uncertainty=StdDevUncertainty(data))
        >>> ndd2 = NDAstroData(data, uncertainty=StdDevUncertainty(data))

        >>> ndd3 = ndd1.add(ndd2)
        >>> ndd3.data
        array([[ 2.,  2.,  2.],
               [ 2.,  2.,  2.],
               [ 2.,  2.,  2.]])
        >>> ndd3.uncertainty.array
        array([[ 1.41421356,  1.41421356,  1.41421356],
               [ 1.41421356,  1.41421356,  1.41421356],
               [ 1.41421356,  1.41421356,  1.41421356]])

    see `NDArithmeticMixin` for a complete list of all supported arithmetic
    operations.

    But also slicing (indexing) is possible::

        >>> ndd4 = ndd3[1,:]
        >>> ndd4.data
        array([ 2.,  2.,  2.])
        >>> ndd4.uncertainty.array
        array([ 1.41421356,  1.41421356,  1.41421356])

    See `NDSlicingMixin` for a description how slicing works (which attributes)
    are sliced.
    """
    def __init__(self, data, uncertainty=None, mask=None, wcs=None,
                 meta=None, unit=None, copy=False, window=None):
        self._scalers = {}
        self._window = window

        super(NDAstroData, self).__init__(FakeArray(data) if is_lazy(data) else data,
                                          None if is_lazy(uncertainty) else uncertainty,
                                          mask, wcs, meta, unit, copy)

        if is_lazy(data):
            self.data = data
        if is_lazy(uncertainty):
            self.uncertainty = uncertainty

    def __deepcopy__(self, memo):
        return self.__class__(self.data, self.uncertainty, self.mask, self.wcs,
                              deepcopy(self.meta), self.unit)

    @property
    def window(self):
        return NDWindowing(self)

    @property
    def shape(self):
        return self._data.shape

    def _extract(self, source, scaling, section=None):
        return scaling(source.data if section is None else source[section])

    def _get_uncertainty(self, section=None):
        if self._uncertainty is not None:
            if is_lazy(self._uncertainty):
                data = self._uncertainty.data if section is None else self._uncertainty[section]
                temp = new_variance_uncertainty_instance(data)
                if section is None:
                    self.uncertainty = temp
                return temp
            elif section is not None:
                return self._uncertainty[section]
            else:
                return self._uncertainty

    def _get_simple(self, target, section=None):
        source = getattr(self, target)
        if source is not None:
            if is_lazy(source):
                if section is None:
                    ret = np.empty(source.shape, dtype=source.dtype)
                    ret[:] = source.data
                    setattr(self, target, ret)
                else:
                    ret = source[section]
                return ret
            elif section is not None:
                return source[section]
            else:
                return source

    @property
    def data(self):
        return self._get_simple('_data')

    @data.setter
    def data(self, value):
        if value is None:
            raise ValueError("Cannot have None as the data value for an NDData object")

        if is_lazy(value):
            self.meta['header'] = value.header
        self._data = value

    @property
    def uncertainty(self):
        return self._get_uncertainty()

    @uncertainty.setter
    def uncertainty(self, value):
        if value is not None and not is_lazy(value):
            if value._parent_nddata is not None:
                value = value.__class__(value, copy=False)
            value.parent_nddata = self
        self._uncertainty = value

    @property
    def mask(self):
        return self._get_simple('_mask')

    @mask.setter
    def mask(self, value):
        self._mask = value

    @property
    def variance(self):
        arr = self._get_uncertainty()
        if arr is not None:
            return arr.array**2

    @variance.setter
    def variance(self, value):
        self.uncertainty = new_variance_uncertainty_instance(value)

    def set_section(self, section, input):
        self.data[section] = input.data
        if self.uncertainty is not None:
            self.uncertainty.array[section] = input.uncertainty.array
        if self.mask is not None:
            self.mask[section] = input.mask

    def __repr__(self):
        if is_lazy(self._data):
            return self.__class__.__name__ + '(Memmapped)'
        else:
            return super(NDAstroData, self).__repr__()
