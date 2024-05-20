''' module for testing app '''
import unittest
from datetime import date
from app import app, db, Fruit, Userz

class BasicTests(unittest.TestCase):

    def setUp(self):
        """Set up test environment."""
        app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:root@localhost/mydatabase'
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()

        db.create_all()  # Create all tables

        # Insert a sample fruit into the database for testing
        self.sample_fruit = Fruit(
            name='Apple',
            quantity=10,
            expiry_date=date(2024, 12, 31),
            days_remaining=30,
            buying_price=0.50,
            selling_price=1.00,
            profit=5.00,
            loss=0.00
        )
        db.session.add(self.sample_fruit)

        self.sample_user = Userz(
            username='testuser',
            email='testuser@example.com',
            password='securepassword',
            password_reset_token='resettoken123'
        )
        db.session.add(self.sample_user)

        db.session.commit()

    def tearDown(self):
        """Clean up after each test."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_home_page(self):
        """Test home page is accessible."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_fruit_creation(self):
        """Test if the fruit was created properly."""
        fruit = Fruit.query.filter_by(name='Apple').first()
        self.assertIsNotNone(fruit)
        self.assertEqual(fruit.name, 'Apple')
        self.assertEqual(fruit.quantity, 10)
        self.assertEqual(fruit.expiry_date, date(2024, 12, 31))

    
    def test_user_creation(self):
        """Test if the user was created properly."""
        user = Userz.query.filter_by(username='testuser').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'testuser@example.com')
        self.assertEqual(user.password, 'securepassword')
        self.assertEqual(user.password_reset_token, 'resettoken123')
    def test_get_data(self):
        """Test the /get_fruit route."""
        response = self.client.get('/get_fruit')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Apple', response.data)  # Check if 'Apple' is in the response
        self.assertIn(b'10', response.data)  # Check if quantity '10' is in the response
        self.assertIn(b'totalProfit', response.data)  # Check if total_profit is in the response
        #self.assertIn(b'totalLoss', response.data)  # Check if total_loss is in the response
        #self.assertRegex(response.data.decode(), r'var\s+totalProfit\s*=\s*5.0;')
        #self.assertRegex(response.data.decode(), r'var\s+totalLoss\s*=\s*0;')
    
    def test_delete_fruit(self):
        """Test the /delete_fruit/<int:fruit_id> route."""
        fruit = Fruit.query.filter_by(name='Apple').first()
        fruit_id = fruit.id
        response = self.client.post(f'/delete_fruit/{fruit_id}')
        self.assertEqual(response.status_code, 302)  # Check if the response is a redirect
        self.assertIsNone(Fruit.query.get(fruit_id))  # Check if the fruit is deleted

    def test_add_fruit(self):
        """Test the /add_fruit route."""
        response = self.client.post('/add_fruit', data={
            'name': 'Banana',
            'quantity': 20,
            'expiry_date': '2024-12-31',
            'buying_price': 0.30,
            'selling_price': 0.60
        })
        self.assertEqual(response.status_code, 302)  # Check if the response is a redirect
        fruit = Fruit.query.filter_by(name='Banana').first()
        self.assertIsNotNone(fruit)  # Check if the fruit was added
        self.assertEqual(fruit.quantity, 20)
        self.assertEqual(fruit.expiry_date, date(2024, 12, 31))
        self.assertEqual(fruit.buying_price, 0.3)
        self.assertEqual(fruit.selling_price, 0.6)
        self.assertEqual(fruit.profit, 6)  # (0.60 - 0.30) * 20 = 6
    
    def test_add_existing_fruit(self):
        """Test adding an existing fruit does not duplicate."""
        response = self.client.post('/add_fruit', data={
            'name': 'Apple',
            'quantity': 10,
            'expiry_date': '2024-12-31',
            'buying_price': 0.50,
            'selling_price': 1.00
        })
        self.assertEqual(response.status_code, 302)  # Check if the response is a redirect
        fruits = Fruit.query.filter_by(name='Apple').all()
        self.assertEqual(len(fruits), 1)  # Check if there's still only one Apple
    def test_update_fruit(self):
        """Test the /update_fruit route."""
        fruit = Fruit.query.filter_by(name='Apple').first()
        fruit_id = fruit.id
        response = self.client.post(f'/update_fruit/{fruit_id}', data={
            'name': 'Updated Apple',
            'quantity': 15
        })
        self.assertEqual(response.status_code, 302)  # Check if the response is a redirect
        updated_fruit = Fruit.query.get(fruit_id)
        self.assertEqual(updated_fruit.name, 'Updated Apple')
        self.assertEqual(updated_fruit.quantity, 15)
    def test_update_nonexistent_fruit(self):
        """Test updating a non-existent fruit returns a JSON message."""
        response = self.client.post('/update_fruit/9999', data={
            'name': 'Nonexistent Fruit',
            'quantity': 10
        })
        self.assertEqual(response.status_code, 200)  # Check if the response is OK
        self.assertIn(b'Fruit not found', response.data)  # Check if 'Fruit not found' message is in the response

    def test_index(self):
        """Test the / route."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<!DOCTYPE html>', response.data)  # Check if HTML content is in the response
        self.assertIn(b'<title>Add New Fruit</title>', response.data)  # Check if the title is in the response

    def test_table(self):
        """Test the /table route."""
        response = self.client.get('/table')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Apple', response.data)  # Check if the fruit name is in the response
        self.assertIn(b'10', response.data)  # Check if the fruit quantity is in the response

    def test_edit_fruit_form(self):
        """Test the /edit_fruit/<int:fruit_id> route."""
        # Test case where fruit exists
        response = self.client.get(f'/edit_fruit/{self.sample_fruit.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Apple', response.data)  # Check if the fruit name is in the response
        self.assertIn(b'10', response.data)  # Check if the fruit quantity is in the response

        # Test case where fruit does not exist
        response = self.client.get('/edit_fruit/999')
        self.assertEqual(response.status_code, 404)
        self.assertIn(b'Fruit not found', response.data)
    
    def test_signup_form(self):
        """Test the /signme route."""
        response = self.client.get('/signme')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<title>Document</title>', response.data)
    
    def test_signup_success(self):
        """Test successful signup."""
        response = self.client.post('/signup', data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'signup successful', response.data)

        # Check if the user is actually added to the database
        user = Userz.query.filter_by(username='newuser').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'newuser@example.com')

    def test_signup_username_exists(self):
        """Test signup with an existing username."""
        # Add a user to the database
        existing_user = Userz(username='existinguser', email='existinguser@example.com', password='password123')
        db.session.add(existing_user)
        db.session.commit()

        response = self.client.post('/signup', data={
            'username': 'existinguser',
            'email': 'newuser@example.com',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'username or email already exist', response.data)

    def test_signup_email_exists(self):
        """Test signup with an existing email."""
        # Add a user to the database
        existing_user = Userz(username='newuser', email='existingemail@example.com', password='password123')
        db.session.add(existing_user)
        db.session.commit()

        response = self.client.post('/signup', data={
            'username': 'newuser2',
            'email': 'existingemail@example.com',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'username or email already exist', response.data)

    def test_login_form(self):
        """Test rendering the login form."""
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data)

    def test_login_success(self):
        """Test successful login."""
        # Add a user to the database
        user = Userz(username='testuser', email='testuser@example.com', password='password123')
        db.session.add(user)
        db.session.commit()

        response = self.client.post('/login_user', data={
            'email': 'testuser@example.com',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect to /table
        #self.assertEqual(response.location, 'http://localhost/get_table')

if __name__ == '__main__':
    unittest.main()

