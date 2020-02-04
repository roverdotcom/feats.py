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
    This is an append-only list meant to store serialized feature states.
    It is immutable by design and returns deep copies so accidental mutations
    are prevented
    """
    def last(self):
        return self[-1]

    def __getitem__(self, index):
        item = super().__getitem__(index)
        return deepcopy(item)

    def __setitem__(self, i, value):
        raise TypeError("'MemoryList' object does not support item assignment")

    def append(self, value):
        clone = deepcopy(value)
        super().append(clone)
