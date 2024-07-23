import unittest
from app import app, db
from models import User, Inventory

class InventoryTestCase(unittest.TestCase):
    def setUp(self):
        app.config.from_object('config_test.TestConfig')
        self.app = app.test_client()
        with app.app_context():
            db.create_all()
            # Create a test user and log them in
            user = User(username='testuser', email='testuser@example.com', role='admin')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            self.app.post('/login', data={
                'username': 'testuser',
                'password': 'password123'
            })

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_view_full_inventory(self):
        response = self.app.get('/view_full_inventory')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Inventory Items', response.data)

    def test_add_inventory_success(self):
        response = self.app.post('/add_inventory', data={
            'material': 'Material1',
            'product_name': 'Product1',
            'total_litres': '100',
            'date_received': '2024-07-23',
            'best_before_date': '2025-07-23',
            'location': 'Warehouse1'
        })
        self.assertEqual(response.status_code, 302)  # Redirect to dashboard
        inventory_item = Inventory.query.filter_by(material='Material1').first()
        self.assertIsNotNone(inventory_item)
        self.assertEqual(inventory_item.product_name, 'Product1')

    def test_take_inventory_success(self):
        with app.app_context():
            inventory_item = Inventory(
                material='Material1',
                product_name='Product1',
                total_litres=100,
                date_received='2024-07-23',
                best_before_date='2025-07-23',
                location='Warehouse1'
            )
            db.session.add(inventory_item)
            db.session.commit()

        response = self.app.post('/take_inventory', data={
            'material': 'Material1',
            'quantity': '50'
        })
        self.assertEqual(response.status_code, 302)  # Redirect to take_inventory
        inventory_item = Inventory.query.filter_by(material='Material1').first()
        self.assertEqual(inventory_item.total_litres, 50)

if __name__ == '__main__':
    unittest.main()
