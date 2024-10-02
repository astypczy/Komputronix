from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file,  jsonify
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required

import sqlite3
from datetime import datetime
from collections import namedtuple

import random
import string

def generate_serial_number():
    characters = string.ascii_letters + string.digits
    serial_number = ''.join(random.choice(characters) for _ in range(12))
    return serial_number

app = Flask(__name__, static_folder='static')
bcrypt = Bcrypt(app)
app.secret_key = "secret_key"

# Function to connect to the database
def get_db_conn():
    conn = sqlite3.connect('shop_DATABASE')
    conn.row_factory = sqlite3.Row
    return conn

# Home page
@app.route('/')
def index():
    conn = get_db_conn()
    products = conn.execute(f"SELECT * FROM ProductTypes ORDER BY product_id ASC LIMIT 3").fetchall()
    conn.close()
    return render_template('index.html', products=products)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# User model for Flask-Login
class User(UserMixin):
    def __init__(self, id):
        self.id = id

# Products page with pagination and sorting
@app.route('/products')
def products():
    page = request.args.get('page', default=1, type=int)
    limit = request.args.get('limit', default=10, type=int)
    sort = request.args.get('sort', default='product_id')
    category = request.args.get('category', default='')
    offset = (page - 1) * limit

    conn = get_db_conn()
    if(category):
    	products = conn.execute(f"SELECT * FROM ProductTypes WHERE category = '{category}' ORDER BY {sort} LIMIT ? OFFSET ?;", (limit, offset)).fetchall()
    	count = conn.execute(f"SELECT COUNT(*) FROM ProductTypes WHERE category = '{category}';").fetchone()[0]
    else:
    	products = conn.execute(f"SELECT * FROM ProductTypes ORDER BY {sort} LIMIT ? OFFSET ?;", (limit, offset)).fetchall()
    	count = conn.execute("SELECT COUNT(*) FROM ProductTypes;").fetchone()[0]
    categories = conn.execute("SELECT DISTINCT category FROM ProductTypes;").fetchall()
    conn.close()

    pages = count // limit + (count % limit > 0)
    return render_template('products.html', products=products, page=page, limit=limit, sort=sort, pages=pages, categories=categories, category=category,count=count)

@app.route('/images/<filename>')
def serve_image(filename):
    return send_file(filename, mimetype='image/jpg')

# Product page with description and adding to cart
@app.route('/product/<int:product_id>', methods=['GET', 'POST'])
def product(product_id):
    conn = get_db_conn()
    product = conn.execute("SELECT * FROM ProductTypes WHERE product_id=?", (product_id,)).fetchone()
    conn.close()

    if request.method == 'POST':
        quantity = request.form['quantity']
        flash(f"{quantity} {product['name']}(s) added to your cart.", 'success')
        return redirect(url_for('add_to_cart', id=product['product_id']))

    return render_template('product.html', product=product)

# Cart page
@app.route('/cart')
def cart():
    return render_template('cart.html')

# Order page
@app.route('/order', methods=['POST', 'GET'])
def order():
    conn = get_db_conn()
    order_id = conn.execute("SELECT * FROM Orders ORDER BY order_id DESC;").fetchone()[0]+1
    if request.method == 'POST':
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        name = request.form['name']
        surname = request.form['surname']
        mail = request.form['email']
        phone = request.form['phone']
        street = request.form['street']
        house_number = request.form['house_number']
        flat_number = request.form['flat_number']
        postal_code = request.form['postal_code']
        locality = request.form['locality']
        delivery = request.form['delivery']
        if(delivery == 'no'):
            streetD = request.form['streetD']
            house_numberD = request.form['house_numberD']
            flat_numberD = request.form['flat_numberD']
            postal_codeD = request.form['postal_codeD']
            localityD = request.form['localityD']
        else:
            streetD = request.form['street']
            house_numberD = request.form['house_number']
            flat_numberD = request.form['flat_number']
            postal_codeD = request.form['postal_code']
            localityD = request.form['locality']

        client_id = conn.execute("SELECT * FROM Clients ORDER BY client_ID DESC;").fetchone()[0]+1
        address_id = conn.execute("SELECT * FROM ClientAddresses ORDER BY address_ID DESC;").fetchone()[0]+1
        delivery_id = conn.execute("SELECT * FROM DeliveryAddresses ORDER BY delivery_ID DESC;").fetchone()[0]+1
	
        cart = session['cart']
        total = session['total']
       
        not_avaible = []
        tmp = {}
        for p in cart:
            avaible = conn.execute("SELECT amount FROM ProductTypes WHERE product_ID == ?;", (p['id'],)).fetchone()[0]
            if(avaible < p['quantity']):
                tmp['name'] = p['name']
                tmp['avaible'] = avaible
                not_avaible.append(tmp)
        if(not_avaible):
            return render_template('not_avaible.html', products=not_avaible)
       
        for p in cart:
           product = p['id']
           
           conn.execute("UPDATE ProductTypes SET amount = amount-? WHERE product_ID == ?;", (p['quantity'],product ))
           pieces = conn.execute("SELECT * FROM ProductElements WHERE product_ID == ? AND Ordered != 1 LIMIT ?;", (product, p['quantity'])).fetchall()
           for piece in pieces:
                conn.execute("INSERT INTO Orders VALUES (?, ?, ?, ?, 'Oczekuje');", (order_id, delivery_id, date, piece['element_id']))
                conn.execute("UPDATE ProductElements SET Ordered = 1 WHERE element_ID == ?;", (piece['element_id'], ))
           
        conn.execute("INSERT INTO Clients VALUES (?, ?, ?, ?, ?, ?, ?);", (client_id, address_id, order_id, phone, mail, name, surname)) 
        conn.execute("INSERT INTO ClientAddresses VALUES (?, ?, ?, ?, ?, ?);", (address_id, street, locality, postal_code, house_number, flat_number))
        conn.execute("INSERT INTO DeliveryAddresses VALUES (?, ?, ?, ?, ?, ?);", (address_id, streetD, localityD, postal_codeD, house_numberD, flat_numberD)) 
        conn.commit()
        conn.close()
        
        session['cart'] = []
        flash("Your order has been submitted. Thank you for shopping with us!", 'success')
        
        return redirect(url_for('order_confirmation', order_id=order_id))

    return render_template('order.html', order_id=order_id)
# Order confirmation page
@app.route('/order_confirmation/<int:order_id>', methods=['POST', 'GET'])
def order_confirmation(order_id):
    # Get the order details from the database
    conn = sqlite3.connect('shop_DATABASE')
    c = conn.cursor()
    c.execute('SELECT * FROM Orders WHERE order_id=?;', (order_id,))
    order = c.fetchone()
    c.execute('SELECT * FROM DeliveryAddresses WHERE delivery_id=?;', (order[1],))
    delivery = c.fetchone()
    conn.close()
    if(delivery[5]):
        delivery_address = delivery[1]+" "+delivery[4]+"/"+str(delivery[5])+", "+delivery[3]+" "+delivery[2]
    else:
        delivery_address = delivery[1]+" "+delivery[4]+", "+delivery[3]+" "+delivery[2]
    # Render the confirmation page with the order details
    return render_template('confirmation_order.html', order=order, delivery_address=delivery_address)

@app.route('/add_to_cart/<int:id>', methods=['POST'])
def add_to_cart(id):
        quantity = request.form.get('quantity', default=1, type=int)
        # get product from the database
        conn = sqlite3.connect('shop_DATABASE')
        c = conn.cursor()
        c.execute('SELECT * FROM ProductTypes WHERE product_id=?', (id,))
        product = c.fetchone()
        conn.close()

        # create cart if it doesn't exist
        if 'cart' not in session:
            session['cart'] = []
        if 'total' not in session:
            session['total'] = 0

        # add product to cart
        session['cart'].append({
            'id': product[0],
            'name': product[1],
            'price': product[3],
            'quantity': quantity,
            'subtotal' : quantity*product[3]
        })
        
        session['total'] += int(session['cart'][-1]['subtotal'])

        flash('Product added to cart!', 'success')
        return redirect(url_for('cart'))
        
@app.route('/remove_from_cart/<int:id>', methods=['POST'])
def remove_from_cart(id):    
    cart = session['cart']
    
    
    for c in session['cart']:
        if c['id'] == id:
            session['cart'].remove(c)
            session['total'] -= c['subtotal']
    return redirect(url_for('cart'))

# Login page
@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login_failed')
def login_failed():
    return render_template('login_failed.html')

@app.route('/welcome/<username>')
def welcome(username):
    return render_template('welcome.html', username=username)

@app.route('/login_check', methods=['POST'])
def login_check():
    username = request.form['username']
    password = request.form['password']
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    # Sprawdź dane logowania tutaj
    if username != "admin" or not bcrypt.check_password_hash(hashed_password, 'admin'):
        return redirect(url_for('login_failed'))
    else:
        # session['username'] = username
        user = User(username)
        login_user(user)
        flash('Login successful', 'success')
        return redirect(url_for('welcome', username = username))
    
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))

# Add page
@app.route('/add')
def add():
    conn = get_db_conn()
    categories = conn.execute("SELECT DISTINCT category FROM ProductTypes;").fetchall()
    conn.close()
    return render_template('add.html', categories = categories)

@app.route('/add_products', methods=['POST'])
def add_products():
    name = request.form['name']
    price = request.form['price']
    amount = request.form['amount']
    photo = request.form['photo']
    producent = request.form['producent']
    description = request.form['description'] 
    category = request.form['category']

    conn = get_db_conn()
    product_id = conn.execute("SELECT * FROM ProductTypes ORDER BY product_ID DESC;").fetchone()[0]+1
    element_id = conn.execute("SELECT * FROM ProductElements ORDER BY element_ID DESC;").fetchone()[0]+1
    conn.execute("INSERT INTO ProductTypes VALUES (?,?,?,?,?,?,?,?);", (product_id, name, category, price, amount, photo, producent,description)) 
    for i in range(int(amount)):
        conn.execute("INSERT INTO ProductElements VALUES (?,?,?,?);", (element_id, product_id, generate_serial_number(), 0)) 
        element_id += 1
    conn.commit()
    conn.close()
    return render_template('products_added.html')
    
@app.route('/orders')
def orders():
    # Pobranie zamówień z bazy danych
    conn = get_db_conn()
    orders = conn.execute("SELECT * FROM Orders").fetchall()
    conn.close()
    return render_template('orders.html', orders=orders)

@app.route('/sort', methods=['POST'])
def sort_orders():
    sort_by = request.form['sort_by']
    # Sortowanie zamówień po wybranej kolumnie (ID lub data)
    conn = get_db_conn()
    orders = conn.execute(f"SELECT * FROM Orders ORDER BY {sort_by}").fetchall()
    conn.close()
    return render_template('orders.html', orders=orders)

@app.route('/edit_order/<int:order_id>', methods=['GET', 'POST'])
def edit_order(order_id):

    # Pobranie aktualnych danych zamówienia z bazy danych
    conn = get_db_conn()
    tmp = conn.execute("select product_id, count(*) as licznik from ProductElements where element_id in (select piece_id from orders where order_id = ?) group by product_id;", (order_id,)).fetchall()
    pieces = []
    sum_value = 0
    for piece in tmp:
      name = conn.execute("select name, price from ProductTypes where product_id == ?;", (piece[0],)).fetchone()
      pieces.append({'name': name[0], 'amount': piece[1], 'id': piece[0]})
      sum_value += piece[1]*name[1]
    order = conn.execute("SELECT * FROM Orders WHERE order_ID=?", (order_id,)).fetchone()
    tmp = conn.execute("SELECT name, surname, client_ID FROM Clients WHERE order_ID=?", (order_id,)).fetchone()
    name = tmp[0]+' '+tmp[1]
    delivery = conn.execute('SELECT * FROM DeliveryAddresses WHERE delivery_id=?;', (order[1],)).fetchone()
    conn.close()
    
    if request.method == 'POST':
      conn = get_db_conn()
      street = request.form['street']
      house_number = request.form['house_number']
      flat_number = request.form['flat_number']
      postal_code = request.form['postal_code']
      locality = request.form['locality']
      status = request.form['status']
      
      conn.execute("UPDATE DeliveryAddresses SET street = ?, locality = ?, postal_code= ?, house_number= ?, flat_number= ? WHERE delivery_ID == ?;", (street, locality, postal_code, house_number, flat_number, order[1]))
      conn.execute("UPDATE Orders SET status = ? WHERE order_ID == ?;", (status, order_id)) 
      conn.commit()
      conn.close()
      return redirect(url_for('orders'))

    # Przekazanie danych zamówienia do formularza
    return render_template('modify_order.html', order=order, products=pieces, name=name, client_id = tmp[2], delivery_address=delivery, len_products=len(pieces), value=sum_value)
    
 # Widok klienta
@app.route('/client/<int:client_id>', methods=['GET', 'POST'])
def client(client_id):
    conn = get_db_conn()
    client = conn.execute("SELECT * FROM Clients WHERE client_id==?", (client_id,)).fetchone()
    address_ = conn.execute("SELECT * FROM ClientAddresses WHERE address_id== (SELECT address_id FROM Clients where client_id == ?)", (client_id,)).fetchone()
  
    if(address_[5]):
        address = address_[1]+" "+address_[4]+"/"+str(address_[5])+", "+address_[3]+" "+address_[2]
    else:
        address = address_[1]+" "+address_[4]+", "+address_[3]+" "+address_[2]
    conn.close()
    info = {'id': client[0], 'name': client[5], 'surname': client[6], 'phone': client[3], 'mail': client[4], 'address': address}
    return render_template('client.html', client=info)
    
@app.route('/remove_from_order', methods=['POST'])
def remove_from_order():  
    order_id = request.form['order_id']  
    product_id = request.form['product_id'] 
    conn = get_db_conn()
    product = conn.execute("DELETE FROM Orders WHERE order_id==? and piece_ID in (SELECT element_ID from ProductElements WHERE product_ID == ?);", (order_id, product_id))
    conn.commit()
    conn.close()
    return redirect(url_for('edit_order', order_id=order_id), code=303)
    
@app.route('/delete_order/<int:order_id>')
def delete_order(order_id):  
    conn = get_db_conn()
    conn.execute("UPDATE ProductElements SET ordered=0 WHERE element_id in (select piece_id from Orders where order_ID == ?);", (order_id,))
    conn.execute("DELETE FROM Orders WHERE order_id==?;", (order_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('orders'))
   
@app.route('/clients')
def clients():
    # Pobranie zamówień z bazy danych
    conn = get_db_conn()
    clients = conn.execute("SELECT * FROM Clients").fetchall()
    conn.close()
    return render_template('clients.html', clients=clients)
    
@app.route('/delete_client/<int:client_id>')
def delete_client(client_id):  
    conn = get_db_conn()
    conn.execute("DELETE FROM ClientAddresses WHERE address_id in (SELECT address_id from Clients WHERE client_id==?);", (client_id,))
    conn.execute("DELETE FROM Clients WHERE client_id==?;", (client_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('clients'))

@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    conn = get_db_conn()
    conn.execute("DELETE FROM ProductTypes WHERE product_id==?;", (product_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('products'))

# editing products
@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
# @login_required
def edit_product(product_id):
    conn = get_db_conn()
    product = conn.execute("SELECT * FROM ProductTypes WHERE product_id=?", (product_id,)).fetchone()

    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        price = request.form['price']
        amount = request.form['amount']
        photo = request.form['photo']
        producent = request.form['producent']
        description = request.form['description']
        
        amount_change = int(amount) - (product[4])
        
        if(amount_change > 0):
           element_id = conn.execute("SELECT * FROM ProductElements ORDER BY element_id DESC;").fetchone()[0]+1
           for i in range(0,amount_change):
               conn.execute("INSERT INTO ProductElements VALUES (?,?,?,?);", (element_id, product_id, generate_serial_number(), 0))
               element_id += 1
        else:
           for i in range(0,abs(amount_change)):
               conn.execute("DELETE FROM ProductElements WHERE element_id == (SELECT element_id FROM ProductElements WHERE product_id == ? ORDER BY element_id ASC LIMIT 1);", (product_id,))

        conn.execute("UPDATE ProductTypes SET name=?, category=?, price=?, amount=?, photo=?, producent=?, description=? WHERE product_id=?", (name, category, price, amount, photo, producent, description, product_id))
        conn.commit()
        conn.close()

        flash('Product updated successfully', 'success')
        return redirect(url_for('product', product_id=product_id))

    conn.close()
    return render_template('edit.html', product=product)
    

@app.route('/sales_stats')
def sales_stats():
    # Pobierz dane z bazy danych lub utwórz przykładowe dane
    conn = get_db_conn()
    tmp = conn.execute("SELECT product_id, COUNT(*) as ilosc FROM ProductElements WHERE Ordered == 1 GROUP BY product_ID ORDER BY ilosc DESC LIMIT 10;").fetchall()
    
    bestselling_quantity = []
    
    for i in tmp:
        name = conn.execute("SELECT name FROM ProductTypes WHERE product_ID == ?;", (i[0],)).fetchone()
        bestselling_quantity.append({'name': name[0], 'quantity': i[1]})
    
    tmp = conn.execute("SELECT ProductElements.product_id, ProductTypes.name, COUNT(*)*ProductTypes.price as wartosc FROM ProductElements, ProductTypes WHERE ProductElements.product_id == ProductTypes.product_id AND ProductElements.Ordered == 1 GROUP BY ProductElements.product_ID ORDER BY wartosc DESC LIMIT 10;").fetchall()
    
    bestselling_value = []
    
    for i in tmp:
        bestselling_value.append({'name': i[1], 'value': i[2]})

    
    tmp = conn.execute("SELECT product_id, COUNT(*) as ilosc FROM ProductElements WHERE ELEMENT_ID IN (SELECT piece_id FROM ORDERS WHERE date(date) > date('now','-7 days')) GROUP BY product_ID ORDER BY ilosc DESC LIMIT 10;").fetchall()
    
    bestselling_week = []
    
    for i in tmp:
        name = conn.execute("SELECT name FROM ProductTypes WHERE product_ID == ?;", (i[0],)).fetchone()
        bestselling_week.append({'name': name[0], 'quantity': i[1]})
        
    tmp = conn.execute("SELECT ProductElements.product_id, ProductTypes.name, COUNT(*)*ProductTypes.price as wartosc FROM ProductElements, ProductTypes WHERE ProductElements.product_id == ProductTypes.product_id AND ProductElements.element_ID IN (SELECT piece_id FROM ORDERS WHERE date(date) > date('now','-7 days')) GROUP BY ProductElements.product_ID ORDER BY wartosc DESC LIMIT 10;").fetchall()
    
    bestselling_week_value = []
    
    for i in tmp:
        bestselling_week_value.append({'name': i[1], 'value': i[2]})
    #bestselling_week = [
     #   {'name': 'Produkt E', 'quantity': 50},
      #  {'name': 'Produkt F', 'quantity' : 40}
       # ]
     
     
    tmp = conn.execute("SELECT ProductTypes.name, COUNT(case ProductElements.ORDERED when 1 then 1 else null end) as ilosc FROM ProductTypes, ProductElements WHERE ProductElements.product_ID == ProductTypes.product_ID GROUP BY ProductTypes.product_ID ORDER BY ilosc ASC LIMIT 10;").fetchall()
    
    worstselling = []
    
    for i in tmp:
        worstselling.append({'name': i[0], 'quantity': i[1]})
    #worstselling = [
     #   {'name': 'Produkt G', 'quantity': 5},
      #  {'name': 'Produkt H', 'quantity': 3},
        # Dodaj więcej rekordów
  #  ]

    return render_template('sales_stats.html', bestselling_quantity=bestselling_quantity, bestselling_value=bestselling_value, bestselling_week=bestselling_week, worstselling=worstselling,bestselling_week_value=bestselling_week_value)

# Add the user loader function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User(user_id)
    
if __name__ == '__main__':
    app.run(debug=True)
