from unittest import TestCase

from feats.django.views.base import parse_field
from feats.django.views.base import compress_formsets


class CompressFormsetTests(TestCase):
    def test_compress_data(self):
        unrelated_data = {
            'segment-INITIAL_FORM': 0,
            'segment-MIN_NUM_FORMS': 0,
            'segment-MAX_NUM_FORMS': 1000,
            'segment-0-segment': 'project.settings.Length',
        }
        correct_data = {
                'the-form-0-field1': '0-field1',
                'the-form-1-field1': '1-field1',
                'the-form-1-field2': '1-field2',
                'the-form-2-field1': '1-field1',
                'the-form-2-field2': '1-field2',
                'the-form-3-field1': '3-field1',
                'the-form-3-field2': '3-field2',
                'the-form-3-field3': '3-field3',

        }
        cases = [
            ({}, {}),
            (unrelated_data, unrelated_data),
            (correct_data, correct_data),
            # Missing 0th form
            ({
                'the-form-1-field1': '0-field1',
                'the-form-1-field2': '0-field2',
                'the-form-2-field1': '1-field1',
                'the-form-2-field2': '1-field2',
            }, {
                'the-form-0-field1': '0-field1',
                'the-form-0-field2': '0-field2',
                'the-form-1-field1': '1-field1',
                'the-form-1-field2': '1-field2',
            }),
            # Gap between forms
            ({
                'the-form-0-field1': '0-field1',
                'the-form-0-field2': '0-field2',
                'the-form-2-field1': '1-field1',
                'the-form-2-field2': '1-field2',
            }, {
                'the-form-0-field1': '0-field1',
                'the-form-0-field2': '0-field2',
                'the-form-1-field1': '1-field1',
                'the-form-1-field2': '1-field2',
            })
        ]
        for case in cases:
            given, expected = case
            with self.subTest(given=given, expected=expected):
                compressed = compress_formsets(given, 'the-form')
                self.assertEqual(compressed, expected)

    def test_parse_field(self):
        cases = (
            ('the-form-0-field', (0, 'field')),
            ('the-form-1-field', (1, 'field')),
            ('the-form-1-field-with-dashes', (1, 'field-with-dashes')),
            ('the-form-10-field-with-dashes', (10, 'field-with-dashes')),
            ('the-form-10-10-field', (10, '10-field')),
            ('', (None, None)),
            ('the-form-10', (None, None)),
            ('not-the-form-1-field', (None, None)),
            ('the-form-TOTAL_FORMS', (None, None)),
            ('the-form-INITIAL_FORMS', (None, None)),
            ('the-form-MIN_NUM_FORMS', (None, None)),
            ('the-form-MAX_NUM_FORMS', (None, None)),
            ('the-form-n0t-a-field', (None, None)),
        )
        for case in cases:
            given, expected = case
            with self.subTest(given=given, expected=expected):
                parsed = parse_field(given, 'the-form')
                self.assertEqual(parsed, expected)
