class FeatureState:
    def __init__(self,
                 segments,
                 selectors,
                 selector_mapping,
                 created_by):
        # selector_mapping is a dictionary from string tuples to selectors
        # The values of the tuple is the segmentation of the input to the
        # feature in the order that the segments are specified
        self.segments = segments
        self.selector_mapping = selector_mapping

    def select_implementation(self, *args) -> str:
        segment_values = [segment(*args) for segment in self.segments]
        selector = self.selector_mapping.get(segment_values, None)
        if selector is None:
            return None
        return selector.select(*args)
