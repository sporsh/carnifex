import shlex
import pipes
from utils import attr_string


class Command(object):
    def __init__(self, command):
        """
        @param command: A command object (eg. a PosixCommand) or string
        """
        self.command = command

    def getCommandLine(self):
        return str(self.command)

    def __str__(self):
        return self.getCommandLine()

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, attr_string(**self.__dict__))


class PosixCommand(Command):
    """
    @ivar fixArgs: True if we should try to automatically fix args to include
                   the process name if it is missing.
    """
    fixArgs = True

    def __init__(self, executable, args=()):
        """
        @param executable: The program to execute. Should be full path
        @param args: Arguments to pass to the process. args[0] is the name
                     of the process (usually the same as the executable)
        """
        if isinstance(executable, basestring):
            parts = shlex.split(executable)
        elif hasattr(executable, '__getitem__'):
            parts = executable

        self.executable = parts[0]
        if args:
            assert len(parts) == 1, "Ambiguous executable and args"
        self.args = args or parts

        # Make sure args[0] is the executable if the fixArgs flag is set:
        if self.fixArgs and args and not executable in args[0]:
            self.args = [executable]
            self.args.extend(args)

    def getCommandLine(self):
        """Correctly quote the arguments and concatenate into one command line
        """
        return ' '.join(pipes.quote(arg) for arg in self.args)

    def __str__(self):
        return self.getCommandLine()


class SSHCommand(Command):
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
        Command.__init__(self, command)
        self.precursor = precursor
        self.path = path

    def getCommandLine(self):
        """Insert the precursor and change directory commands
        """
        commandLine = self.precursor + self.sep if self.precursor else ''
        commandLine += self.cd + ' ' + self.path + self.sep if self.path else ''
        commandLine += str(self.command)
        return commandLine
