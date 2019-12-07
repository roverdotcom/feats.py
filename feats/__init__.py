from .feature import default
from .registry import Registry

registry = Registry()

__all__ = [registry.feature, registry.segment, default]
