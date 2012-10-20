from carnifex.inductor import ProcessInductor
from commandline import createPosixCommand, PosixCommand


class LocalProcessInductor(ProcessInductor):
    """Uses a twisted reactor to spawn processes locally.
    """
    def __init__(self, reactor):
        self.reactor = reactor

    def createCommand(self, commandLine=None, executable=None, args=None):
        if commandLine and not executable and not args:
            return createPosixCommand(commandLine)
        elif executable:
            return PosixCommand(executable, *args)

    def execute(self, processProtocol, command, env={},
                path=None, uid=None, gid=None, usePTY=0, childFDs=None):
        if isinstance(command, basestring):
            command = createPosixCommand(command)
        executable = command.executable
        args = command.args
        return self.reactor.spawnProcess(processProtocol, executable, args,
                                         env, path, uid, gid,
                                         usePTY, childFDs)
