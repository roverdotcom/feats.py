from typing import Dict

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
            state = states[-1]
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

    def valid_segments(self):
        """
        Find the segments which can take the same inputs as the given class
        """
        input_type = None
        if len(self.feature.input_types) == 0:
            return {}
        elif len(self.feature.input_types) > 1:
            return {}
        input_type = self.feature.input_types[0]
        found = {}
        for name, segment in self.app.segments.items():
            impl = segment.find_implementation(input_type)
            if impl is not None:
                found[name] = segment
        return found


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
        self.storage = storage

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
        self.storage[feature].append(state)
