import inspect
from collections import defaultdict
from typing import Dict


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
            implementations: Dict[str, Implementation],
            annotations: Dict[str, list]):

        if len(implementations) == 0:
            # TODO: Describe what an implementation needs
            raise ValueError(
                "Definition did not contain at least one implementation"
            )

        self.description = description
        self.implementations = implementations
        self.annotations = annotations

    @classmethod
    def from_function(cls, fn):
        implementations: Dict[str, Implementation] = {}
        annotations = defaultdict(list)
        impl = Implementation(fn)
        implementations[impl.name] = impl

        if hasattr(fn, '_feats_annotations_'):
            for annotation in fn._feats_annotations_:
                annotations[annotation].append(impl)

        return cls(fn.__doc__, implementations, annotations)

    @classmethod
    def from_object(cls, obj):
        implementations: Dict[str, Implementation] = {}
        annotations = defaultdict(list)

        for key in dir(obj):
            value = getattr(obj, key)
            if key.startswith('_') or not callable(value):
                continue
            impl = Implementation(value)
            implementations[impl.name] = impl
            if hasattr(value, '_feats_annotations_'):
                for annotation in value._feats_annotations_:
                    annotations[annotation].append(impl)

        return cls(obj.__doc__, implementations, annotations)
