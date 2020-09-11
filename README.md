<p align="center">
  <img width = "500" src="./deli_logo_med_res.gif"/>
  <br/>
  Serving you all the finest TESS visualizations at
  <a href="https://online.tess.science">online.tess.science</a>.
</p>

## Installation

Developers:

```
pip install -e ".[develop]"
pre-commit install
```

This will install the repository in developer mode and enable pre-commit hooks
for automatic formatting using the [black](https://github.com/psf/black) python
formatter. Whenever you commit, `pre-commit` will automatically format your
code; note that if changes are made, you'll need to run the commit command
again.

Users:

```
pip install .
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
