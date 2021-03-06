import numpy as np
from matplotlib import pyplot

import wot.graphics

# ------ Configuration variables -------
matrix_file = 'matrix.txt'
days_file = 'days.txt'
gene_x_plot = 0
gene_y_plot = 1
destination_file = "generated_data.png"
# --------------------------------------

color1 = [.08, .34, .59]  # first color
color2 = [.08, .59, .34]  # final color

ds = wot.io.read_dataset(matrix_file)
wot.io.add_row_metadata_to_dataset(ds, days_path=days_file)

# you can use any of the columns here, or metadata information :
cell_colors = np.asarray(ds.obs['day'])
cell_colors = cell_colors / max(cell_colors)
cell_colors = [wot.graphics.color_mix(color1, color2, d)
               for d in cell_colors]
wot.set_cell_metadata(ds, 'color', cell_colors)

pyplot.figure(figsize=(5, 5))
pyplot.axis('off')
wot.graphics.plot_2d_dataset(pyplot, ds,
                             x=gene_x_plot, y=gene_y_plot, colors=ds.obs['color'].values)
pyplot.autoscale(enable=True, tight=True)
pyplot.tight_layout(pad=0)
pyplot.savefig(destination_file)
