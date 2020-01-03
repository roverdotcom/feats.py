import json
from .selector import Selector
from .errors import InvalidSerializerVersion
from .errors import UnknownSegmentName


class FeatureState:
    version = 'v1'

    def __init__(self,
                 segments,
                 selectors,
                 selector_mapping,
                 created_by):
        # selector_mapping is a dictionary from string tuples to selectors
        # The values of the tuple is the segmentation of the input to the
        # feature in the order that the segments are specified
        self.segments = segments
        self.selectors = selectors
        self.selector_mapping = selector_mapping
        self.created_by = created_by

    def select_implementation(self, *args) -> str:
        segment_values = [segment(*args) for segment in self.segments]
        selector = self.selector_mapping.get(segment_values, None)
        if selector is None:
            return None
        return selector.select(*args)

    def serialize(self, app) -> dict:
        """
        Serializes the data we need for the feature state to be stored
        eg:
        {
            'segmentation': 'country,device',
            'segment:us,android': 'selector:0',
            'selector:0': '{"type": "experiment", "data": {...json...}}'
            'created_by': 'foo@bar.com',
            'version': 'v1',
        }
        """
        state = {
            'segmentation': ','.join([app._name(s) for s in self.segments]),
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
                'data': selector.serialize_data(),
            })

        for values_tuple, selector in self.selector_mapping.items():
            segments = ','.join(values_tuple)
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
        selector = app.get_selector(parsed['type'])
        return selector.from_data(parsed['data'])

    @classmethod
    def deserialize(cls, app, data: dict):
        """
        Compiles the serialized data from the store and constructs an
        instance of FeatureState from it.
        """
        version = data.pop('version')
        if version != cls.version:
            return InvalidSerializerVersion
        segmentation = data.pop('segmentation').split(',')
        created_by = data.pop('created_by')
        selector_data = {
            k: cls._build_selector(app, v) for k, v in data.items() if k.startswith('selector:')
        }
        segment_data = {
            k:v for k, v in data.items()
            if k.startswith('segment:')
        }
        selector_mapping = {}
        segments = [app.get_segment(app, segment) for segment in segmentation]
        for segment, selector_key in segment_data.items():
            selector = selector_data[selector_key]
            # Convert "selector:us,android" to ('us', 'android')
            key = tuple(segment.split(':')[1].split(','))
            selector_mapping[key] = selector

        return cls(
            segments=segments,
            selectors=selector_data.values(),
            selector_mapping=selector_mapping,
            created_by=created_by,
        )
