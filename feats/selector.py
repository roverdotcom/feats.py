import abc
import hashlib
from bisect import bisect
from itertools import accumulate
from random import choices
from typing import Callable, Mapping

Weights = Mapping[str, int]
Segment = Callable[[object], str]


class Selector(metaclass=abc.ABCMeta):
    """
    A Selector decides the implementation a given input to a feature should use
    """

    def __init__(self, name: str):
        self.name = name
        """
        A short recognizable human description of the purpose of this selector
        """

    @abc.abstractmethod
    def select(self, value) -> str:
        """
        Returns the name of the feature implementation to use.
        value: The object that will be given to the feature.
        """

    @abc.abstractmethod
    def used_implementation(self, impl: str, value):
        """
        Informs this selector that the given object has used a certain implementation
        """

    @classmethod
    @abc.abstractmethod
    def from_data(cls, app, configuration):
        """
        Returns an instance of the selector from the provided data
        """

    @abc.abstractmethod
    def serialize_data(self, app) -> dict:
        """
        Serializes the configuration of the selector for serialization
        """


class Default(Selector):
    """
    """
    def __init__(self, feature):
        super().__init__("Default")
        self.feature = feature

    def select(self, *args, **kwargs) -> str:
        return self.feature.default_implementation.name

    def used_implementation(self, impl: str, *args):
        pass

    # TODO: Separate out the distinction between a Selector and a user-created one.
    @classmethod
    def from_data(cls, app, configuration):
        pass

    def serialize_data(self, app) -> dict:
        pass


class Static(Selector):
    """
    Static Selectors return a single implementation based on the
    configured value.
    """
    def __init__(self, name: str, value: str):
        super().__init__(name)
        self.value = value

    def select(self, *args, **kwargs) -> str:
        return self.value

    def used_implementation(self, impl: str, *args):
        pass

    @classmethod
    def from_data(cls, app, configuration):
        return cls(
            name=configuration['name'],
            value=configuration['value']
        )

    def serialize_data(self, app):
        return {
            'name': self.name,
            'value': self.value,
        }


class Rollout(Selector):
    """
    Rollout Selectors return a deterministic implementation based on the
    configured weightings.
    They are designed to gradually enable a new feature over time.
    """
    def __init__(self, name: str, segment: Segment, weights: Weights):
        super().__init__(name)
        self.segment = segment
        self.weights = weights
        self.population = list(weights.keys())
        if len(self.population) == 0:
            raise ValueError("Must supply at least one weight to the selector")
        self.cum_weights = list(accumulate(weights.values()))
        self.modulo = self.cum_weights[-1]
        if self.modulo == 0:
            raise ValueError("Must supply at least one positive weight to the selector")
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
        key = self.segment.segment(value)
        hash = int(self._hex_hash(key), 16)
        bucket = hash % self.modulo
        return self.population[bisect(self.cum_weights, bucket)]

    def used_implementation(self, impl: str, value: object):
        pass

    @classmethod
    def from_data(cls, app, configuration):
        return cls(
            name=configuration['name'],
            segment=app.get_segment(configuration['segment']),
            weights=configuration['weights'],
        )

    def serialize_data(self, app):
        return {
            'name': self.name,
            'segment': self.segment.name,
            'weights': self.weights,
        }

T = TypeVar('T')

class ExperimentPersister(Generic[T], metaclass=abc.ABCMeta):
    def __init__(self, experiment_name):
        self.experiment_name = experiment_name

    @abc.abstractmethod
    def get_existing_test_group(self, obj: T) -> str:
        """
        Returns the previously persisted group for the object.
        """

    @abc.abstractmethod
    def persist_test_group(self, obj: T, group: str) -> str:
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
            name: str,
            persister: Type[ExperimentPersister],
            weights: Weights
    ):
        super().__init__(name)
        self.persister = persister(name)
        self.population = list(weights.keys())
        self.weights = list(weights.values())

    def select(self, value: object) -> str:
        existing_group = self.persister.get_existing_test_group(value)
        if existing_group is not None:
            return existing_group

        choice = choices(self.population, self.weights)[0]
        return choice

    def used_implementation(self, impl: str, value: object):
        self.persister.persist_test_group(value, impl)

    @classmethod
    def from_data(cls, app, configuration):
        return cls(
            name=configuration['name'],
            persister=app.persisters[configuration['persister']],
            weights=configuration['weights'],
        )

    def serialize_data(self, app):
        return {
            'name': self.name,
            'persister': app._name(self.persister),
            'weights': self.weights,
        }
