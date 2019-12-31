from .meta import Definition
from collections import Counter


def default(fn):
    if hasattr(fn, '_feats_annotations_'):
        fn._feats_annotations_.append('default')
    else:
        fn._feats_annotations_ = ['default']

    return fn


def _check_same_inputs(definition: Definition) -> None:
    input_types = Counter([
        tuple(impl.input_types) for impl in definition.implementations.values()
    ])
    errors = []
    if len(input_types) > 1:
        errors.append(
            "The inputs to all implementations must be the same {}".format(
                input_types
            )
        )

    if errors:
        raise ValueError(errors)


def _check_default(definition: Definition) -> None:
    defaults = definition.annotations['default']
    if len(defaults) == 0:
        raise ValueError("Must specify a default implementation")
    elif len(defaults) > 1:
        raise ValueError("Must specify only one default implementation")


class Feature:
    def __init__(self, definition):
        _check_same_inputs(definition)
        _check_default(definition)
        self.definition = definition

    @property
    def description(self):
        return self.definition.description

    @property
    def input_types(self):
        return self.definition.implementations[0].input_types

    @property
    def default_implementation(self):
        return self.definition.annotations['default'][0]

    @property
    def implementations(self):
        return self.definition.implementations


class _TrueDefault:
    @default
    def true(self, *args) -> bool:
        return True

    def false(self, *args) -> bool:
        return False


class _FalseDefault:
    def true(self, *args) -> bool:
        return True

    @default
    def false(self, *args) -> bool:
        return False
