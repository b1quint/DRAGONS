#
#                                                        mappers.recipeMapper.py
# ------------------------------------------------------------------------------
import pkgutil

from importlib import import_module

from .baseMapper import Mapper
from ..utils.errors import RecipeNotFound
from ..utils.mapper_utils import find_user_recipe
from ..utils.mapper_utils import RECIPEMARKER

# ------------------------------------------------------------------------------
class RecipeMapper(Mapper):
    """
    Retrieve the appropriate recipe for a dataset, using all defined defaults:

    >>> ad = astrodata.open(<fitsfile>)
    >>> adinputs = [ad]
    >>> rm = RecipeMapper(adinputs)
    >>> recipe = rm.get_applicable_recipe()
    >>> recipe.__name__ 
    'qaReduce'

    """
    def get_applicable_recipe(self):
        recipefn = find_user_recipe(self.recipename)
        if recipefn is None:
            tag_match, recipefn = self._retrieve_recipe()

        if recipefn is None:
            raise RecipeNotFound("Recipe '{}' not found.".format(self.recipename))

        return recipefn

    # --------------------------------------------------------------------------
    # Recipe search cascade
    def _retrieve_recipe(self):
        """
        Start of the recipe library search cascade.

        :returns: tuple including the best tag set match and the primitive class
                  that provided the match.
        :rtype: <tuple>, (set, class)
        
        """
        matched_set = (set([]), None)
        for rlib in self._get_tagged_recipes():
            if hasattr(rlib, 'recipe_tags'):
                if self.tags.issuperset(rlib.recipe_tags):
                    isect = rlib.recipe_tags
                    matched_set = (isect, rlib) if isect > matched_set[0] else matched_set
                else:
                    continue
            else:
                continue

        isection, rlib = matched_set
        try:
            recipe_actual = getattr(rlib, self.recipename)
        except AttributeError:
            recipe_actual = None
        return isection, recipe_actual

    def _get_tagged_recipes(self):
        loaded_pkg = self._package_loader(self.pkg)
        for rmod, ispkg in self._generate_recipe_modules(loaded_pkg.__path__[0]):
            if not ispkg:
                yield import_module(rmod)
            else:
                continue

    def _generate_recipe_modules(self, pkg, recipedir=RECIPEMARKER):
        pkg_importer = pkgutil.ImpImporter(pkg)
        for pkgname, ispkg in pkg_importer.iter_modules():
            if ispkg and pkgname == recipedir:
                break 
            else:
                continue

        loaded_pkg = self._package_loader(pkgname)
        for context_pkg, ispkg in self._generate_context_pkg(loaded_pkg.__path__[0]):
            yield context_pkg, ispkg

    def _generate_context_pkg(self, pkg):
        pkg_importer = pkgutil.ImpImporter(pkg)
        for pkgname, ispkg in pkg_importer.iter_modules():
            if ispkg and pkgname == self.context:
                break
            else:
                continue

        loaded_pkg = self._package_loader(pkgname)
        for mod, ispkg in self._generate_context_libs(loaded_pkg.__path__[0]):
            yield mod, ispkg

    def _generate_context_libs(self, pkg):
        pkg_importer = pkgutil.ImpImporter(pkg)
        for pkgname, ispkg in pkg_importer.iter_modules():
            if not ispkg:
                yield pkgname, ispkg
            else:
                continue