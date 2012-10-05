from twisted.trial.unittest import TestCase
from carnifex.process import ReactorProcessFactory
from twisted.internet import reactor
from carnifex.inductor import ProcessInductor


class InductorTest(TestCase):
    def test_real_run(self):
        executable = 'echo'
        echo_text = "hello world!"
        expected_stdout = echo_text + '\n'

        processFactory = ReactorProcessFactory(reactor)
        inductor = ProcessInductor(processFactory)
        result = inductor.run(executable, args=(executable, echo_text))
        @result.addCallback
        def check_result(result):
            expected_result = (expected_stdout, '', 0)
            self.assertEqual(result, expected_result)
        return result
