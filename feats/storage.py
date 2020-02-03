from copy import deepcopy

from typing import MutableMapping, MutableSequence
from .state import FeatureState
from collections import defaultdict

Storage = MutableMapping[str, MutableSequence[FeatureState]]
"""
Storage maps the name of a feature to the history of feature states for it.
The most recent state is defined as tail of the sequence, while the oldest state
is at the head of the sequence.

If this Storage has not yet seen a key, it should return an empty sequence.
"""

Memory: Storage = lambda: defaultdict(MemoryList)
"""
The Memory storage keeps all data in memory. When the application exits, all data
will be lost.
Mainly useful for testing environments.
"""
class MemoryList(list):
    """
    An implementation of list with deepcopy guard rails to prevent
    mutating state in the memory store
    """
    def last(self):
        return self[-1]

    def __getitem__(self, index):
        item = super().__getitem__(index)
        return deepcopy(item)

    def __setitem__(self, i, value):
        clone = deepcopy(value)
        super().__setitem__(i, clone)

    def append(self, value):
        clone = deepcopy(value)
        super().append(clone)
