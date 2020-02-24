import json

from unittest import TestCase

import feats.errors as errors
from feats.app import App
from feats.selector import Rollout
from feats.storage import Memory
from feats.state import FeatureState


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
