import .template
import .header
from .sidebar import Sidebar
import os

with open(os.path.join(os.path.dirname(__file__), 'index.html')) as file:
    _html = file.read()


class Index(Template):

    def header(self):
        pass

    def sidebar(self):
        return Sidebar(active_feature=None)

    def main(self):
        pass

    def footer(self):
        return ""
