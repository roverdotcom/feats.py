import inspect
from typing import Dict
import copy

from .storage import Storage
from .errors import UnknownSelectorName, UnknownSegmentName
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
        state = self.get_current_state()
        name = None
        if state is None:
            name = state.select_implementation(*args)

        if name is None:
            name = self.feature.default_implementation.name

        return name

    def create(self, *args) -> object:
        """
        Returns the appropriate implementation to use for the argument(s).

        The implementation is found using any configured segmentations and
        selectors for the feature.
        """
        impl_name = self.find(*args)
        return self.feature.implementations[impl_name].fn(*args)

    def set_state(self, new_state: FeatureState):
        serialized_state = copy.deepcopy(new_state.serialize(self.app))
        self.app.storage[self.name].append(serialized_state)

    def get_current_state(self) -> FeatureState:
        states = self.app.storage[self.name]
        try:
            state_data = states.last()
        except IndexError:
            return None

        return FeatureState.deserialize(self.app, state_data)

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
        self.selectors: Dict[str, Selector] = {}
        self.storage = storage

        for cls in [Experiment, Rollout, Static]:
            self.register_selector(cls)

    def _name(self, cls):
        """
        Constructs the fully qualified name of the given class.
        This includes the module path, if any, and the class's qualified name.
        """
        if hasattr(cls, '__qualname__'):
            name = cls.__qualname__
        else:
            name = cls.__class__.__qualname__
        module = getattr(cls, '__module__', None)
        if module:
            name = '.'.join((module, name))
        return name

    def register_selector(self, cls):
        """
        A method for registering Selectors by module name with the app for
        serializing/deserializing
        """
        self.selectors[self._name(cls)] = cls

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
        if not inspect.isclass(cls):
            raise ValueError("Invalid feature object - expected class")

        obj = cls()
        definition = Definition.from_object(obj)
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

    def boolean(self, fn):
        """
        Similar to `feature` but operates on a function. Initializes the
        wrapped function and returns a handle to the registered boolean
        feature.

        The handle has a method, create, which can be invoked to obtain an
        implementation to use.

        Example:
        @my_app.boolean
        def MyFeature() -> bool:
            return True

        This function will be automatically annotated as the default
        implementation.
        """
        if not callable(fn):
            raise ValueError("Boolean feature must be a function")

        return_type = inspect.signature(fn).return_annotation
        if return_type != bool:
            raise ValueError(f"Expected bool return type - got {return_type}")

        fn = self.default(fn)
        definition = Definition.from_function(fn)
        feature = Feature(definition)
        name = fn.__name__
        handle = FeatureHandle(self, name, feature)
        self.features[name] = handle

        return handle

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
        if not inspect.isclass(cls):
            raise ValueError("Invalid segment object - expected class")

        obj = cls()
        name = self._name(cls)
        definition = Definition.from_object(obj)
        seg = Segment(name, definition)
        self.segments[name] = seg
        return seg
