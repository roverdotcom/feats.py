import json
from typing import Optional
from .selector import Selector
from .errors import InvalidSerializerVersion


class FeatureState:
    version = 'v1'

    @classmethod
    def initial(cls, created_by):
        return cls(
                segments=[],
                selectors=[],
                selector_mapping={},
                created_by=created_by
        )

    def __init__(self,
                 segments,
                 selectors,
                 selector_mapping,
                 created_by):
        # selector_mapping is a dictionary from string tuples to selectors
        # The values of the tuple is the segmentation of the input to the
        # feature in the order that the segments are specified
        # the special "None" key, if specified, is used if no mapping is found.
        self.segments = segments
        self.selectors = selectors
        self.selector_mapping = selector_mapping
        self.created_by = created_by
        for selector in self.selector_mapping.values():
            if selector not in self.selectors:
                raise ValueError(f"{selector.name} was mapped, but not included in the set of selectors for this feature")

    def find_selector(self, *args) -> Optional[Selector]:
        segment_values = tuple([segment.segment(*args) for segment in self.segments])
        return self.selector_mapping.get(segment_values, self.selector_mapping.get(None))

    def add_selector(self, selector: Selector, created_by: str) -> 'FeatureState':
        selectors = self.selectors.copy()
        selector_mapping = self.selector_mapping.copy()
        segments = self.segments.copy()
        selectors.append(selector)

        return FeatureState(
                segments,
                selectors,
                selector_mapping,
                created_by,
        )

    def update_selector(self, index: int, selector: Selector, created_by: str) -> 'FeatureState':
        selectors = self.selectors.copy()
        selector_mapping = self.selector_mapping.copy()
        segments = self.segments.copy()
        current_selector = selectors[index]

        mapped_to = [key for key, value in selector_mapping.items() if value == current_selector]
        for key in mapped_to:
            selector_mapping[key] = selector
        selectors[index] = selector

        return FeatureState(
                segments,
                selectors,
                selector_mapping,
                created_by,
        )

    def remove_selector(self, index: int, created_by: str) -> 'FeatureState':
        removed = self.selectors[index]

        selectors = self.selectors[:index] + self.selectors[index+1:]
        segments = self.segments.copy()

        selector_mapping = { key: value for key, value in self.selector_mapping.items() if value != removed }
        return FeatureState(
                segments,
                selectors,
                selector_mapping,
                created_by,
        )


    def serialize(self, app) -> dict:
        """
        Serializes the data we need for the feature state to be stored
        """
        state = {
            'segmentation': json.dumps([s.name for s in self.segments]),
            'created_by': self.created_by,
            'version': self.version,
        }
        # Build a map of keys to selectors and a reversed version for lookups
        selector_map = {}
        for i, selector in enumerate(self.selectors):
            key = f'selector:{i}'
            selector_map[selector] = key
            state[key] = json.dumps({
                'type': app._name(selector),
                'data': selector.serialize_data(app),
            })

        for values_tuple, selector in self.selector_mapping.items():
            segments = json.dumps(values_tuple)
            key = f'segment:{segments}'
            # Get the key from the reversed map (selector instance -> key)
            state[key] = selector_map[selector]

        return state

    @classmethod
    def _build_selector(cls, app, selector_data):
        """
        Fetches the correct selector based on the type parameter in the JSON blob,
        then uses that selector type's deserialize method to construct a selector
        from the parsed data
        """
        parsed = json.loads(selector_data)
        SelectorClass = app.get_selector(parsed['type'])
        # Initialize the appropriate selector
        return SelectorClass.from_data(app, parsed['data'])

    @classmethod
    def deserialize(cls, app, data: dict):
        """
        Compiles the serialized data from the store and constructs an
        instance of FeatureState from it.
        """
        version = data['version']
        if version != cls.version:
            raise InvalidSerializerVersion
        segmentation = json.loads(data['segmentation'])
        created_by = data['created_by']
        selector_data = {
            k: cls._build_selector(app, v) for k, v in data.items() if k.startswith('selector:')
        }
        segment_data = {
            k: v for k, v in data.items() if k.startswith('segment:')
        }
        segments = [app.get_segment(segment) for segment in segmentation]

        selector_mapping = {}
        for segment, selector_key in segment_data.items():
            selector = selector_data[selector_key]
            # Convert 'selector:["us","android"]' to ('us', 'android')
            key = json.loads(segment.split(':', 1)[1])
            # key can be none if they are using a fallthrough
            if key is not None:
                key = tuple(key)
            selector_mapping[key] = selector

        return cls(
            segments=segments,
            selectors=list(selector_data.values()),
            selector_mapping=selector_mapping,
            created_by=created_by,
        )
