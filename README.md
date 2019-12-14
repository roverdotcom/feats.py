# feats.py (WIP)
Feats.py is a feature flag library for Python applications. We built it
based on our learnings from using the [Gargoyle](https://github.com/adamchainz/gargoyle)
library in production for a medium-sized engineering organization.

Instead of giving the ability to turn features on or off, feats.py is based on
the ability to choose between implementations of a feature. This allows for
non-binary choices, which can help reduce the need for feature flags which depend
on other feature flags and encourge a more object-oriented programming style.
In the situations where there is a need to simply turn something on or off,
feats.py supports that as well.

# Requirements

* `>=` Python 3.6
* `>=` Redis 5.0

# App Setup

In order to use Feats, we must first configure an App with which to register
features and segments. At the moment, the only configuration of the App is the
storage backend to use.

Feats contains two backend storages at the moment, an in-memory store and a redis
backed store. The in-memory store is only useful for testing environments. Redis
should be used in all other cases. Our Redis usage is based on streams, which require
Redis 5.0 or higher.

# Features

# Segments

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
