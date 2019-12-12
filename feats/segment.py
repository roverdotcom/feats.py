from inspect import getclasstree

from functools import lru_cache

from .meta import Definition
from .meta import Implementation


class Segment:
    def __init__(self, definition: Definition):
        _check_output_type(definition)
        _check_input_types(definition)
        self.definition = definition
        self.input_mapping = {
            impl.input_types[0]: impl
            for impl in self.definition.implementations
        }

    @lru_cache(maxsize=32)
    def find_implementation(self, cls) -> Implementation:
        """
        For the given class, finds the implementation inside of the definition
        that matches the input type to that class.
        If multiple implementations are valid, it will raise a ValueError.

        This method is cached under the assumption a small set of classes will
        be given to the segment and class hierarchies don't change at runtime.
        """
        # couldn't find a way to isinstance between N classes, so we'll do it
        # ourselves

        tree = getclasstree(cls, unique=True)
        found = []
        for cur_cls, parent_cls in tree:
            impl = self.input_mapping.get(cur_cls)
            if impl is not None:
                found.append(impl)

        if len(found) == 0:
            raise ValueError("No Implementation which matches {}".format(cls))
        elif len(found) > 1:
            # TODO: Better error messages about which impls match
            raise ValueError("Multiple implementations match {}".format(cls))
        return found[0]

    def __call__(self, value) -> str:
        """
        Segments the value by calling the implementation appropriate to the
        value's type.
        """
        impl = self.find_implementation(type(value))
        return impl(value)


def _check_input_types(definition: Definition):
    for impl in definition.implementations:
        if len(impl.input_types) == 0:
            raise ValueError("Must specify an input")
        if len(impl.input_types) > 1:
            raise ValueError("Cannot specify more than one input to a segment")


def _check_output_type(definition: Definition):
    for impl in definition.implementations:
        if impl.output_type is not str:
            # TODO: Better error messages for this impl,
            # collect all impls that are wrong
            raise ValueError("All implementations must return str")
