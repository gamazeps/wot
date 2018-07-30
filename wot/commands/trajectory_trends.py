#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os

import h5py
import numpy as np
import pandas as pd
import scipy
import wot.io
import wot.ot

def compute_trajectories(ot_model, *populations):
    """
    Computes the average and variance of each gene over time for the given populations

    Parameters
    ----------
    ot_model : wot.OTModel
        The OTModel used to find ancestors and descendants of the population
    *populations : wot.Population
        The target populations

    Returns
    -------
    timepoints : 1-D array
        The list of timepoints indexing the other two return values
    means : ndarray
        The list of the means of each gene at each timepoint
    variances : ndarray
        The list of the variances of each gene at each timepoint

    Notes
    -----
    If only one population is given, means and variances will have two dimensions, otherwise three

    Examples
    --------
    >>> timepoints, means, variances = compute_trajectories(ot_model, pop1, pop2, pop3)
    >>> means[i][j][k] # -> the mean value of the ancestors of population i at time j for gene k
    """
    timepoints = [wot.model.unique_timepoint(*populations)]
    traj, variances = [], []
    def update(*populations):
        m, v = ot_model.population_mean_and_variance(*populations)
        traj.append(m); variances.append(v)

    update(*populations)
    while ot_model.can_pull_back(*populations):
        populations = ot_model.pull_back(*populations)
        timepoints.append(wot.model.unique_timepoint(*populations))
        update(*populations)
    def unpack(arr):
        arr = [ arr[::-1,i,:] for i in range(arr.shape[1]) ]
        return arr if len(arr) > 1 else arr[0]
    return timepoints[::-1], unpack(np.asarray(traj)), unpack(np.asarray(variances))

def main(argv):
    parser = argparse.ArgumentParser(description='Generate mean expression profiles for '\
            'ancestors and descendants of each cell set at the given timepoint')
    parser.add_argument('--matrix', help=wot.commands.MATRIX_HELP, required=True)
    parser.add_argument('--cell_days', help=wot.commands.CELL_DAYS_HELP, required=True)
    parser.add_argument('--tmap', help=wot.commands.TMAP_HELP, required=True)
    parser.add_argument('--cell_set', help=wot.commands.CELL_SET_HELP, required=True)
    parser.add_argument('--time', help='Timepoint to consider', required=True)
    parser.add_argument('--out', help='Prefix for output file names', default='wot_trajectory')

    args = parser.parse_args(argv)

    ot_model = wot.initialize_ot_model(args.matrix, args.cell_days, tmap_dir = args.tmap)
    # TODO: refactor the following with census
    cell_sets = wot.io.read_cell_sets(args.cell_set)
    keys = list(cell_sets.keys())
    populations = ot_model.population_from_ids(*[cell_sets[name] for name in keys], at_time=float(args.time))
    # Get rid of empty populations : just ignore them
    keys = [ keys[i] for i in range(len(keys)) if populations[i] is not None ]
    populations = [ p for p in populations if p is not None ]

    if len(populations) == 0:
        raise ValueError("No cells from the given cell sets are present at that time")

    timepoints, trajectories, variances = compute_trajectories(ot_model, *populations)

    row_meta = pd.DataFrame([], index=timepoints, columns=[])
    col_meta = ot_model.matrix.col_meta.copy()
    for i in range(len(trajectories)):
        cs_name = keys[i]
        res = wot.Dataset(trajectories[i], row_meta, col_meta)
        # TODO: write the variances to a different file if a flag is passed
        wot.io.write_dataset(res, args.out + '_' + cs_name, output_format='txt', txt_full=False)
