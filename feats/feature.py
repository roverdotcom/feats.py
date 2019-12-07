from .meta import Definition


def default():
    def wrap(fn):
        fn.__class__._feats_default = fn
        return fn
    return wrap


def _check_same_inputs(definition: Definition) -> None:
    input_type = definition.implementations[0].input_type
    for impl in definition.implementations[1, -1]:
        if impl.input_type != input_type:
            raise ValueError("All Input Types must be the same")


class Feature:
    def __init__(self, obj, definition):
        _check_same_inputs(definition)
        self.definition = definition

    @property
    def input_type(self):
        return self.definition.implementations[0].input_type


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
