"""
@author: Geir Sporsheim
@license: see LICENCE for details
"""

from carnifex.command import PosixCommand

class SSHCommand(PosixCommand):
    """Representation of a command to send to a remote machine for execution.

    @ivar cd:: The command used to change working directory (usually 'cd')
    @ivar sep: Operator to join the precursor, cd command and command line
               Usually ';' (or '&&') for bash like command lines.
    """

    cd = 'cd'
    sep = ';'

    def __init__(self, command, precursor=None, path=None):
        """
        @param precursor: Precursor to the command line (eg. 'source /etc/profile')
        @param path: The path to change directory to before execution
        """
        PosixCommand.__init__(self, command)
        self.precursor = precursor
        self.path = path

    def getCommandLine(self):
        """Insert the precursor and change directory commands
        """
        commandLine = self.precursor + self.sep if self.precursor else ''
        commandLine += self.cd + ' ' + self.path + self.sep if self.path else ''
        commandLine += PosixCommand.getCommandLine(self)
        return commandLine
