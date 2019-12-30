from feats import default
from feats.django.apps import feats

@feats.feature
class ExampleFeature:
    @default
    def default_selection(self) -> str:
        return "This is the default"

    def first_alternative(self) -> str:
        return "Alternative 1"

    def second_alternative(self) -> str:
        return "Alternative 2"
        



