from unittest import TestCase

from feats.meta import Implementation
from feats.utils import fn_to_implementations
from feats.utils import obj_to_implementations


class FullySpecified:
    def nullary(self) -> str:
        return "nullary"

    def unary(self, arg1: str) -> int:
        return int(arg1)
    unary._feats_annotations_ = ["special"]

    def binary(self, arg1: str, arg2: int) -> float:
        return float(arg2)
    binary._feats_annotations_ = ["special", "default"]

    def _private(self) -> str:
        return "Don't look at me!"
    _private._feats_annotations_ = ["hidden"]


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
    return True


FullySpecifiedFunc._feats_annotations_ = ["default"]


def NoReturnTypeFunc(arg: str):
    return True


def NoInputTypeFunc(arg) -> bool:
    return True


def PartialInputTypeFunc(arg1, arg2: str) -> bool:
    return True


class FunctionToImplementationsTests(TestCase):
    def test_invalid_fns(self):
        for fn in (NoReturnTypeFunc, NoInputTypeFunc, PartialInputTypeFunc):
            with self.subTest(fn), self.assertRaises(ValueError):
                implementations, annotations = fn_to_implementations(fn)

    def test_fully_specified_fn(self):
        fn = FullySpecifiedFunc
        implementations, annotations = fn_to_implementations(fn)
        with self.subTest("impls"):
            self.assertEqual(len(implementations), 1)
            self.assertTrue(fn.__name__ in implementations)
            self.assertEqual(fn, implementations[fn.__name__].fn)

        with self.subTest("annotations"):
            self.assertEqual(len(annotations), 1)
            default = annotations["default"]
            self.assertEqual(len(default), 1)
            self.assertEqual(default[0].fn, fn)

            with self.subTest("undeclared"):
                self.assertEqual(len(annotations["undeclared"]), 0)


class ObjectToImplementationsTests(TestCase):
    def test_incomplete(self):
        with self.assertRaises(ValueError):
            obj = Incomplete()
            implementations, annotations = obj_to_implementations(obj)

    def test_empty(self):
        obj = Empty()
        implementations, annotations = obj_to_implementations(obj)
        self.assertEqual(len(implementations), 0)
        self.assertEqual(len(annotations), 0)

    def test_fully_specified(self):
        obj = FullySpecified()
        implementations, annotations = obj_to_implementations(obj)
        with self.subTest("impls"):
            self.assertEqual(len(implementations), 3)
            for name in ["nullary", "unary", "binary"]:
                with self.subTest(name):
                    self.assertTrue(name in implementations)
                    self.assertEqual(
                        getattr(obj, name),
                        implementations[name].fn
                    )

        with self.subTest("annotations"):
            self.assertEqual(len(annotations), 2)
            with self.subTest("default"):
                default = annotations["default"]
                self.assertEqual(len(default), 1)
                self.assertEqual(default[0].fn, obj.binary)

            with self.subTest("special"):
                special = annotations["special"]
                self.assertEqual(len(special), 2)
                names = set([x.name for x in special])
                self.assertEqual(set(["binary", "unary"]), names)

            with self.subTest("undeclared"):
                self.assertEqual(len(annotations["undeclared"]), 0)

        with self.subTest("private methods"):
            self.assertIsNone(implementations.get("_private"))
            self.assertIsNone(annotations.get("_private"))
