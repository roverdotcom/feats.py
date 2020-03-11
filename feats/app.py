import inspect
from typing import Dict, List, Optional, Type
import copy

from .storage import Storage
from .errors import UnknownSelectorName, UnknownSegmentName
from .feature import Feature
from .feature import default
from .meta import Definition
from .segment import Segment
from .selector import Experiment, Rollout, Selector, Static, Default
from .state import FeatureState


class FeatureHandle:
    def __init__(self, app: 'App', name: str, feature: Feature):
        self.app = app
        self.name = name
        self.feature = feature

    def find_selector(self, *args) -> Selector:
        state = self.state
        if state is not None:
            selector = state.find_selector(*args)
            return selector
        return Default(self.feature)

    def find_implementation(self, *args) -> str:
        """
        Returns the name of the implementation to use for the argument(s).
        """
        selector = self.find_selector(*args)
        return selector.select(*args)

    def used_implementation(self, impl: str, *args):
        selector = self.find_selector(*args)
        selector.used_implementation(impl, *args)

    @property
    def state(self) -> Optional[FeatureState]:
        states = self.app.storage[self.name]
        try:
            state_data = states.last()
        except IndexError:
            return None

        return FeatureState.deserialize(self.app, state_data)

    @state.setter
    def state(self, new_state: FeatureState):
        serialized_state = copy.deepcopy(new_state.serialize(self.app))
        self.app.storage[self.name].append(serialized_state)

    def valid_segments(self):
        """
        Returns the segments which can take the same inputs as this feature
        """
        input_type = None
        if len(self.feature.input_types) != 1:
            return {}

        input_type = self.feature.input_types[0]
        found = {}
        for name, segment in self.app.segments.items():
            impl = segment.find_implementation(input_type)
            if impl is not None:
                found[name] = segment
        return found


class FeatureFactory(FeatureHandle):
    def create(self, *args) -> object:
        """
        Returns the appropriate implementation to use for the argument(s).

        The implementation is found using any configured segmentations and
        selectors for the feature.
        """
        selector = self.find_selector(*args)
        name = selector.select(*args)
        selector.used_implementation(name, *args)
        return self.feature.implementations[name].fn(*args)


class FeatureConditional(FeatureHandle):
    def is_enabled(self, *args) -> bool:
        selector = self.find_selector(*args)
        name = selector.select(*args)
        selector.used_implementation(name, *args)
        return bool(self.feature.implementations[name].fn(*args))


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
            self.selectors[self._name(cls)] = cls

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

    def get_applicable_features(self, input_types: List[Type]) -> List[FeatureHandle]:
        """
        Returns the registered features which require values of the given input types.
        """
        return [
                handle for handle in self.features.values()
                if handle.feature.input_types == input_types
        ]

    def feature(self, cls) -> FeatureFactory:
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
        handle = FeatureFactory(self, name, feature)
        # TODO: Prevent double-write
        self.features[name] = handle
        return handle

    def default(self, fn):
        """
        Annotates the given function as the default implementation of the feature.
        Only valid for functions inside of a class annotated with @feature
        """
        return default(fn)

    def boolean(self, fn) -> FeatureConditional:
        """
        Similar to `feature` but operates on a boolean function.
        wrapped function and returns a handle to the registered boolean
        feature.

        Example:
        @my_app.boolean
        def MyFeature() -> bool:
            return True

        # Defaults to returning True
        MyFeature.is_enabled()

        This function will be automatically annotated as the default value,
        and can be configured to either return True, False or the default value.

        """
        if not callable(fn):
            raise ValueError("Boolean feature must be a function")

        return_type = inspect.signature(fn).return_annotation
        if return_type != bool:
            raise ValueError(f"Expected bool return type - got {return_type}")

        definition = Definition.from_function(fn)
        feature = Feature(definition)
        name = self._name(fn)
        handle = FeatureConditional(self, name, feature)
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
