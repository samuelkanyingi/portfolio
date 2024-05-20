# Import necessary libraries
from flask import Flask, jsonify,  render_template
from flask import request, redirect, flash, url_for, make_response
from io import BytesIO  # create in-memory binary streams.
import openpyxl  # read Excel files.
from flask_sqlalchemy import SQLAlchemy
import json
from flask_mail import Mail, Message  # import module for sending emails
# Import module for scheduling background tasks
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, date
from flask_migrate import Migrate  # Assist in database migrations
import secrets  # Import module for generating secure tokens

app = Flask(__name__)  # Create a Flask application instance

app.secret_key = 'your_secret_key'  # Secret key for the application
# Configure email sending using Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587  # Port number for the SMTP server
# Enable Transport Layer Security (TLS) for email communications
app.config['MAIL_USE_TLS'] = True
# Your Gmail username for authentication
app.config['MAIL_USERNAME'] = 'samuelkanyingi2016'
# App-specific password generated from Gmail for secure access
app.config['MAIL_PASSWORD'] = 'qqkrtntaclievmqj'
# Database URI for SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:root@localhost/mydatabase'
# Default sender email address for outgoing emails
app.config['MAIL_DEFAULT_SENDER'] = ('samuelkanyingi2016@gmail.com')
mail = Mail(app)  # Configure database migrations using Flask-Migrate

db = SQLAlchemy(app)  # Initialize SQLAlchemy
migrate = Migrate(app, db)


# Create a database model
class Fruit(db.Model):
    __tablename__ = 'fruit'  # Name of the database table
    id = db.Column(db.Integer, primary_key=True)  # New column for id
    name = db.Column(db.String(50), unique=True)  # New column for name
    quantity = db.Column(db.Integer)  # New column for quantity
    expiry_date = db.Column(db.Date)  # New column for expiration date
    days_remaining = db.Column(db.Integer)  # Remaining days to expiry
    buying_price = db.Column(db.Float)  # New column for buying price
    selling_price = db.Column(db.Float)  # New column for selling price
    profit = db.Column(db.Float)  # New column for profit
    loss = db.Column(db.Float)  # New column for loss

    def calculate_days_remaining(self):
        # Check if expiry_date is a string
        if isinstance(self.expiry_date, str):
            # Convert expiry_date string to datetime.date object
            self.expiry_date = datetime.strptime(self.expiry_date, '%Y-%m-%d').date()
            # If expiry_date is set (not None or empty)
        if self.expiry_date:
            today = date.today()  # Get today's date
            # Calculate the number of days remaining until the expiry_date
            self.days_remaining = (self.expiry_date - today).days
            db.session.commit()  # Save the calculated days


class Userz(db.Model):
    __tablename__ = 'userz'  # Name of the database table
    # Username of the user, limited to 50 characters
    id = db.Column(db.Integer, primary_key=True)
    # Username of the user, limited to 50 characters
    username = db.Column(db.String(50))
    # Email address of the user, limited to 50 characters
    email = db.Column(db.String(50))
    # Password of the user, stored as a string
    password = db.Column(db.String(50))
    # Password tokens of the user, stored as a string
    password_reset_token = db.Column(db.String(100))


def reset_ids():
    # Fetch all fruits from the database
    fruits = Fruit.query.all()

    # Reset the IDs sequentially
    for i, fruit in enumerate(fruits, start=1):
        fruit.id = i

    # Commit the changes
    db.session.commit()


@app.route('/get_fruit')
def get_data():
    # Query all the fruit records from the database
    fruits = Fruit.query.all()
    # Extract the names of all fruits
    names = [fruit.name for fruit in fruits]
    # Extract the quantities of all fruits
    quantities = [fruit.quantity for fruit in fruits]
    # Create a dictionary with names and quantities
    data = {'names': names, 'quantities': quantities}
    # Calculate the total profit by summing the profit values of all fruits
    total_profit = db.session.query(db.func.sum(Fruit.profit)).scalar() or 0
    # Calculate the total loss by summing the loss values of all fruits
    total_loss = db.session.query(db.func.sum(Fruit.loss)).scalar() or 0
    # Create a dictionary with total profit and total loss for pie chart data
    pie_chart_data = {'total_profit': total_profit, 'total_loss': total_loss}
    # Call a function to reset IDs
    reset_ids()
    # Render the 'chart.html' template with the data and pie chart data
    return render_template('chart.html',
                           data=data, pie_chart_data=pie_chart_data)


@app.route('/delete_fruit/<int:fruit_id>', methods=['POST', 'GET'])
def delete_fruit(fruit_id):
    # Retrieve the fruit record with the given fruit_id from the database
    fruit = Fruit.query.get(fruit_id)
    # Check if the fruit exists
    if fruit:
        db.session.delete(fruit)  # Delete the fruit record from the database
        db.session.commit()  # Commit the changes to the database

        reset_ids()  # Call a function to reset IDs
        return redirect('/table')  # Redirect to the '/table' route
    else:
        # Return a JSON response with a message if the fruit was not found
        return jsonify({'message': 'Fruit not found'})


@app.route('/update_fruit/<int:fruit_id>', methods=['GET', 'POST'])
def update_fruit(fruit_id):
    # Retrieve the fruit record with the given fruit_id from the database
    fruit = Fruit.query.get(fruit_id)
    # Check if the fruit exists
    if fruit:
        # Update the fruit's name with the value from the form
        fruit.name = request.form.get('name', fruit.name)
        # Update the fruit's quantity with the value from the form
        fruit.quantity = float(request.form.get('quantity', fruit.quantity))
        fruit.buying_price = float(request.form.get('buying_price', fruit.buying_price))
        fruit.selling_price = float(request.form.get('selling_price', fruit.selling_price))
        fruit.expiry_date = request.form.get('expiry_date', fruit.expiry_date)
        fruit.profit = (fruit.selling_price - fruit.buying_price) * fruit.quantity
        fruit.loss = 0 if fruit.profit >= 0 else -fruit.profit
        db.session.commit()  # Commit the changes to the database
        reset_ids()  # Call a function to reset IDs
        # Redirect to the '/table' route after successful update
        return redirect('/table')
    else:
        # Return a JSON response with a message if the fruit was not found
        return jsonify({'message': 'Fruit not found'})


@app.route('/addFruit', methods=['GET'])
def add_form():
    # Render the 'index.html' template when the root URL ('/addFruit') is accessed
    return render_template('index.html')

@app.route('/add_fruit', methods=['POST', 'GET'])
def add_fruit():
    if request.method == 'GET':
        return render_template('index.html')
    else:
    # Retrieve form data for the new fruit
        name = request.form['name']
        quantity = int(request.form['quantity'])
        expiry_date = request.form['expiry_date']
        buying_price = int(request.form['buying_price'])
        selling_price = int(request.form['selling_price'])
    

    # Check if a fruit with the same name already exists in the database
        existing_fruit = Fruit.query.filter_by(name=name).first()
        if existing_fruit:
        # If the fruit already exists, redirect to the '/table' route
        # without adding
            return redirect('/table')
    # Calculate the profit as
    # (selling price - buying price) * quantity, rounded to the nearest integer
        profit = (selling_price - buying_price) * quantity
    # Calculate the loss as 0 if profit is non-negative
    # otherwise as the absolute value of profit
        loss = 0 if profit >= 0 else -profit

    # Create a new Fruit instance with the provided data
        new_fruit = Fruit(
                      name=name, quantity=quantity, buying_price=buying_price,
                      selling_price=selling_price, expiry_date=expiry_date,
                      profit=profit, loss=loss)

    # Calculate the number of days remaining until
    # the expiry date for the new fruit
        new_fruit.calculate_days_remaining()
    # Add the new fruit to the database session
        db.session.add(new_fruit)
    # Commit the changes to save the new fruit to the database
        db.session.commit()
        reset_ids()  # Call a function to reset IDs

    # Redirect to the '/table' route after successful addition
        return redirect('/table')


@app.route('/', methods=['GET', 'POST'])
def index():
    # Render the 'index.html' template when the root URL ('/') is accessed
    return render_template('login.html')

@app.route('/table')
def table():
    # Retrieve all fruit records from the database
    fruits = Fruit.query.all()
    LOW_INVENTORY_THRESHOLD = 2  # Define a threshold for low inventory
    # Render the 'table.html' template with the list of fruits
    # and the low inventory threshold
    return render_template('table.html', fruits=fruits,
                           LOW_INVENTORY_THRESHOLD=LOW_INVENTORY_THRESHOLD)


@app.route('/edit_fruit/<int:fruit_id>', methods=['GET'])
def edit_fruit_form(fruit_id):
    # Retrieve the fruit record with the given fruit_id from the database
    fruit = Fruit.query.get(fruit_id)
    # Check if the fruit exists
    if fruit:
        # Render the 'edit_form.html' template with the fruit data
        return render_template('edit_form.html', fruit=fruit)
    else:
        # Handle the case where the fruit is not found with 404 status code
        return "Fruit not found", 404


@app.route('/signme', methods=['POST', 'GET'])
def signup_form():
    return render_template('signup.html')  # Render the 'signup.html' template


@app.route('/signup', methods=['POST'])
def signup():
    # Retrieve form data for username, email, and password
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']

    # Check if a user with the same username or email
    # already exists in the database
    if Userz.query.filter_by(username=username).first() or Userz.query.filter_by(email=email).first():
        # If a user with the same username or email exists
        # return an error message
        return "username or email already exist"

    db.create_all()  # Create all tables defined in the database models
    # Create a new user instance with the provied username,email, and password
    new_user = Userz(username=username, email=email, password=password)
    db.session.add(new_user)  # Add the new user to the database session
    db.session.commit()  # Commit the changes to the database
    # Return a success message indicating that the signup was successful
    return "signup successful"


@app.route('/login', methods=['POST', 'GET'])
def login_form():
    # Render the 'login.html' template when the root URL ('/login') is accessed
    return render_template('login.html')


@app.route('/login_user', methods=['POST'])
def login_user():
    # Retrieve email and password from the form data
    email = request.form.get('email')
    password = request.form.get('password')

    # Check if a user with the provided email and password
    # exists in the database
    if Userz.query.filter_by(email=email).first() and Userz.query.filter_by(password=password).first():
        # If a user with the provided email and password exists
        # redirect to the '/table' route
        return redirect('/table')
    else:
        # If the login details are invalid
        # flash an error message and redirect to the login form
        flash("Invalid login details")
        return redirect(url_for('login_form'))


@app.route('/forgot-password', methods=['GET'])
def forgot_password():
    # Render the 'forgot_password.html' template
    # when the route is accessed via a GET request
    return render_template('forgot_password.html')


def generate_token():
    # Generate a secure random token using secrets module
    return secrets.token_urlsafe(16)


@app.route('/forgot-password', methods=['POST'])
def send_password_reset_email():
    # Retrieve email from the form data
    email = request.form.get('email')

    # Check if email exists in the user database
    user = Userz.query.filter_by(email=email).first()
    if user:
        token = generate_token()  # Generate a password reset token
        # Update the user's password reset token in the database
        user.password_reset_token = token
        db.session.commit()  # commit  changes
        # Send the password reset link to the user's email
        send_password_reset_link(email, token)
        # Redirect the user to a page to check their email
        return redirect('/check-email')

    else:
        # If the email address is not found in the database
        # flash an error message and render the forgot password page again
        flash('Email address not found!', 'danger')
        return render_template('forgot_password.html')


@app.route('/check-email')
def check_email():
    # Flash a success message indicating that
    # the password reset link has been sent to the user's email
    flash('Password reset link has been sent to your email.'
          'Please check your inbox.', 'success')
    # Render the 'check_email.html' template
    return render_template('check_email.html')


@app.route('/reset-password/<token>', methods=['GET'])
def reset_password(token):
    # Render the 'reset_password.html' template and pass the token as context
    return render_template('reset_password.html', token=token)


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def update_password(token):
    # Initialize new_password to None
    new_password = None
    # If the request method is POST, retrieve email, new password
    # and token from the form data
    if request.method == 'POST':
        email = request.form['email']
        new_password = request.form['password']
        token = request.form['token']

        # Check if there's a user with the provided email and password
        # reset token
        user = Userz.query.filter_by(email=email, password_reset_token=token).first()
        if user:
            # If a user is found, update their password and reset
            # the password reset token
            user.password = new_password
            user.password_reset_token = None
            db.session.commit()
            # If a user is found, update their password and reset
            # the password reset token
            flash("Password updated successfully!", "success")
            return redirect('/login')
        else:
            # If no user is found with the provided email and token,
            # return an error message
            return "Invalid token!"


def send_password_reset_link(email, token):
    # Create a message object with the subject "Password Reset" and
    # the recipient's email address
    msg = Message("Password Reset", recipients=[email])
    # Set the body of the email message
    msg.body = f"To reset your password, click on the following link: https://web-02.samservices.tech/reset-password/{token}"
    # Send the email message
    mail.send(msg)


@app.route('/search', methods=['POST'])
def search():
    LOW_INVENTORY_THRESHOLD = 4  # Define a threshold for low inventory
    # Retrieve the search query from the form submission
    search_query = request.form['query']

    # Query the database to find items that match the search query
    matching_items = Fruit.query.filter(Fruit.name.ilike
                                        (f'%{search_query}%')).all()

    # Render the template with the matching items
    return render_template('table.html', fruits=matching_items,
                           LOW_INVENTORY_THRESHOLD=LOW_INVENTORY_THRESHOLD)


@app.route('/export', methods=['GET', 'POST'])
def export_excel():
    # Fetch all fruit data from the database
    fruit_data = Fruit.query.all()

    # Create a new Excel workbook
    wb = openpyxl.Workbook()
    ws = wb.active

    # Add column headers to the Excel sheet
    ws.append([
        "ID", "Name", "Quantity", "Days Remaining", "Buying Price (KES)",
        "Selling Price (KES)", "Profit/Loss (KES)"])

    # Add fruit data to the Excel sheet
    for fruit in fruit_data:
        ws.append([
            fruit.id, fruit.name, fruit.quantity, fruit.days_remaining,
            fruit.buying_price, fruit.selling_price, fruit.profit, fruit.loss])

    # Save Excel workbook to BytesIO buffer
    excel_data = BytesIO()
    wb.save(excel_data)
    excel_data.seek(0)

    # Create response with Excel data
    response = make_response(excel_data.getvalue())

    # Set response headers for downloading the Excel file
    response.headers['Content-Disposition'] = (
            'attachment; filename=fruit_inventory.xlsx')
    response.headers['Content-Type'] = (
            'application/vnd.openxmlformats-officedocument.'
            'spreadsheetml.sheet')
    return response


@app.route('/landing')
def land():
    # Render the 'landing.html' template
    return render_template('landing.html')


@app.route('/get_profit_data')
def get_profit_loss_data():
    # Query the database to calculate total profit and total loss
    total_profit = db.session.query(db.func.sum(Fruit.profit)).scalar() or 0
    total_loss = db.session.query(db.func.sum(Fruit.loss)).scalar() or 0
    # Render the 'chart.html' template with total profit and total loss data
    return render_template('chart.html',
                           total_profit=total_profit, total_loss=total_loss)


if __name__ == '__main__':
    '''
    If the script is executed directly by Python (not imported)
    Start the Flask application in debug mode, allowing for automatic reloading
    Of the application when changes are made to the source code
    '''
    app.run(debug=True, port=5000)
