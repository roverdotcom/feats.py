from typings import Dict, List

from .feature import Feature
from .meta import Definition
from .segment import Segment
from .state import DefaultState, FeatureState


class FeatureHandle:
    def __init__(self, registry, feature):
        self.registry = registry
        self.feature = feature

    def create(self, *args):
        """
        Returns the appropriate implementation to use for the argument(s).

        The implementation is found using any configured segmentations and
        selectors for the feature.
        """
        impl = self.registry.states[self.feature].select_implementation(*args)
        return impl(*args)


class Registry:
    """
    Registry is where all features, segments and the configurations for them
    are held. An application can have multiple registries, but typically
    will use the default one created in __init__.py.
    """
    def __init__(self):
        # TODO Index by input classes?
        self.segments: List[Segment] = []
        self.states: Dict[Feature, FeatureState] = []

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
            self.states[ft] = DefaultState(ft.default_implementation)
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
        self.states[feature] = state

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
