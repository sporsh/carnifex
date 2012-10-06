from carnifex.process import ProcessFactory


class ReactorProcessFactory(ProcessFactory):
    """Use a twisted reactor to spawn processes locally.
    """
    def __init__(self, reactor):
        self.reactor = reactor

    def spawnProcess(self, processProtocol, executable, args=(), env={},
                     path=None, uid=None, gid=None, usePTY=0, childFDs=None):
        return self.reactor.spawnProcess(processProtocol, executable, args, env,
                                         path, uid, gid, usePTY, childFDs)
