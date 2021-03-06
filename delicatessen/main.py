# delicatessen
from . import tools

# Standard library
import pathlib
import sys
from collections import OrderedDict

# Third-party
import astropy.table as at
import numpy as np
import pandas as pd
import requests
from io import BytesIO
from bokeh.io import curdoc
from bokeh.layouts import column, row, Spacer
from bokeh.models import (
    ColumnDataSource,
    AjaxDataSource,
    Div,
    Select,
    MultiSelect,
    Slider,
    CheckboxGroup,
    Panel,
    Tabs,
    CustomJS,
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
    ResetTool,
)
from bokeh.models import Range1d
from bokeh.palettes import Viridis256
from bokeh.transform import linear_cmap
from bokeh.server.server import Server


DELI_PATH = pathlib.Path(__file__).parent.absolute()
LOGO_URL = "delicatessen/static/images/logo.gif"


class Selector:
    def __init__(
        self,
        name="Specials",
        descr="Choose one",
        kind="specials",
        css_classes=[],
        entries={},
        default="",
        title=None,
        none_allowed=False,
    ):
        self.name = name
        self.descr = descr
        self.entries = entries
        self.kind = kind
        self.css_classes = css_classes
        options = sorted(entries.keys())
        if none_allowed:
            options = ["None"] + options
        if title is None:
            title = "."
            css_classes = ["deli-selector", "hide-title"]
        else:
            css_classes = ["deli-selector"]
        self.widget = MultiSelect(
            options=options,
            value=[default],
            # height=150,
            size=8,
            name="deli-selector",
            title=title,
            css_classes=css_classes,
        )

        # HACK: force MultiSelect to only have 1 value selected
        def multi_select_hack(attr, old, new):
            if len(new) > 1:
                self.widget.value = old

        self.widget.on_change("value", multi_select_hack)

    @property
    def value(self):
        # HACK: This is because we are useing MultiSelect instead of Select
        return self.widget.value[0]

    def layout(self, additional_widgets=[], width=None):
        title = Div(
            text="""<h2>{0}</h2><h3>{1}</h3>""".format(self.name, self.descr),
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
                css_classes=["controls"],
            ),
            footer,
            css_classes=self.css_classes,
        )


class Plot:
    def __init__(self, parent, dataset, parameters):

        self.parent = parent
        self.dataset = dataset

        # Set up the controls
        self.tools = Selector(
            name="Beverages",
            descr="Choose a plotting tool",
            kind="tools",
            css_classes=["tools"],
            entries={"Deli-LATTE": tools.DeliLATTE},
            default="None",
            none_allowed=True,
        )
        self.data = Selector(
            name="Main Dishes",
            descr="Choose a dataset",
            kind="datasets",
            css_classes=["data"],
            entries={
                "Test data": "test",
                # "TOI Catalog": "toi",
                # "Confirmed Planets": "confirmed",
            },
            default="Test data",
        )
        self.xaxis = Selector(
            name="Build-Your-Own",
            descr="Choose the parameters to plot",
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
            default="dist",
            title="Y Axis",
        )
        self.size = Selector(
            name="Sides",
            descr="Choose additional parameters to plot",
            kind="parameters",
            css_classes=["sides"],
            entries=parameters,
            default="None",
            title="Marker Size",
            none_allowed=True,
        )
        self.color = Selector(
            kind="parameters",
            css_classes=["sides"],
            entries=parameters,
            default="None",
            title="Marker Color",
            none_allowed=True,
        )
        self.checkbox_labels = [
            "Flip x-axis",
            "Flip y-axis ",
            "Log scale x-axis",
            "Log scale y-axis",
        ]
        self.specials = Selector(
            name="Specials",
            descr="Choose a special",
            kind="specials",
            css_classes=["specials"],
            entries={},
            default="None",
            none_allowed=True,
        )

        self.checkbox_group = CheckboxGroup(
            labels=self.checkbox_labels, active=[]
        )

        self.source = ColumnDataSource(
            data=dict(x=[], y=[], size=[], color=[])
        )

        # Register the callbacks
        for control in [self.xaxis, self.yaxis, self.size, self.color]:
            control.widget.on_change("value", self.param_callback)
        self.tools.widget.on_change("value", self.tool_callback)
        self.data.widget.on_change("value", self.data_callback)
        self.checkbox_group.on_click(self.checkbox_callback)

        # Setup the plot
        self.setup_plot()

        # Load and display the data
        self.param_callback(None, None, None)

    def setup_plot(
        self,
        x_axis_type="linear",
        y_axis_type="linear",
        x_flip=False,
        y_flip=False,
    ):
        # Set up the plot
        self.plot = figure(
            plot_height=620,
            min_width=600,
            title="",
            x_axis_type=x_axis_type,
            y_axis_type=y_axis_type,
            tools="",
            sizing_mode="stretch_both",
        )

        # Enable Bokeh tools
        self.plot.add_tools(PanTool(), TapTool(), ResetTool())

        # Axes orientation and labels
        self.plot.x_range.flipped = x_flip
        self.plot.y_range.flipped = y_flip
        self.plot.xaxis.axis_label = self.xaxis.value
        self.plot.yaxis.axis_label = self.yaxis.value

        # Plot the data
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

        # -- HACKZ --

        # Update the plot element in the HTML layout
        if hasattr(self.parent, "layout"):
            self.parent.layout.children[0].children[-1] = self.plot

        # Make the cursor a grabber when panning
        code_pan_start = """
            Bokeh.grabbing = true
            var elm = document.getElementsByClassName('bk-canvas-events')[0]
            elm.style.cursor = 'grabbing'
        """
        code_pan_end = """
            if(Bokeh.grabbing) {
                Bokeh.grabbing = false
                var elm = document.getElementsByClassName('bk-canvas-events')[0]
                elm.style.cursor = 'grab'
            }
        """
        self.plot.js_on_event("panstart", CustomJS(code=code_pan_start))
        self.plot.js_on_event("panend", CustomJS(code=code_pan_end))

        # Add a hover tool w/ a pointer cursor
        code_hover = """
        if((Bokeh.grabbing == 'undefined') || !Bokeh.grabbing) {
            var elm = document.getElementsByClassName('bk-canvas-events')[0]
            if (cb_data.index.indices.length > 0) {
                elm.style.cursor = 'pointer'
                Bokeh.pointing = true
            } else {
                if((Bokeh.pointing == 'undefined') || !Bokeh.pointing)
                    elm.style.cursor = 'grab'
                else
                    Bokeh.pointing = false
            }
        }
        """
        self.plot.add_tools(
            HoverTool(
                callback=CustomJS(code=code_hover),
                tooltips=[("TIC ID", "@ticid")],
            )
        )

    def tool_callback(self, attr, old, new):
        if self.tools.value != "None":
            self.parent.change_tool(self.tools.entries[self.tools.value])
        else:
            self.parent.change_tool(tools.BaseTool)

    def data_callback(self, attr, old, new):
        # TODO: Change datasets!
        pass

    def param_callback(self, attr, old, new):
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
            size = (
                25
                * (self.dataset[s_name] - np.min(self.dataset[s_name]))
                / (np.max(self.dataset[s_name]) - np.min(self.dataset[s_name]))
            )
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

    def checkbox_callback(self, new):
        """
        Triggered when the user interacts with check boxes in appearance panel.

        """
        if 0 in self.checkbox_group.active:
            x_flip = True
        else:
            x_flip = False
        if 1 in self.checkbox_group.active:
            y_flip = True
        else:
            y_flip = False
        if 2 in self.checkbox_group.active:
            x_axis_type = "log"
        else:
            x_axis_type = "linear"
        if 3 in self.checkbox_group.active:
            y_axis_type = "log"
        else:
            y_axis_type = "linear"

        # Axis labels are disappearing on selection of checkboxes
        self.setup_plot(
            x_axis_type=x_axis_type,
            y_axis_type=y_axis_type,
            x_flip=x_flip,
            y_flip=y_flip,
        )

    def layout(self):
        panels = [None, None, None]

        # Main panel: data
        panels[0] = Panel(
            child=row(
                row(
                    column(
                        self.data.layout(),
                        Spacer(height=10),
                        self.tools.layout(),
                        width=160,
                    ),
                    Spacer(width=10),
                    column(
                        self.xaxis.layout([self.yaxis.widget]),
                        Spacer(height=10),
                        self.size.layout([self.color.widget]),
                    ),
                    css_classes=["panel-inner"],
                ),
                css_classes=["panel-outer"],
            ),
            title="Main Menu",
        )

        # Secondary panel: prix fixe
        panels[1] = Panel(
            child=row(
                row(self.specials.layout(), css_classes=["panel-inner"]),
                css_classes=["panel-outer"],
            ),
            title="Prix Fixe",
        )

        # Tertiary panel: appearance
        checkbox_panel = row(
            row(
                column(
                    Div(
                        text="""<h2>Toppings</h2><h3>Choose axes transforms</h3>""",
                        css_classes=["controls"],
                    ),
                    row(
                        self.checkbox_group,
                        width=160,
                        css_classes=["controls"],
                    ),
                    css_classes=["axes-checkboxes"],
                ),
                css_classes=["panel-inner"],
            ),
            css_classes=["panel-outer"],
        )
        panels[2] = Panel(child=checkbox_panel, title="Garnishes")

        # All tabs
        tabs = Tabs(tabs=panels, css_classes=["tabs"])

        # Logo
        header = Div(
            text=f"""<img src="{LOGO_URL}"></img>""",
            css_classes=["header-image"],
            width=320,
            height=100,
        )

        return row(column(header, tabs), Spacer(width=30), self.plot)


class Delicatessen:
    def __init__(self, doc, data_file=None):

        # Current HTML document
        self.doc = doc

        # This is to have a default / test data file to show. But we probably
        # want to change this, or remove the default when we "release"!
        if data_file is None:
            data_file = DELI_PATH / "data" / "TESS-Gaia-mini.csv"

        # The data file can be any file format that astropy.table can read:
        data = at.Table.read(data_file)
        dataset = data.to_pandas()

        # Things the user can plot - now the labels are the same as the table
        # column names! We may want to make these nicer for things like "ra"?
        parameters = OrderedDict((col, col) for col in sorted(dataset.columns))

        self.dataset = dataset

        # Instantiate the plot
        self.primary = Plot(self, dataset, parameters)
        self.layout = column(
            self.primary.layout(), Div(), sizing_mode="stretch_width"
        )

        # Set up the tool (none by default)
        self.change_tool(tools.BaseTool)

        # Go!
        self.doc.add_root(self.layout)
        self.doc.title = "delicatessen"

    def change_tool(self, tool):
        self.secondary = tool(self)
        self.layout.children.pop()
        self.layout.children.append(self.secondary.layout())


data_file = None
if len(sys.argv) > 1:
    data_file = sys.argv[1]

Delicatessen(curdoc(), data_file=data_file)
