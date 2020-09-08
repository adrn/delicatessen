import numpy as np
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import (
    ColumnDataSource,
    Div,
    Select,
    MultiSelect,
    Slider,
    TextInput,
)
from bokeh.plotting import figure
from bokeh.models.tools import TapTool
from bokeh.models.callbacks import CustomJS
from bokeh.palettes import Viridis256
from bokeh.transform import linear_cmap
import os

PATH = os.path.abspath(os.path.dirname(__file__))

# Load an example dataset
data = np.loadtxt(
    os.path.join(PATH, "data", "TESS-Gaia-mini.csv"), delimiter=",", skiprows=1
)
ra, dec, par, sid, _, _, ticid, tmag, dist = data.T
data = dict(ra=ra, dec=dec, dist=dist, ticid=ticid)

# Things the user can plot (label: parameter name)
axis_map = {"Right Ascension": "ra", "Declination": "dec", "Distance": "dist"}

# Input controls
x_axis = Select(
    title="X Axis",
    options=sorted(axis_map.keys()),
    value="Right Ascension",
    height=150,
    name="deli-selector",
    css_classes=["deli-selector"],
)
y_axis = Select(
    title="Y Axis",
    options=sorted(axis_map.keys()),
    value="Declination",
    height=150,
    name="deli-selector",
    css_classes=["deli-selector"],
)
s_axis = Select(
    title="Marker Size",
    options=sorted(axis_map.keys()) + ["None"],
    value="Distance",
    height=150,
    name="deli-selector",
    css_classes=["deli-selector"],
)
c_axis = Select(
    title="Marker Color",
    options=sorted(axis_map.keys()) + ["None"],
    value="Distance",
    height=150,
    name="deli-selector",
    css_classes=["deli-selector"],
)
controls = [s_axis, c_axis, x_axis, y_axis]

# Primary plot
source1 = ColumnDataSource(data=dict(x=[], y=[], size=[], color=[]))
plot1 = figure(
    plot_height=600,
    plot_width=700,
    title="",
    tooltips=[("TIC ID", "@ticid")],
    tools="tap",
    sizing_mode="scale_both",
)
plot1.circle(
    x="x",
    y="y",
    source=source1,
    size="size",
    color=linear_cmap(field_name="color", palette=Viridis256, low=0, high=1),
    line_color=None,
)
taptool = plot1.select(type=TapTool)

# Secondary plot
source2 = ColumnDataSource(data=dict(x=[], y=[]))
plot2 = figure(
    plot_height=300, plot_width=700, title="", sizing_mode="scale_both",
)
plot2.circle(
    x="x", y="y", source=source2, line_color=None, color="black", alpha=0.1
)

# Events
def callback1(attr, old, new):
    """
    Triggered when the user changes what we're plotting on the main plot.

    """
    # Update the axis labels
    x_name = axis_map[x_axis.value]
    y_name = axis_map[y_axis.value]
    plot1.xaxis.axis_label = x_axis.value
    plot1.yaxis.axis_label = y_axis.value

    # Update the "extras"
    if s_axis.value != "None":
        s_name = axis_map[s_axis.value]
        size = data[s_name] / np.min(data[s_name])
    else:
        size = np.ones_like(data["ticid"]) * 5
    if c_axis.value != "None":
        c_name = axis_map[c_axis.value]
        color = (data[c_name] - np.min(data[c_name])) / (
            np.max(data[c_name]) - np.min(data[c_name])
        )
    else:
        color = np.zeros_like(data["ticid"])

    # Update the data source
    source1.data = dict(
        x=data[x_name],
        y=data[y_name],
        size=size,
        ticid=data["ticid"],
        color=color,
    )


def callback2(attr, old, new):
    """
    Triggered when the user selects a point on the main plot.

    """
    # Get the TIC ID
    ticid = source1.data["ticid"][source1.selected.indices[0]]
    print("Fetching data for TIC ID {0}".format(ticid))

    # TODO: Actually fetch the data from MAST.
    # For now just populate with random numbers
    source2.data = dict(x=np.arange(10000), y=np.random.randn(10000))


# Register the callbacks
source1.selected.on_change("indices", callback2)
for control in controls:
    control.on_change("value", callback1)

# Display things on the page

spacer = Div()

build_your_own_title = Div(
    text="""
<h2>Build-Your-Own</h2>
<h3>Choose one per axis</h3>
"""
)
extras_title = Div(
    text="""
<h2>Extras</h2>
<h3>Choose one per axis</h3>
"""
)

inputs = column(
    column(
        build_your_own_title,
        row(x_axis, y_axis, width=320, css_classes=["build-your-own"]),
    ),
    spacer,
    column(
        extras_title, row(s_axis, c_axis, width=320, css_classes=["extras"]),
    ),
    width=320,
)
inputs.sizing_mode = "fixed"
l = column(row(inputs, spacer, plot1), plot2)

# Load and display the data
callback1(None, None, None)

# Go!
curdoc().add_root(l)
curdoc().title = "delicatessen"
