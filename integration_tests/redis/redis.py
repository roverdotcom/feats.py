from unittest import TestCase
from unittest.mock import patch

from feats.redis import ConnectionError
from feats.redis import FeatureStream
from feats.redis import RedisClient
from feats.redis import StreamIterator
from feats.redis import NotConnectedError


class RedisClientTests(TestCase):
    def setUp(self):
        super().setUp()
        self.client = RedisClient(host='redis')
        self.bad_client = RedisClient(host='invalid')
        self.client.connect()

    def test_connection_errors_bad_connection(self):
        with self.assertRaises(ConnectionError):
            self.bad_client.connect()

    def test_connect_returns_true(self):
        self.assertTrue(self.client.connect())

    def test_connect_returns_cached_connection(self):
        conn = self.client.connection
        self.client.connect()
        self.assertIs(conn, self.client.connection)

    def test_connection_property_raises_error(self):
        self.client.disconnect()
        with self.assertRaises(NotConnectedError):
            self.client.connection

    def test_connection_property_returns_conn_object(self):
        self.assertIsNotNone(self.client.connection)

    def test_disconnect_closes_connection(self):
        conn = self.client.connection
        with patch.object(conn.connection_pool, 'disconnect') as mock:
            self.client.disconnect()
            mock.assert_called_once()
            self.assertIsNone(self.client._connection_object)

class FeatureTests(TestCase):
    def setUp(self):
        super().setUp()
        self.client = RedisClient(host='redis')
        self.client.connect()
        self._purge_stream()

    @property
    def _stream_name(self):
        return 'my-feature-stream'

    def _get_stream(self):
        return self.client[self._stream_name]

    def _purge_stream(self):
        self.client.connection.xtrim(self._stream_name, 0)

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

    def test_stream_bound_to_key(self):
        stream_key = 'a-feature-stream-key'
        stream = self.client['a-feature-stream-key']
        self.assertEqual(stream.key, stream_key)

    def test_stream_keeps_redis_connection_object(self):
        stream = self._get_stream()
        self.assertIs(stream._redis, self.client.connection)

    def test_stream_write_read(self):
        stream = self._get_stream()
        key = stream.append({'some_data': 'some_value'})
        expected_tuple = (key, {b'some_data': b'some_value'})
        self.assertEqual(stream.read(key), expected_tuple)

    def test_stream_info(self):
        self._populate_stream()
        stream = self._get_stream()
        info = stream.info()
        self.assertEqual(info['length'], 4)
        self.assertEqual(info['first-entry'][1], {b'foo': b'bar'})
        self.assertEqual(info['last-entry'][1], {b'more': b'things'})

    def test_stream_length(self):
        self._populate_stream()
        stream = self._get_stream()
        self.assertEqual(len(stream), 4)

    def test_firt_gets_first_entry(self):
        self._populate_stream()
        stream = self._get_stream()
        self.assertEqual(stream.first()[b'foo'], b'bar')

    def test_last_gets_last_entry(self):
        self._populate_stream()
        stream = self._get_stream()
        self.assertEqual(stream.last()[b'more'], b'things')


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
        iterator = iter(self._get_stream())
        stream.append({'another': 'value'})
        for item in stream:
            print(item)
            self.assertNotEqual(item, {b'another': b'value'})
