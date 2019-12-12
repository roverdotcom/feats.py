import abc
import hashlib
from bisect import bisect_left
from itertools import accumulate
from random import choices
from typing import Callable, Mapping

Weights = Mapping[str, int]
Segment = Callable[[object], str]


class Selector(metaclass=abc.ABCMeta):
    """
    A Selector decides the implementation a given input to a feature should use
    """
    @abc.abstractmethod
    def select(self, value) -> str:
        """
        Returns the name of the feature implementation to use.
        value: The object that will be given to the feature.
        """


class Static(Selector):
    """
    Static Selectors return a single implementation based on the
    configured value.
    """
    def __init__(self, value: str):
        self.value = value

    def select(self, *args, **kwargs) -> str:
        return self.value


class Rollout(Selector):
    """
    Rollout Selectors return a deterministic implementation based on the
    configured weightings.
    They are designed to gradually enable a new feature over time.
    """
    def __init__(self, segment: Segment, weights: Weights):
        self.segment = segment
        self.population = list(weights.keys())
        self.cum_weights = list(accumulate(weights.values()))
        self.modulo = self.cum_weights[-1]
        self.digest_size = self.modulo // 128 + 1

    def _hex_hash(self, key: str) -> str:
        # We aren't looking for anything cryptographically secure here
        # blake2s let's us specify the digest size (i.e the hash string length)
        # which is normally going to be 1 byte. We don't need anything larger
        # than the modulo into our implementation buckets
        return hashlib.blake2s(
            key.encode('utf-8'),
            digest_size=self.digest_size
        ).hexdigest()

    def select(self, value: object) -> str:
        key = self.segment(value)
        hash = int(self._hex_hash(key), 16)
        bucket = hash % self.modulo
        return self.population[bisect_left(self.cum_weights, bucket)]


class ExperimentPersister(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def get_existing_test_group(self, obj: object) -> str:
        """
        Returns the previously persisted group for the object.
        """

    @abc.abstractmethod
    def persist_test_group(self, obj: object, group: str) -> str:
        """
        Associates the provided test group to the specified object so that
        future checks return the group the object was already bucketed in.

        The storage of results may not always be durable. For instance,
        a cookie based implementation depends on the cookie not expiring or
        otherwise being removed from the user's machine.
        It is not guaranteed that a call to get_existing_test_group will
        always return the group given here

        If the object was already associated with the given experiment slug,
        it will not be overwritten.

        Returns the group the object is associated with for the given
        experiment slug, or None if the object is not a valid target for this
        persister.
        """


class Experiment(Selector):
    """
    Experiment Selectors return a random implementation based on the
    configured weightings.
    They remember selected values for a given segment so that future selections
    will return the same value.

    They can be used for doing A/B testing of two or more
    implementations of a feature.
    """
    def __init__(
            self,
            segment: Segment,
            persister: ExperimentPersister,
            weights: Weights
    ):
        self.segment = segment
        self.persister = persister
        self.population = list(weights.keys())
        self.weights = list(weights.values())

    def select(self, value: object) -> str:
        key = self.segment(value)
        existing_group = self.persister.get_existing_test_group(key)
        if existing_group is not None:
            return existing_group

        choice = choices(self.population, self.weights)[0]
        return self.persister.persist_test_group(key, choice)
