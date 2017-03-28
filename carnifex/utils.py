"""
@author: Geir Sporsheim
@license: see LICENCE for details
"""

def attr_string(filterKeys=(), filterValues=(), **kwargs):
    """Build a string consisting of 'key=value' substrings for each keyword
    argument in :kwargs:

    @param filterKeys: list of key names to ignore
    @param filterValues: list of values to ignore (e.g. None will ignore all
                         key=value pairs that has that value.
    """
    return ', '.join([str(k)+'='+repr(v) for k, v in kwargs.items()
                      if k not in filterKeys and v not in filterValues])
