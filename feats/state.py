from .meta import Implementation
import abc


class FeatureState(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def select_implementation(self, value) -> Implementation:
        pass


class CurrentFeatureState(FeatureState):
    """
    An object proxy for feature states.
    """
    def __init__(self, current_state):
        self.current_state = current_state




class DefaultState(FeatureState):
    def __init__(self, default: Implementation):
        self.default = default

    def select_implementation(self, *args) -> Implementation:
        return self.default


class UnaryState(FeatureState):
    """
    UnaryState holds the segmentation and how selectors should be used for a
    feature which has a single input.
    """
    # TODO: Nullary features, which don't have selector mappings, but a single
    # selector. Probably make this an ABC instead

    def __init__(self,
                 segments,
                 default_implementation: Implementation,
                 selector_mapping):
        # selector_mapping is a dictionary from string tuples to selectors
        # The values of the tuple is the segmentation of the input to the
        # feature in the order that the segments are specified
        self.segments = segments
        self.selector_mapping = selector_mapping

    def select_implementation(self, value) -> Implementation:
        segment_values = [segment(value) for segment in self.segments]
        selector = self.selector_mapping.get(segment_values, None)
        if selector is None:
            return self.default_implementation
        return selector.select_implementation(value)
