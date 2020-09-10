# delicatessen
from .base import BaseTool

# Third-party
import numpy as np
from bokeh.models import ColumnDataSource, Panel, Tabs
from bokeh.plotting import figure

import sys
import json
import requests
import lightkurve as lk
from urllib.parse import quote as urlencode
from tess_stars2px import tess_stars2px_function_entry

import http.client as httplib
import astropy.io.fits as pf
from bokeh.layouts import column, row, Spacer
# --- functions needed to download the TESS data


def mastQuery(request, proxy_uri=None):

    host = "mast.stsci.edu"
    # Grab Python Version
    version = ".".join(map(str, sys.version_info[:3]))

    # Create Http Header Variables
    headers = {
        "Content-type": "application/x-www-form-urlencoded",
        "Accept": "text/plain",
        "User-agent": "python-requests/" + version,
    }

    # Encoding the request as a json string
    requestString = json.dumps(request)
    requestString = urlencode(requestString)

    # opening the https connection
    if None == proxy_uri:
        conn = httplib.HTTPSConnection(host)
    else:
        port = 443
        url = urlparse(proxy_uri)
        conn = httplib.HTTPSConnection(url.hostname, url.port)

        if url.username and url.password:
            auth = "%s:%s" % (url.username, url.password)
            headers["Proxy-Authorization"] = "Basic " + str(
                base64.b64encode(auth.encode())
            ).replace("b'", "").replace("'", "")
        conn.set_tunnel(host, port, headers)

    # Making the query
    conn.request("POST", "/api/v0/invoke", "request=" + requestString, headers)

    # Getting the response
    resp = conn.getresponse()
    head = resp.getheaders()
    content = resp.read().decode("utf-8")

    # Close the https connection
    conn.close()

    return head, content


def download_data(tic, binfac=5, test="no"):

    """
    Download the LCs for the chosen target star.
    
    Parameters
    ----------
    indir   :   str
        path to where the data will be saved (defaul = "./LATTE_output")
    tic : str
        TIC (Tess Input Catalog) ID of the target
    binfac  :  int
        The factor by which the data should be binned. 
        Default = 5 (which is what is shown on PHT)
    
    test   :   str
        in order to test the function with unittests we want to run it 
        with an input file (string to input file)

    Returns
    -------
    alltime  :  list
        times (not binned)
    allflux  :  list
        normalized flux (not binned)
    allflux_err  :  list
        normalized flux errors (not binned)
    all_md  :  list
        times of the momentum dumps
    alltimebinned  :  list
        binned time
    allfluxbinned  :  list
        normalized binned flux
    allx1  :  list
        CCD column position of target’s flux-weighted centroid. In x direction
    allx2  :  list
        The CCD column local motion differential velocity aberration 
        (DVA), pointing drift, and thermal effects. In x direction
    ally1  :  list
        CCD column position of target’s flux-weighted centroid. In y direction
    ally2  :  list
        The CCD column local motion differential velocity aberration 
        (DVA), pointing drift, and thermal effects. In y direction
    alltimel2  :  list
        time used for the x and y centroid position plottin
    allfbkg  :  list
        background flux
    start_sec  :  list
        times of the start of the sector
    end_sec  :  list
        times of the end of the sector
    in_sec  :  list
        the sectors for which data was downloaded
    tessmag  :  float
        TESS magnitude of the target star
    teff  :  float
        effective temperature of the tagret star (K)
    srad  :  float
        radius of the target star (solar radii)

    """

    # -------------------
    # find the sectors in which the target is osberved using TESS POINT

    starTics = np.array(["{}".format(tic)], dtype=np.int64)
    ticStringList = ["{0:d}".format(x) for x in starTics]

    # Setup mast query
    request = {
        "service": "Mast.Catalogs.Filtered.Tic",
        "params": {
            "columns": "*",
            "filters": [{"paramName": "ID", "values": ticStringList}],
        },
        "format": "json",
        "removenullcolumns": True,
    }

    headers, outString = mastQuery(request)

    outObject = json.loads(outString)
    starRa = np.array([x["ra"] for x in outObject["data"]])[0]
    starDec = np.array([x["dec"] for x in outObject["data"]])[0]

    (
        outID,
        outEclipLong,
        outEclipLat,
        outSec,
        outCam,
        outCcd,
        outColPix,
        outRowPix,
        scinfo,
    ) = tess_stars2px_function_entry(tic, starRa, starDec)

    # -------------------

    def rebin(arr, new_shape):
        shape = (
            new_shape[0],
            arr.shape[0] // new_shape[0],
            new_shape[1],
            arr.shape[1] // new_shape[1],
        )
        return arr.reshape(shape).mean(-1).mean(1)

    sector_codes = {
        "1": ["2018206045859", "0120"],
        "2": ["2018234235059", "0121"],
        "3": ["2018263035959", "0123"],
        "4": ["2018292075959", "0124"],
        "5": ["2018319095959", "0125"],
        "6": ["2018349182459", "0126"],
        "7": ["2019006130736", "0131"],
        "8": ["2019032160000", "0136"],
        "9": ["2019058134432", "0139"],
        "10": ["2019085135100", "0140"],
        "11": ["2019112060037", "0143"],
        "12": ["2019140104343", "0144"],
        "13": ["2019169103026", "0146"],
        "14": ["2019198215352", "0150"],
        "15": ["2019226182529", "0151"],
        "16": ["2019253231442", "0152"],
        "17": ["2019279210107", "0161"],
        "18": ["2019306063752", "0162"],
        "19": ["2019331140908", "0164"],
        "20": ["2019357164649", "0165"],
        "21": ["2020020091053", "0167"],
        "22": ["2020049080258", "0174"],
        "23": ["2020078014623", "0177"],
        "24": ["2020106103520", "0180"],
        "25": ["2020133194932", "0182"],
        "26": ["2020160202036", "0188"],
    }

    last_sector = sorted(np.array(list(sector_codes), dtype=int))[-1]

    # only look at the sectors that have alreadt been observed:

    sectors = outSec[outSec <= last_sector]

    dwload_link = []  # list of the download lins=ks

    for sector in sectors:

        sector = str(sector)

        download_url = (
            "https://mast.stsci.edu/api/v0.1/Download/file/?uri=mast:TESS/product/tess"
            + sector_codes[sector][0].rjust(13, "0")
            + "-s"
            + sector.rjust(4, "0")
            + "-"
            + str(tic).rjust(16, "0")
            + "-"
            + sector_codes[sector][1]
            + "-s_lc.fits"
        )

        dwload_link.append(download_url)

    # define all the empty lists to append to in order to return
    # the data that will be requrides later on in the script

    alltimebinned = []
    allfluxbinned = []

    allx1 = []
    allx2 = []
    ally1 = []
    ally2 = []
    alltimel2 = []
    allfbkg = []

    start_sec = []
    end_sec = []
    in_sec = []

    alltime = []
    allflux = []
    allflux_err = []
    all_md = []

    # loop through all the download links - all the data that we want to access
    for lcfile in dwload_link:

        # !-!-!-!-!-!-!-
        # if this a test run, download the file already on the system
        if test != "no":
            lchdu = pf.open(lcfile)
        # !-!-!-!-!-!-!-

        else:
            try:
                # use the downlload link to download the file from the server
                # - need an internet connection for this to work
                response = requests.get(lcfile)

                # open the file using the response url
                lchdu = pf.open(
                    response.url
                )  # this needs to be a URL - not a file
            except:
                continue

        # open and view columns in lightcurve extension
        lcdata = lchdu[1].data
        lchdu[1].columns

        f02 = lcdata["PDCSAP_FLUX"]  # Presearch Data Conditioning
        f02_err = lcdata["PDCSAP_FLUX_ERR"]
        quality = lcdata[
            "QUALITY"
        ]  # quality flags as determined by the SPOC pipeline
        time = lcdata["TIME"]
        f0 = lcdata["SAP_FLUX"]  #
        fbkg = lcdata["SAP_BKG"]  # background flux

        med = np.nanmedian(
            f02
        )  # determine the median flux (ignore nan values)
        f1 = f02 / med  # normalize by dividing byt the median flux
        f1_err = f02_err / med  # normalise the errors on the flux

        x1 = lcdata[
            "MOM_CENTR1"
        ]  # CCD column position of target’s flux-weighted centroid
        x1 -= np.nanmedian(x1)
        y1 = lcdata["MOM_CENTR2"]
        y1 -= np.nanmedian(y1)
        x2 = lcdata["POS_CORR1"]  # The CCD column local motion differential
        # velocity aberration (DVA), pointing drift, and thermal effects.
        x2 -= np.nanmedian(x2)
        y2 = lcdata["POS_CORR2"]
        y2 -= np.nanmedian(y2)
        l = quality > 0  # good quality data
        l2 = quality <= 0  # bad quality data

        sec = int(lchdu[0].header["SECTOR"])  # the TESS observational sector

        tessmag = lchdu[0].header["TESSMAG"]  # magnitude in the FITS header
        teff = lchdu[0].header[
            "TEFF"
        ]  # effective temperature in the FITS header (kelvin)
        srad = lchdu[0].header[
            "RADIUS"
        ]  # stellar radius in the FITS header (solar radii)

        flux = lcdata["SAP_FLUX"]

        lchdu.close()

        # store the sector we are looking at
        in_sec.append(sec)

        # binned data
        N = len(time)
        n = int(np.floor(N / binfac) * binfac)
        X = np.zeros((2, n))
        X[0, :] = time[:n]
        X[1, :] = f1[:n]
        Xb = rebin(X, (2, int(n / binfac)))

        time_binned = Xb[0]
        flux_binned = Xb[1]

        # the time of the momentum dumps are indicated by the quality flag
        mom_dump = np.bitwise_and(quality, 2 ** 5) >= 1

        # store the relevant information in the given list
        alltime.append(list(time))
        allflux.append(list(f1))
        allflux_err.append(list(f1_err))
        all_md.append(list(time[mom_dump]))

        alltimebinned.append(list(time_binned))
        allfluxbinned.append(list(flux_binned))

        allx1.append(list(x1[l2]))
        allx2.append(list(x2[l2]))
        ally1.append(list(y1[l2]))
        ally2.append(list(y2[l2]))
        alltimel2.append(list(time[l2]))

        allfbkg.append(fbkg)

        start_sec.append([time[0]])
        end_sec.append([time[-1]])

    alltime = np.hstack(alltime)
    allflux = np.hstack(allflux)
    allflux_err = np.hstack(allflux_err)
    all_md = np.hstack(all_md)
    alltimebinned = np.hstack(alltimebinned)
    allfluxbinned = np.hstack(allfluxbinned)
    allx1 = np.hstack(allx1)
    allx2 = np.hstack(allx2)
    ally1 = np.hstack(ally1)
    ally2 = np.hstack(ally2)
    alltimel2 = np.hstack(alltimel2)
    allfbkg = np.hstack(allfbkg)

    return (
        alltime,
        allflux,
        allflux_err,
        all_md,
        alltimebinned,
        allfluxbinned,
        allx1,
        allx2,
        ally1,
        ally2,
        alltimel2,
        allfbkg,
        start_sec,
        end_sec,
        in_sec,
        tessmag,
        teff,
        srad,
    )


# - - - - - - - - - - - - - - - - - - - - - - - - -

class DeliLATTE(BaseTool):
    def __init__(self, parent):
        self.parent = parent
        self.source = ColumnDataSource(data=dict(x=[], y=[]))
        self.source_binned = ColumnDataSource(
            data=dict(x_binned=[], y_binned=[])
        )

        self.plot = figure(
            plot_height=300, plot_width=1200, title="", sizing_mode="scale_both"
        )

        self.plot.circle(
            x="x",
            y="y",
            source=self.source,
            line_color=None,
            color="darkorange",
            alpha=0.8,
            size =3)

        self.plot.circle(
            x="x_binned",
            y="y_binned",
            source=self.source_binned,
            line_color=None,
            color="black",
            alpha=0.5,
            size =3)

        # axis labels
        self.plot.xaxis.axis_label = "Time (BJD - 2457000)"
        self.plot.yaxis.axis_label = "Normalised Flux"


        # - - - Backgrounds - - - -
        # - - - - - - - - - - - - -

        self.source_bkg = ColumnDataSource(
            data=dict(x_bkg=[], y_bkg=[]))

        # add an extra figure to plot an additional parameter - such as the background or the centroid shifts. 
        self.plot_bkg = figure(
            plot_height=400, plot_width=1200, title="", sizing_mode="scale_both", x_range=self.plot.x_range
        )

        self.plot_bkg.circle(
            x="x_bkg",
            y="y_bkg",
            source=self.source_bkg,
            line_color=None,
            color="blue",
            alpha=0.5,
            size =3)

        self.plot_bkg.xaxis.axis_label = "Time (BJD - 2457000)"
        self.plot_bkg.yaxis.axis_label = "Background Flux"


        # - - - Centroic Plot - - - 
        # - - - - - - - - - - - - - 

        self.source_xcen1 = ColumnDataSource(
            data=dict(x_xcen1=[], y_xcen1=[]))

        self.source_xcen2 = ColumnDataSource(
            data=dict(x_xcen2=[], y_xcen2=[]))

        self.source_ycen1 = ColumnDataSource(
            data=dict(x_ycen1=[], y_ycen1=[]))

        self.source_ycen2 = ColumnDataSource(
            data=dict(x_ycen2=[], y_ycen2=[]))

        self.plot_xcen = figure(
            plot_height=200, plot_width=1200, title="", sizing_mode="scale_both", x_range=self.plot.x_range)
        
        self.plot_ycen = figure(
            plot_height=200, plot_width=1200, title="", sizing_mode="scale_both", x_range=self.plot.x_range)


        self.plot_xcen.circle(
            x="x_xcen1",
            y="y_xcen1",
            source=self.source_xcen1,
            line_color=None,
            color="red",
            alpha=0.4,
            size = 2)

        self.plot_xcen.circle(
            x="x_xcen2",
            y="y_xcen2",
            source=self.source_xcen2,
            line_color=None,
            color="black",
            alpha=0.3,
            size =2)

        self.plot_ycen.circle(
            x="x_ycen1",
            y="y_ycen1",
            source=self.source_ycen1,
            line_color=None,
            color="red",
            alpha=0.4,
            size =2)

        self.plot_ycen.circle(
            x="x_ycen2",
            y="y_ycen2",
            source=self.source_ycen2,
            line_color=None,
            color="black",
            alpha=0.3,
            size =2)


        #self.plot_xcen.xaxis.axis_label = "Time (BJD - 2457000)"
        self.plot_xcen.yaxis.axis_label = "x-centroid"
        self.plot_ycen.xaxis.axis_label = "Time (BJD - 2457000)"
        self.plot_ycen.yaxis.axis_label = "y-centroid"


        # - - - Periodogram - - - 
        # - - - - - - - - - - - - - 

        self.source_periodgrm = ColumnDataSource(
            data=dict(x_periodgrm=[], y_periodgrm=[]))
        
        self.source_periodgrm_smooth = ColumnDataSource(
            data=dict(x_periodgrm_smooth=[], y_periodgrm_smooth=[]))

        # add an extra figure to plot an additional parameter - such as the background or the centroid shifts. 
        self.plot_periodgrm = figure(
            plot_height=400, plot_width=1200, title="", sizing_mode="scale_both", x_axis_type="log", y_axis_type="log")

        self.plot_periodgrm.line(
            x="x_periodgrm",
            y="y_periodgrm",
            source=self.source_periodgrm,
            line_color="black",
            color="black",
            alpha=1,)

        self.plot_periodgrm.line(
            x="x_periodgrm_smooth",
            y="y_periodgrm_smooth",
            source=self.source_periodgrm_smooth,
            line_color="red",
            color="red",
            alpha=1,)

        self.plot_periodgrm.xaxis.axis_label = "Frequency (micro Hz)"
        self.plot_periodgrm.yaxis.axis_label = "Power Spectral Density (A^2 mu Hz^-1"

        # -    -    -    -    -

        # Register the callback
        self.parent.primary.source.selected.on_change("indices", self.callback)


    def callback(self, attr, old, new):
        """
        Triggered when the user selects a point on the main plot.
        """
        # If a point is selected...
        if len(self.parent.primary.source.selected.indices):

            # Get the TIC ID
            ticid = self.parent.primary.source.data["ticid"][
                self.parent.primary.source.selected.indices[0]
            ]
            print("Fetching data for TIC ID {0}".format(ticid))

            (
                alltime,
                allflux,
                allflux_err,
                all_md,
                alltimebinned,
                allfluxbinned,
                allx1,
                allx2,
                ally1,
                ally2,
                alltimel2,
                allfbkg,
                start_sec,
                end_sec,
                in_sec,
                tessmag,
                teff,
                srad,
            ) = download_data(ticid, binfac=5, test="no")


            print("... download done.")

            self.source.data = dict(x=alltime, y=allflux)

            self.source_binned.data = dict(
                x_binned=alltimebinned, y_binned=allfluxbinned)

            # - - - Backgrounds - - - -
            # - - - - - - - - - - - - -
            self.source_bkg.data = dict(
                x_bkg=alltime, y_bkg=allfbkg)


            # - - - Centroic Plot - - - 
            # - - - - - - - - - - - - - 

            self.source_xcen1.data = dict(
                x_xcen1=alltimel2, y_xcen1=allx1)
            self.source_xcen2.data = dict(
                x_xcen2=alltimel2, y_xcen2=allx2)
            
            # -   -   -   -   -   -   -  
            self.source_ycen1.data = dict(
                x_ycen1=alltimel2, y_ycen1=ally1)
            self.source_ycen2.data = dict(
                x_ycen2=alltimel2, y_ycen2=ally2)

            # - - - Periodogram - - - -
            # - - - - - - - - - - - - -
            finite_mask = np.isfinite(alltime) & np.isfinite(allflux) 

            lc = lk.lightcurve.LightCurve(time = alltime[finite_mask], flux = allflux[finite_mask])
    
            lc = lc.remove_outliers().remove_nans()
            ls = lc.to_periodogram(normalization = 'psd')
    
            smooth = ls.smooth(method='boxkernel', filter_width=20.)
    
            freq = ls.frequency
            power = ls.power
    
            freq_smooth = smooth.frequency
            power_smooth = smooth.power

            self.source_periodgrm.data = dict(
                x_periodgrm=freq, y_periodgrm=power)

            self.source_periodgrm_smooth.data = dict(
                x_periodgrm_smooth=freq_smooth, y_periodgrm_smooth=power_smooth)
            

        else:
            # Clear the plot
            self.source.data = dict(x=[], y=[])
            self.source_binned.data = dict(x_binned=[], y_binned=[])
            # - - - 
            self.source_bkg.data = dict(x_bkg=[], y_bkg=[])
            # - - -
            self.source_xcen.data = dict(x_xcen1=[], y_xcen1=[])
            self.source_xcen.data = dict(x_xcen2=[], y_xcen2=[])
            self.source_ycen.data = dict(x_ycen1=[], y_ycen1=[])
            self.source_ycen.data = dict(x_ycen2=[], y_ycen2=[])

            self.source_periodgrm.data = dict(x_periodgrm=[], y_periodgrm=[])
            self.source_periodgrm_smooth.data = dict(x_periodgrm_smooth=[], y_periodgrm_smooth=[])

            # self.plot.xaxis.axis_label = 'Time (BJD - 2457000)'
            # self.plot.yaxis.axis_label = 'Normalised Flux'

    def layout(self):


        panels = [None, None, None]

        # Main panel: data
        panels[0] = Panel(child = self.plot_bkg, title = 'Background Flux')

        # Secondary panel: appearance
        panels[1] = Panel(child = column(self.plot_xcen, self.plot_ycen), title = 'Centroid Position')
        
        panels[2] = Panel(child = self.plot_periodgrm, title = 'Periodorgram')

        # panels[1] = Panel(child=self.checkbox_group, title="appearance",)

        tabs = Tabs(tabs=panels, css_classes=["tabs"])


        return column(self.plot, tabs)

