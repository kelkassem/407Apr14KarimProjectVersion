from flask import Flask, request, jsonify, render_template, abort, redirect
from flask_mysqldb import MySQL
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your-secret-key'

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'weshill03'
app.config['MYSQL_DB'] = 'smoochez'
mysql = MySQL(app)

# Login Setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Role-based decorator
def role_required(*roles):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                return abort(403)
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper

# User Class
class User(UserMixin):
    def __init__(self, id, name, email, password, role):
        self.id = id
        self.name = name
        self.email = email
        self.password = password
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user_data = cur.fetchone()
    cur.close()
    if user_data:
        return User(*user_data)
    return None

# --- Routes ---

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user_data = cur.fetchone()
        cur.close()
        if user_data and check_password_hash(user_data[3], password):
            user = User(*user_data)
            login_user(user)
            print("🔐 Logged in:", user.email)
            return redirect('/admin')
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

# Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

# Home (Public - For Customers)
@app.route('/')
def home():
    return render_template('index.html')

# Admin Home (after login)
@app.route('/admin')
@login_required
def admin_home():
    return render_template('index.html')

# Public Customer Page (optional alias)
@app.route('/customer')
def customer_page():
    return render_template('index.html')

# Submit Custom Order
@app.route('/user', methods=['POST'])
def custom_order():
    if request.is_json:
        data = request.get_json()
        item_id = data['item_id']
        item_type = data['item_type']
        item_description = data['item_description']
        name = data['name']
        email = data['email']
        address_line1 = data['address1']
        address_line2 = data['address2']
        city = data['city']
        state = data['state']
        zip_code = data['zip']

        cur = mysql.connection.cursor()
        sql = """INSERT INTO orders (
            item_id, item_type, item_description, name, email,
            address_line1, address_line2, city, state, zip_code)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        cur.execute(sql, (item_id, item_type, item_description, name, email,
                          address_line1, address_line2, city, state, zip_code))
        mysql.connection.commit()
        cur.close()

        return jsonify(message="Order Request Successful"), 201
    return jsonify(error="Invalid Submission"), 400

# Admin View Orders
@app.route('/users', methods=['GET'])
@login_required
@role_required('Admin')
def get_orders():
    cur = mysql.connection.cursor()
    cur.execute("SELECT item_id, item_type, item_description, name, email FROM orders")
    orders = cur.fetchall()
    cur.close()

    order_dicts = []
    for order in orders:
        order_data = {
            'item_id': order[0],
            'item_type': order[1],
            'item_description': order[2],
            'name': order[3],
            'email': order[4]
        }
        order_dicts.append(order_data)

    return jsonify(order_dicts)

# Static Pages
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/gallery')
def gallery():
    return render_template('gallery.html')

@app.route('/custom-order')
def custom_order_page():
    return render_template('contact us.html')  # Keep exact filename

@app.route('/materials')
def materials():
    return render_template('materials.html')

if __name__ == '__main__':
    app.run(debug=True)
