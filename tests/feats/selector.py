from unittest import TestCase
from feats.selector import Static
from feats.selector import Rollout


class StaticTests(TestCase):

    def test_returns_given_value_no_args(self):
        self.assertEqual(Static('foo').select(), 'foo')

    def test_returns_given_value_has_args(self):
        self.assertEqual(Static('bar').select(object()), 'bar')


class RolloutTests(TestCase):
    # specifically chosen keys which will modulo 10 to their index in this list
    keys = [
        'ju',
        'kx',
        'bn',
        'ao',
        'bN',
        'bi',
        'iN',
        'gU',
        'fA',
        'jA',
    ]

    def segment(self, key):
        return key

    def test_rollout_single_weight(self):
        selector = Rollout(self.segment, {
            '0': 1,
        })
        for key in self.keys:
            self.assertEqual(
                selector.select(key), 
                '0'
            )


    def test_rollout_zero_weight(self):
        with self.assertRaises(ValueError):
            selector = Rollout(self.segment, {
                '0': 0,
            })

    def test_rollout_no_weight(self):
        with self.assertRaises(ValueError):
            selector = Rollout(self.segment, {})

    def test_rollout_equal_weights(self):
        selector = Rollout(self.segment, {
            '0': 1,
            '1': 1,
            '2': 1,
            '3': 1,
            '4': 1,
            '5': 1,
            '6': 1,
            '7': 1,
            '8': 1,
            '9': 1,
        })
        for key in self.keys:
            with self.subTest(key):
                self.assertEqual(self.keys.index(key), int(selector.select(key)))

    def test_rollout_differing_weights(self):
        selector = Rollout(self.segment, {
            '0': 4,
            '4': 2,
            '6': 3,
            '9': 1,
        })
        for key in self.keys[0:4]:
            with self.subTest(key):
                self.assertEqual('0', selector.select(key))
        for key in self.keys[4:6]:
            with self.subTest(key):
                self.assertEqual('4', selector.select(key))
        for key in self.keys[6:9]:
            with self.subTest(key):
                self.assertEqual('6', selector.select(key))
        for key in self.keys[9:]:
            with self.subTest(key):
                self.assertEqual('9', selector.select(key))

