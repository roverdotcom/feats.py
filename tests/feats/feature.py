from unittest import TestCase

import feats
from feats.app import App
from feats.storage import Memory


class InvalidUnaryFeatures:
    class NoImpls:
        pass

    class NoDefault:
        def foo(self, arg: str) -> str:
            return "foo"

    class DifferentInputs:
        @feats.default
        def foo(self, arg: str) -> str:
            return "foo"

        def bar(self, arg: int) -> str:
            return "bar"

    class DifferentArity:
        @feats.default
        def foo(self, arg: str) -> str:
            return "foo"

        def bar(self, arg1: str, arg2: int) -> str:
            return "bar"

    class NoReturnType:
        @feats.default
        def foo(self, arg: str):
            return "foo"

    class PartialNoReturnType:
        @feats.default
        def foo(self, arg: str) -> str:
            return "foo"

        def bar(self, arg: str):
            return "bar"

    class AmbiguousDefault:
        @feats.default
        def foo(self, arg: str) -> str:
            return "foo"

        @feats.default
        def bar(self, arg: str) -> str:
            return "bar"


class InvalidNullaryFeatures:
    class NoImpls:
        pass

    class NoDefault:
        def foo(self) -> str:
            return "foo"

    class NoReturnType:
        @feats.default
        def foo(self):
            return "foo"

    class DifferentArity:
        @feats.default
        def foo(self) -> str:
            return "foo"

        def bar(self, arg: str) -> str:
            return "bar"

    class PartialNoReturnType:
        @feats.default
        def foo(self) -> str:
            return "foo"

        def bar(self):
            return "bar"


class ValidUnaryFeatures:
    class One:
        @feats.default
        def foo(self, arg: str) -> str:
            return "foo"

    class Two:
        @feats.default
        def foo(self, arg: str) -> str:
            return "foo"

        def bar(self, arg: str) -> str:
            return "bar"

    class Three:
        @feats.default
        def foo(self, arg: str) -> str:
            return "foo"

        def bar(self, arg: str) -> str:
            return "bar"

        def baz(self, arg: str) -> str:
            return "baz"

    class DifferentOutput:
        @feats.default
        def foo(self, arg: str) -> str:
            return "foo"

        def one(self, arg: str) -> int:
            return 1


class ValidNullaryFeatures:
    class One:
        @feats.default
        def foo(self) -> str:
            return "foo"

    class Two:
        @feats.default
        def foo(self) -> str:
            return "foo"

        def bar(self) -> str:
            return "bar"

    class Three:
        @feats.default
        def foo(self) -> str:
            return "foo"

        def bar(self) -> str:
            return "bar"

        def baz(self) -> str:
            return "baz"


class ValidSegments:
    class One:
        def reticulate_string(self, value: str) -> str:
            return "reticulated string"

    class Two:
        def reticulate_string(self, value: str) -> str:
            return "reticulated string"

        def reticulate_integer(self, value: int) -> str:
            return "reticulated int"

    class Three:
        def reticulate_string(self, value: str) -> str:
            return "reticulated string"

        def reticulate_integer(self, value: int) -> str:
            return "reticulated int"

        def reticulate_float(self, value: float) -> str:
            return "reticulated float"


class InvalidSegments:
    class NoImpls:
        pass

    class NoReturnType:
        def reticulate_string(self, value: str):
            return "reticulated string"

    class NoInput:
        def reticulate_none(self) -> str:
            return "reticulated nothing"

    class PartialNoReturnType:
        def reticulate_string(self, value: str) -> str:
            return "reticulated string"

        def reticulate_int(self, value: int):
            return "reticulated int"

    class IncorrectReturnType:
        def reticulate_string(self, value: str) -> int:
            return 0


class AppTests(TestCase):
    def setUp(self):
        super().setUp()
        self.app = App(storage=Memory())

    def _definition_test(self, cls):
        definitions = [
            value
            for key, value in cls.__dict__.items()
            if not key.startswith('_')
        ]
        self.assertNotEqual(len(definitions), 0)
        return definitions

    def test_valid_unary(self):
        for definition in self._definition_test(ValidUnaryFeatures):
            with self.subTest(definition):
                handle = self.app.feature(definition)
                self.assertIsNotNone(handle)
                self.assertEqual(handle.create(), 'foo')

    def test_valid_nullary(self):
        for definition in self._definition_test(ValidNullaryFeatures):
            with self.subTest(definition):
                handle = self.app.feature(definition)
                self.assertIsNotNone(handle)
                self.assertEqual(handle.create(), 'foo')

    def test_valid_segments(self):
        for definition in self._definition_test(ValidSegments):
            with self.subTest(definition):
                handle = self.app.segment(definition)
                self.assertIsNotNone(handle)

    def test_invalid_unary(self):
        for definition in self._definition_test(InvalidUnaryFeatures):
            with self.subTest(definition), self.assertRaises(ValueError):
                self.app.feature(definition)

    def test_invalid_nullary(self):
        for definition in self._definition_test(InvalidNullaryFeatures):
            with self.subTest(definition), self.assertRaises(ValueError):
                self.app.feature(definition)

    def test_invalid_segments(self):
        for definition in self._definition_test(InvalidSegments):
            with self.subTest(definition), self.assertRaises(ValueError):
                self.app.segment(definition)
