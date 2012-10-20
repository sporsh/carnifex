import shlex
import pipes
from utils import attr_string

def parseCommandLine(commandLine, **kwargs):
    """Utility method for generating arguments for executing a command.
    In essence, this will generate the 'executable' and 'args' arguments for you.

    @param commandLine: The command line string to parse into arguments
    @param kwargs: Additional arguments for execution (eg. 'env', 'uid', etc.)
    """
    #TODO: Make this parse redirection of file descriptors (i.e. 2>&1 etc.) to a childFDs map?
    args = shlex.split(commandLine)
    kwargs['executable'] = args[0]
    kwargs['args'] = args
    return kwargs


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
    fixArgs = True

    def __init__(self, executable, *args):
        self.executable = executable
        self.args = list(args) or [executable]

        # Make sure args[0] is the executable if the fixArgs flag is set:
        if self.fixArgs and args and not executable in args[0]:
            self.args.insert(0, executable)

    def getCommandLine(self):
        """Correctly quote the arguments and concatenate into one command line
        """
        return ' '.join(pipes.quote(arg) for arg in self.args)

    def __str__(self):
        return self.getCommandLine()


class SSHCommand(Command):
    def getCommandLine(self, precursor=None, path=None, cd='cd', sep=';'):
        """
        @param precursor: Precursor to the command line (eg. 'source /etc/profile')
        @param cd: The command used to change working directory (usually 'cd')
        @param sep: Syntax for separating several commands in one command line.
                    Usually '&&' or ;' for bash like command lines.
        """
        commandLine = precursor + sep if precursor else ''
        commandLine += cd + ' ' + path + sep if path else ''
        commandLine += str(self.command)
        return commandLine
