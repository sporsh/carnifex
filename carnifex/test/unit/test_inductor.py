from twisted.trial.unittest import TestCase
from carnifex.test.unit.mocks import MockProcessInductor

stdout, stderr = 1, 2
fauxProcessData = [(stdout, 'some output'),
                   (stderr, 'error message'),
                   (stdout, 'info message'),
                   (stderr, 'os failure')]


class InductorTest(TestCase):
    def test_run(self):
        inductor = MockProcessInductor(fauxProcessData)
        result = inductor.run(executable='foo')
        @result.addCallback
        def check_result(result):
            expected_stdout = ''.join([data for fd, data in fauxProcessData
                                       if fd is stdout])
            expected_stderr = ''.join([data for fd, data in fauxProcessData
                                       if fd is stderr])
            expected_result = (expected_stdout, expected_stderr, 0)
            self.assertEqual(result, expected_result)
        return result

    def test_getOutput(self):
        inductor = MockProcessInductor(fauxProcessData)
        output = inductor.getOutput(executable='foo')
        @output.addCallback
        def check_output(result):
            expected_stdout = ''.join([data for fd, data in fauxProcessData
                                       if fd is stdout])
            self.assertEqual(result, expected_stdout)
        return output

    def test_getExitStatus(self):
        inductor = MockProcessInductor(fauxProcessData)
        output = inductor.getExitStatus(executable='foo')
        @output.addCallback
        def check_output(result):
            expected_result = 0
            self.assertEqual(result, expected_result)
        return output
