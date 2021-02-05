from pathlib import Path

from objects.file import FileObject
from test.unit.analysis.analysis_plugin_test_class import AnalysisPluginTest

from ..code.password_file_analyzer import AnalysisPlugin, crack_hash

TEST_DATA_DIR = Path(__file__).parent / 'data'


class TestAnalysisPluginPasswordFileAnalyzer(AnalysisPluginTest):

    PLUGIN_NAME = 'users_and_passwords'

    def setUp(self):
        super().setUp()
        config = self.init_basic_config()
        self.analysis_plugin = AnalysisPlugin(self, config=config)

    def test_process_object_shadow_file(self):
        test_file = FileObject(file_path=str(TEST_DATA_DIR / 'passwd_test'))
        processed_object = self.analysis_plugin.process_object(test_file)
        results = processed_object.processed_analysis[self.PLUGIN_NAME]

        self.assertEqual(len(results), 14)
        for item in [
            'vboxadd:unix', 'mongodb:unix', 'clamav:unix', 'pulse:unix', 'johndoe:unix', 'max:htpasswd',
            'test:mosquitto', 'admin:htpasswd', 'root:unix', 'user:unix', 'user2:unix'
        ]:
            assert item in results
            assert item in results['summary']
        self._assert_pw_match(results, 'max:htpasswd', 'dragon')  # MD5 apr1
        self._assert_pw_match(results, 'johndoe:unix', '123456')
        self._assert_pw_match(results, 'test:mosquitto', '123456')
        self._assert_pw_match(results, 'admin:htpasswd', 'admin')  # SHA-1
        self._assert_pw_match(results, 'root:unix', 'root')  # DES
        self._assert_pw_match(results, 'user:unix', '1234')  # Blowfish / bcrypt
        self._assert_pw_match(results, 'user2:unix', 'secret')  # MD5

    def test_process_object_password_in_binary_file(self):
        test_file = FileObject(file_path=str(TEST_DATA_DIR / 'passwd.bin'))
        processed_object = self.analysis_plugin.process_object(test_file)
        results = processed_object.processed_analysis[self.PLUGIN_NAME]

        assert len(results) == 4
        for item in ['johndoe:unix', 'max:htpasswd']:
            assert item in results
            assert item in results['summary']
        self._assert_pw_match(results, 'johndoe:unix', '123456')
        self._assert_pw_match(results, 'max:htpasswd', 'dragon')

    @staticmethod
    def _assert_pw_match(results: dict, key: str, pw: str):
        user, type_ = key.split(':')
        assert 'type' in results[key]
        assert 'password-hash' in results[key]
        assert 'password' in results[key]
        assert results[key]['type'] == type_
        assert results[key]['password'] == pw
        assert results['tags'][f'{user}_{pw}']['value'] == f'Password: {user}:{pw}'


def test_crack_hash_failure():
    passwd_entry = [b'user', b'$6$Ph+uRn1vmQ+pA7Ka$fcn9/Ln3W6c6oT3o8bWoLPrmTUs+NowcKYa52WFVP5qU5jzadqwSq8F+Q4AAr2qOC+Sk5LlHmisri4Eqx7/uDg==']
    result_entry = {}
    assert crack_hash(b':'.join(passwd_entry[:2]), result_entry) is False
    assert 'ERROR' in result_entry


def test_crack_hash_success():
    passwd_entry = 'test:$dynamic_82$2c93b2efec757302a527be320b005a935567f370f268a13936fa42ef331cc7036ec75a65f8112ce511ff6088c92a6fe1384fbd0f70a9bc7ac41aa6103384aa8c$HEX$010203040506'
    result_entry = {}
    assert crack_hash(passwd_entry.encode(), result_entry, '--format=dynamic_82') is True
    assert 'password' in result_entry
    assert result_entry['password'] == '123456'
