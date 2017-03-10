#
#                                                                  gemini_python
#
#                                                    recipe_system.utils.findexe
# ------------------------------------------------------------------------------
import os
import psutil

def findexe(exe):
    """
    Function recieves an executable name, 'exe', as a string, and returns
    a list of pids that match the name.

    Parameters:
    ----------
        exe: Name of a running executable.
        type: <str>

    Returns:
    -------
        pids: a list of extant pids found running 'exe'
        type: <list>

    E.g., find autoredux,

    >>> findexe('autoredux')
    [98684]
    >>> findexe('python')
    [16644, 43756, 82326, 88852, 98684]

    """
    pids = []
    for proc in psutil.process_iter():
        pinfo = proc.as_dict(attrs=['pid', 'cmdline'])
        cl = pinfo['cmdline']
        if not cl:
            continue
        else:
            arg1 = cl[0]
        try:
            arg2 = cl[1]
        except IndexError:
            arg2 = ''

        subarg1 = os.path.split(arg1)[1].strip()
        subarg2 = os.path.split(arg2)[1].strip() if arg2 else arg2
        if exe == subarg1 or exe == subarg2:
            pids.append(pinfo['pid'])

    return pids
