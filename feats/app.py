from typing import List

from .storage import Storage
from .feature import Feature
from .feature import default
from .meta import Definition
from .segment import Segment
from .state import FeatureState


class FeatureHandle:
    def __init__(self, app: 'App', name: str, feature: Feature):
        self.app = app
        self.name = name
        self.feature = feature

    def find(self, *args) -> str:
        """
        Returns the name of the implementation to use for the argument(s).
        """

        states = self.app.storage[self.name]
        try:
            state_data = states[-1]
            state = FeatureState.deserialize(state_data)
            name = state.select_implementation(*args)
        except IndexError:
            name = None

        if name is None:
            return self.feature.default_implementation.name
        return name

    def create(self, *args) -> object:
        """
        Returns the appropriate implementation to use for the argument(s).

        The implementation is found using any configured segmentations and
        selectors for the feature.
        """
        impl_name = self.find(*args)
        return self.feature.implementations[impl_name].fn(*args)


class App:
    """
    App is where all features, segments and the configurations for them
    are held. An application can have multiple app, but typically will use
    a single one.
    """
    def __init__(self, *, storage: Storage):
        """
        storage: where to store and retrieve feature states
        """
        # TODO Index by input classes?
        self.segments: List[Segment] = []
        self.features = {}
        self.storage = storage

    def feature(self, cls):
        """
        # TODO: Clearer docs
        Initializes the wrapped class and returns a handle to the registered
        feature.

        The handle has a method, create, which can be invoked to obtain an
        implementation to use.

        Example:
        @feats.feature
        class MyFeature:
            @feats.default
            def old_implementation(self):
                return OldImplementation()

            def new_implementation(self):
                return NewImplementation()

        # defaults to returning OldImplementation unless state has been
        # configured to return NewImplementation
        MyFeature.create()
        """
        definition = Definition(cls())
        feature = Feature(definition)
        name = cls.__qualname__
        module = getattr(cls, '__module__', None)
        if module:
            name = '.'.join((module, name))
        handle = FeatureHandle(self, name, feature)
        # TODO: Prevent double-write
        self.features[name] = handle
        return handle

    def default(self, fn):
        return default(fn)

    def segment(self, cls):
        definition = Definition(cls())
        seg = Segment(definition)
        self.segments.append(seg)
        return seg

    def configure_feature(self, feature: Feature, state: FeatureState):
        # TODO: Validate state against segments?
        serialized_state = state.serialize()
        self.storage[feature].append(serialized_state)

    def find_segments(self, input_cls):
        """
        Find the segments which can take the same inputs as the given class
        """
        found = []
        for segment in self.segments:
            for impl in segment.impementations:
                if impl.input_type == input_cls:
                    found.append(segment)
                    break
        return found
