import itertools
from types import FunctionType, MethodType

from munch import munchify
from viktor import File


class MockEntity:
    """Mock class for Viktor Entity object"""

    def __init__(self, entity_id: int, name: str = None, params: dict = None, entity_document: File = None):
        self.id = entity_id
        self.name = name
        self._params = params or {}
        self._entity_document = entity_document

    @property
    def last_saved_params(self):
        return munchify(self._params)

    def get_file(self):
        return self._entity_document


class MockEntityList(list):
    """ "Mock class for Viktor Entity list"""

    def __init__(self, *args):
        list.__init__(self, *args)


def get_method_names(cls, inherited_methods: bool):
    """Function to get all method names of a class, boolean to exclude inherited methods.
    Excludes dunder methods."""

    def listMethods(cls):
        return set(x for x, y in cls.__dict__.items()
                   if isinstance(y, (FunctionType, MethodType, staticmethod)))

    def listParentMethods(cls):
        return set(itertools.chain.from_iterable(
            listMethods(c).union(listParentMethods(c)) for c in cls.__bases__))

    def list_subclass_methods(cls, is_narrow):
        methods = listMethods(cls)
        if is_narrow:
            parentMethods = listParentMethods(cls)
            return set(cls for cls in methods if not (cls in parentMethods))
        else:
            return methods

    return list_subclass_methods(cls, inherited_methods)