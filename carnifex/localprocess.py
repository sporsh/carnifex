"""
@author: Geir Sporsheim
@license: see LICENCE for details
"""

from carnifex.inductor import ProcessInductor
from carnifex.command import PosixCommand
from twisted.internet import defer


class LocalProcessInductor(ProcessInductor):
    """Uses a twisted reactor to spawn processes locally.
    """
    def __init__(self, reactor):
        self.reactor = reactor

    def execute(self, processProtocol, command, env={},
                path=None, uid=None, gid=None, usePTY=0, childFDs=None):
        posixCommand = (command if isinstance(command, PosixCommand)
                                else PosixCommand(command))

        process = self.reactor.spawnProcess(processProtocol,
                                            posixCommand.executable,
                                            posixCommand.args,
                                            env, path, uid, gid,
                                            usePTY, childFDs)

        return defer.succeed(process)
