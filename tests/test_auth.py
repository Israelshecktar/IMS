import unittest
from app import app, db
from models import User

class AuthTestCase(unittest.TestCase):
    def setUp(self):
        app.config.from_object('config_test.TestConfig')
        self.app = app.test_client()
        with app.app_context():
            db.create_all()
            # Create a test user
            user = User(username='testuser', email='testuser@example.com', role='admin')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_login_success(self):
        response = self.app.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect to dashboard

    def test_login_failure(self):
        response = self.app.post('/login', data={
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertIn(b'Invalid username or password', response.data)

    def test_logout(self):
        self.app.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        })
        response = self.app.get('/logout')
        self.assertEqual(response.status_code, 302)  # Redirect to login

if __name__ == '__main__':
    unittest.main()
