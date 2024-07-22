import unittest
from flask import session
from app import app, db, User

class FlaskLoginTestCase(unittest.TestCase):

    def setUp(self):
        # Load the configuration from config.py
        app.config.from_object('config')
        app.config['SQLALCHEMY_DATABASE_URI'] = app.config['TEST_SQLALCHEMY_DATABASE_URI']
        app.config['TESTING'] = True
        self.app = app.test_client()
        
        # Create tables and add test data
        with app.app_context():
            db.create_all()
            user = User(username='testuser', email='test@example.com', role='admin')
            user.set_password('testpassword')
            db.session.add(user)
            db.session.commit()

    def test_login_route_get(self):
        # Test the GET request to the login route
        response = self.app.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data)

    def test_login_route_post_success(self):
        # Test the POST request to the login route with valid credentials
        response = self.app.post('/login', data=dict(username='testuser', password='testpassword'), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with self.app as client:
            with client.session_transaction() as sess:
                self.assertEqual(sess['username'], 'testuser')

    def test_login_route_post_invalid_credentials(self):
        # Test the POST request to the login route with invalid credentials
        response = self.app.post('/login', data=dict(username='testuser', password='wrongpassword'), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid credentials', response.data)
        with self.app as client:
            with client.session_transaction() as sess:
                self.assertNotIn('username', sess)

if __name__ == '__main__':
    unittest.main()
