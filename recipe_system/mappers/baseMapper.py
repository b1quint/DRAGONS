#
#                                                                        DRAGONS
#
#                                                          mappers.baseMapper.py
# ------------------------------------------------------------------------------
from builtins import object

from ..utils.mapper_utils import dictify
from ..utils.mapper_utils import dotpath

# ------------------------------------------------------------------------------
class Mapper(object):
    """
    This is the base class for classes
    :class:`~recipe_system.mappers.recipeMapper.RecipeMapper`
    and
    :class:`~recipe_system.mappers.primitiveMapper.PrimitiveMapper`.

    It provides initialization only.

    Recipes and primitives are algorithmically selected via instropection of
    module and class attributes that match on a dataset's tags attribute.

    Parameters
    ----------

    dtags : <set>
            A set of AstroData tags from input dataset. These are decoupled
            from astrodata objects so as not to introduce 'ad' objects into
            mapper generators.

    ipkg  : <str>
            Instrument package name, as returned by,

                ad.instrument(generic=True)

    drpkg : <str>
            The data reduction package to map. Default is 'geminidr'.
            This package *must* be importable.

    recipename : <str>
                 The recipe to use for processing. Passed by user
                 with -r or set by caller. Else 'default' recipe.

    mode : <str>
           Pipeline mode. Selection criterion for recipe sets.
           Supported modes:
           'sq' - Science Quality (default)
           'qa' - Quality Assessment
           'ql' - Quicklook

    """
    def __init__(self, dtags, ipkg, mode='sq', drpkg='geminidr', recipename='_default'):
        self.tags = dtags
        self.mode = mode
        self.dotpackage = dotpath(drpkg, ipkg)
        self.recipename = recipename

    @property
    def upload(self):
        return self._upload

    @upload.setter
    def upload(self, upl):
        if upl is None:
            self._upload = None
        elif isinstance(upl, str):
            self._upload = [seg.lower().strip() for seg in upl.split(',')]
        elif isinstance(upl, list):
            self._upload = upl
        else:
            raise TypeError("'upload' must be one of None, <str>, or <list>")
        return
