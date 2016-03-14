# Making a traceback

import traceback, sys

def make_trace():
    """
    Returns a traceback.
    """
    return "".join(traceback.format_exception(*sys.exc_info()))

