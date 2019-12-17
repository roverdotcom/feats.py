from feats.app import App
from feats.feature import Feature
import os
import html


def user_format(value, **kwargs):
    """
    Format a string with user input
    """
    escaped_kwargs = {key: html.escape(value) for key, value in kwargs.items()}
    return value.format(**escaped_kwargs)


def readfile(filename):
    with open(os.path.dirname(__file__).join(filename)) as file:
        return file.read()


class Template:
    html = readfile("template.html")

    def __init__(self, *, header="", sidebar="", main="", footer=""):
        self.header = header
        self.sidebar = sidebar
        self.main = main
        self.footer = footer

    def render(self):
        self.html.format(
            header=self.header,
            sidebar=self.sidebar,
            main=self.main,
            footer=self.footer
        )


class FeatureNavSidebar:
    html = readfile("sidebar.html")
    item = readfile("_item.html")

    def __init__(self, *, features):
        self.features = features

    @property
    def items(self):
        return ''.join([
            user_format(
                self.item,
                href=item.name,
                name=item.name,
            ) for item in self.features
        ])

    def render(self):
        return self.html.format(items=self.items)


class Index:
    html = readfile("index.html")

    def __init__(self, app: App):
        self.app = app

    def render(self):
        sidebar = FeatureNavSidebar(self.app.features)
        return Template(sidebar=sidebar)


class Detail:
    html = readfile("detail.html")

    def __init__(self, app: App, feature: Feature):
        self.app = app
        self.feature = feature

    def main(self):
        return user_format(self.html, feature=self.feature)

    def render(self):
        sidebar = FeatureNavSidebar(self.app.features)
        return Template(sidebar=sidebar, main=self.main)


class Edit:
    html = readfile("edit.html")

    def __init__(self, app: App, feature: Feature):
        self.app = app
        self.feature = feature

    def main(self):
        return user_format(self.html, feature=self.feature)
