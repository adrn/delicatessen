# delicatessen

<p align="center">
  <img width = "500" src="./deli_logo_med_res.gif"/>
</p>

Serving you all the finest visualizations at online.tess.science

To start the default bokeh server with a test data set (included in the repo):
```
bokeh serve --show delicatessen
```

To start a bokeh server in "development mode" (which auto-detects modified files
so you don't have to keep stopping/starting the server), use:
```
bokeh serve --show delicatessen --dev
```

You can also start a server with your own data file by passing in the full path
to the data file via the `--args` argument to `bokeh serve`. For example, to
visualize the data table stored in `here/is/my/data.fits`:
```
bokeh serve delicatessen --args here/is/my/data.fits
```

Check out the [Projects](https://github.com/adrn/delicatessen/projects/1) page
if you are interested in contributing!
