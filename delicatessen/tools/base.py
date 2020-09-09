# Third-party
import numpy as np
from bokeh.models import ColumnDataSource, Div
from bokeh.plotting import figure


class BaseTool:
    def __init__(self, primary_plot):
        self.primary_plot = primary_plot

    def callback(self, attr, old, new):
        pass

    def layout(self):
        return Div()
