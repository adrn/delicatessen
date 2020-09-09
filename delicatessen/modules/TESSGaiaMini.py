# delicatessen
from .base import BasePlot

# Third-party
import numpy as np
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure


class Plot(BasePlot):
    def __init__(self, primary_plot):
        self.primary_plot = primary_plot
        self.source = ColumnDataSource(data=dict(x=[], y=[]))
        self.plot = figure(
            plot_height=300, plot_width=700, title="", sizing_mode="scale_both"
        )
        self.plot.circle(
            x="x",
            y="y",
            source=self.source,
            line_color=None,
            color="black",
            alpha=0.1,
        )

        # Register the callback
        self.primary_plot.source.selected.on_change("indices", self.callback)

    def callback(self, attr, old, new):
        """
        Triggered when the user selects a point on the main plot.

        """
        # If a point is selected...
        if len(self.primary_plot.source.selected.indices):

            # Get the TIC ID
            ticid = self.primary_plot.source.data["ticid"][
                self.primary_plot.source.selected.indices[0]
            ]
            print("Fetching data for TIC ID {0}".format(ticid))

            # TODO: Actually fetch the data from MAST.
            # For now just populate with random numbers
            self.source.data = dict(
                x=np.linspace(0, 1, 10000), y=np.random.randn(10000)
            )

        else:

            # Clear the plot
            self.source.data = dict(x=[], y=[])

    def layout(self):
        return self.plot
