from typings import Dict, List

from .storage import Storage
from .feature import Feature
from .meta import Definition
from .segment import Segment
from .state import DefaultState, FeatureState


class FeatureHandle:
    def __init__(self, app: 'App', name: str, feature: Feature):
        self.app = app
        self.name = name
        self.feature = feature
        self.default_state = DefaultState(ft.default_implementation.name)

    def create(self, *args):
        """
        Returns the appropriate implementation to use for the argument(s).

        The implementation is found using any configured segmentations and
        selectors for the feature.
        """
        states = self.app.storage[self.name]
        try:
            state = states[-1]
        except IndexError:
            state = self.default_state

        return impl(*args)


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
        self.storage = storage

    def feature(self):
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
        def wrap(cls):
            definition = Definition(cls())
            ft = Feature(definition)
            return FeatureHandle(self, ft)

        return wrap

    def segment(self):
        def wrap(cls):
            definition = Definition(cls())
            seg = Segment(definition)
            self.segments.append(seg)
            return seg

        return wrap

    def configure_feature(self, feature: Feature, state: FeatureState):
        # TODO: Validate state against segments
        self.storage[feature].append(state)

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
