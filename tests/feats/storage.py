from unittest import TestCase
from feats.storage import Memory


class MemoryStorageTests(TestCase):
    def setUp(self):
        super().setUp()
        self.storage = Memory()
        self.stream_name = 'test:feature'
        self.sample_data = {
            'some': 'serialized_data'
        }
        self.storage[self.stream_name].append(self.sample_data)

    def test_last_returns_deep_copy(self):
        stream = self.storage[self.stream_name]
        last = stream.last()
        self.assertEqual(self.sample_data, last)
        self.assertIsNot(self.sample_data, last)

    def test_mutating_does_not_change_state_in_memory(self):
        stream = self.storage[self.stream_name]
        last = stream.last()
        last['some'] = 'new_data'
        self.assertEqual(
            self.storage[self.stream_name].last(),
            self.sample_data
        )

    def test_append_saves_copy(self):
        stream = self.storage[self.stream_name]
        data = {
            'new': 'entry'
        }
        stream.append(data)
        data['new'] = 'data'
        self.assertEqual(stream.last()['new'], 'entry')

    def test_set_saves_copy(self):
        stream = self.storage[self.stream_name]
        data = {
            'new': 'entry'
        }
        stream[0] = data
        data['new'] = 'data'
        self.assertEqual(stream[0]['new'], 'entry')

    def test_get_item_returns_copy(self):
        stream = self.storage[self.stream_name]
        last = stream[0]
        self.assertEqual(self.sample_data, last)
        self.assertIsNot(self.sample_data, last)
