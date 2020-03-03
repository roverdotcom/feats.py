import inspect
from functools import wraps
from collections import defaultdict
from typing import Dict, List


class Implementation:
    def __init__(self, fn):
        self.fn = fn
        self.name = fn.__name__
        self.description = inspect.getdoc(fn)

        signature = inspect.signature(fn)
        self.output_type = signature.return_annotation
        has_output = self.output_type != inspect.Signature.empty

        self.input_types = []
        errors = []
        for name, param in signature.parameters.items():
            if param.annotation == inspect.Parameter.empty:
                errors.append(
                    "{} does not declare an input type for {}".format(fn, name)
                )
            else:
                self.input_types.append(param.annotation)

        if not has_output:
            errors.append("{} does not declare an output type".format(fn))
        if errors:
            raise ValueError(errors)


class Definition:
    """
    """

    def __init__(
            self,
            description: str,
            implementations: List[Implementation],
            annotations: Dict[str, list]):

        if len(implementations) == 0:
            # TODO: Describe what an implementation needs
            raise ValueError(
                "Definition did not contain at least one implementation"
            )

        self.description = description
        self.implementations = {
            impl.name: impl for impl in implementations
        }
        self.annotations = annotations

    @classmethod
    def from_function(cls, fn):
        # Wraps fn so we keep the same type annotations as the original fn
        @wraps(fn, assigned=('__annotations__',))
        def Enabled(*args, **kwargs):
            # Call fn so we enforce the correct args
            fn(*args, **kwargs)
            return True

        @wraps(fn, assigned=('__annotations__',))
        def Default(*args, **kwargs):
            """
            Keeps the default behavior of the feature
            """
            return fn(*args, **kwargs)

        @wraps(fn, assigned=('__annotations__',))
        def Disabled(*args, **kwargs):
            fn(*args, **kwargs)
            return False

        annotations = defaultdict(list)
        default = Implementation(Default)
        if hasattr(fn, '_feats_annotations_'):
            for annotation in fn._feats_annotations_:
                annotations[annotation].append(default)

        implementations = [
            Implementation(Enabled),
            default,
            Implementation(Disabled),
        ]

        return cls(inspect.getdoc(fn), implementations, annotations)

    @classmethod
    def from_object(cls, obj):
        implementations: List[Implementation] = []
        annotations = defaultdict(list)

        for key in dir(obj):
            value = getattr(obj, key)
            if key.startswith('_') or not callable(value):
                continue
            impl = Implementation(value)
            implementations.append(impl)
            if hasattr(value, '_feats_annotations_'):
                for annotation in value._feats_annotations_:
                    annotations[annotation].append(impl)

        return cls(inspect.getdoc(obj), implementations, annotations)
