from unittest import TestCase

from feats.feature import default
from feats.meta import Implementation, Definition


class FullySpecified:
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


@default
def FullySpecifiedFunc(arg: str) -> bool:
    return True


def NoReturnTypeFunc(arg: str):
    return True


def NoInputTypeFunc(arg) -> bool:
    return True


def PartialInputTypeFunc(arg1, arg2: str) -> bool:
    return True


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
    def test_invalid(self):
        for cls in (Empty, Incomplete):
            with self.subTest(cls), self.assertRaises(ValueError):
                Definition.from_object(cls())

    def test_fully_specified(self):
        obj = FullySpecified()
        definition = Definition.from_object(obj)
        with self.subTest("impls"):
            impls = definition.implementations
            self.assertEqual(len(impls), 3)
            for name in ["nullary", "unary", "binary"]:
                with self.subTest(name):
                    self.assertTrue(name in impls)
                    self.assertEqual(getattr(obj, name), impls[name].fn)

        with self.subTest("annotations"):
            self.assertEqual(len(definition.annotations), 2)
            with self.subTest("default"):
                default = definition.annotations["default"]
                self.assertEqual(len(default), 1)
                self.assertEqual(default[0].fn, obj.binary)

            with self.subTest("special"):
                special = definition.annotations["special"]
                self.assertEqual(len(special), 2)
                names = set([x.name for x in special])
                self.assertEqual(set(["binary", "unary"]), names)

            with self.subTest("undeclared"):
                self.assertEqual(len(definition.annotations["undeclared"]), 0)

    def test_invalid_fns(self):
        for fn in (NoReturnTypeFunc, NoInputTypeFunc, PartialInputTypeFunc):
            with self.subTest(fn), self.assertRaises(ValueError):
                Definition.from_function(fn)

    def test_fully_specified_fn(self):
        fn = FullySpecifiedFunc
        definition = Definition.from_function(fn)
        with self.subTest("impls"):
            impls = definition.implementations
            self.assertEqual(len(impls), 1)
            self.assertTrue(fn.__name__ in impls)
            self.assertEqual(fn, impls[fn.__name__].fn)

        with self.subTest("annotations"):
            self.assertEqual(len(definition.annotations), 1)
            default = definition.annotations["default"]
            self.assertEqual(len(default), 1)
            self.assertEqual(default[0].fn, fn)

            with self.subTest("undeclared"):
                self.assertEqual(len(definition.annotations["undeclared"]), 0)
