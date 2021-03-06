# Authors: F. Alex Wolf <http://falexwolf.de>
#          P. Angerer
"""Toplevel plotting functions for AnnData.
"""

import os
import numpy as np

from ..compat.matplotlib import pyplot as pl
from matplotlib import rcParams
from matplotlib.figure import SubplotParams as sppars
from matplotlib.colors import is_color_like
from .. import settings as sett
from .. import logging as logg
from .. import utils as sc_utils
from .. import readwrite
from . import utils
from .utils import scatter_base, scatter_group


# -------------------------------------------------------------------------------
# Toplevel Helper Functions
# -------------------------------------------------------------------------------


def savefig(writekey):
    """Save current figure to file.

    The filename is generated as follows:
    ```
    if sett.run_name != '': writekey = sett.run_name + '_' + writekey
    filename = sett.figdir + writekey + sett.plotsuffix + '.' + sett.file_format_figs
    ```
    """
    if rcParams['savefig.dpi'] < 300:
        dpi = 300
        logg.m('... you are using a very low resolution for saving figures, adjusting to dpi=300')
    else:
        dpi = rcParams['savefig.dpi']
    if not os.path.exists(sett.figdir): os.makedirs(sett.figdir)
    if sett.run_name != '': writekey = sett.run_name + '_' + writekey
    filename = sett.figdir + writekey + sett.plotsuffix + '.' + sett.file_format_figs
    logg.m('... saving figure to file', filename)
    pl.savefig(filename, dpi=dpi)
    pl.close()  # clear figure


def savefig_or_show(writekey, show=None):
    show = sett.autoshow if show is None else show
    if sett.savefigs: savefig(writekey)
    elif show: pl.show()


# -------------------------------------------------------------------------------
# Toplevel Plotting Functions
# -------------------------------------------------------------------------------


def matrix(matrix, xlabels=None, ylabels=None, cshrink=0.5,
           cmap='Greys'):
    fig = pl.figure(figsize=(5, 5))
    pl.imshow(matrix, cmap=cmap)
    if xlabels is not None:
        pl.xticks(range(len(xlabels)), xlabels, rotation='vertical')
    if ylabels is not None:
        pl.yticks(range(len(ylabels)), ylabels)
    pl.colorbar(shrink=cshrink)
    pl.show()


def violin(adata, smp, jitter=True, size=1, color='black', show=None):
    """Violin plot.

    Wraps seaborn.violinplot.

    Parameters
    ----------
    jitter : float or bool (default: True)
        See sns.stripplot.

    Returns
    -------
    A seaborn.FacetGrid that allows to access the matplotlib.Axis objects.
    """
    import pandas as pd
    import seaborn as sns
    smp_df = adata.smp.to_df()
    smp_tidy = pd.melt(smp_df, value_vars=smp)
    sns.set_style('whitegrid')
    g = sns.FacetGrid(smp_tidy, col='variable', sharey=False)
    g = g.map(sns.violinplot, 'value', inner=None, orient='vertical')
    g = g.map(sns.stripplot, 'value', orient='vertical', jitter=jitter, size=size,
                 color=color).set_titles(
                     col_template='{col_name}').set_xlabels('')
    show = sett.autoshow if show else show
    if show: pl.show()
    utils.init_plotting_params()  # reset fig_params, seaborn overwrites settings
    sett.set_dpi()  # reset resolution
    return g


def scatter(adata,
            x=None,
            y=None,
            color='grey',
            basis=None,
            names=None,
            comps=None,
            cont=None,
            layout='2d',
            legendloc='right margin',
            cmap=None,
            pal=None,
            right_margin=None,
            size=None,
            titles=None,
            show=True):
    """Scatter plots.

    Color with sample annotation (`color in adata.smp_keys()`) or gene
    expression (`color in adata.var_names`).

    Parameters
    ----------
    adata : AnnData
        Annotated data matrix.
    x : str or None
        x coordinate.
    y : str or None
        y coordinate.
    color : str or list of strings, optional (default: 'grey')
        Sample/Cell annotation key for coloring (either a key for adata.smp or a
        var_name or a uniform matplotlib color). String annotation is plotted assuming categorical annotation,
        float and integer annotation is plotted assuming continuous
        annoation.
    basis : {'pca', 'tsne', 'diffmap'}
        String that denotes a plotting tool.
    names : str, optional (default: all names in color)
        Allows to restrict groups in sample annotation (color) to a few.
    comps : str, optional (default: '1,2')
         String in the form '1,2,3'.
    cont : bool, None (default: None)
        Switch on continuous layout, switch off categorical layout.
    layout : {'2d', '3d'}, optional (default: '2d')
         Layout of plot.
    legendloc : see matplotlib.legend, optional (default: 'lower right')
         Options for keyword argument 'loc'.
    cmap : str (default: 'viridis')
         String denoting matplotlib color map.
    pal : list of str (default: matplotlib.rcParams['axes.prop_cycle'].by_key()['color'])
         Colors cycle to use for categorical groups.
    right_margin : float (default: None)
         Adjust how far the plotting panel extends to the right.
    size : float (default: None)
         Point size. Sample-number dependent by default.
    titles : str, optional (default: None)
         Provide titles for panels as "my title1,another title,...".

    Returns
    -------
    A list of matplotlib.Axis objects.
    """
    # write params to a config file
    params = locals()
    del params['adata']
    if os.path.exists('.scanpy/config_plotting.txt'):
        params = sc_utils.update_params(readwrite.read_params('.scanpy/config_plotting.txt', verbosity=2), params)
        if right_margin != params['right_margin']:
            right_margin = params['right_margin']
            sett.m(2, '... setting right_margin to saved value', right_margin)
    readwrite.write_params('.scanpy/config_plotting.txt', params)
    del params
    # compute components
    if comps is None: comps = '1,2' if '2d' in layout else '1,2,3'
    if isinstance(comps, str): comps = comps.split(',')
    comps = np.array(comps).astype(int) - 1
    titles = None if titles is None else titles.split(',') if isinstance(titles, str) else titles
    color_keys = ['grey'] if color is None else color.split(',') if isinstance(color, str) else color
    names = None if names is None else names.split(',') if isinstance(names, str) else names
    # highlights
    highlights = adata.add['highlights'] if 'highlights' in adata.add else []
    if basis is not None:
        try:
            Y = adata.smp['X_' + basis][:, comps]
        except KeyError:
            sett.mi('--> compute the basis using plotting tool', basis, 'first')
            raise
    else:
        x_arr = adata.get_smp_array(x)
        y_arr = adata.get_smp_array(y)
        Y = np.c_[x_arr[:, None], y_arr[:, None]]

    if size is None:
        n = Y.shape[0]
        size = 120000 / n
        # logg.m('... setting point size to {:.2}'.format(size))

    pal_was_none = False
    if pal is None: pal_was_none = True
    pal = utils.default_pal(pal)

    component_name = ('DC' if basis == 'diffmap'
                      else 'Spring' if basis == 'spring'
                      else 'tSNE' if basis == 'tsne'
                      else 'PC' if basis == 'pca'
                      else None)
    axis_labels = (x, y) if component_name is None else None
    show_ticks = True if component_name is None else False

    # the actual color ids, e.g. 'grey' or '#109482'
    color_ids = [None if not is_color_like(color_key)
                 else color_key for color_key in color_keys]
    categoricals = []
    colorbars = []
    for icolor_key, color_key in enumerate(color_keys):
        if color_ids[icolor_key] is not None:
            c = color_ids[icolor_key]
            continuous = True
            categorical = False
            colorbars.append(False)
        else:
            c = 'white' if layout == '2d' else 'white'
            categorical = False
            continuous = False
            # test whether we have categorial or continuous annotation
            if color_key in adata.smp_keys():
                if adata.smp[color_key].dtype.char in ['S', 'U']:
                    categorical = True
                    if cont is True:
                        c = adata.smp[color_key]
                else:
                    continuous = True
                    c = adata.smp[color_key]
                # sett.m(0, '... coloring according to', color_key)
            # coloring according to gene expression
            elif color_key in set(adata.var_names):
                c = adata[:, color_key].X
                continuous = True
                # sett.m(0, '... coloring according to expression of gene', color_key)
            else:
                raise ValueError('"' + color_key + '" is invalid!'
                                 + ' specify valid sample annotation, one of '
                                 + str(adata.smp_keys()) + ' or a gene name '
                                 + str(adata.var_names))
            if cont is not None:
                categorical = not cont
                continuous = cont
            colorbars.append(True if continuous else False)
        if categorical: categoricals.append(icolor_key)
        color_ids[icolor_key] = c

    if right_margin is None and legendloc == 'right margin':
        right_margin = 0.3
    if titles is None and color_keys[0] is not None:
        titles = [color_key.replace('_', ' ') if not is_color_like(color_key) else '' for color_key in color_keys]

    axs = scatter_base(Y,
                       titles=titles,
                       component_name=component_name,
                       axis_labels=axis_labels,
                       component_indexnames=comps + 1,
                       layout=layout,
                       colors=color_ids,
                       highlights=highlights,
                       colorbars=colorbars,
                       right_margin=right_margin,
                       sizes=[size for c in color_keys],
                       cmap='viridis' if cmap is None else cmap,
                       show_ticks=show_ticks)

    for icolor_key in categoricals:
        color_key = color_keys[icolor_key]
        if (not color_key + '_colors' in adata.add or not pal_was_none
            or len(adata.add[color_key + '_names']) != len(adata.add[color_key + '_colors'])):
            utils.add_colors_for_categorical_sample_annotation(adata, color_key, pal)
        # actually plot the groups
        mask_remaining = np.ones(Y.shape[0], dtype=bool)
        if names is None:
            for iname, name in enumerate(adata.add[color_key + '_names']):
                if name not in sett._ignore_categories:
                    mask = scatter_group(axs[icolor_key], color_key, iname,
                                         adata, Y, layout, size=size)
                    mask_remaining[mask] = False
        else:
            for name in names:
                if name not in set(adata.add[color_key + '_names']):
                    raise ValueError('"' + name + '" is invalid!'
                                     + ' specify valid name, one of '
                                     + str(adata.add[color_key + '_names']))
                else:
                    iname = np.flatnonzero(adata.add[color_key + '_names'] == name)[0]
                    mask = scatter_group(axs[icolor_key], color_key, iname,
                                         adata, Y, layout, size=size)
                    mask_remaining[mask] = False
        if mask_remaining.sum() > 0:
            data = [Y[mask_remaining, 0], Y[mask_remaining, 1]]
            if layout == '3d': data.append(Y[mask_remaining, 2])
            axs[icolor_key].scatter(*data, marker='.', c='grey', s=size,
                                    edgecolors='none', zorder=-1)
        if legendloc == 'right margin':
            legend = axs[icolor_key].legend(frameon=False, loc='center left',
                                            bbox_to_anchor=(1, 0.5),
                                            ncol=2 if len(adata.add[color_key + '_names']) > 14 else 1)
        elif legendloc != 'none':
            legend = axs[icolor_key].legend(frameon=False, loc=legendloc)
        if legend is not None:
            for handle in legend.legendHandles: handle.set_sizes([300.0])
    if show: pl.show()
    return axs

def ranking(adata, attr, keys, labels=None, color='black', n_points=30):
    """Plot rankings.

    See, for example, how this is used in pl.pca_ranking.

    Parameters
    ----------
    adata : AnnData
        The data.
    attr : {'var', 'add', 'smp'}
        An attribute of AnnData.
    keys : str or list of str
        Used to look up an array from the attribute of adata.

    Returns
    -------
    Returns matplotlib gridspec with access to the axes.
    """
    scores = getattr(adata, attr)[keys]
    n_panels = len(keys) if isinstance(keys, list) else 1
    if n_panels == 1: scores, keys = scores[:, None], [keys]
    if labels is None:
        labels = adata.var_names if attr == 'var' else np.arange(scores.shape[0]).astype(str)
    if isinstance(labels, str):
        labels = [labels + str(i+1) for i in range(scores.shape[0])]
    from matplotlib import gridspec
    if n_panels <= 5: n_rows, n_cols = 1, n_panels
    else: n_rows, n_cols = 2, int(n_panels/2 + 0.5)
    fig = pl.figure(figsize=(n_cols * rcParams['figure.figsize'][0],
                             n_rows * rcParams['figure.figsize'][1]))
    left, bottom = 0.2/n_cols, 0.13/n_rows
    gs = gridspec.GridSpec(nrows=n_rows, ncols=n_cols, wspace=0.2,
                           left=left, bottom=bottom,
                           right=1-(n_cols-1)*left-0.01/n_cols,
                           top=1-(n_rows-1)*bottom-0.1/n_rows)
    for iscore, score in enumerate(scores.T):
        pl.subplot(gs[iscore])
        indices = np.argsort(score)[::-1][:n_points+1]
        for ig, g in enumerate(indices):
            pl.text(ig, score[g], labels[g], color=color,
                    rotation='vertical', verticalalignment='bottom',
                    horizontalalignment='center', fontsize=8)
        pl.title(keys[iscore].replace('_', ' '))
        if n_panels <= 5 or count > n_cols: pl.xlabel('ranking')
        pl.xlim(-0.9, ig + 0.9)
        score_min, score_max = np.min(score[indices]), np.max(score[indices])
        pl.ylim((0.95 if score_min > 0 else 1.05) * score_min,
                (1.05 if score_max > 0 else 0.95) * score_max)
    return gs


def ranking_deprecated(adata, toolkey, n_genes=20):
    """Plot ranking of genes

    Parameters
    ----------
    adata : AnnData
        Annotated data matrix.
    n_genes : int
        Number of genes.
    """

    # one panel for each ranking
    scoreskey = adata.add[toolkey + '_scoreskey']
    n_panels = len(adata.add[toolkey + '_rankings_names'])

    def get_scores(irank):
        allscores = adata.add[toolkey + '_' + scoreskey][irank]
        scores = allscores[adata.add[toolkey + '_rankings_geneidcs'][irank, :n_genes]]
        scores = np.abs(scores)
        return scores

    # the limits for the y axis
    ymin = 1e100
    ymax = -1e100
    for irank in range(len(adata.add[toolkey + '_rankings_names'])):
        scores = get_scores(irank)
        ymin = np.min([ymin, np.min(scores)])
        ymax = np.max([ymax, np.max(scores)])
    ymax += 0.3*(ymax-ymin)

    # number of panels
    if n_panels <= 5:
        n_panels_y = 1
        n_panels_x = n_panels
    else:
        n_panels_y = 2
        n_panels_x = int(n_panels/2+0.5)

    fig = pl.figure(figsize=(n_panels_x * 4, n_panels_y * 4))

    from matplotlib import gridspec
    left = 0.2/n_panels_x
    bottom = 0.13/n_panels_y
    gs = gridspec.GridSpec(nrows=n_panels_y,
                           ncols=n_panels_x,
                           left=left,
                           right=1-(n_panels_x-1)*left-0.01/n_panels_x,
                           bottom=bottom,
                           top=1-(n_panels_y-1)*bottom-0.1/n_panels_y,
                           wspace=0)

    count = 1
    for irank in range(len(adata.add[toolkey + '_rankings_names'])):
        pl.subplot(gs[count-1])
        scores = get_scores(irank)
        for ig, g in enumerate(adata.add[toolkey + '_rankings_geneidcs'][irank, :n_genes]):
            marker = (r'\leftarrow' if adata.add[toolkey + '_zscores'][irank, g] < 0
                                    else r'\rightarrow')
            pl.text(ig, scores[ig],
                    r'$ ' + marker + '$ ' + adata.var_names[g],
                    color='red' if adata.add[toolkey + '_zscores'][irank, g] < 0 else 'green',
                    rotation='vertical', verticalalignment='bottom',
                    horizontalalignment='center',
                    fontsize=8)
        title = adata.add[toolkey + '_rankings_names'][irank]
        pl.title(title)
        if n_panels <= 5 or count > n_panels_x:
            pl.xlabel('ranking')
        if count == 1 or count == n_panels_x+1:
            pl.ylabel(scoreskey)
        else:
            pl.yticks([])
        pl.ylim([ymin, ymax])
        pl.xlim(-0.9, ig+1-0.1)
        count += 1


def timeseries(X, **kwargs):
    """Plot X. See timeseries_subplot."""
    pl.figure(figsize=(2*rcParams['figure.figsize'][0], rcParams['figure.figsize'][1]),
              subplotpars=sppars(left=0.12, right=0.98, bottom=0.13))
    timeseries_subplot(X, **kwargs)


def timeseries_subplot(X,
                       c=None,
                       varnames=(),
                       highlightsX=(),
                       xlabel='',
                       ylabel='gene expression',
                       yticks=None,
                       xlim=None,
                       legend=True,
                       pal=None,
                       cmap='viridis'):
    """Plot X.

    Call this with:
    X with one column, c categorical
    X with one column, c continuous
    X with n columns, c is of length n
    """

    if c is not None:
        use_cmap = isinstance(c[0], float) or isinstance(c[0], np.float32)
    pal = utils.default_pal(pal)
    x_range = np.arange(X.shape[0])
    if X.shape[1] > 1:
        colors = pal[:X.shape[1]].by_key()['color']
        subsets = [(x_range, X[:, i]) for i in range(X.shape[1])]
    elif use_cmap:
        colors = [c]
        subsets = [(x_range, X[:, 0])]
    else:
        levels, _ = np.unique(c, return_inverse=True)
        colors = np.array(pal[:len(levels)].by_key()['color'])
        subsets = [(x_range[c == l], X[c == l, :]) for l in levels]

    for i, (x, y) in enumerate(subsets):
        pl.scatter(
            x, y,
            marker='.',
            edgecolor='face',
            s=rcParams['lines.markersize'],
            c=colors[i],
            label=varnames[i] if len(varnames) > 0 else '',
            cmap=cmap,
        )
    ylim = pl.ylim()
    for ih, h in enumerate(highlightsX):
        pl.plot([h, h], [ylim[0], ylim[1]], '--', color='black')
    pl.ylim(ylim)
    if xlim is not None:
        pl.xlim(xlim)
    pl.xlabel(xlabel)
    pl.ylabel(ylabel)
    if yticks is not None:
        pl.yticks(yticks)
    if len(varnames) > 0 and legend == True:
        pl.legend(frameon=False)


def timeseries_as_heatmap(X, varnames=None, highlightsX=None, cmap='viridis'):
    """Plot timeseries as heatmap.

    Parameters
    ----------
    X : np.ndarray
        Data array.
    varnames : array_like
        Array of strings naming variables stored in columns of X.
    """
    if highlightsX is None:
        highlightsX = []
    if varnames is None:
        varnames = []
    if len(varnames) == 0:
        varnames = np.arange(X.shape[1])
    if varnames.ndim == 2:
        varnames = varnames[:, 0]

    # transpose X
    X = X.T
    minX = np.min(X)

    # insert space into X
    if False:
        # generate new array with highlightsX
        space = 10  # integer
        Xnew = np.zeros((X.shape[0], X.shape[1] + space*len(highlightsX)))
        hold = 0
        _hold = 0
        space_sum = 0
        for ih, h in enumerate(highlightsX):
            _h = h + space_sum
            Xnew[:, _hold:_h] = X[:, hold:h]
            Xnew[:, _h:_h+space] = minX * np.ones((X.shape[0], space))
            # update variables
            space_sum += space
            _hold = _h + space
            hold = h
        Xnew[:, _hold:] = X[:, hold:]

    fig = pl.figure(figsize=(1.5*4, 2*4))
    im = pl.imshow(np.array(X, dtype=np.float_), aspect='auto',
              interpolation='nearest', cmap=cmap)
    pl.colorbar(shrink=0.5)
    pl.yticks(range(X.shape[0]), varnames)
    for ih, h in enumerate(highlightsX):
        pl.plot([h, h], [0, X.shape[0]], '--', color='black')
    pl.xlim([0, X.shape[1]-1])
    pl.ylim([0, X.shape[0]-1])
