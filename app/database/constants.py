'''
constant values used in various places
'''

class LogLevel:
    ''' logging level types '''
    INFO = 0
    WARN = 1
    CRIT = 2

TIME_FORMAT = '%Y-%m-%d %H-%M-%S'

class Primality:
    ''' primality constants '''
    UNKNOWN = -1
    COMPOSITE = 0
    PROBABLE = 1
    PRIME = 2
