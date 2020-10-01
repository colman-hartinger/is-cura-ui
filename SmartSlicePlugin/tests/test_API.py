import unittest
from unittest.mock import MagicMock, patch

from UM.PluginRegistry import PluginRegistry
from UM.Application import Application

from SmartSliceTestCase import _SmartSliceTestCase

class MockThor():
    def init(self):
        self._token = None
        self._active_connection = True
        self._subscription = None

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

    def smartslice_subscription(self):
        if self._subscription:
            return 200, "active"
        elif not self._subscription:
            return 200, "inactive"
        else:
            return 429, None

    def new_smartslice_job(self, threemf):
        job = object
        job.status = 102
        return 200, job

    def get_token(self):
        return self._token

    def set_token(self, token):
        self._token = token

class test_API(_SmartSliceTestCase):
    @classmethod
    def setUpClass(cls):
        from SmartSlicePlugin.SmartSliceCloudConnector import SmartSliceAPIClient

        mockConnector = MagicMock()
        mockConnector.status = MagicMock()
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
        self._api._client._subscription = None

        self._api._app_preferences.removePreference(self._api._username_preference)
        self._api._app_preferences.addPreference(self._api._username_preference, "old@email.com")

    def tearDown(self):
        pass

    def test_0_check_token_create(self):
        self._api._token = "good"
        self._api._createTokenFile()

        self._api._token = "cleared"
        self._api._getToken()

        self.assertIsNotNone(self._api._token)
        self.assertEqual(self._api._token, "good")

    def test_1_check_token_good(self):
        self._api._checkToken()

        self.assertEqual(self._api._client._token, "good")

    def test_2_check_token_bad(self):
        self._api._token = None
        self._api._checkToken()

        self.assertNotEqual(self._api._client._token, "good")

    def test_3_login_success(self):
        self._api._login_username = "good@email.com"
        self._api._login_password = "goodpass"

        self.assertFalse(self._api.logged_in)

        self._api._login()

        self.assertFalse(self._api.badCredentials)
        self.assertEqual(self._api._login_password, "")
        self.assertEqual(self._api._app_preferences.getValue(self._api._username_preference), self._api._login_username)
        self.assertEqual(self._api._token, "good")
        self.assertTrue(self._api.logged_in)

    def test_4_login_credentials_failure(self):
        self._api._login_username = "bad"
        self._api._login_password = "nopass"

        self._api._login()

        self.assertTrue(self._api.badCredentials)
        self.assertEqual(self._api._login_password, "")
        self.assertNotEqual(self._api._app_preferences.getValue(self._api._username_preference), self._api._login_username)
        self.assertIsNone(self._api._token)
        self.assertFalse(self._api.logged_in)

    def test_5_login_connection_failure(self):
        self._api._login_username = "good@email.com"
        self._api._login_password = "goodpass"
        self._api._client._active_connection = False

        self._api._login()

        self.assertIsNotNone(self._api._error_message)
        self.assertEqual(self._api._error_message.getText(), "Internet connection issue:\nPlease check your connection and try again.")
        self.assertTrue(self._api._error_message.visible)
        self.assertFalse(self._api.logged_in)

    def test_6_logout(self):
        self._api._token = "good"
        self._api._loginPassword = "goodpass"

        self._api.logout()

        self.assertIsNone(self._api._token)
        self.assertIsNone(self._api._getToken())
        self.assertEqual(self._api._login_password, "")
        self.assertEqual(self._api._app_preferences.getValue(self._api._username_preference), "")

    def test_7_subscription_active(self):
        self._api._client._subscription = True

        subscription = self._api.getSubscription()

        self.assertEqual(subscription, "active")

    def test_8_subscription_inactive(self):
        self._api._client._subscription = False

        subscription = self._api.getSubscription()

        self.assertEqual(subscription, "inactive")

    def test_9_submit_job_success(self):
        #JobStatusTracker = MagicMock(MagicMock())
        pass

    def test_10_submit_job_fail(self):
        pass

    def test_11_submit_job_queued(self):
        pass

    def test_12_cancel_job_success(self):
        pass

    def test_13_cancel_job_fail(self):
        pass