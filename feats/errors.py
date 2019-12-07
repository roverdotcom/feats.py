"""
This file will hold tools to generate user-friendly errors for common situations

This includes:
    Specified a feature with no implementations, e.g

    class MyFeature:
        def hello(self):
            return Foo()

    does not specify any implementations. These must declare a return type.

    Specified a feature with no default implementation, e.g

    class MyFeature:
        def hello(self) -> Foo:
            return Foo()

    does not specify any default implementation using @feats.default


Ideally, we can print out the offending implementation and a fix for it, or give
reasons about the implementation that the person can solve.
"""
