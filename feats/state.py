import json
from .selector import Selector
from .errors import InvalidSerializerVersion


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

    def _get_module_name(self, klass):
        name = klass.__qualname__
        module = getattr(klass, '__module__', None)
        if module:
            return '.'.join((module, name))
        return name

    def serialize(self) -> dict:
        """
        Serializes the data we need for the feature state to be stored
        """
        state = {
            'segmentation': ','.join([self._get_module_name(s) for s in self.segments]),
            'created_by': self.created_by,
            'version': self.version,
        }
        # A map for looking up the key name by selector for later
        selector_map = {}
        for selector, i in self.selectors:
            key = f'selector:{i}'
            selector_map[selector] = key
            state[key] = json.dumps({
                # TODO: define these methods
                'type': selector.get_type(),
                'data': selector.serialize_data(),
            })

        for i, (values, selector) in enumerate(self.selector_mapping.items()):
            segments = ','.join(values)
            key = f'segment:{segments}'
            state[key] = selector_map[selector]

        return state

    @classmethod
    def _build_segment(cls, key, value):
        # TODO: reference a map to get the class from the module name
        pass

    @classmethod
    def _build_selector(cls, key, value):
        # TODO: Get the type then get the type of selector
        # TODO: deserialize it
        pass

    @classmethod
    def deserialize(cls, data: dict):
        version = data.pop('version')
        if version != cls.version:
            return InvalidSerializerVersion
        segmentation = data.pop('segmentation').split(',')
        created_by = data.pop('created_by')
        selector_data = {
            k: cls._build_selector(v) for k, v in data.items() if k.startswith('selector:')
        }
        # Join a segment key to a selector instance
        segment_data = {
            k:v for k, v in data.items()
            if k.startswith('segment:')
        }
        selector_mapping = {}
        segments = [cls._build_segment(segment) for segment in segmentation]
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
