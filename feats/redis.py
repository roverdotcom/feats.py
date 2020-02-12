from typing import List
from redis import Redis
from .errors import StorageUnavailableException


class StreamIterator:
    """
    An iterator class used to iterate over the entirety of a feature stream
    This works by pre-loading the entire stream into memory
    Note: any updates to the stream during iteration will be left out
    eg if a value is written in the middle of iteration it will not appear as
    the last value at the end of the loop
    """
    def __init__(self, stream):
        self.index = 0
        self.end = len(stream)
        self.stream = stream

    def __iter__(self):
        self.index = 0
        return self

    def __next__(self):
        if self.index >= self.end:
            raise StopIteration
        result = self.stream[self.index]
        self.index += 1
        return result[1]


class FeatureStream:
    """
    This class provides utility methods for retrieving data from Redis.
    It should not be initialized directly but instead returned from keying off
    a RedisClient instance.
    """
    def __init__(self, redis, key, prefix=None):
        self.key = self._get_key(key, prefix)
        self._redis = redis

    def _get_key(self, key, prefix) -> str:
        """
        Builds the Redis stream key. If `prefix` is provided, it will be used
        as the prefix for the feature key.
        """
        if prefix:
            return f"{prefix}:feature:{key}"
        return f"feature:{key}"

    def append(self, state) -> str:
        """
        Adds FeatureState data to the head of the Redis Stream and returns
        the Redis auto-generated id
        """
        return self._redis.xadd(self.key, state)

    def info(self) -> dict:
        """
        Wrapper for redis xinfo
        """
        if self._redis.exists(self.key):
            return self._redis.xinfo_stream(self.key)
        else:
            return None

    def read(self, index) -> dict:
        """
        reads the stream for a given redis-generated key (eg '1576268467400-0')
        and returns a single value, stripping off the id
        """
        return self.range(start=index, end=index)[0]

    def range(self, start='-', end='+') -> List[dict]:
        """
        reads the stream for a range of ids, default is entire stream
        """
        return self._redis.xrange(self.key, min=start, max=end)

    def last(self) -> dict:
        """
        Returns the value of the latest entry in the Redis Stream (omitting id)
        """
        info = self.info()
        if info is None:
            return None
        return info['last-entry'][1]

    def first(self) -> dict:
        """
        Returns the value of the first entry in the Redis Stream (omitting id)
        """
        info = self.info()
        if info is None:
            return None
        return info['first-entry'][1]

    def __len__(self) -> int:
        """
        Wrapper for stream xlen
        """
        return self._redis.xlen(self.key)

    def __iter__(self) -> StreamIterator:
        """
        Fetches the entire Redis stream and loads it into memory then returns
        a StreamIterator that will iterate over all values in the stream.
        """
        # Fetch the entire list and then iterate over it synchronously
        stream = self.range()
        return StreamIterator(stream)


class RedisClient:
    """
    Wrapper class for the redis-py connection, provides some utility methods
    to adhere to the Storage interface -- namely indexing on stream keys and
    getting a Stream object with an append method back.

    Initializing this class initializes the redis connection client but does
    _not_ test the connection to redis server.
    """
    def __init__(self, host='localhost', port=6379, db=0, key_prefix=None, **options):
        self.key_prefix = key_prefix
        self._connection_object = self._connect(host, port, db, **options)

    def _connect(self, host, port, db, **options):
        """
        Creats a reids connection with the args provided to the constructor
        and returns the connection object (does not actually connect to redis)
        """
        return Redis(**{
            'host': host,
            'port': port,
            'db': db,
            'decode_responses': True,
            **options
        })

    @property
    def connection(self):
        if self._connection_object is None:
            raise StorageUnavailableException

        return self._connection_object

    def disconnect(self):
        """
        Disconnects the client's connection pool from the redis server.
        If someone still has a reference to this _connection_object and
        calls redis methods directly on it the connection will be
        re-established. But once the connection object is out of scope
        python's GC will clean it disconnect us from the server
        Note: It is not strictly necessary to call this method to clean up
        a connection
        """
        if self._connection_object is not None:
            self._connection_object.connection_pool.disconnect()
            self._connection_object = None

    def __getitem__(self, key: str) -> FeatureStream:
        """
        The main way by which streams are interacted with. Use the feature name
        as the key to return the stream bound to that key. If `key_prefix`
        was provided on client initialization, it will be used as the prefix on
        the feature key.
        """
        return FeatureStream(self.connection, key, self.key_prefix)
