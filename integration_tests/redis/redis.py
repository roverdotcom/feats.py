from unittest import TestCase
from unittest.mock import patch

from feats.redis import FeatureStream
from feats.redis import RedisClient
from feats.redis import StreamIterator
from feats.errors import StorageUnavailableException


class RedisClientTests(TestCase):
    def setUp(self):
        super().setUp()
        self.client = RedisClient(host='redis')

    def test_connection_property_raises_error(self):
        self.client.disconnect()
        with self.assertRaises(StorageUnavailableException):
            self.client.connection

    def test_keying_on_client_raises_exception(self):
        self.client.disconnect()
        with self.assertRaises(StorageUnavailableException):
            self.client['somefeature']

    def test_connection_property_returns_conn_object(self):
        self.assertIsNotNone(self.client.connection)

    def test_disconnect_closes_connection(self):
        conn = self.client.connection
        with patch.object(conn.connection_pool, 'disconnect') as mock:
            self.client.disconnect()
            mock.assert_called_once()
            self.assertIsNone(self.client._connection_object)

    def test_options_can_override_defaults(self):
        client = RedisClient(host='redis', decode_responses=False)
        self.assertFalse(client.connection.connection_pool.connection_kwargs.get('decode_responses'))
        self.assertTrue(self.client.connection.connection_pool.connection_kwargs.get('decode_responses'))

    def test_calls_feature_stream_with_prefix(self):
        key = 'somefeature'
        prefix = 'myprefix'
        client = RedisClient(host='redis', key_prefix=prefix)
        with patch.object(FeatureStream, '__init__', return_value=None) as mock:
            client[key]
            mock.assert_called_once_with(client.connection, key, prefix)


class FeatureTests(TestCase):
    def setUp(self):
        super().setUp()
        self.client = RedisClient(host='redis')
        self._purge_stream()

    @property
    def _stream_name(self):
        return 'my-feature-stream'

    def _get_stream(self):
        return self.client[self._stream_name]

    def _purge_stream(self):
        stream_name = self.client[self._stream_name].key
        self.client.connection.xtrim(stream_name, 0)

    def _populate_stream(self):
        stream = self._get_stream()
        stream.append({'foo': 'bar'})
        stream.append({'fizz': 'buzz'})
        stream.append({'some': 'stuff'})
        stream.append({'more': 'things'})


class FeatureStreamTests(FeatureTests):
    def test_keying_client_returns_featurestream(self):
        stream = self.client['my-feature-stream']
        self.assertIsInstance(stream, FeatureStream)

    def test_stream_bound_to_namespaced_key(self):
        stream_key = 'feature:a-feature-stream-key'
        stream = self.client['a-feature-stream-key']
        self.assertEqual(stream.key, stream_key)

    def test_stream_key_uses_key_prefix_if_set(self):
        client = RedisClient(host='redis', key_prefix='envname')
        stream_key = 'envname:feature:a-feature-stream-key'
        stream = client['a-feature-stream-key']
        self.assertEqual(stream.key, stream_key)

    def test_stream_keeps_redis_connection_object(self):
        stream = self._get_stream()
        self.assertIs(stream._redis, self.client.connection)

    def test_stream_write_read(self):
        stream = self._get_stream()
        key = stream.append({'some_data': 'some_value'})
        expected_tuple = (key, {'some_data': 'some_value'})
        self.assertEqual(stream.read(key), expected_tuple)

    def test_stream_info(self):
        self._populate_stream()
        stream = self._get_stream()
        info = stream.info()
        self.assertEqual(info['length'], 4)
        self.assertEqual(info['first-entry'][1], {'foo': 'bar'})
        self.assertEqual(info['last-entry'][1], {'more': 'things'})

    def test_stream_length(self):
        self._populate_stream()
        stream = self._get_stream()
        self.assertEqual(len(stream), 4)

    def test_first_gets_first_entry(self):
        self._populate_stream()
        stream = self._get_stream()
        self.assertEqual(stream.first()['foo'], 'bar')

    def test_last_gets_last_entry(self):
        self._populate_stream()
        stream = self._get_stream()
        self.assertEqual(stream.last()['more'], 'things')


class StreamIteratorTests(FeatureTests):
    def test_iterator_retuns_stream_iterator(self):
        iterator = iter(self._get_stream())
        self.assertIsInstance(iterator, StreamIterator)

    def test_iterates_over_entries(self):
        self._populate_stream()
        stream = self._get_stream()
        for item in stream:
            self.assertIsNotNone(item)

    def test_does_not_change_size_during_iteration(self):
        self._populate_stream()
        stream = self._get_stream()
        for item in stream:
            stream.append({'another': 'value'})
            self.assertNotEqual(item, {'another': 'value'})


class MultipleClientTests(FeatureTests):
    def setUp(self):
        super().setUp()
        self.client2 = RedisClient(host='redis')
        self._purge_stream()

    def _get_stream2(self):
        return self.client2[self._stream_name]

    def test_reads_changes_from_other_client(self):
        stream1 = self._get_stream()
        stream2 = self._get_stream2()
        stream1.append({'my': 'data'})
        self.assertEqual(stream2.last(), {'my': 'data'})

    def test_iteration_does_not_read_second_client_data(self):
        self._populate_stream()
        stream1 = self._get_stream()
        stream2 = self._get_stream2()
        for item in stream2:
            stream1.append({'another': 'value'})
            self.assertNotEqual(item, {'another': 'value'})
