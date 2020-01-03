from typing import Dict

from .storage import Storage
from .errors import UnknownSelectorName
from .feature import Feature
from .feature import default
from .meta import Definition
from .segment import Segment
from .selector import Experiment, Rollout, Selector, Static
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
            state = FeatureState.deserialize(self.app, state_data)
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
        self.segments: Dict[str, Segment] = {}
        self.features: Dict[str, FeatureHandle] = {}
        self.selectors: Dict[str, Selector] = {}
        self.storage = storage

        for cls in [Experiment, Rollout, Static]:
            self.register_selector(cls)

    def _name(self, cls):
        """
        Constructs the fully qualified name of the given class.
        This includes the module path, if any, and the class's qualified name.
        """
        name = cls.__qualname__
        module = getattr(cls, '__module__', None)
        if module:
            name = '.'.join((module, name))
        return name

    def register_selector(self, cls):
        """
        A method for registering Selectors with the app for
        serializing/deserializing
        """
        self.selector[self._name(cls)] = cls

    def get_selector(self, class_name):
        if class_name not in self.selectors:
            raise UnknownSelectorName(class_name)
        return self.selectors[class_name]

    def get_segment(self, segment_name):
        """
        Fetches the segment from our application related to the fully qualified name
        """
        segment = self.segments.get(segment_name)
        if segment is None:
            raise UnknownSegmentName(segment_name)
        return segment

    def feature(self, cls):
        """
        # TODO: Clearer docs
        Initializes the wrapped class and returns a handle to the registered
        feature.

        The handle has a method, create, which can be invoked to obtain an
        implementation to use.

        Example:
        @my_app.feature
        class MyFeature:
            @my_app.default
            def old_implementation(self) -> OldImplementation:
                return OldImplementation()

            def new_implementation(self) -> NewImplementation:
                return NewImplementation()

        # defaults to returning OldImplementation unless state has been
        # configured to return NewImplementation
        MyFeature.create()
        """
        definition = Definition(cls())
        feature = Feature(definition)
        name = self._name(cls)
        handle = FeatureHandle(self, name, feature)
        # TODO: Prevent double-write
        self.features[name] = handle
        return handle

    def default(self, fn):
        """
        Annotates the given function as the default implementation of the feature.
        Only valid for functions inside of a class annotated with @feature
        """
        return default(fn)

    def segment(self, cls):
        """
        TODO: Clearer Docs
        Initializes the wrapped class and returns a handle to the registered
        segment.

        Example
        @my_app.segment
        class MySegment:
            def integers(self, i: int) -> str:
                return str(i)

            def floats(self, f: float) -> str:
                return str(f)
        """

        definition = Definition(cls())
        seg = Segment(definition)
        name = self._name(cls)
        self.segments[name] = seg
        return seg

    def configure_feature(self, feature: Feature, state: FeatureState):
        # TODO: Validate state against segments?
        serialized_state = state.serialize(self)
        self.storage[feature].append(serialized_state)

    def find_segments(self, input_cls):
        """
        Find the segments which can take the same inputs as the given class
        """
        # TODO: Consider indexing segments by input types
        found = []
        for segment in self.segments.values():
            for impl in segment.impementations:
                if impl.input_type == input_cls:
                    found.append(segment)
                    break
        return found
