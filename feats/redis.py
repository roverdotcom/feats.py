from typing import List
from redis import Redis
from redis.exceptions import ConnectionError


class NotConnectedError(ConnectionError):
    pass


class StreamIterator:
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
    def __init__(self, redis, key):
        self.key = key
        self._redis = redis

    def append(self, state) -> str:
        return self._redis.xadd(self.key, state)

    def info(self):
        return self._redis.xinfo_stream(self.key)

    def read(self, index) -> dict:
        """
        reads the stream for a given redis-generated key (eg '1576268467400-0')
        """
        return self.range(start=index, end=index)[0]

    def range(self, start='-', end='+') -> List[dict]:
        """
        reads the stream for a range of ids, default is entire stream
        """
        return self._redis.xrange(self.key, min=start, max=end)

    def last(self) -> dict:
        info = self.info()
        return info['last-entry'][1]

    def first(self) -> dict:
        info = self.info()
        return info['first-entry'][1]

    def __len__(self) -> int:
        return self._redis.xlen(self.key)

    def __iter__(self) -> StreamIterator:
        # Fetch the entire list and then iterate over it synchronously
        stream = self.range()
        return StreamIterator(stream)


class RedisClient:
    def __init__(self, host='localhost', port=6379, db=0, decode_responses=True, **options):
        self._connection_object = self._connect(host, port, db, decode_responses, **options)

    def _connect(self, host, port, db, decode_responses, **options):
        """
        Connects to redis with the args provided to the constructor
        and returns a connection object (does not actually connect to redis)
        """
        return Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=decode_responses,
            **options
        )

    @property
    def connection(self):
        if self._connection_object is None:
            raise NotConnectedError

        return self._connection_object

    def disconnect(self):
        if self._connection_object is not None:
            # if someone still has a reference to this _connection_object and
            # calls redis methods directly on it the connection will be
            # re-established. But once the connection object is out of scope
            # python's GC will disconnect us from the server
            self._connection_object.connection_pool.disconnect()
            self._connection_object = None

    def __getitem__(self, key: str) -> FeatureStream:
        return FeatureStream(self.connection, key)
