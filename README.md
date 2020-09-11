<p align="center">
  <img width = "500" src="./deli_logo_med_res.gif"/>
</p>

Serving you all the finest TESS visualizations at
[online.tess.science](https://online.tess.science).

## Installation

Developers:

```
pip install -e ".[develop]"
pre-commit install
```

Users:

```
python setup.py install
```

## Usage

To start the default bokeh server with a test data set (included in the repo),
run the following from the command line:

```
deli
```

To start a bokeh server in "development mode" (which auto-detects modified files
so you don't have to keep stopping/starting the server), run:

```
deli --dev
```

You can also start a server with your own data file by passing in the full path
to the data file via the `--args` argument to `bokeh serve`. For example, to
visualize the data table stored in `here/is/my/data.fits`, run:

```
deli --args here/is/my/data.fits
```

Check out the [issues](https://github.com/adrn/delicatessen/issues)
if you are interested in contributing to this project!
