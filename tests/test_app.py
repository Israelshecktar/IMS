import unittest
from app import app, db
from models import User

class RegisterTestCase(unittest.TestCase):
    def setUp(self):
        app.config.from_object('config_test.TestConfig')
        self.app = app.test_client()
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_register_success(self):
        response = self.app.post('/register', data={
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'password123',
            'role': 'admin'
        })
        self.assertEqual(response.status_code, 302)  # Redirect to login
        user = User.query.filter_by(username='testuser').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'testuser@example.com')

    def test_register_missing_password(self):
        response = self.app.post('/register', data={
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': '',
            'role': 'admin'
        })
        self.assertIn(b'Password cannot be empty', response.data)

    def test_register_invalid_role(self):
        response = self.app.post('/register', data={
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'password123',
            'role': 'invalid_role'
        })
        self.assertIn(b'Invalid role selected', response.data)

    def test_register_existing_username(self):
        with app.app_context():
            user = User(username='testuser', email='testuser@example.com', role='admin')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()

        response = self.app.post('/register', data={
            'username': 'testuser',
            'email': 'newemail@example.com',
            'password': 'password123',
            'role': 'admin'
        })
        self.assertIn(b'Username already exists', response.data)

if __name__ == '__main__':
    unittest.main()
