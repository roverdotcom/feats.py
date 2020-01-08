from unittest import TestCase

from feats.meta import Implementation, Definition
from feats.utils import fn_to_implementations
from feats.utils import obj_to_implementations


class FullySpecified:
    """
    This is a feature class
    """
    def nullary(self) -> str:
        return "nullary"

    def unary(self, arg1: str) -> int:
        return int(arg1)
    unary._feats_annotations_ = ["special"]

    def binary(self, arg1: str, arg2: int) -> float:
        return float(arg2)
    binary._feats_annotations_ = ["special", "default"]


class Incomplete:
    def no_return(self):
        return "no_return"

    def no_input_type(self, arg1) -> int:
        return "no_input_type"

    def partial_input_type(self, arg1, arg2: str) -> str:
        return "partial_input_type"


class Empty:
    pass


def FullySpecifiedFunc(arg: str) -> bool:
    """
    This is a feature function
    """
    return True


FullySpecifiedFunc._feats_annotations_ = ["default"]


class ImplementationTests(TestCase):
    def test_fully_specified(self):
        obj = FullySpecified()
        input_types = {
            obj.nullary: [],
            obj.unary: [str],
            obj.binary: [str, int],
        }
        output_types = {
            obj.nullary: str,
            obj.unary: int,
            obj.binary: float,
        }
        names = {
            obj.nullary: "nullary",
            obj.unary: "unary",
            obj.binary: "binary",
        }

        with self.subTest("input_types"):
            for fn, expected in input_types.items():
                with self.subTest(fn):
                    self.assertEqual(Implementation(fn).input_types, expected)

        with self.subTest("output_type"):
            for fn, expected in output_types.items():
                self.assertEqual(Implementation(fn).output_type, expected)

        with self.subTest("names"):
            for fn, expected in names.items():
                self.assertEqual(Implementation(fn).name, expected)

        with self.subTest("call"):
            with self.subTest("nullary"):
                self.assertEqual(Implementation(obj.nullary).fn(), "nullary")
            with self.subTest("unary"):
                self.assertEqual(Implementation(obj.unary).fn("10"), 10)
            with self.subTest("binary"):
                self.assertEqual(Implementation(obj.binary).fn("1", 2), 2.0)

    def test_incomplete(self):
        obj = Incomplete()
        with self.subTest("no_return"), self.assertRaises(ValueError):
            Implementation(obj.no_return)

        with self.subTest("no_input_type"), self.assertRaises(ValueError):
            Implementation(obj.no_input_type)

        with self.subTest("partial_input_type"), self.assertRaises(ValueError):
            Implementation(obj.partial_input_type)


class DefinitionTests(TestCase):
    def test_empty(self):
        with self.assertRaises(ValueError):
            obj = Empty()
            implementations, annotations = obj_to_implementations(obj)
            Definition(obj.__doc__, implementations, annotations)

    def test_fully_specified(self):
        obj = FullySpecified()
        implementations, annotations = obj_to_implementations(obj)
        definition = Definition(obj.__doc__, implementations, annotations)

        self.assertEqual(definition.description.strip(), "This is a feature class")
        self.assertEqual(definition.implementations, implementations)
        self.assertEqual(definition.annotations, annotations)

    def test_fully_specified_fn(self):
        fn = FullySpecifiedFunc
        implementations, annotations = fn_to_implementations(fn)
        definition = Definition(fn.__doc__, implementations, annotations)

        self.assertEqual(definition.description.strip(), "This is a feature function")
        self.assertEqual(definition.implementations, implementations)
        self.assertEqual(definition.annotations, annotations)
