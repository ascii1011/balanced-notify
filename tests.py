#!notify/bin/python
import os
import unittest

from config import basedir
from app import app, db
import simplejson as json

USER_ID = 1
TEST_NOTIFICATION = dict(
    message='Checkout this cool new feature on the Balanced dashboard',
    uid=USER_ID
)


class TestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        db['notifications'].remove()
        db['users'].remove()
        db['users'].insert(
            [{'email': 'app@balancedpayments.com',
              '_id': USER_ID},
             {'email': 'tests@balancedpayments.com'}])

    def tearDown(self):
        db['notifications'].remove()
        db['users'].remove()

    def assertStatus(self, response, status_code):
        """
        Helper method to check matching response status.

        :param response: Flask response
        :param status_code: response status code (e.g. 200)
        """
        self.assertEqual(response.status_code, status_code)


    def test_create_notification(self):
        TEST_NOTIFICATION['uid'] = USER_ID
        res = self.app.post(
            '/notification',
            data=TEST_NOTIFICATION,
            headers={'x-balanced-admin': '1'})
        data = json.loads(res.data)
        assert data['data'] and len(data['data']) >= 1
        self.assertStatus(res, 201)
        return data['data']

    def test_create_notification_unauthorized(self):
        TEST_NOTIFICATION['uid'] = USER_ID
        res = self.app.post(
            '/notification',
            data=TEST_NOTIFICATION)
        self.assertStatus(res, 401)

    def test_create_notification_not_admin_authorized(self):
        TEST_NOTIFICATION['uid'] = USER_ID
        res = self.app.post(
            '/notification',
            data=TEST_NOTIFICATION,
            headers={'x-balanced-user': USER_ID})
        self.assertStatus(res, 401)

    def test_create_multi_notification(self):
        TEST_NOTIFICATION.pop('uid', None)
        res = self.app.post(
            '/notification',
            data=TEST_NOTIFICATION,
            headers={'x-balanced-admin': '1'})
        data = json.loads(res.data)
        assert isinstance(data['data'], list) and len(data['data']) > 1
        self.assertStatus(res, 201)

    def test_get_notifications(self):
        notification_id = self.test_create_notification()
        res = self.app.get(
            '/notifications',
            headers={'x-balanced-user': USER_ID})
        assert TEST_NOTIFICATION.get('message') in res.data
        data = json.loads(res.data)
        assert notification_id == data['data'][0]['id']
        self.assertStatus(res, 200)

    def test_get_notifications_unauthorized(self):
        notification_id = self.test_create_notification()
        res = self.app.get(
            '/notifications')
        self.assertStatus(res, 401)

    def test_delete_notifications(self):
        notification_id = self.test_create_notification()
        res = self.app.delete(
            '/notification/' + notification_id,
            headers={'x-balanced-user': USER_ID})
        self.assertStatus(res, 204)
        self.test_get_no_notifications()

    def test_delete_notifications_unauthorized(self):
        notification_id = self.test_create_notification()
        res = self.app.delete(
            '/notification/' + notification_id)
        self.assertStatus(res, 401)

    def test_delete_notifications_another_user(self):
        notification_id = self.test_create_notification()
        res = self.app.delete(
            '/notification/' + notification_id,
            headers={'x-balanced-user': '5'})
        self.assertStatus(res, 403)

    def test_delete_notifications_random_id(self):
        res = self.app.delete(
            '/notification/1dnnn',
            headers={'x-balanced-user': '5'})
        self.assertStatus(res, 403)

    def test_get_no_notifications(self):
        res = self.app.get(
            '/notifications', headers={'x-balanced-user': USER_ID})
        assert '[]' in res.data
        self.assertStatus(res, 200)

    def test_get_users(self):
        res = self.app.get(
            '/users', headers={'x-balanced-admin': '1'})
        data = json.loads(res.data)
        assert isinstance(data['data'], list) and len(data['data']) > 1
        self.assertStatus(res, 200)

    def test_get_users_unauthorized(self):
        res = self.app.get(
            '/users')
        self.assertStatus(res, 401)

    def test_get_users_not_admin_authorized(self):
        res = self.app.get(
            '/users', headers={'x-balanced-user': '1'})
        self.assertStatus(res, 401)


if __name__ == '__main__':
    unittest.main()
