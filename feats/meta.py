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
