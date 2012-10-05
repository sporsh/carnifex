class ProcessFactory(object):
    """Class that encapsulate functionality to spawn processes
    """
    def spawnProcess(self, processProtocol, executable, args=(), env={},
                     path=None, uid=None, gid=None, usePTY=0, childFDs=None):
        raise NotImplementedError()


class ReactorProcessFactory(ProcessFactory):
    def __init__(self, reactor):
        self.reactor = reactor

    def spawnProcess(self, processProtocol, executable, args=(), env={},
                     path=None, uid=None, gid=None, usePTY=0, childFDs=None):
        self.reactor.spawnProcess(processProtocol, executable, args, env,
                                  path, uid, gid, usePTY, childFDs)
