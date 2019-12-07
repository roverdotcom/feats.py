from typings import List


class Implementation:
    def __init__(self, fn_self, fn):
        # TODO: Test if fn is a __call__able that the annotations are correct
        typings = fn.__annotations__.copy()
        # return is a special typing specific to the return value of the fn
        output_type = typings.pop('return')
        input_arg = fn.__annotations__.popitem()

        has_output = self.output_type is not None
        has_input = input_arg is not None
        if not has_output or not has_input:
            # TODO: Handle no input argument
            # TODO: Add more descriptive error messaging
            raise ValueError("Missing type annotation")

        self.fn = fn
        self.fn_self = fn_self
        self.name = fn.__name__
        self.input_type = input_arg[1]
        self.output_type = output_type

    def __call__(self, *args, **kwargs):
        return self.fn(self.fn_self, *args, **kwargs)


class Definition:
    """
    """

    def __init__(self, obj):
        self.implementations: List[Implementation] = []
        for key, value in type(obj).__dict__.items():
            if key.startswith('_') or not callable(value):
                continue
            self.implementations.append(Implementation(value))

        if len(self.implementations) == 0:
            # TODO: Describe what an implementation needs
            raise ValueError(
                "Definition did not contain at least one implementation"
            )
