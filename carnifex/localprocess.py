from carnifex.inductor import ProcessInductor


class LocalProcessInductor(ProcessInductor):
    """Uses a twisted reactor to spawn processes locally.
    """
    def __init__(self, reactor):
        self.reactor = reactor

    def execute(self, processProtocol, executable, args=None):
        args = args or (executable,)
        return self.reactor.spawnProcess(processProtocol, executable, args)
