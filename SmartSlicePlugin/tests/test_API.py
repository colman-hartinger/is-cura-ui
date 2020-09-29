import unittest
from unittest.mock import MagicMock, patch

from UM.PluginRegistry import PluginRegistry
from UM.Application import Application

from SmartSliceTestCase import _SmartSliceTestCase

class MockThor():
    def init(self):
        self._token = None
        self._active_connection = True

    def info(self):
        if self._active_connection:
            return 200, None
        else:
            raise Exception("Failed, no connection!")

    def whoami(self):
        if self._token == "good":
            return 200, None
        else:
            return 401, None

    def basic_auth_login(self, username, password):
        if username == "good@email.com" and password == "goodpass":
            self._token = "good"
            return 200, None
        elif username == "bad" or password == "bad":
            self._token = "bad"
            return 400, None
        else:
            self._token = "bad"
            return 404, None

    def get_token(self):
        return self._token

class test_API(_SmartSliceTestCase):
    @classmethod
    def setUpClass(cls):
        from SmartSlicePlugin.SmartSliceCloudConnector import SmartSliceAPIClient

        mockConnector = MagicMock()
        mockConnector.extension = MagicMock(MagicMock())
        mockConnector.extension.metadata = MagicMock()
        cls._api = SmartSliceAPIClient(mockConnector)
        cls._api._client = MockThor()

        #cls._preferences = Application.getInstance().getPreferences()

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self._api._login_username = None
        self._api._login_password = None
        self._api._client._active_connection = True

        self._api._app_preferences.removePreference(self._api._username_preference)
        self._api._app_preferences.addPreference(self._api._username_preference, "old@email.com")

    def tearDown(self):
        pass

    def test_0_login_success(self):
        self._api._login_username = "good@email.com"
        self._api._login_password = "goodpass"

        self._api._login()

        self.assertFalse(self._api.badCredentials)
        self.assertEqual(self._api._login_password, "")
        self.assertEqual(self._api._app_preferences.getValue(self._api._username_preference), self._api._login_username)
        self.assertEqual(self._api._token, "good")

    def test_1_login_credentials_failure(self):
        self._api._login_username = "bad"
        self._api._login_password = "nopass"

        self._api._login()

        self.assertTrue(self._api.badCredentials)
        self.assertEqual(self._api._login_password, "")
        self.assertNotEqual(self._api._app_preferences.getValue(self._api._username_preference), self._api._login_username)
        self.assertIsNone(self._api._token)

    def test_2_login_connection_failure(self):
        self._api._login_username = "good@email.com"
        self._api._login_password = "goodpass"
        self._api._client._active_connection = False

        self._api._login()

        self.assertIsNotNone(self._api._error_message)
        self.assertEqual(self._api._error_message.getText(), "Internet connection issue:\nPlease check your connection and try again.")
        self.assertTrue(self._api._error_message.visible)

    def test_3_logout(self):
        self._api._token = "good"
        self._api._loginPassword = "goodpass"

        self._api.logout()

        self.assertIsNone(self._api._token)
        self.assertIsNone(self._api._getToken())
        self.assertEqual(self._api._login_password, "")
        self.assertEqual(self._api._app_preferences.getValue(self._api._username_preference), "")