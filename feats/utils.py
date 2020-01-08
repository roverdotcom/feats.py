from collections import defaultdict
from typing import Dict

from .meta import Implementation


def fn_to_implementations(fn):
    implementations: Dict[str, Implementation] = {}
    annotations = defaultdict(list)
    impl = Implementation(fn)
    implementations[impl.name] = impl

    if hasattr(fn, '_feats_annotations_'):
        for annotation in fn._feats_annotations_:
            annotations[annotation].append(impl)

    return implementations, annotations


def obj_to_implementations(obj):
    implementations: Dict[str, Implementation] = {}
    annotations = defaultdict(list)

    for key in dir(obj):
        value = getattr(obj, key)
        if key.startswith('_') or not callable(value):
            continue
        impl = Implementation(value)
        implementations[impl.name] = impl
        if hasattr(value, '_feats_annotations_'):
            for annotation in value._feats_annotations_:
                annotations[annotation].append(impl)

    return implementations, annotations
