from twisted.trial.unittest import TestCase
from carnifex.inductor import ProcessInductor
from carnifex.process import ReactorProcessFactory
from twisted.python import failure
from twisted.internet.error import ProcessDone

stdout_data = ['command output', 'info message']
stderr_data = ['error message', 'system failure']
result_status = 0


class MockReactor(object):
    def spawnProcess(self, processProtocol, executable, args, env, path,
                     uid, gid, usePTY, childFDs):
        for data in stdout_data:
            processProtocol.outReceived(data)
        for data in stderr_data:
            processProtocol.errReceived(data)
        reason = failure.Failure(ProcessDone(status=result_status))
        processProtocol.processEnded(reason)


class InductorTest(TestCase):
    def test_run(self):
        processFactory = ReactorProcessFactory(MockReactor())
        inductor = ProcessInductor(processFactory)
        result = inductor.run(executable='foo')
        @result.addCallback
        def check_result(result):
            expected_result = (''.join(stdout_data),
                               ''.join(stderr_data),
                               result_status)
            self.assertEqual(result, expected_result)
        return result

    def test_getOutput(self):
        processFactory = ReactorProcessFactory(MockReactor())
        inductor = ProcessInductor(processFactory)
        output = inductor.getOutput(executable='foo')
        print "OUTPUT", output

    def test_getExitStatus(self):
        processFactory = ReactorProcessFactory(MockReactor())
        inductor = ProcessInductor(processFactory)
        output = inductor.getExitStatus(executable='foo')
        print "OUTPUT", output
