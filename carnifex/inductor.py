class ProcessInductor(object):
    """Creates and follow up processes of local or remotely executed commands.
    """

    def __init__(self, processFactory):
        self.processFactory = processFactory

    def execute(self, processProtocol, executable, args=None):
        """Form a command and start a process in the desired environment.
        """
        return self.processFactory.spawnProcess(processProtocol,
                                                executable,
                                                args or (executable,))
