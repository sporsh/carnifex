class ProcessFactory(object):
    """Class that encapsulate functionality to spawn processes
    """
    def spawnProcess(self, processProtocol, executable, args=(), env={},
                     path=None, uid=None, gid=None, usePTY=0, childFDs=None):
        raise NotImplementedError()
