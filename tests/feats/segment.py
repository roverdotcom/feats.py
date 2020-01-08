from feats.segment import Segment
from unittest import TestCase
from feats.meta import Definition
from feats.utils import fn_to_implementations
from feats.utils import obj_to_implementations


class StringSegment:
    def string(self, value: str) -> str:
        return "string"


class IntSegment:
    def int(self, value: int) -> str:
        return "int"


class StringIntSegment(StringSegment, IntSegment):
    pass


class AmbiguousSegment:
    def obj_1(self, value: object) -> str:
        return "obj_1"

    def obj_2(self, value: object) -> str:
        return "obj_2"


class SegmentTests(TestCase):

    def test_ambiguous(self):
        with self.assertRaises(ValueError):
            obj = AmbiguousSegment()
            implementations, annotations = obj_to_implementations(obj)
            Segment(Definition(obj.__doc__, implementations, annotations))

    def test_one_impl(self):
        obj = IntSegment()
        implementations, annotations = obj_to_implementations(obj)
        segment = Segment(Definition(obj.__doc__, implementations, annotations))

        with self.subTest("valid input"):
            self.assertEqual("int", segment(1))

        with self.subTest("invalid input"), self.assertRaises(ValueError):
            segment("hello")

    def test_two_impl(self):
        obj = StringIntSegment()
        implementations, annotations = obj_to_implementations(obj)
        segment = Segment(Definition(obj.__doc__, implementations, annotations))

        with self.subTest("valid input str"):
            self.assertEqual("string", segment("hi"))

        with self.subTest("valid input int"):
            self.assertEqual("int", segment(0))

        with self.subTest("invalid input"), self.assertRaises(ValueError):
            segment(object())
