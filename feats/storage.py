from typing import MutableMapping, MutableSequence
from .state import FeatureState

Storage = MutableMapping[str, MutableSequence[FeatureState]]
"""
Storage maps the name of a feature to the history of feature states for it.
The most recent state is defined as tail of the sequence, while the oldest state
is at the head of the sequence.

If this Storage has not yet seen a key, it should return an empty sequence.
"""

Memory: Storage = lambda: defaultdict(list)
"""
The Memory storage keeps all data in memory. When the application exits, all data
will be lost.
Mainly useful for testing environments.
"""

