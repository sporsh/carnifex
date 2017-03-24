import sys
from twisted.trial.unittest import TestCase
from .mocks import MockProcessInductor

stdout, stderr = 1, 2
fauxProcessData = [(stdout, b'some output'),
                   (stderr, b'error message'),
                   (stdout, b'info message'),
                   (stderr, b'os failure')]

if sys.version_info.major >= 3:
    def tostr(text):
        return str(text, 'utf8')
else:
    def tostr(text):
        return text

class InductorTest(TestCase):
    def test_run(self):
        inductor = MockProcessInductor(None, fauxProcessData)
        result = inductor.run(command='foo')
        @result.addCallback
        def check_result(result):
            expected_stdout = b''.join([data for fd, data in fauxProcessData
                                        if fd is stdout])
            expected_stderr = b''.join([data for fd, data in fauxProcessData
                                        if fd is stderr])
            expected_result = (
                tostr(expected_stdout), tostr(expected_stderr), 0)
            self.assertEqual(result, expected_result)
        return result

    def test_getOutput(self):
        inductor = MockProcessInductor(None, fauxProcessData)
        output = inductor.getOutput(command='foo')
        @output.addCallback
        def check_output(result):
            expected_stdout = b''.join([data for fd, data in fauxProcessData
                                        if fd is stdout])
            self.assertEqual(result, tostr(expected_stdout))
        return output

    def test_getExitCode(self):
        expectedExitCode = 47
        inductor = MockProcessInductor(None, fauxProcessData, exitCode=expectedExitCode)
        output = inductor.getExitCode(command='foo')
        @output.addCallback
        def checkExitCode(exitCode):
            self.assertEqual(exitCode, expectedExitCode)
        return output
