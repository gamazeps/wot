import numpy as np
from matplotlib import pyplot

import wot.graphics

# ------ Configuration variables -------
matrix_file = 'matrix.txt'
bg_color = "#80808080"
gene_x_plot = 0
gene_y_plot = 1
cell_sets_file = 'cell_sets.gmt'
target_cell_set = "Red blood cells"
target_timepoint = 7
destination_file = "ancestors.png"
# --------------------------------------

ds = wot.io.read_dataset(matrix_file)

tmap_model = wot.tmap.TransportMapModel.from_directory('tmaps')

transparent = lambda x: wot.graphics.hexstring_of_rgba((.08, .34, .59, x))


def color_cells(population):
    p = population.p
    if not np.isclose(max(p), 0):
        p = p / max(p)
    color = [transparent(x) for x in p]
    wot.set_cell_metadata(ds, 'color', color,
                          indices=tmap_model.cell_ids(population))


pyplot.figure(figsize=(5, 5))
pyplot.axis('off')
wot.set_cell_metadata(ds, 'color', bg_color)

wot.graphics.plot_2d_dataset(pyplot, ds, x=gene_x_plot, y=gene_y_plot)

cell_sets = wot.io.read_sets(cell_sets_file, as_dict=True)
population = tmap_model.population_from_ids(
    cell_sets[target_cell_set],
    at_time=target_timepoint)[0]
color_cells(population)

while tmap_model.can_pull_back(population):
    population = tmap_model.pull_back(population)
    color_cells(population)

wot.graphics.plot_2d_dataset(pyplot, ds,
                             x=gene_x_plot, y=gene_y_plot, s=1, colors=ds.obs['color'].values)
wot.graphics.legend_figure(pyplot,
                           [["#316DA2", "Ancestors of {}".format(target_cell_set)]])
pyplot.autoscale(enable=True, tight=True)
pyplot.tight_layout(pad=0)
pyplot.savefig(destination_file)
