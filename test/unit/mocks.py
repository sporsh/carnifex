from twisted.internet._baseprocess import BaseProcess
from carnifex.inductor import ProcessInductor
from twisted.internet.error import ProcessTerminated, ProcessDone


class MockProcess(BaseProcess):
    data = []
    write = data.append

    def run(self, fauxProcessData):
        for childFd, data in fauxProcessData:
            self.proto.childDataReceived(childFd, data)

    def terminate(self, signal):
        """Simulate that the process was terminated with a signal
        """
        self.processEnded((None, signal))

    def exit(self, exitCode):
        """Simulate that the process exited
        """
        self.processEnded((exitCode, None))

    def _getReason(self, status):
        exitCode, signal = status
        if exitCode or signal:
            return ProcessTerminated(exitCode, signal, status)
        return ProcessDone(status)


class MockProcessInductor(ProcessInductor):
    def __init__(self, reactor, fauxProcessData, exitCode=0):
        self.reactor = reactor
        self.fauxProcessData = fauxProcessData
        self._exitCode = exitCode

    def execute(self, processProtocol, executable, args=(), env={},
                path=None, uid=None, gid=None, usePTY=0, childFDs=None):
        process = MockProcess(processProtocol)
        process.run(self.fauxProcessData)
        processProtocol.makeConnection(process)
        process.exit(self._exitCode)
        return process
