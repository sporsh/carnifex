from twisted.trial.unittest import TestCase
from carnifex.inductor import ProcessInductor
from twisted.python import failure
from twisted.internet.error import ProcessDone

stdout_data = ['command output', 'info message']
stderr_data = ['error message', 'system failure']
result_status = 0


class MockProcessInductor(ProcessInductor):
    def execute(self, processProtocol, executable, args=None):
        for data in stdout_data:
            processProtocol.outReceived(data)
        for data in stderr_data:
            processProtocol.errReceived(data)
        reason = failure.Failure(ProcessDone(status=result_status))
        processProtocol.processEnded(reason)


class InductorTest(TestCase):
    def test_run(self):
        inductor = MockProcessInductor()
        result = inductor.run(executable='foo')
        @result.addCallback
        def check_result(result):
            expected_result = (''.join(stdout_data),
                               ''.join(stderr_data),
                               result_status)
            self.assertEqual(result, expected_result)
        return result

    def test_getOutput(self):
        inductor = MockProcessInductor()
        output = inductor.getOutput(executable='foo')
        @output.addCallback
        def check_output(result):
            expected_result = ''.join(stdout_data)
            self.assertEqual(result, expected_result)
        return output

    def test_getExitStatus(self):
        inductor = MockProcessInductor()
        output = inductor.getExitStatus(executable='foo')
        @output.addCallback
        def check_output(result):
            expected_result = 0
            self.assertEqual(result, expected_result)
        return output
