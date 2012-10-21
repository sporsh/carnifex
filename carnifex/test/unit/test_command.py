from twisted.trial.unittest import TestCase
from carnifex.command import PosixCommand
from carnifex.ssh.command import SSHCommand

class PosixCommandTest(TestCase):
    def test_posix_command_from_command_line(self):
        executable = 'command'
        args = ['-arg', 'value', '--extra=something']
        commandLine = "%s %s" % (executable, ' '.join(args))
        posixCommand = PosixCommand(commandLine)
        self.assertEqual(posixCommand.executable, executable)
        self.assertEqual(posixCommand.args, [executable]+args)

    def test_posix_command_from_args(self):
        args = ['command', '-arg', 'value', '--extra=something']
        posixCommand = PosixCommand(args)
        self.assertEqual(posixCommand.executable, args[0])
        self.assertEqual(posixCommand.args, args)

    def test_posix_command_from_executable_and_args(self):
        executable = 'command'
        args = ['command', '-arg', 'value', '--extra=something']
        posixCommand = PosixCommand(executable, args)
        self.assertEqual(posixCommand.executable, executable)
        self.assertEqual(posixCommand.args, args)

    def test_posix_command_fix_args(self):
        executable = 'command'
        args = ['-arg', 'value', '--extra=something']
        posixCommand = PosixCommand(executable, args)
        self.assertEqual(posixCommand.executable, executable)
        self.assertEqual(posixCommand.args, [executable]+args)

    def test_posix_command_ambiguous(self):
        executable = 'command -ambiguous -args'
        args = ['command', '-arg', 'value', '--extra=something']
        self.failUnlessRaises(Exception, PosixCommand, executable, args)


class SSHCommandTest(TestCase):
    def test_ssh_command_with_precursor_and_path(self):
        sshCommand = SSHCommand('command', 'precursor', '/some/path')
        sshCommand.cd = 'CD'
        sshCommand.sep = '#'
        self.assertEqual(sshCommand.getCommandLine(),
                         'precursor#CD /some/path#command')
