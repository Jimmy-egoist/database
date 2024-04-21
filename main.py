from flask import Flask, render_template, request, redirect, url_for, session
from flaskext.mysql import MySQL
import keyring
import os
import math
app = Flask(__name__)
mysql = MySQL()
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = '1414514yzc'
app.config['MYSQL_DATABASE_DB'] = 'project'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['SECRET_KEY'] = "random string"

mysql.init_app(app)

# This project has been uploaded to GitHub.

@app.route('/', methods=['GET', 'POST'])
def index():
    session.permanent = False
    if 'loggedin' in session:
        print(session.get('loggedin'))
    else:
        session['cart_cost'] = 0
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute('select p.pid,p.name,p.price,p.path from products p')
    if request.method == "POST":
        details = request.form
        print(details)
        if 'price-ascending' in details['sort_by']:
            cursor.execute('select p.pid,p.name,p.price,p.path from products p order by p.price asc')
        elif 'price-descending' in details['sort_by']:
            cursor.execute('select p.pid,p.name,p.price,p.path from products p order by p.price desc')


    itemdata = cursor.fetchall()
    cursor.close()
    return render_template('index.html', itemdata=itemdata)

@app.route('/login/', methods=['GET', 'POST'])
def login():
    message = ''
    if request.method == "POST":
        details = request.form
        email = details['email']
        password = details['password']
        try:
            if request.form['login']=='login':
                log_session = 'loggedin'
                conn = mysql.connect()
                cursor = conn.cursor()
                cursor.execute(f'SELECT * FROM customer WHERE `email` = %s AND `password` = %s', (email, password))
                acct = cursor.fetchall()
                if acct:
                    session[log_session] = True
                    session['id'] = acct[0]
                    session['welcome_name'] = acct[1]
                    session['email'] = acct[4]
                    session['kind'] = acct[3]
                    message = 'Logged in successfully!'
                    cursor.execute(f"SELECT CAST(SUM(I.quantity*P.price) AS CHAR) FROM Transactions T, Cart_Items I, Products P WHERE T.order_date IS NULL AND T.customer_id={session['id']} AND T.order_num=I.cart_id AND I.product_id=P.product_id GROUP BY I.cart_id")
                    session['cart_cost'] = cursor.fetchone()[0]
                    cursor.close()
                else:
                    message = 'Incorrect username/password!'
                    return render_template('login.html', message=message)
            elif request.form['login']=='employee':
                log_session = 'emp_loggedin'
                conn = mysql.connect()
                cursor = conn.cursor()
                cursor.execute(f'SELECT * FROM salesman WHERE `email` = %s AND `password` = %s', (email, password))
                acct = cursor.fetchall()
                if acct:
                    session[log_session] = True
                    session['id'] = acct[0]
                    session['welcome_name'] = acct[0][1]
                    session['email'] = acct[1]
                    message = 'Logged in successfully!'

                    cursor.execute(f"SELECT job_title FROM Job_Titles J, Salespersons S WHERE S.salesperson_id={session['id']} AND S.job_title_id=J.title_id")
                    session['job_title'] = cursor.fetchone()[0]
                    cursor.close()
                else:
                    # Account doesnt exist or username/password incorrect
                    message = 'Incorrect username/password!'
                    return render_template('login.html', message=message)
        except:
            conn.rollback()
            conn.close()
            message = "Error Occurred"

        print(message)
        return redirect(url_for('index'))
    return render_template('login.html', message=message, cart_cost=session['cart_cost'])

@app.route('/logout/')
def logout():
    session.pop('loggedin', None)
    session.pop('emp_loggedin', None)
    session.pop('id', None)
    session.pop('welcome_name', None)
    session.pop('email', None)
    session.pop('cart_cost', None)
    session.pop('kind', None)
    session.pop('job_title', None)
    return redirect(url_for('index'))

@app.route('/signup/', methods=['GET', 'POST'])
def signup():
    message = ''

    if request.method == "POST":
        details = request.form
        fullname = details['fullname']
        emailid = details['emailid']
        password = details['password']
        confirmpassword = details['confirmpassword']
        # address
        address = details['address']

        #kind of customer
        kind = details['kind']
        if kind=="Personal":
            kindid=0
        if kind=="Business":
            kindid=1

        conn = mysql.connect()
        cursor = conn.cursor()

        try:
            found_empty = False
            for key, value in details.items():
                if value == '':
                    print(f'key: {key}')
                    found_empty = True
                    break
                # Address and customer into the table
                if not found_empty:
                    cursor.execute("select max(cid) from customer")
                    maxcid=cursor.fetchall()[0][0]
                    print(maxcid)
                    cid=str(int(maxcid)+1)
                    print(fullname,address,kindid,emailid,password)
                    cursor.execute(f'INSERT INTO customer VALUES ("{cid}","{fullname}", "{address}","{kindid}","{emailid}","{password}")')
                    cursor.execute(f'SELECT cid FROM customer WHERE cid="{cid}"')
                    customer_id = cursor.fetchone()[0]
                    print(customer_id,"insert succeed")

                    print('success')
                    conn.commit()
                cursor.close()
                message = "Sign-up Successfully!"
        except Exception as e:
            conn.rollback()
            cursor.close()
            message = "Error Occurred"
            print(e)
        return redirect(url_for('index'))
    return render_template('signup.html', error=message)

@app.route('/view_product/', methods=['GET', 'POST'])
def view_product():
    conn = mysql.connect()
    cursor = conn.cursor()
    prod_id = request.args.get('id')
    if request.method == 'GET':
        name = ''
        inv = ''
        price = ''

        img = ''
        cursor.execute(f"SELECT P.name, P.inventory, P.price,P.path from products P WHERE P.pid={prod_id} ")
        prod_data = cursor.fetchone()
        if prod_data:
            name = prod_data[0]
            inv = prod_data[1]
            price = prod_data[2]
            img = prod_data[3]
        print(prod_data)
        return render_template('view_product.html', product_id=id, name=name, inv=inv, price=price, img=img)
    elif request.method == 'POST':
        details = request.form
        quant = details['quantity']
        print(f"Product ID: {prod_id}")
        print(f"Quantity: {quant}")
        print(f"Customer ID: {session['id']}")

        try:


            cursor.execute("select max(item_id) from cart")
            item_id = cursor.fetchone()[0]
            if item_id is None:
                item_num = "1"
            else:
                item_num = str(int(item_id) + 1)
            print(item_num,int(quant),int(prod_id))
            cid=session['id'][0]
            print(cid)
            cursor.execute(f'insert into cart values("{item_num}",now(),"{quant}","{prod_id}","{cid}")')
            print("insert success")

            cursor.execute(f'SELECT CAST(SUM(I.quantity*P.price) AS CHAR) FROM cart I, products P WHERE I.product_id=P.pid and I.cid="{cid}"')
            session['cart_cost'] = cursor.fetchone()[0]
            print(session['cart_cost'])
            conn.commit()
        except:
            print("failed to add item")
            conn.rollback()
        return redirect(url_for("cart"))
    return render_template('view_product.html')

@app.route('/cart/', methods=['GET', 'POST'])
def cart():
    message = ''
    success = ''
    order_id = ''
    conn=mysql.connect()
    cursor = conn.cursor()
    cursor.execute(f"SELECT I.item_id FROM cart I, products P WHERE I.product_id=P.pid AND I.cid={session['id'][0]}")
    cart_info = cursor.fetchone()
    print(cart_info)
    if cart_info:
        print("valid cart found")
        order_id = cart_info[0]

    print(f"Order ID: {order_id}")
    cursor.execute(f"SELECT I.product_id, P.name, P.path, I.quantity, P.inventory, P.price, P.price*I.quantity AS \'Cost\', I.created_date FROM cart I, products P WHERE  I.product_id=P.pid AND I.cid={session['id'][0]} ORDER BY I.item_id")
    cart_data = cursor.fetchall()
    if cart_data:
        print(cart_data)
        if request.method == "POST":
            try:
                cursor.execute(f"SELECT P.pid,P.inventory, sum(I.quantity) FROM products P, cart I WHERE P.pid=I.product_id group BY I.product_id")
                inventory_comp = cursor.fetchall()
                print("inventory",inventory_comp)
                inv_check = True
                for row in inventory_comp:
                    inv = row[1]
                    quant = row[2]
                    if quant > inv:
                        inv_check = False
                print(f"Inventory check is {inv_check}")

                if inv_check :
                    cid = session['id'][0]
                    print('Checks passed')
                    for row in cart_data:
                        print(row)
                        cursor.execute(f"UPDATE products SET inventory=inventory-{row[3]} WHERE  pid={row[0]}")
                        cursor.execute("select max(order_id) from transactions")
                        order_id = cursor.fetchone()[0]
                        if order_id is None:
                            order_num = "1"
                        else:
                            order_num = str(int(order_id) + 1)
                        cursor.execute(f'insert into transactions values ("{order_num}",now(),"1","{row[0]}","{row[3]}","{cid}")')
                    message = 'Transaction Complete - Order Processed!'
                    session.pop('cart_cost', None)

                    cursor.execute(f'delete from cart where cid="{cid}"')
                    success = True
                    conn.commit()
                else:
                    message = 'Error: Unable to complete transaction'
                    success = False
                    return render_template('cart.html', cart_data=cart_data, message=message, success=success)
                cursor.close()
            except:
                conn.rollback()
                conn.close()
                success = False
                message = "Error Occurred"
    else:
        message = 'Error Loading Cart'
        success = False
        return render_template('cart.html', cart_data=cart_data, message=message, success=success)
    print(message)
    return render_template('cart.html', cart_data=cart_data, message=message, success=success)

@app.route('/empty_cart/')
def empty_cart():
    conn = mysql.connect()
    cursor = conn.cursor()
    if session['id']:
        cid=session['id'][0]
        cursor.execute(f"DELETE FROM cart WHERE cid={cid}")
        conn.commit()
        session.pop('cart_cost', None)
    return redirect(request.referrer)

@app.route('/remove_item/')
def remove_item():
    conn = mysql.connect()
    cursor = conn.cursor()
    order_num = request.args.get('cart', None)
    product_id = request.args.get('product', None)
    cid=session['id'][0]
    print(f"Order Number: {order_num}")
    print(f"Product ID: {product_id}")
    print(cid)
    try:
        cursor.execute(f'DELETE FROM cart WHERE product_id="{order_num}" AND cid="{cid}"')
        print("delete item success")
        conn.commit()
        cursor.execute(f'SELECT CAST(SUM(I.quantity*P.price) AS CHAR) FROM cart I, products P WHERE I.product_id=P.pid and I.cid="{cid}"')
        cost=cursor.fetchone()[0]
        print(type(session['cart_cost']))
        session['cart_cost'] = cost
        if cursor.fetchone()[0] is None:
            print(cursor.fetchone()[0])
            session['cart_cost'] ="0"

        conn.commit()
    except:
        print("delete failed")
        conn.rollback()
    cursor.close()
    print(f"Cart Cost: ${session['cart_cost']}")
    return redirect(url_for('cart'))

@app.route('/orders/')
def orders():
    conn=mysql.connect()
    cursor = conn.cursor()
    order_data = ''
    print(session['id'])
    if session['id']:
        sql = "SELECT T.order_id, T.date, P.name, T.quantity, T.quantity*P.price, S.sname FROM transactions T, products P, salesman S WHERE T.cid=%s AND T.price=P.pid AND T.salesman=S.sid GROUP BY T.order_id"
        print(sql)
        cid=session['id'][0]
        print(cid)
        cursor.execute(f'SELECT T.order_id, T.date, P.name, T.quantity, T.quantity*P.price, S.sname FROM transactions T, products P, salesman S WHERE T.cid="{cid}" AND T.price=P.pid AND T.salesman=S.sid GROUP BY T.order_id')
        order_data = cursor.fetchall()
        print(order_data)
    cursor.close()
    return render_template('orders.html', order_data=order_data)

@app.route('/customers/')
def customers():
    conn=mysql.connect()
    cursor = conn.cursor()
    cursor.execute('SELECT C.cid, C.name,  C.email, C.`home&business`, C.address FROM customer C  ORDER BY C.cid ASC')
    cust_data = cursor.fetchall()
    print(cust_data)
    return render_template('customers.html', cust_data=cust_data)

@app.route('/edit_customer/', methods=['GET', 'POST'])
def edit_customer():
    message = ''
    conn = mysql.connect()
    cursor = conn.cursor()
    edit_id = request.args.get('id', None)
    if request.method == "GET":
        print(f"Edited User's ID: {edit_id}")
        edit_kind = request.args.get('kind', None)

        cursor.execute(f'SELECT  C.name,  C.email, C.`home&business`, C.address FROM customer C WHERE C.cid="{edit_id}" ')
        cust_data = cursor.fetchone()

        if cust_data:
            fname = cust_data[0]
            email = cust_data[1]
            address = cust_data[3]

        print(edit_kind)
        return render_template('edit_customer.html', firstname=fname, emailid=email, address=address, kind=edit_kind)
    elif request.method == "POST":
        details = request.form
        value=request.args.get('submit',None)
        print(value)
        fullname = details['fullname']
        emailid = details['emailid']
        # address
        address = details['address']

        # kind of customer
        kind = details['kind']

        print(f"firstName: {fullname}")
        print(f"emailid: {emailid}")
        print(f"address: {address}")
        print(f'customer type: {kind}')
        if kind=="Personal":
            hb=0
        else:
            hb=1
        try:
            cursor.execute(f'UPDATE customer SET name="{fullname}", email="{emailid}",address="{address}", `home&business`="{hb}" WHERE cid="{edit_id}"')
            print("customer update success")

            conn.commit()
            print('success')
            cursor.close()
            message = "Edited Successfully!"
        except Exception as e:
            conn.rollback()
            cursor.close()
            message = "Error Occurred"
            print(message)
        return redirect(url_for('customers'))
    return render_template('edit_customer.html', message=message)

@app.route('/remove_customer/')
def remove_customer():
    conn = mysql.connect()
    cursor = conn.cursor()
    cust = request.args.get('id')
    print(cust)
    try:
        cursor.execute(f"DELETE FROM customer WHERE cid={cust}")
        conn.commit()
        print("delete customer success")
    except:
        conn.rollback()
        print("delete customer failure")
    cursor.close()
    return redirect(url_for('customers'))

@app.route('/add_customer/', methods=['GET', 'POST'])
def add_customer():
    message = ''
    conn = mysql.connect()
    cursor = conn.cursor()
    edit_id = request.args.get('id', None)

    if request.method == "POST":
        details = request.form
        value=request.args.get('submit',None)
        print(value)
        fullname = details['fullname']
        emailid = details['emailid']
        # address
        address = details['address']

        # kind of customer
        kind = details['kind']
        password = details['password']
        print(f"firstName: {fullname}")
        print(f"emailid: {emailid}")
        print(f"address: {address}")
        print(f'customer type: {kind}')
        print(f'password: {password}')
        if kind=="Personal":
            hb=0
        else:
            hb=1
        cursor.execute("select max(cid) from customer")
        cid = cursor.fetchone()
        print(cid)
        cust_id = int(cid[0]) + 1
        try:

            cursor.execute(f'insert into customer values ("{cust_id}","{fullname}","{address}","{hb}","{emailid}","{password}")')
            print("customer insert success")

            conn.commit()
            print('success')
            cursor.close()
            message = "Insert Successfully!"
        except Exception as e:
            conn.rollback()
            cursor.close()
            message = "Error Occurred"
            print(message)
        return redirect(url_for('customers'))
    return render_template('add_customer.html', message=message)

@app.route('/products/')
def products():
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Products P ORDER BY P.pid ASC')
    prod_data = cursor.fetchall()
    print(prod_data)
    return render_template('products.html', prod_data=prod_data)

@app.route('/edit_product/', methods=['GET', 'POST'])
def edit_product():
    message = ''
    conn = mysql.connect()
    cursor = conn.cursor()
    edit_id = request.args.get('id', None)
    new = request.args.get('new', None)

    if request.method == "GET":
        name = ''
        inv = ''
        price = ''
        img = ''
        if new == 'False':
            cursor.execute(f"SELECT * FROM Products P WHERE P.pid={edit_id} ")
            prod_data = cursor.fetchone()
            if prod_data:
                name = prod_data[1]
                inv = prod_data[2]
                price = prod_data[3]
                img = prod_data[4]
        return render_template('edit_product.html', product_id=edit_id, name=name, inv=inv, price=price,  img=img)
    elif request.method == "POST":
        details = request.form
        name = details['name']
        inv = details['inv']
        price = details['price']
        img = details['img']
        try:
            if new == 'False':
                cursor.execute(f'UPDATE Products SET name="{name}", inventory="{inv}", price="{price}",path="{img}" WHERE pid="{edit_id}"')
            conn.commit()
            cursor.close()
            message = "Edited Successfully!"
        except Exception as e:
            conn.rollback()
            cursor.close()
            message = "Error Occurred"
        return redirect(url_for('products'))
    return render_template('edit_product.html', message=message)

@app.route('/remove_product/')
def remove_product():
    conn = mysql.connect()
    cursor = conn.cursor()
    prod_id = request.args.get('id', None)
    print(prod_id)
    try:
        cursor.execute(f"DELETE FROM Products WHERE pid={prod_id}")
        conn.commit()
    except:
        conn.rollback()
    cursor.close()
    return redirect(url_for('products'))

@app.route('/add_product/', methods=['GET', 'POST'])
def add_product():
    message = ''
    conn = mysql.connect()
    cursor = conn.cursor()
    if request.method == "POST":
        details = request.form
        name = details['name']
        inv = details['inv']
        price = details['price']
        img = details['img']
        try:
            cursor.execute("select max(pid) from products")
            pid=int(cursor.fetchone()[0])+1
            cursor.execute(f'insert into Products values ("{pid}","{name}","{inv}","{price}","{img}")')
            conn.commit()
            cursor.close()
            message = "Edited Successfully!"
        except Exception as e:
            conn.rollback()
            cursor.close()
            message = "Error Occurred"
        return redirect(url_for('products'))
    return render_template('add_product.html', message=message)

@app.route('/search_result/', methods=['GET', 'POST'])
def search_result():
    conn = mysql.connect()
    cursor = conn.cursor()
    print(request)

    if request.method == "POST":
        details = request.form
        print(details)
        if 'searchtext' in details:
            text = details['searchtext']
            global Search_Text
            Search_Text = text

            cursor.execute(f'SELECT pid, name, price, path FROM products WHERE  (products.name LIKE "%{text}")  ')

        else:
            print(Search_Text)
            text= Search_Text
            if 'price-ascending' in details['sort_by']:

                cursor.execute(
                    f'SELECT products.product_id, products.name, products.price, product_description.image_path FROM'
                    f' products,product_description WHERE (products.product_id = product_description.product_id AND'
                    f' products.name LIKE "%{text}") OR (products.product_id = product_description.product_id AND' \
                    f' products.name LIKE "{text}% ") OR (products.product_id = product_description.product_id AND' \
                    f' products.name LIKE "%{text}%") order by products.price asc')
            elif 'price-descending' in details['sort_by']:
                cursor.execute(
                    f'SELECT products.product_id, products.name, products.price, product_description.image_path FROM'
                    f' products,product_description WHERE (products.product_id = product_description.product_id AND'
                    f' products.name LIKE "%{text}") OR (products.product_id = product_description.product_id AND' \
                    f' products.name LIKE "{text}% ") OR (products.product_id = product_description.product_id AND' \
                    f' products.name LIKE "%{text}%") order by products.price desc')

        products_name = cursor.fetchall()
        print(f"products_name: {products_name}")
        cursor.close()
    return render_template('search_result.html', itemdata=products_name)

@app.route('/stores/')
def stores():
    conn=mysql.connect()
    cursor = conn.cursor()
    cursor.execute('SELECT sid, address, manager, salesman_num,rid FROM store  ORDER BY sid ASC')
    store_data = cursor.fetchall()
    print(store_data)
    cursor.close()
    return render_template('stores.html', store_data=store_data)

@app.route('/edit_store/', methods=['GET', 'POST'])
def edit_store():
    message = ''
    conn=mysql.connect()
    cursor = conn.cursor()
    edit_id = request.args.get('id', None)
    new = request.args.get('new', None)
    print(f"Edited ID: {edit_id}")
    print(f"Is new store: {new}")
    if request.method == "GET":

        if new == 'False':
            cursor.execute(f'SELECT address,manager,salesman_num,rid FROM Store  WHERE sid="{edit_id}" ')
            store_data = cursor.fetchone()
            if store_data:
                print(store_data)
                address = store_data[0]
                manager = store_data[1]
                salesman_num = store_data[2]
                rid = store_data[3]

        return render_template('edit_store.html', store_id=edit_id, address=address,manager=manager,salesman_num=salesman_num,rid=rid)
    elif request.method == "POST":
        details = request.form
        address = details['address']
        manager = details['manager']
        salesman_num = details['salesman_num']
        rid = details['rid']

        try:

            cursor.execute(f'UPDATE Store SET address="{address}",manager="{manager}",salesman_num="{salesman_num}",rid="{rid}"')
            print("store update success")

            conn.commit()
            print('success')
            cursor.close()
            message = "Edited Successfully!"
        except Exception as e:
            conn.rollback()
            cursor.close()
            message = "Error Occurred"
            print(message)
        return redirect(url_for('stores'))
    return render_template('edit_store.html', message=message)

@app.route('/remove_store/')
def remove_store():
    conn = mysql.connect()
    cursor = conn.cursor()
    store_id = request.args.get('id', None)
    print(store_id)
    try:
        cursor.execute(f"DELETE FROM Store WHERE sid={store_id}")
        conn.commit()
        print("delete store success")
    except:
        conn.rollback()
        print("delete store failure")
    cursor.close()
    return redirect(url_for('stores'))

@app.route('/add_store/', methods=['GET', 'POST'])
def add_store():
    message = ''
    conn=mysql.connect()
    cursor = conn.cursor()
    edit_id = request.args.get('id', None)
    new = request.args.get('new', None)
    print(f"Edited ID: {edit_id}")
    print(f"Is new store: {new}")
    if request.method == "POST":
        details = request.form
        address=details['address']
        manager=details['manager']
        salesman_num=details['salesman_num']
        rid=details['rid']
        print(details)
        cursor.execute("select max(sid) from store")
        id=cursor.fetchone()[0]
        if id is None:
            sid=1
        else:
            sid=int(id)+1
        print(sid)

        try:

            cursor.execute(f'INSERT INTO store values ("{sid}","{address}","{manager}","{salesman_num}","{rid}")')
            print("store insert success")
            conn.commit()
            print('success')
            cursor.close()
            message = "Edited Successfully!"
        except Exception as e:
            conn.rollback()
            cursor.close()
            message = "Error Occurred"
            print(message)
        return redirect(url_for('stores'))
    return render_template('add_store.html', message=message)

@app.route('/analytics/')
def analytics():
    conn=mysql.connect()
    cursor = conn.cursor()
    cursor.execute('SELECT P.name AS \'Product Name\', SUM(I.quantity) AS \'Sales\', I.quantity*P.price AS \'Profit\' FROM transactions I, products P WHERE I.price = P.pid GROUP BY I.price ORDER BY SUM(I.quantity) DESC ')
    product_sales = cursor.fetchall()
    print(product_sales)

    cursor.execute('SELECT P.name AS \'Product Name\', SUM(I.quantity) AS \'Sales\' FROM transactions I, products P WHERE I.price = P.pid GROUP BY I.price ORDER BY SUM(I.quantity) DESC LIMIT 3')
    product_categories = cursor.fetchall()
    print(product_categories)

    cursor.execute(('select c.name,sum(p.price*t.quantity) from transactions t,products p,customer c where c.cid=t.cid and t.price=p.pid group by c.cid order by sum(p.price) desc limit 3'))
    cus_sales=cursor.fetchall()

    cursor.execute('SELECT P.name AS \'Product Name\', I.quantity*P.price AS \'Profit\' FROM transactions I, products P WHERE I.price = P.pid GROUP BY I.price ORDER BY I.quantity*P.price DESC limit 3')
    profit = cursor.fetchall()
    print(product_sales)

    return render_template('analytics.html', product_sales=product_sales,product_categories=product_categories,cus_sales=cus_sales,profit=profit)

if __name__ == '__main__':
    app.run(debug=True)