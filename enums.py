# Enums used in the pipeline


def enum(*sequential):
    """
    Makes an enumerator type: http://stackoverflow.com/a/1695250/165544
    """
    enums = dict(zip(sequential, range(len(sequential))))
    enums['lookup'] = dict((value, key) for key, value in enums.iteritems())
    return type('Enum', (), enums)

# The possible statuses of a pipeline
Status = enum('Init', 'Parsing', 'Running', 'Done', 'Error', 'ParseError', 'Deleted')

# The possible message types from the pipeline
Message = enum('StatusChange', 'Increment')


def finished(status):
    """The statuses that signify a finished build"""
    return status == Status.Done or status == Status.Error or status == Status.ParseError
