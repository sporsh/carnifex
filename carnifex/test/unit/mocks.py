from twisted.internet._baseprocess import BaseProcess
from carnifex.inductor import ProcessInductor
from twisted.internet.error import ProcessTerminated, ProcessDone


class MockProcess(BaseProcess):
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
    def __init__(self, fauxProcessData):
        self.fauxProcessData = fauxProcessData

    def execute(self, processProtocol, executable, args=None):
        process = MockProcess(processProtocol)
        process.run(self.fauxProcessData)
        processProtocol.makeConnection(process)
        process.exit(0)
        return process
