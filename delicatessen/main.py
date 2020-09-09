# Standard library
import pathlib
from collections import OrderedDict

# Third-party
import astropy.table as at
import numpy as np
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import (
    ColumnDataSource,
    Div,
    Select,
    MultiSelect,
    Slider,
)
from bokeh.plotting import figure
from bokeh.models.tools import (
    BoxSelectTool,
    BoxZoomTool,
    LassoSelectTool,
    PanTool,
    PolySelectTool,
    TapTool,
    WheelZoomTool,
    WheelPanTool,
    ZoomInTool,
    ZoomOutTool,
    HoverTool,
    CrosshairTool,
)
from bokeh.models import Range1d
from bokeh.palettes import Viridis256
from bokeh.transform import linear_cmap

PATH = pathlib.Path(__file__).parent.absolute()
DATA_PATH = PATH / "data" / "TESS-Gaia-mini.csv"

# Load an example dataset - can be any file format that astropy.table can read
data = at.Table.read(DATA_PATH)
dataset = data.to_pandas()

# Things the user can plot (label: parameter name)
parameters = OrderedDict((col, col) for col in sorted(dataset.columns))


class Selector:
    def __init__(
        self,
        name="Specials",
        kind="specials",
        css_classes=[],
        entries={},
        default="",
        title="",
        none_allowed=False,
    ):
        self.name = name
        self.entries = entries
        self.kind = kind
        self.css_classes = css_classes
        options = sorted(entries.keys())
        if none_allowed:
            options += ["None"]
        self.widget = Select(
            options=options,
            value=default,
            height=150,
            name="deli-selector",
            title=title,
            css_classes=["deli-selector"],
        )

    @property
    def value(self):
        return self.widget.value

    def layout(self, additional_widgets=[], width=None):
        title = Div(
            text="""<h2>{0}</h2><h3>Choose one</h3>""".format(self.name),
            css_classes=["controls"],
        )
        footer = Div(
            text="""<a href="#">About the {0}</a>""".format(self.kind),
            css_classes=["controls", "controls-footer"],
        )
        if width is None:
            width = 160 * (1 + len(additional_widgets))
        return column(
            title,
            row(
                self.widget,
                *additional_widgets,
                width=width,
                css_classes=["controls"]
            ),
            footer,
            css_classes=self.css_classes,
        )


class PrimaryPlot:
    def __init__(self, dataset):

        self.dataset = dataset

        # Set up the controls
        self.specials = Selector(
            name="Specials",
            kind="specials",
            css_classes=["specials"],
            entries={
                "Color-magnitude diagram": "cmd",
                "Period vs. radius": "pr",
                "Period vs. transit duration": "pdt",
            },
            default="Color-magnitude diagram",
        )
        self.data = Selector(
            name="Datasets",
            kind="datasets",
            css_classes=["data"],
            entries={"TOI Catalog": "toi", "Confirmed Planets": "confirmed"},
            default="Confirmed Planets",
        )
        self.xaxis = Selector(
            name="Build-Your-Own",
            kind="parameters",
            css_classes=["build-your-own"],
            entries=parameters,
            default="ra",
            title="X Axis",
        )
        self.yaxis = Selector(
            kind="parameters",
            css_classes=["build-your-own"],
            entries=parameters,
            default="dec",
            title="Y Axis",
        )
        self.size = Selector(
            name="Sides",
            kind="parameters",
            css_classes=["sides"],
            entries=parameters,
            default="dist",
            title="Marker Size",
            none_allowed=True,
        )
        self.color = Selector(
            kind="parameters",
            css_classes=["sides"],
            entries=parameters,
            default="dist",
            title="Marker Color",
            none_allowed=True,
        )

        # Set up the plot
        self.source = ColumnDataSource(
            data=dict(x=[], y=[], size=[], color=[])
        )
        self.plot = figure(
            plot_height=600,
            plot_width=700,
            title="",
            tooltips=[("TIC ID", "@ticid")],
            sizing_mode="scale_both",
        )
        self.plot.circle(
            x="x",
            y="y",
            source=self.source,
            size="size",
            color=linear_cmap(
                field_name="color", palette=Viridis256, low=0, high=1
            ),
            line_color=None,
        )
        self.plot.add_tools(
            BoxSelectTool(),
            BoxZoomTool(),
            LassoSelectTool(),
            PanTool(),
            PolySelectTool(),
            TapTool(),
            WheelZoomTool(),
            WheelPanTool(),
            ZoomInTool(),
            ZoomOutTool(),
            HoverTool(),
            CrosshairTool(),
        )

        # Register the callback
        for control in [
            self.specials,
            self.data,
            self.xaxis,
            self.yaxis,
            self.size,
            self.color,
        ]:
            control.widget.on_change("value", self.callback)

    def callback(self, attr, old, new):
        """
        Triggered when the user changes what we're plotting on the main plot.

        """
        # Update the axis labels
        x_name = self.xaxis.entries[self.xaxis.value]
        y_name = self.yaxis.entries[self.yaxis.value]
        self.plot.xaxis.axis_label = self.xaxis.value
        self.plot.yaxis.axis_label = self.yaxis.value

        # Update the "sides"
        if self.size.value != "None":
            s_name = self.size.entries[self.size.value]
            size = self.dataset[s_name] / np.min(self.dataset[s_name])
        else:
            size = np.ones_like(self.dataset["ticid"]) * 5
        if self.color.value != "None":
            c_name = self.color.entries[self.color.value]
            color = (self.dataset[c_name] - np.min(self.dataset[c_name])) / (
                np.max(self.dataset[c_name]) - np.min(self.dataset[c_name])
            )
        else:
            color = np.zeros_like(self.dataset["ticid"])

        # Update the data source
        self.source.data = dict(
            x=self.dataset[x_name],
            y=self.dataset[y_name],
            size=size,
            ticid=self.dataset["ticid"],
            color=color,
        )


class SecondaryPlot:
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


# Instantiate the plots
primary = PrimaryPlot(dataset)
secondary = SecondaryPlot(primary)


# Display things on the page
spacer = Div()
or_spacer = Div(css_classes=["or-spacer"])
inputs_left = column(
    primary.data.layout(), spacer, primary.specials.layout(), width=160
)
inputs_right = column(
    primary.xaxis.layout([primary.yaxis.widget]),
    spacer,
    primary.size.layout([primary.color.widget]),
)
header = Div(
    text="""
<img src="https://raw.githubusercontent.com/adrn/delicatessen/master/deli_logo_med_res.gif"></img>
""",
    css_classes=["header-image"],
    width=320,
    height=100,
)
inputs = column(header, row(inputs_left, or_spacer, inputs_right))
layout = column(row(inputs, spacer, primary.plot), secondary.plot,)

# Load and display the data
primary.callback(None, None, None)

# Go!
curdoc().add_root(layout)
curdoc().title = "delicatessen"
