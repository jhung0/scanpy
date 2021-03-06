# coding: utf-8
# Author: F. Alex Wolf (http://falexwolf.de)
"""tSNE

Notes
-----
This module automatically choose from three t-SNE versions from
- sklearn.manifold.TSNE
- Dmitry Ulyanov (multicore, fastest)
  https://github.com/DmitryUlyanov/Multicore-TSNE
  install via 'pip install psutil cffi', get code from github
"""

import numpy as np
from ..tools.pca import pca
from .. import settings as sett
from .. import logging as logg


def tsne(adata, random_state=0, n_pcs=50, perplexity=30, n_jobs=None, copy=False):
    u"""tSNE

    Reference
    ---------
    L.J.P. van der Maaten and G.E. Hinton.
    Visualizing High-Dimensional Data Using t-SNE.
    Journal of Machine Learning Research 9(Nov):2579-2605, 2008.

    Parameters
    ----------
    adata : AnnData
        Annotated data matrix, optionally with adata.smp['X_pca'], which is
        written when running sc.pca(adata). Is directly used for tSNE.
    random_state : unsigned int or -1, optional (default: 0)
        Change to use different intial states for the optimization, if -1, use
        default behavior of implementation (sklearn uses np.random.seed,
        Multicore-TSNE produces a new plot at every call).
    n_pcs : int, optional (default: 50)
        Number of principal components in preprocessing PCA.
    perplexity : float, optional (default: 30)
        The perplexity is related to the number of nearest neighbors that
        is used in other manifold learning algorithms. Larger datasets
        usually require a larger perplexity. Consider selecting a value
        between 5 and 50. The choice is not extremely critical since t-SNE
        is quite insensitive to this parameter.
    n_jobs : int or None (default: None)
        Use the multicore implementation, if it is installed. Defaults to
        sett.n_jobs.

    Notes
    -----
    X_tsne : np.ndarray of shape n_samples x 2
        Array that stores the tSNE representation of the data. Analogous
        to X_pca, X_diffmap and X_spring.
    is added to adata.smp.
    """
    logg.m('compute tSNE', r=True)
    adata = adata.copy() if copy else adata
    # preprocessing by PCA
    if 'X_pca' in adata.smp and adata.smp['X_pca'].shape[1] >= n_pcs:
        X = adata.smp['X_pca'][:, :n_pcs]
        logg.m('... using X_pca for tSNE')
    else:
        if n_pcs > 0 and adata.X.shape[1] > n_pcs:
            logg.m('... preprocess using PCA with', n_pcs, 'PCs')
            logg.m('avoid this by setting n_pcs = 0', v='hint')
            X = pca(adata.X, random_state=random_state, n_comps=n_pcs)
            adata.smp['X_pca'] = X
        else:
            X = adata.X
    logg.m('... using', n_pcs, 'principal components')
    # params for sklearn
    params_sklearn = {'perplexity': perplexity,
                      'random_state': None if random_state == -1 else random_state,
                      'verbose': sett.verbosity,
                      'learning_rate': 200,
                      'early_exaggeration': 12,
                      # 'method': 'exact'
                      }
    n_jobs = sett.n_jobs if n_jobs is None else n_jobs
    # deal with different tSNE implementations
    multicore_failed = False
    if n_jobs > 1:
        try:
            from MulticoreTSNE import MulticoreTSNE as TSNE
            tsne = TSNE(n_jobs=n_jobs, **params_sklearn)
            logg.m('... using MulticoreTSNE')
            X_tsne = tsne.fit_transform(X.astype(np.float64))
        except ImportError:
            multicore_failed = True
            sett.m(0, '--> did not find package MulticoreTSNE: to speed up the computation install it from\n'
                   '    https://github.com/DmitryUlyanov/Multicore-TSNE')
    if n_jobs == 1 or multicore_failed:
        from sklearn.manifold import TSNE
        tsne = TSNE(**params_sklearn)
        logg.m('consider installing the package MulticoreTSNE from\n'
               '        https://github.com/DmitryUlyanov/Multicore-TSNE\n'
               '    Even for `n_jobs=1` this speeds up the computation considerably.',
               v='hint')
        logg.m('... using sklearn.manifold.TSNE')
        X_tsne = tsne.fit_transform(X)
    # update AnnData instance
    adata.smp['X_tsne'] = X_tsne
    logg.m('finished', t=True, end=' ')
    logg.m('and added\n'
           '    "X_tsne" coordinates, the tSNE representation of X (adata.smp)')
    return adata if copy else None
