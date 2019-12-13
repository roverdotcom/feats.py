from unittest import TestCase

from feats.meta import Implementation


class FullySpecified:
    def nullary(self) -> str:
        return "nullary"

    def unary(self, arg1: str) -> int:
        return int(arg1)

    def binary(self, arg1: str, arg2: int) -> float:
        return float(arg2)


class Incomplete:
    def no_return(self):
        return "no_return"

    def no_input_type(self, arg1) -> int:
        return "no_input_type"

    def partial_input_type(self, arg1, arg2: str) -> str:
        return "partial_input_type"


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
                self.assertEqual(Implementation(obj.nullary)(), "nullary")
            with self.subTest("unary"):
                self.assertEqual(Implementation(obj.unary)("10"), 10)
            with self.subTest("binary"):
                self.assertEqual(Implementation(obj.binary)("1", 2), 2.0)

    def test_incomplete(self):
        obj = Incomplete()
        with self.subTest("no_return"), self.assertRaises(ValueError):
            Implementation(obj.no_return)

        with self.subTest("no_input_type"), self.assertRaises(ValueError):
            Implementation(obj.no_input_type)
