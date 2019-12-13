from functools import lru_cache
from inspect import getmro

from .meta import Definition, Implementation


class Segment:
    def __init__(self, definition: Definition):
        _check_output_type(definition)
        _check_input_type(definition)
        self.definition = definition
        self.input_mapping = {
            impl.input_types[0]: impl
            for impl in self.definition.implementations.values()
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

        tree = getmro(cls)
        found = []
        for cur_cls in tree:
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


def _check_input_type(definition: Definition):
    input_mros = []
    for impl in definition.implementations.values():
        if len(impl.input_types) == 0:
            raise ValueError("Must specify an input")
        if len(impl.input_types) > 1:
            raise ValueError("Cannot specify more than one input to a segment")
        input_mros.append(getmro(impl.input_types[0]))

    # no input type can be in the MRO of another
    # this rule can probably be relaxed later on,
    # but could cause unintended consequences if changing an existing
    # segment, as existing inputs could be segmented differently than
    # previously stored.
    errors = []
    for i, my_mro in enumerate(input_mros):
        for j, other_mro in enumerate(input_mros):
            if i == j:
                continue
            if my_mro[0] in other_mro:
                errors.append(
                    "{} cannot be segmented alongside {}".format(
                        my_mro[0], other_mro[0]
                    )
                )
    if errors:
        raise ValueError(errors)


def _check_output_type(definition: Definition):
    for impl in definition.implementations.values():
        if impl.output_type is not str:
            # TODO: Better error messages for this impl,
            # collect all impls that are wrong
            raise ValueError("All implementations must return str")
