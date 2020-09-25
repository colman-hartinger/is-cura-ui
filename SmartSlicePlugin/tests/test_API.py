import unittest
from unittest.mock import MagicMock, patch

from UM.PluginRegistry import PluginRegistry
from UM.Application import Application

from SmartSliceTestCase import _SmartSliceTestCase
from ..SmartSliceCloudConnector import SmartSliceAPIClient

class MockThor():
    def init(self):
        self._token = None

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
            return 400, None
        else:
            return 404, None

    def get_token(self):
        return self._token

class SmartSliceAPITest(_SmartSliceTestCase):
    @classmethod
    def setUpClass(cls):
        pluginObject = PluginRegistry.getPluginObject("SmartSlice")
        cls._api = SmartSliceAPIClient(pluginObject.cloud)
        cls._api._client = MockThor()

        #cls._preferences = Application.getInstance().getPreferences()

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self._api._login_username = None
        self._api._login_password = None

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