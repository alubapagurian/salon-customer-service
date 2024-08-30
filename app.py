from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Database setup
def init_db():
    conn = sqlite3.connect('salon.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY,
            designer_name TEXT,
            date TEXT,
            customer_name TEXT,
            customer_phone TEXT,
            service_items TEXT,
            products TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS services (
            name TEXT PRIMARY KEY,
            price REAL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS designers (
            name TEXT PRIMARY KEY
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS service_designers (
            service_name TEXT,
            designer_name TEXT,
            percentage REAL,
            PRIMARY KEY (service_name, designer_name),
            FOREIGN KEY (service_name) REFERENCES services(name),
            FOREIGN KEY (designer_name) REFERENCES designers(name)
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return redirect(url_for('record'))

@app.route('/get_designers')
def get_designers():
    conn = sqlite3.connect('salon.db')
    c = conn.cursor()
    c.execute('SELECT name FROM designers')
    designers = c.fetchall()
    
    designer_data = []
    for designer in designers:
        designer_name = designer[0]
        service_data = {}
        for service in ['洗髮', '剪髮', '染髮', '燙髮', '護髮', '彩妝', '頭皮護理']:
            c.execute('SELECT price FROM services WHERE name = ?', (service,))
            price = c.fetchone()
            c.execute('SELECT percentage FROM service_designers WHERE service_name = ? AND designer_name = ?', (service, designer_name))
            designer_commission = c.fetchone()
            service_data[service] = {
                'price': price[0] if price else 0,
                'designer_commission': designer_commission[0] if designer_commission else 0
            }
        designer_data.append({
            'name': designer_name,
            'services': service_data
        })
    conn.close()
    return jsonify(designers=designer_data)

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    conn = sqlite3.connect('salon.db')
    c = conn.cursor()
    if request.method == 'POST':
        data = request.json
        conn = sqlite3.connect('salon.db')
        c = conn.cursor()
        
        # Clear existing data
        c.execute('DELETE FROM designers')
        c.execute('DELETE FROM services')
        c.execute('DELETE FROM service_designers')
        
        for designer in data['designers']:
            c.execute('INSERT INTO designers (name) VALUES (?)', (designer['name'],))
            for service, details in designer['services'].items():
                c.execute('INSERT OR REPLACE INTO services (name, price) VALUES (?, ?)', (service, details['price']))
                c.execute('INSERT INTO service_designers (service_name, designer_name, percentage) VALUES (?, ?, ?)', 
                          (service, designer['name'], details['commission']))
        
        conn.commit()
        conn.close()
        return jsonify(success=True)

        for key, value in request.form.items():
            if key.startswith('price_'):
                parts = key.split('_')
                designer_name = parts[1]
                service_name = parts[2]
                price = float(value)
                c.execute('INSERT OR REPLACE INTO services (name, price) VALUES (?, ?)', (service_name, price))
            elif key.startswith('designer_commission_'):
                parts = key.split('_')
                designer_name = parts[2]
                service_name = parts[3]
                designer_commission = float(value)
                c.execute('INSERT OR REPLACE INTO service_designers (service_name, designer_name, percentage) VALUES (?, ?, ?)', (service_name, designer_name, designer_commission))
        conn.commit()
        conn.close()
        return redirect(url_for('setup'))
    
    c.execute('SELECT name FROM designers')
    designers = c.fetchall()
    services = ['洗髮', '剪髮', '染髮', '燙髮', '護髮', '彩妝', '頭皮護理']
    designer_data = []
    for designer in designers:
        designer_name = designer[0]
        service_data = {}
        for service in services:
            c.execute('SELECT price FROM services WHERE name = ?', (service,))
            price = c.fetchone()[0]
            c.execute('SELECT percentage FROM service_designers WHERE service_name = ? AND designer_name = ?', (service, designer_name))
            designer_commission = c.fetchone()[0]
            # Fetch auxiliary commission if stored separately
            auxiliary_commission = 0  # Replace with actual fetch logic
            service_data[service] = {
                'price': price,
                'designer_commission': designer_commission,
                'auxiliary_commission': auxiliary_commission
            }
        designer_data.append({
            'name': designer_name,
            'services': service_data
        })
    conn.close()
    return render_template('setup.html', designers=designer_data, services=services)

@app.route('/record', methods=['GET', 'POST'])
def record():
    date = datetime.now().strftime('%Y-%m-%d')
    if request.method == 'POST':
        customer_id = request.form.get('id', None)
        designer_name = request.form['designer_name']
        date = request.form['date']
        customer_name = request.form['customer_name']
        customer_phone = request.form['customer_phone']
        service_items = ', '.join(request.form.getlist('service_items'))
        
        product_names = request.form.getlist('product_name')
        product_quantities = request.form.getlist('product_quantity')
        products = ', '.join([f"{name} x {quantity}" for name, quantity in zip(product_names, product_quantities)])

        conn = sqlite3.connect('salon.db')
        c = conn.cursor()
        if customer_id:
            c.execute('''
                REPLACE INTO customers (id, designer_name, date, customer_name, customer_phone, service_items, products)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (customer_id, designer_name, date, customer_name, customer_phone, service_items, products))
        else:
            c.execute('''
                INSERT INTO customers (designer_name, date, customer_name, customer_phone, service_items, products)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (designer_name, date, customer_name, customer_phone, service_items, products))
        conn.commit()
        conn.close()

        return redirect(url_for('record'))

    filter_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))

    conn = sqlite3.connect('salon.db')
    c = conn.cursor()
    c.execute('SELECT * FROM customers WHERE date = ?', (date,))
    customers = c.fetchall()
    c.execute('SELECT name FROM designers')
    designers = c.fetchall()
    conn.close()

    return render_template('record.html', customers=customers, datetime=datetime, filter_date=filter_date, designers=designers)

@app.route('/records', methods=['GET'])
def get_records():
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    conn = sqlite3.connect('salon.db')
    c = conn.cursor()
    c.execute('SELECT * FROM customers WHERE date = ?', (date,))
    customers = c.fetchall()
    conn.close()
    return jsonify(customers=[{
        'id': customer[0],
        'designer_name': customer[1],
        'date': customer[2],
        'customer_name': customer[3],
        'customer_phone': customer[4],
        'service_items': customer[5],
        'products': customer[6]
    } for customer in customers])

@app.route('/query', methods=['GET', 'POST'])
def query():
    customers = []
    if request.method == 'POST':
        query_method = request.form['query_method']
        query_value = request.form['query_value']

        conn = sqlite3.connect('salon.db')
        c = conn.cursor()

        if query_method == 'by_date':
            c.execute('SELECT * FROM customers WHERE date = ?', (query_value,))
        elif query_method == 'by_designer':
            c.execute('SELECT * FROM customers WHERE designer_name = ?', (query_value,))
        elif query_method == 'by_customer':
            c.execute('SELECT * FROM customers WHERE customer_name = ?', (query_value,))
        elif query_method == 'by_phone':
            c.execute('SELECT * FROM customers WHERE customer_phone = ?', (query_value,))
        elif query_method == 'by_service':
            c.execute('SELECT * FROM customers WHERE service_items = ?', (query_value,))
        elif query_method == 'by_product':
            c.execute('SELECT * FROM customers WHERE products LIKE ?', (f'%{query_value}%',))

        customers = c.fetchall()
        conn.close()

    return render_template('query.html', customers=customers)

@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    conn = sqlite3.connect('salon.db')
    c = conn.cursor()
    c.execute('DELETE FROM customers WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify(success=True)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)