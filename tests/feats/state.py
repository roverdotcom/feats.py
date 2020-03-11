import json

from unittest import TestCase
from collections import namedtuple

import feats.errors as errors
from feats.app import App
from feats.selector import Rollout
from feats.selector import Static
from feats.storage import Memory
from feats.state import FeatureState


class FeatureStateBuilderTests(TestCase):

    def setUp(self):
        super().setUp()
        self.initial = FeatureState.initial('sentinel')

    def test_initial(self):
        self.assertEqual([], self.initial.segments)
        self.assertEqual([], self.initial.selectors)
        self.assertEqual({}, self.initial.selector_mapping)
        self.assertEqual('sentinel', self.initial.created_by)

    def test_add_selector(self):
        selector = Static('new_selector', 'sentinel')
        other_selector = Static('other_selector', 'sentinel')
        tests = [
            (self.initial, [selector]),
            (FeatureState(
                segments=[],
                selectors=[other_selector],
                selector_mapping={None: other_selector},
                created_by='test'
            ),
            [other_selector, selector]),
        ]

        for initial, expected in tests:
            with self.subTest():
                new_state = initial.add_selector(selector, 'test')
                self.assertEqual(new_state.selectors, expected)
                self.assertEqual(new_state.selector_mapping, initial.selector_mapping)
                self.assertEqual(new_state.segments, initial.segments)
                self.assertEqual(new_state.created_by, 'test')

    def test_remove_selector(self):
        selector_to_remove = Static('to_remove', 'sentinel')
        other_selector = Static('other_selector', 'other')

        tests = [
                (
                    [selector_to_remove],
                    {},
                    0,
                    [],
                    {},
                ),
                (
                    [selector_to_remove],
                    {None: selector_to_remove},
                    0,
                    [],
                    {}
                ),
                (
                    [other_selector, selector_to_remove],
                    {None: other_selector},
                    1,
                    [other_selector],
                    {None: other_selector},
                ),
                (
                    [other_selector, selector_to_remove],
                    {None: other_selector},
                    1,
                    [other_selector],
                    {None: other_selector},
                )
        ]
        for initial_selector, initial_map, index, expected_selectors, expected_map in tests:
            with self.subTest():
                initial_state = FeatureState(
                        segments=[],
                        selectors=initial_selector.copy(),
                        selector_mapping=initial_map.copy(),
                        created_by='test'
                )
                new_state = initial_state.remove_selector(index, 'test2')
                self.assertEqual(new_state.segments, [])
                self.assertEqual(new_state.selectors, expected_selectors)
                self.assertEqual(new_state.selector_mapping, expected_map)
                self.assertEqual(new_state.created_by, 'test2')

    def test_update_selector(self):
        selector_to_update = Static('to_update', 'sentinel')
        updated_selector = Static('updated_selector', 'updated')
        other_selector = Static('other_selector', 'other')
        tests = [
                (
                    [selector_to_update],
                    {},
                    0,
                    [updated_selector],
                    {},
                ),
                (
                    [selector_to_update],
                    {None: selector_to_update},
                    0,
                    [updated_selector],
                    {None: updated_selector}
                ),
                (
                    [other_selector, selector_to_update],
                    {None: other_selector},
                    1,
                    [other_selector, updated_selector],
                    {None: other_selector},
                ),
                (
                    [other_selector, selector_to_update],
                    {None: other_selector, ('a',): selector_to_update, ('b',): selector_to_update},
                    1,
                    [other_selector, updated_selector],
                    {None: other_selector, ('a',): updated_selector, ('b',): updated_selector},
                )
        ]
        for initial_selector, initial_map, index, expected_selectors, expected_map in tests:
            with self.subTest():
                initial_state = FeatureState(
                        segments=[],
                        selectors=initial_selector.copy(),
                        selector_mapping=initial_map.copy(),
                        created_by='test'
                )
                new_state = initial_state.update_selector(index, updated_selector, 'test2')
                self.assertEqual(new_state.segments, [])
                self.assertEqual(new_state.selectors, expected_selectors)
                self.assertEqual(new_state.selector_mapping, expected_map)
                self.assertEqual(new_state.created_by, 'test2')


class SerializeStateTests(TestCase):
    def setUp(self):
        super().setUp()
        self.app = App(storage=Memory())
        @self.app.segment
        class TestSegment:
            def segment(self, key: str) -> str:
                return key

        @self.app.feature
        class TestFeature:
            @self.app.default
            def foo(self) -> str:
                return 'foo'

            def bar(self) -> str:
                return 'bar'

    def _serialized_data(self, **kwargs):
        (key, _), = self.app.segments.items()
        selector = self._create_rollout_selector()
        return {
            'version': FeatureState.version,
            'segment:["value_match"]': 'selector:0',
            'segmentation': json.dumps([key]),
            'created_by': 'foo@bar.baz',
            'selector:0': json.dumps({
                'type': self.app._name(Rollout),
                'data': selector.serialize_data(self.app),
            }),
            **kwargs
        }

    def _create_rollout_selector(self):
        (_, v), = self.app.segments.items()
        return Rollout('test.name', v, {
            '0': 1,
        })

    def _build_selector_mapping(self, selectors):
        return {
            ('value_match',): selectors[0],
        }

    def _create_feature_state(self, **kwargs):
        selectors = [self._create_rollout_selector()]
        (_, segment), = self.app.segments.items()
        selector_mapping = self._build_selector_mapping(selectors)
        return FeatureState(**{
            'segments': [segment],
            'selectors': selectors,
            'selector_mapping': selector_mapping,
            'created_by': 'foo@bar.baz',
            **kwargs
        })

    def test_deserialize_raises_error_wrong_serializer_version(self):
        with self.assertRaises(errors.InvalidSerializerVersion):
            FeatureState.deserialize(self.app, self._serialized_data(
                version='v0',
            ))

    def test_raises_error_unknown_segment(self):
        with self.assertRaises(errors.UnknownSegmentName):
            FeatureState.deserialize(self.app, self._serialized_data(
                segmentation='["unknown.path"]',
            ))

    def test_raises_error_unknown_selector(self):
        with self.assertRaises(errors.UnknownSelectorName):
            FeatureState.deserialize(self.app, self._serialized_data(**{
                'selector:0': json.dumps({
                    'type': 'some.wrong.path',
                }),
            }))

    def test_serializes_data(self):
        self.assertEqual(
            self._serialized_data(),
            self._create_feature_state().serialize(self.app)
        )

    def test_deserializes_data(self):
        feature_state = FeatureState.deserialize(self.app, self._serialized_data())
        constructed = self._create_feature_state()
        self.assertEqual(feature_state.segments, constructed.segments)
        self.assertEqual(feature_state.created_by, constructed.created_by)
        self.assertEqual(feature_state.selector_mapping[('value_match',)].__class__, Rollout)
        self.assertEqual(feature_state.selectors[0].__class__, Rollout)

    def test_serializes_with_fallthrough(self):
        selector = self._create_rollout_selector()
        state = self._create_feature_state(
            selectors=[selector],
            selector_mapping={None: selector}
        )
        serialized = state.serialize(self.app)
        data = self._serialized_data()
        data.pop('segment:["value_match"]')
        data['segment:null'] = 'selector:0'
        self.assertEqual(data, serialized)

    def test_deserializes_fallthrough(self):
        data = self._serialized_data()
        data.pop('segment:["value_match"]')
        data['segment:null'] = 'selector:0'
        feature_state = FeatureState.deserialize(self.app, data)
        selector = self._create_rollout_selector()
        constructed = self._create_feature_state(
            selectors=[selector],
            selector_mapping={None: selector}
        )
        self.assertEqual(feature_state.segments, constructed.segments)
        self.assertEqual(feature_state.created_by, constructed.created_by)
        self.assertEqual(feature_state.selector_mapping[None].__class__, Rollout)
        self.assertEqual(feature_state.selectors[0].__class__, Rollout)
