#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse

import h5py
import numpy as np
import pandas as pd
import wot.io


def get_scores(ds1, ds2, ds1_time_index, ds2_time_index, score_function):
    scores = np.zeros(shape=ds1.x.shape[1])
    for feature_idx in range(ds1.x.shape[1]):  # each feature
        m1 = ds1.x[ds1_time_index, feature_idx]
        m2 = ds2.x[ds2_time_index, feature_idx]
        v1 = ds1.variance[ds1_time_index, feature_idx]
        v2 = ds2.variance[ds2_time_index, feature_idx]
        scores[feature_idx] = score_function(m1, m2, v1, v2)
    return scores


def main(argv):
    parser = argparse.ArgumentParser(
        description='Compute differentially expressed genes from output of trajectory_trends. Outputs a ranked list for each comparison.')
    parser.add_argument('--matrix1', help=wot.commands.MATRIX_HELP, required=True)
    parser.add_argument('--matrix2', help=wot.commands.MATRIX_HELP)
    parser.add_argument('--score',
                        help='Method to compute differential gene expression score. Choices are signal to noise, mean difference, and fold change',
                        choices=['s2n', 'mean_difference', 'fold_change'])

    args = parser.parse_args(argv)
    ds1 = wot.io.read_dataset(args.matrix1)

    # hack to add variance
    f = h5py.File(args.matrix1, 'r')
    ds1.variance = f['/layers/variance'][()]
    f.close()
    ds2 = None
    if args.matrix2 is not None:
        ds2 = wot.io.read_dataset(args.matrix2)
        f = h5py.File(args.matrix2, 'r')
        ds2.variance = f['/layers/variance'][()]
        f.close()

    def s2n(m1, m2, v1, v2):
        denom = (np.sqrt(v1) + np.sqrt(v2))
        s2n = 0.0 if denom == 0.0 else ((m1 - m2) / denom)
        return s2n

    def fold_change(m1, m2, v1, v2):
        return m1 / m2

    def mean_difference(m1, m2, v1, v2):
        return m1 - m2

    # dataset has time on rows, genes on columns
    score_function = locals()[args.score]

    if ds2 is not None:
        for i in range(ds1.x.shape[0]):  # each time
            scores = get_scores(ds1, ds2, i, i, score_function)
            pd.DataFrame(index=ds1.col_meta.index.values, data={'scores': scores}).to_csv(
                str(ds1.row_meta.index.values[i]) + '.rnk', sep='\t', header=False)
    else:
        for i in range(1, ds1.x.shape[0]):
            scores = get_scores(ds1, ds1, i - 1, i, score_function)
            pd.DataFrame(index=ds1.col_meta.index.values, data={'scores': scores}).to_csv(
                str(ds1.row_meta.index.values[i - 1]) + '_' + str(ds1.row_meta.index.values[i]) + '.rnk', sep='\t',
                header=False)
