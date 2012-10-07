from twisted.trial.unittest import TestCase
from carnifex.localprocess import LocalProcessInductor
from twisted.internet import reactor


class InductorTest(TestCase):
    def test_real_run(self):
        executable = 'echo'
        echo_text = "hello world!"
        expected_stdout = echo_text + '\n'

        inductor = LocalProcessInductor(reactor)
        result = inductor.run(executable, args=(executable, echo_text))
        @result.addCallback
        def check_result(result):
            expected_result = (expected_stdout, '', 0)
            self.assertEqual(result, expected_result)
        return result
