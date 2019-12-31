import inspect
from collections import defaultdict
from typing import Dict


class Implementation:
    def __init__(self, fn):
        self.fn = fn
        self.name = fn.__name__
        self.description = fn.__doc__

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

    def __init__(self, obj):
        self.description = obj.__doc__
        self.implementations: Dict[str, Implementation] = {}
        self.annotations = defaultdict(list)
        for key in dir(obj):
            value = getattr(obj, key)
            if key.startswith('_') or not callable(value):
                continue
            impl = Implementation(value)
            self.implementations[impl.name] = impl
            if hasattr(value, '_feats_annotations_'):
                for annotation in value._feats_annotations_:
                    self.annotations[annotation].append(impl)

        if len(self.implementations) == 0:
            # TODO: Describe what an implementation needs
            raise ValueError(
                "Definition did not contain at least one implementation"
            )
