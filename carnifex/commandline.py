import shlex

def parseCommandLine(commandLine, **kwargs):
    """Utility method for generating arguments for executing a command.
    In essence, this will generate the 'executable' and 'args' arguments for you.

    @param commandLine: The command line string to parse into arguments
    @param kwargs: Additional arguments for execution (eg. 'env', 'uid', etc.)
    """
    #TODO: Make this parse redirection of file descriptors (i.e. 2>&1 etc.) to a childFDs map?
    args = shlex.split(commandLine)
    kwargs['executable'] = args[0]
    kwargs['args'] = args
    return kwargs
