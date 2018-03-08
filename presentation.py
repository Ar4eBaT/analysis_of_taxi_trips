import numpy as np
import pandas as pd
from glob import glob

file_path = np.sort(glob("new_data/*.csv", recursive=True))
predictions_path = np.sort(glob("new_result/*.csv", recursive=True))

input_data = []
for i in range(6):
    real_data = pd.read_csv(file_path[i])
    pred_data = pd.read_csv(predictions_path[i])
    real_data.time = real_data.time.astype(np.datetime64)
    real_data.trips = real_data.trips.astype(int)
    real_data["predictions"] = pred_data.trips
    input_data.append(real_data)
    del real_data
    del pred_data

regions = np.sort(pd.unique(input_data[0].region))

from ipywidgets import widgets
from IPython.display import display
from ipywidgets import interact

import holoviews as hv
hv.notebook_extension('bokeh')

# Set plot and style options
hv.util.opts('Area [width=700 shared_axes=False logz=True] {+framewise} ')
hv.util.opts("Curve [xaxis=None yaxis=None show_grid=False, show_frame=False] (color='orangered') {+framewise}")

def get_data(region, prediction_for=1, **kwargs):
    data = input_data[prediction_for - 1][input_data[prediction_for - 1].region == region].sort_values("time")
    return hv.Area((data.time, data.trips), 'Time', 'Trips') * hv.Area((data.time, data.predictions), 'Time', 'Pred')

n_regions = pd.read_csv("regions.csv", sep=";")

lats = n_regions[["south", "north"]].get_values()
lons = n_regions[["west", "east"]].get_values()
reg_data = n_regions["region"].get_values()

data = input_data[0]

coord = []
for i in range(n_regions.shape[0]):
    reg_label = "region_" + str(reg_data[i])
    if reg_label not in regions:
        continue
    coords = []
    coords.extend(list(map(lambda x: [lons[i][0], x], lats[i])))
    coords.extend(list(map(lambda x: [lons[i][1], x], lats[i][::-1])))

    n_dict = {("lon", "lat") : coords,
              "detailed name" : reg_label,
              "Mean trips" : int(data[data.region == reg_label].trips.mean())}
    coord.append(n_dict)

choropleth = hv.Polygons(coord, ["lon", "lat"], [('detailed name', 'Region'), 'Mean trips'], label="NY Taxi trips")

plot_opts = dict(logz=True, tools=['hover'], xaxis=None, yaxis=None,
                 show_grid=False, show_frame=False, width=500, height=500,
                 color_index='Mean trips', colorbar=True, toolbar='above')
style = dict(line_color='white')

# %opts Area [width=700] {+framewise}

dmap = hv.DynamicMap(get_data, kdims=['region', "prediction_for"]).redim.values(region=regions, prediction_for=range(1,7))

res = (dmap + choropleth.opts(style=style, plot=plot_opts)).cols(1)

# Obtain Bokeh document and set the title
doc = hv.renderer('bokeh').server_doc(res)
doc.title = 'NYC Taxi predictions'
