"""
@author: Geir Sporsheim
@license: see LICENCE for details
"""

def attr_string(filterKeys=(), filterValues=(), **kwargs):
    return ', '.join([str(k)+'='+repr(v) for k, v in kwargs.iteritems() if k not in filterKeys and v not in filterValues])
