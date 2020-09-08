"""
To run this:

    bokeh serve --show app.py

"""
import numpy as np
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, Div, Select, Slider, TextInput
from bokeh.plotting import figure
from bokeh.models.tools import TapTool

# Load an example dataset
data = np.loadtxt("TESS-Gaia-mini.csv", delimiter=",", skiprows=1)
ra, dec, par, sid, _, _, ticid, tmag, dist = data.T
data = dict(ra=ra, dec=dec, dist=dist, ticid=ticid)

# Things the user can plot (label: parameter name)
axis_map = {"Right Ascension": "ra", "Declination": "dec", "Distance": "dist"}

# Input controls
x_axis = Select(
    title="X Axis", options=sorted(axis_map.keys()), value="Right Ascension"
)
y_axis = Select(
    title="Y Axis", options=sorted(axis_map.keys()), value="Declination"
)
s_axis = Select(
    title="Marker Size", options=sorted(axis_map.keys()), value="Distance"
)
controls = [s_axis, x_axis, y_axis]

# Primary plot
source1 = ColumnDataSource(data=dict(x=[], y=[], size=[]))
plot1 = figure(
    plot_height=600,
    plot_width=700,
    title="",
    tooltips=[("TIC ID", "@ticid")],
    tools="tap",
    sizing_mode="scale_both",
)
plot1.circle(
    x="x", y="y", source=source1, size="size", line_color=None,
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
    # Get the parameters to plot (x axis, y axis, and marker size)
    x_name = axis_map[x_axis.value]
    y_name = axis_map[y_axis.value]
    s_name = axis_map[s_axis.value]

    # Update the labels
    plot1.xaxis.axis_label = x_axis.value
    plot1.yaxis.axis_label = y_axis.value

    # Update the data source
    source1.data = dict(
        x=data[x_name],
        y=data[y_name],
        size=data[s_name] / np.min(data[s_name]),
        ticid=data["ticid"],
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
inputs = column(*controls, width=320)
inputs.sizing_mode = "fixed"
l = column(row(inputs, plot1), plot2)

# Load and display the data
callback1(None, None, None)

# Go!
curdoc().add_root(l)
curdoc().title = "delicatessen"
