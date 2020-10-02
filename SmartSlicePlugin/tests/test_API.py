import unittest
from unittest.mock import MagicMock, patch

from typing import Callable

from UM.PluginRegistry import PluginRegistry
from UM.Application import Application

import pywim

from SmartSliceTestCase import _SmartSliceTestCase

class MockJob():
    def init(self):
        self.status = None
        self.canceled = False
        self.api_job_id = None
        self.id = None
        self.errors = []

    def setError(self, error):
        errorMessage = MockError()
        errorMessage.message = "Error occurred!"
        self.errors = [errorMessage]

class MockError():
    def init(self):
        self.error = ""
        self.message = ""

class MockThor():
    def init(self):
        self._token = None
        self._active_connection = True
        self._subscription = None
        self._job_test = None

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
        job = MockJob()
        job.status = pywim.http.thor.JobInfo.Status.queued
        job.api_job_id = "queued"
        job.id = "queued"
        return 200, job

    def smartslice_job_wait(self, jobID, timeout: int = 600, callback: Callable[[object], bool] = None):
        job = MockJob()
        if jobID == "finished":
            job.status = pywim.http.thor.JobInfo.Status.finished
            job.id = "finished"
            return 200, job
        elif jobID == "running":
            job.status = pywim.http.thor.JobInfo.Status.running
            job.id = self._job_test
            return 200, job
        elif jobID == "failed":
            job.status = pywim.http.thor.JobInfo.Status.failed
            job.id = "failed"
            errorMessage = MockError()
            errorMessage.message = "Job Failed!"
            job.errors = [errorMessage]
            return 200, job
        elif jobID == "queued":
            job.status = pywim.http.thor.JobInfo.Status.queued
            job.id = "running"
            return 200, job
        elif jobID == "crashed":
            job.status = pywim.http.thor.JobInfo.Status.crashed
            job.id = "crashed"
            return 200, job
        else:
            return 500, None

    def smartslice_job_abort(self, job_id):
        if job_id == "goodCancel":
            return 200, None
        else:
            error = MockError()
            error.error = "Failed to abort job!"
            return 400, error

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
        mockConnector.cancelCurrentJob = MagicMock()
        cls._api = SmartSliceAPIClient(mockConnector)
        cls._api._client = MockThor()

        #cls._preferences = Application.getInstance().getPreferences()

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self._api._login_username = None
        self._api._login_password = None
        self._api._error_message = None
        self._api._client._active_connection = True
        self._api._client._subscription = None
        self._api._client._job_test = "finished"

        self._api._app_preferences.removePreference(self._api._username_preference)
        self._api._app_preferences.addPreference(self._api._username_preference, "old@email.com")

    def tearDown(self):
        pass

    def test_00_check_token_create(self):
        self._api._token = "good"
        self._api._createTokenFile()

        self._api._token = "cleared"
        self._api._getToken()

        self.assertIsNotNone(self._api._token)
        self.assertEqual(self._api._token, "good")

    def test_01_check_token_good(self):
        self._api._checkToken()

        self.assertEqual(self._api._client._token, "good")

    def test_02_check_token_bad(self):
        self._api._token = None
        self._api._checkToken()

        self.assertNotEqual(self._api._client._token, "good")

    def test_03_login_success(self):
        self._api._login_username = "good@email.com"
        self._api._login_password = "goodpass"

        self.assertFalse(self._api.logged_in)

        self._api._login()

        self.assertFalse(self._api.badCredentials)
        self.assertEqual(self._api._login_password, "")
        self.assertEqual(self._api._app_preferences.getValue(self._api._username_preference), self._api._login_username)
        self.assertEqual(self._api._token, "good")
        self.assertTrue(self._api.logged_in)

    def test_04_login_credentials_failure(self):
        self._api._login_username = "bad"
        self._api._login_password = "nopass"

        self._api._login()

        self.assertTrue(self._api.badCredentials)
        self.assertEqual(self._api._login_password, "")
        self.assertNotEqual(self._api._app_preferences.getValue(self._api._username_preference), self._api._login_username)
        self.assertIsNone(self._api._token)
        self.assertFalse(self._api.logged_in)

    def test_05_login_connection_failure(self):
        self._api._login_username = "good@email.com"
        self._api._login_password = "goodpass"
        self._api._client._active_connection = False

        self._api._login()

        self.assertIsNotNone(self._api._error_message)
        self.assertEqual(self._api._error_message.getText(), "Internet connection issue:\nPlease check your connection and try again.")
        self.assertTrue(self._api._error_message.visible)
        self.assertFalse(self._api.logged_in)

    def test_06_logout(self):
        self._api._token = "good"
        self._api._loginPassword = "goodpass"

        self._api.logout()

        self.assertIsNone(self._api._token)
        self.assertIsNone(self._api._getToken())
        self.assertEqual(self._api._login_password, "")
        self.assertEqual(self._api._app_preferences.getValue(self._api._username_preference), "")

    def test_07_subscription_active(self):
        self._api._client._subscription = True

        subscription = self._api.getSubscription()

        self.assertEqual(subscription, "active")

    def test_08_subscription_inactive(self):
        self._api._client._subscription = False

        subscription = self._api.getSubscription()

        self.assertEqual(subscription, "inactive")

    def test_09_submit_job_success(self):
        #JobStatusTracker = MagicMock(MagicMock())
        job = MockJob()
        job.canceled = False
        job_data = object
        self._api._client._job_test = "finished"

        submitResult = self._api.submitSmartSliceJob(job, job_data)

        self.assertEqual(submitResult.status, pywim.http.thor.JobInfo.Status.finished)

    def test_10_submit_job_fail(self):
        job = MockJob()
        job.canceled = False
        job_data = object
        self._api._client._job_test = "failed"

        submitResult = self._api.submitSmartSliceJob(job, job_data)

        self.assertIsNone(submitResult)

    def test_11_cancel_job_success(self):
        self._api.cancelJob("goodCancel")

        self.assertIsNone(self._api._error_message)

    def test_12_cancel_job_fail(self):
        self._api.cancelJob("badCancel")

        self.assertIsNotNone(self._api._error_message)
        self.assertEqual(self._api._error_message.getText(), "SmartSlice Server Error (400: Bad Request):\nFailed to abort job!")
        self.assertTrue(self._api._error_message.visible)