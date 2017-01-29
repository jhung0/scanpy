# coding: utf-8
"""
Example Data and Example Use Cases
==================================

From package Scanpy (https://github.com/theislab/scanpy).
Written in Python 3 (compatible with 2).
Copyright 2016-2017 F. Alexander Wolf (http://falexwolf.de).

"""

from . import builtin, user
from .. import utils
from .. import settings as sett

def exdata(format='plain'):
    """
    Show available example data.
    """
    if format == 'plain':
        s = utils.pretty_dict_string(dexdata())
        print(s)
    elif format == 'markdown':
        s = utils.markdown_dict_string(builtin.dexdata)
    print(s)

def examples():
    """
    Show available example use cases.
    """
    s = utils.pretty_dict_string(dexamples())
    print(s)

def dexdata(): 
    """ Example data. """
    all_dex = utils.merge_dicts(builtin.dexdata, user.dexdata)
    try:
        # additional possibility to add example module
        from . import user_private
        all_dex = utils.merge_dicts(all_dex, user_private.dexdata) 
    except ImportError:
        pass
    return all_dex

def dexamples():
    """ Example use cases. """
    builtin_dex = utils.fill_in_datakeys(builtin.dexamples, builtin.dexdata)
    user_dex = utils.fill_in_datakeys(user.dexamples, user.dexdata)
    all_dex = utils.merge_dicts(builtin_dex, user_dex) 
    try:
        # additional possibility to add example module
        from . import user_private
        user_private_dex = utils.fill_in_datakeys(user_private.dexamples, 
                                                  user_private.dexdata)
        all_dex = utils.merge_dicts(all_dex, user_private_dex) 
    except ImportError:
        pass
    return all_dex

def example(exkey, return_module=False):
    """
    Read and preprocess data for predefined example.

    Parameters
    ----------
    exkey : str
        Key for the example dictionary in _examples.
    return_module : bool, optional
        Return example module.

    Returns
    -------
    ddata : dict containing
        X : np.ndarray
            Data array for further processing, columns correspond to genes,
            rows correspond to samples.
        rownames : np.ndarray
            Array storing the experimental labels of samples.
        colnames : np.ndarray
            Array storing the names of genes.

        There might be further entries such as
        groupnames_n : np.ndarray
            Array of shape (number of samples) that indicates groups.
        xroot : np.ndarray or int
            Expression vector or index of root cell for DPT analysis.

    Returns additionally, if return_module == True:
    exmodule : dict, optional
        Example module.
    """
    try:
        _exkey = getattr(user, exkey)
        exmodule = user
    except AttributeError:
        try:
            # additional possibility to add example module
            from . import user_private
            _exkey = getattr(user_private, exkey)
            exmodule = user_private
        except (ImportError, AttributeError):
            try:
                _exkey = getattr(builtin, exkey)
                exmodule = builtin
            except AttributeError:
                msg = ('Do not know how to run example "' + exkey +
                       '".\nEither define a function ' + exkey + '() '
                       'in scanpy/exs/user.py that returns a data dictionary.\n'
                       'Or use one of the available examples:'
                       + exkeys_str())
                from sys import exit
                exit(msg)

    # run the function
    ddata = _exkey()

    # add exkey to ddata
    ddata['exkey'] = exkey
    sett.m(0, 'X has shape', ddata['X'].shape[0], 'x', ddata['X'].shape[1])
    # do sanity checks on data dictionary
    ddata = check_ddata(ddata)
    
    if return_module:
        return ddata, exmodule
    else:
        return ddata

def annotate(ddata, exkey):
    """
    Annotates ddata if a corresponding function is present.
    """
    try:
        ddata = getattr(user, exkey + '_annotate')(ddata)
    except:
        try:
            ddata = getattr(builtin, exkey + '_annotate')(ddata)
        except:
            raise ValueError('Did not find separate function for annotation.\n'
                             'Try calling sc.example(' + exkey + ').')
    return ddata

#-------------------------------------------------------------------------------
# Checking of data dictionary
# - Might be replaced with a data class.
#-------------------------------------------------------------------------------

# howtos
howto_specify_subgroups = '''no key "groupnames_n" in ddata dictionary found
--> you might provide a list/1d-array of subgroup names (strings) or
    integers with length = n = number of cells/samples.'''

def check_ddata(ddata):
    """
    Do sanity checks on ddata dictionary.
    """
    import numpy as np
    if not 'groupnames_n' in ddata:
        sett.m(0, howto_specify_subgroups)
    else: 
        try:
            ddata['groupnames_n'] = np.array(ddata['groupnames_n'], dtype=int)
        except:
            ddata['groupnames_n'] = np.array(ddata['groupnames_n'], dtype=str)
        if not 'groupnames' in ddata:
            ddata['groupnames'] = np.unique(ddata['groupnames_n'])            
        # just an array for iterating quickly
        if not 'groupmasks' in ddata:
            groupmasks = []
            for groupname in ddata['groupnames']: 
                groupmasks.append(groupname == np.array(ddata['groupnames_n']))
            ddata['groupmasks'] = np.array(groupmasks)
        # for indexing into groupnames and groupmasks
        if not 'groupids' in ddata:
            ddata['groupids'] = np.arange(len(ddata['groupnames']), dtype=int)
        # for plotting
        if not 'groupcolors' in ddata:
            from ..compat.matplotlib import pyplot as pl
            ddata['groupcolors'] = pl.cm.jet(pl.Normalize()(ddata['groupids']))
        sett.m(0,'groupnames in ddata', ddata['groupnames'])
    return ddata

def exkeys_str():
    str = '\n'
    for k in sorted(dexamples().keys()):
        str += '    ' + k + '\n'
    return str