![](https://github.com/roverdotcom/feats.py/workflows/Unit%20Tests/badge.svg?branch=master) ![](https://github.com/roverdotcom/feats.py/workflows/Integration%20Tests/badge.svg?branch=master)


# COMING SOON!

Feats.py is still actively being developed and as such, is **not** yet ready for
real world applications. Until then, please feel free to review this
documentation and keep an eye on this repo for an initial release!

# feats.py (WIP)
Feats.py is a feature flag library for Python applications. We built it
based on our learnings from using the [Gargoyle](https://github.com/adamchainz/gargoyle)
library in production within a medium-sized engineering organization.

Instead of giving the ability to turn features on or off, feats is based on
the ability to choose between implementations of a feature. This allows for
non-binary choices, which can help reduce the need for feature flags which depend
on other feature flags and encourge a more object-oriented programming style.
In the situations where there is a need to simply turn something on or off,
feats.py supports that as well.

# Requirements

* `>=` Python 3.6
* `>=` Redis 5.0

# Table of Contents

* [App Setup](#app-Setup)
* [Features](#features)
* [Segments](#segments)
* [Configuration](#configuration)
* [Examples](#examples)
  * [Ops Example](#operations)
  * [Rollout Example](#rollout)
  * [Experiment Example](#product-experiments)

# App Setup

In order to use Feats, we must first configure an App with which to register
features and segments. At the moment, the only configuration of the App is the
storage backend to use.

Feats contains two backend storages at the moment, an in-memory store and a redis
backed store. The in-memory store is only useful for testing environments. Redis
should be used in all other cases. Our Redis usage is based on streams, which require
Redis 5.0 or higher.

By convention, the feats app should be placed in the "feats.py" file of your
module.

```python
#myapp/feats.py
import feats
import myapp.config
app = feats.App(storage=RedisStorage(redis=Redis(decode_responses=True)))
```

When we need to declare features and segments, we will then always use the
app we have defined in myapp/feats.py `from myapp.feats import app`

# Features

Now that we have an App, we can start declaring Features.

A Feature declares all of the implementations that can be interchangebly used.
Implementations can be as simple as the button text to use, or as large as
an entire replacement View to render.

To declare a feature, decorate a class with `app.feature`.
```python
from myapp.feats import app

@app.feature
class ConfirmText:
    @app.default
    def submit(self) -> str:
        return "Submit"

    def save(self) -> str:
        return "Save"
```

The decorator replaces the class declaration with a factory-style object. We can
call the `create` method on this object to receive the confirmation text to use.

```python
text = ConfirmText.create()
```

The above will by default return "Submit" because the submit method was decorated
as the default. All features are required to have a default.

In order to have "Save" returned, we can [configure](#configuration) feats to do so.

## Boolean Features

Sometimes all we need is the ability to turn something on or off. For instance,
we may want to just disable processing images during a DDOS attack.
For this, we can use boolean features. These simply return `True` or `False`
depending on if they are enabled or disabled.

They can be declared using a single function instead of a class

```python
@app.boolean
def ImageProcessing() -> bool:
    return True # This is the default value
```

And can be used like so

```python
if ImageProcessing.is_enabled():
    process_image()
```

# Segments

We will normally want to pass in data to a feature. This allows us to select
certain users to receive an implementation. Without segments, all users will
have to receive a single implementation.

Segments tell feats how to group input objects. A segment declaration
holds functions which can convert all of your business objects into that grouping.

All segments have a single typed input argument and must return strings.

For instance,
```python
from myapp.feats import app
@app.segment
class Subdivision:
    """
    The ISO 3166-2 Subdivision Code, e.g US-WA
    """
    def user(self, user: User) -> str:
        return self.address(user.address)

    def address(self, address: Address) -> str:
        return "{}-{}".format(address.country_code, address.subdivision_code)
```
is a valid segment. It declares how to convert both a user and an address into
a subdivision code.

However, the following is not valid.
```python
from myapp.feats import app
@app.segment
class Subdivision:
    """
    The ISO 3166-2 Subdivision Code, e.g US-WA
    """
    def user(self, user) -> str: # Invalid, must declare the input type
        return self.address(user.address)

    def address(self, address: Address): # Invalid, must declare return type as str
        return "{}-{}".format(address.country_code, address.subdivision_code)
```


## Feature Inputs

Once we have segments declared, we can extend our features to take in objects.

Both class based features and function based features support this.

```python
@app.feature
class ConfirmText:
    def submit(self, user: User) -> str:
        return translate(user.language, "Submit")

    def save(self, user: User) -> str:
        return translate(user.language, "Save")

ConfirmText.create(user) # create will now require a user argument

@app.boolean
def ImageProcessing(user: User) -> bool:
    return True

ImageProcessing.is_enabled(user) # is_enabled will also require a user argument
```

Inside of a class, all of the implementations must take exactly the same arguments.
Like segments, they also must be strictly typed. This typing lets feats know which
segments are valid for which features.

```python
@app.feature
class ConfirmText:
    def submit(self, user) -> str: # Invalid, must declare input type
        return "Submit"
    def save(self) -> str: # Invalid, must have same number of inputs
        return "Save"
    def persist(self, request: HttpRequest) -> str # Invalid, must have same input types
        return "Persist"
```

# Configuration

# Examples

## Operations

Let's say our application has the ability to charge credit cards using a generic
payment provider. We have negotiated a good rate with a certain provider, and
prefer to use them whenever possible.
However, if they have technical difficulties, we still want the ability to
charge cards, even if it means more overhead.

To do this, we could declare a PaymentProcessor feature like so

```python
@app.feature
class PaymentProcessor:
    @app.default
    def acme(self, user: User) -> AcmeProcessor:
        """
        2% + $0.30 / Transaction
        """
        return AcmeProcessor()

    def premium(self, user: User) -> PremiumProcessor:
        """
        4% + $0.50 / Transaction
        """
        return PremiumProcessor()
```

Here, we have defined the cheaper processor as our default, and can take in a user
to segment off of. When asked for a payment processor, feats will always return
AcmeProcessor, unless we have configured the app otherwise.

It is important to understand that PaymentProcessor has been replaced by a handle
into the feats app. Production code creates payment processors in a factory-style.

```python
processor = PaymentProcessor.create(user)
processor.charge()
```

The acme and premium methods are no longer available to call directly
```python
processor = PaymentProcessor.acme(user) # AttributeError
processor = PaymentProcessor().acme(user) # AttributeError
```

Because our payment processor sometimes has trouble only in certain regions, we
will define segmentation of that user object based on their country.

```python
@app.segment
class Country:
    """
    The ISO-3166 2 char country code of the object
    """
    def user(self, user: User) -> str:
        return self.address(user.address)

    def address(self, address: Address) -> str:
        return address.country_code
```

Now, if our monitoring system alerts of payment difficulties in Canada, we can
change the payment processor for Canadian users to the premium one.

[TODO: Screenshots of changing to premium in CA]


After Acme has resolved their issues, we can rollback to the previous state to
have Acme process charges in Canada again.

[TODO: Screenshots of rollback]

## Rollouts

Continuing our example from before, we have now negotiated an even better rate
with a third provider. Any number of things can go wrong when integrating with
a new third party. We'd like to start using them in production by slowly
rolling them out to users.

We can extend our previous feature to add a third implementation like so
```python
@app.feature
class PaymentProcessor:
    @app.default
    def acme(self, user: User) -> AcmeProcessor:
        """
        2% + $0.30 / Transaction
        """
        return AcmeProcessor()

    def premium(self, user: User) -> PremiumProcessor:
        """
        4% + $0.50 / Transaction
        """
        return PremiumProcessor()

    def aperture(self, user: User) -> ApertureProcessor:
        """
        1% + $0.00 / Transaction
        """
        return ApertureProcessor()
```

When rolling out, we will want to start in the US and give 5% of users the new
Aperture payment processor. In order to do this, we'll need to provide a second
segmentation of user ids. The users ids is what we will take 5% of, if we were
to only use countries, we would be taking 5% of all countries.

```python
@app.segment
class UserId:
    def user(self, user: User) -> str:
        return str(user.id)
```

We can then configure the payment processor to give 5% of American users Aperture
by doing the following

[TODO: Screenshots of multi-segmented rollout]


As we are certain there are no integration issues on either side, we can give
more users the new processor

[TODO: Screenshots of increasing rollout]

## Product Experiments

Let's say our application is a TODO list.
We think our users will respond positively to having priorities of items TODO,
and would like to perform a randomized experiment to understand if that is the
case.

As before, we start off with the feature.

```python
@app.feature
class AllowedPriorities:
    @app.default
    def no_priority(self, user: User) -> List[str]:
        return []

    def two_priorities(self, user: User) -> List[str]:
        return ["Important", "Normal"]

    def three_priorities(self, user: User) -> List[str]:
        return ["Important", "Normal", "Unimportant"]
```

[TODO: Screenshots of experiment]
