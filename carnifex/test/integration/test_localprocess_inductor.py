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

    def test_real_run_unknown_command(self):
        executable = 'thiscommandshouldnotexist'

        inductor = LocalProcessInductor(reactor)
        result = inductor.run(executable)
        @result.addCallback
        def check_result(result):
            stdout, stderr, code = result
            self.assertEqual(stdout, '')
            self.assertNotEqual(stderr, '')
            self.assertNotEqual(code, 0)
        return result

    def test_getExitStatus_false(self):
        inductor = LocalProcessInductor(reactor)
        result = inductor.getExitStatus('false')
        @result.addCallback
        def check_result(result):
            self.assertNotEqual(result, 0, "The 'false' command should "
                                "exit with a nonzero code")
        return result

    def test_getExitStatus_true(self):
        inductor = LocalProcessInductor(reactor)
        result = inductor.getExitStatus('true')
        @result.addCallback
        def check_result(result):
            self.assertEqual(result, 0, "The 'true' command should "
                             "exit with code 0")
        return result
