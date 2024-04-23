from flask import Flask, render_template, request, flash, redirect, url_for, session, jsonify
from requests.auth import HTTPBasicAuth
from models import *
import os
import yagmail
import datetime as dt
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from authorize import role_required


basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__, template_folder='template')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'dessertbydaya.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'beyond_course_scope'
db.init_app(app)

# Product image parameters
app.config['PRODUCT_UPLOAD_PATH'] = 'static/assets'

# Product order restrictions
app.config['MAX_QUANTITY_PER_ITEM'] = 20

# PayPal API parameters
app.config['PAYPAL_API'] = 'https://api-m.sandbox.paypal.com/v2'
app.config['PAYPAL_CLIENT_ID'] = ''
app.config['PAYPAL_SECRET'] = ''

# yagmail parameters
app.config['GMAIL_USER'] = ''
app.config['GMAIL_APP_PASSWORD'] = ''

login_manager = LoginManager()
login_manager.login_view = 'login' # default login route
login_manager.init_app(app)

# ------------------------------------------------- LOGIN ----------------------------------------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ------------------------------------------------- ERROR ----------------------------------------------------------
@app.errorhandler(404)
def page_not_found(e):
   flash(
       f'Sorry! This page does not exist.','error')
   return render_template("404.html")

# ------------------------------------------------- ROUTES FOR ALL USERS------------------------------------------------
#LOGIN PAGE
@app.route('/login', methods=['GET', 'POST'])
def login():
    default_manager_route_function = 'customer_view_all'
    default_employee_route_function = 'customer_view_all'
    default_customer_route_function = 'customer_view'

    if request.method == 'GET':
        # Determine where to redirect user if they are already logged in
        if current_user and current_user.is_authenticated:
            if current_user.role in ['MANAGER']:
                return redirect(url_for(default_manager_route_function))
            if current_user.role in ['EMPLOYEE']:
                return redirect(url_for(default_employee_route_function))
        else:
            redirect_route = request.args.get('next')
            return render_template('login.html', redirect_route=redirect_route)

    elif request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        redirect_route = request.form.get('redirect_route')

        user = User.query.filter_by(username=username).first()

        # Validate user credentials and redirect them to initial destination
        if user and check_password_hash(user.password, password):
            login_user(user)

            if current_user.role in ['MANAGER']:
                return redirect(redirect_route if redirect_route else url_for(default_manager_route_function))
            if current_user.role in ['EMPLOYEE']:
                return redirect(redirect_route if redirect_route else url_for(default_employee_route_function))
            elif current_user.role == 'CUSTOMER':
                # check if correct id is used
                return redirect(redirect_route if redirect_route else url_for(default_customer_route_function,customer_id=current_user['customer_id']))
        else:
            flash(f'Incorrect username or password was used ', 'error')

        return redirect(url_for('login'))

    return redirect(url_for('login'))

# LOGOUT PAGE
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash(f'Logout success', 'success')
    return redirect(url_for('home'))

# ABOUT
@app.route('/about')
def about():
    return render_template('about.html')
# ------------------------------------------------- ROUTES FOR CUSTOMERS--------------------------------------------
# HOME
@app.route('/')
def home():
    return render_template('home.html')

# CUSTOMER PROFILE
@app.route('/customer/view/<int:customer_id>')
@login_required
@role_required(['MANAGER', 'EMPLOYEE', 'CUSTOMER'])
def customer_view(customer_id):
    if current_user.role in ['MANAGER', 'EMPLOYEE']:
        customer = Customer.query.filter_by(customer_id=customer_id).first()
        users = User.query.order_by(User.user_id) \
            .all()
        # changed template rendered from create-account to products because the registration isnt done yet
        if customer:
            return render_template('product_view_all.html', customer=customer, users=users, action='read')

        else:
            flash(f'Customer attempting to be viewed could not be found!', 'error')
            return redirect(url_for('customer_view_all'))

    elif current_user.role == 'CUSTOMER':
        customer = (Customer.query.filter_by(email=current_user.email).first())
        users = User.query.order_by(User.user_id) \
            .all()
        # changed template rendered from create-account to products because the registration isnt done yet
        if customer:
            return render_template('product_view_all.html', customer=customer, users=users, action='read')

        else:
            flash(f'Your record could not be located. Please create an account', 'error')
            return redirect(url_for('error'))

    # This point should never be reached as all roles are accounted for. Adding defensive programming as a double check.
    else:
        flash(f'Invalid request.', 'error')
        return render_template('error.html')

# VIEW ALL PRODUCTS
@app.route('/product/view')
def product_view_all():
# check if order by or with entities for this query statement
   products = Product.query.all()
   # print(f"Products: {products}")
   return render_template('product_view_all.html', products=products)

# VIEW INDIVIDUAL PRODUCTS
@app.route('/product/<int:product_id>')
def product_view(product_id):
    product = Product.query.get(product_id)
    product_category = ProductCategory.query.order_by(ProductCategory.category_id).all()

    if product:
        return render_template('product_view.html', product=product, product_category=product_category)
    else:
        flash(f'The dessert you are looking for does not exist.', 'error')
        return redirect(url_for('home'))


# CONTACT US / CUSTOM ORDERS
# leads to error
@app.route('/contact-us', methods=['GET', 'POST'])
def contact_us():
    if request.method == 'POST':
        user = app.config['GMAIL_USER']
        app_password = app.config['GMAIL_APP_PASSWORD']
        to = user
        subject = 'DessertbyDaya - Contact Us Form Submission'
        contents = [request.form.get('message')]
        with yagmail.SMTP(user, app_password) as yag:
            if request.form.get('agree_cc'):
                yag.send(to, subject, contents, cc=request.form.get('email'))
            else:
                yag.send(to, subject, contents)
        email = request.form['email']
        message = request.form['message']

        messages = Messages(time=dt.datetime.now(), email=email, message=message)
        db.session.add(messages)
        db.session.commit()
        flash(f'Your message was successfully sent!', 'success')

# create a contact html
        return render_template('contact-us.html', form_submitted=True)
    else:
        return render_template('contact-us.html')

# CART PAYMENT
@app.route('/cart-payment', methods=['GET', 'POST'])
@login_required
def cart_payment():
    if 'cart' in session:
        user = User.query.filter_by(user_id=current_user.user_id).first()
        # if we are doing update on customer profile we may not need this email update
        #if request.method == 'POST':
            #user.email = request.form.get('email')
            #db.session.commit()
            #flash(f'Email was successfully updated!', 'success')
        return render_template('cart-payment.html', products=session['cart'], cart_count=len(session['cart']), cart_total=session['cart_total'], customer_email=user.email)
    else:
        return render_template('cart-payment.html', cart_count=0)

# CART CLEAR
@app.route('/cart/clear')
@login_required
def clear_cart():
    if 'cart' in session:
        del(session['cart'])
        flash(f"Your cart is now empty.", 'success')
    else:
        flash(f"Your cart is already empty.", 'error')
    return redirect(url_for('product_view_all'))

#CART ADD
@app.route('/cart/add/<int:product_id>', methods=['GET','POST'])
@login_required
def cart_add(product_id):
    product = Product.query.filter_by(product_id=product_id).first()
    quantity = int(request.args.get('quantity'))

    if product:

        if 'cart' not in session:
            session['cart'] = []

        found_item = next((item for item in session['cart'] if ((item['product_id'] == product_id))), None)

        if found_item:
            found_item['quantity'] += quantity

            if found_item['quantity'] > app.config['MAX_QUANTITY_PER_ITEM']:
                found_item['quantity'] = app.config['MAX_QUANTITY_PER_ITEM']
                flash(f"You cannot order more than {app.config['MAX_QUANTITY_PER_ITEM']} of the same item.")

        else:
            session['cart'].append(
                {'product_id': product.product_id, 'product_name':product.product_name,
                 'product_image':product.product_image, 'quantity': product.quantity,
                 'product_price':product.product_price}
            )

        session['cart_total'] = sum(item['product_price']*item['quantity'] for item in session['cart'])
        flash(f"{product.product_name} has been successfully added to your cart.", 'success')
        return redirect(url_for('cart_payment'))
    else:
        flash(f'Product does not exist. Submit a custom order form through the contact page.', 'error')

# CART REMOVE
@app.route('/cart/remove/<int:index>', methods=['GET'])
@login_required
def cart_remove(index):
    if 'cart' in session:
        if index < len(session['cart']):
            product_name = session['cart'][index]['product_name']
            session['cart'].pop(index)
            flash(f"{product_name} has been successfully removed from your cart.", 'success')

        else:
            flash(f'Product not found in cart.', 'error')

    session['cart_total'] = sum(item['product_price'] * item['quantity'] for item in session['cart'])

    return redirect(url_for('cart_payment'))

# PROCESS ORDER
@app.route('/process-order/')
@login_required
def process_order():
    flash(f"Email receipt was successfully sent to {User.query.filter_by(user_id=current_user.user_id).first().email}", 'success')
    # create thank you html page
    return render_template('thank-you.html', order_number=session['current_order_id'])

# PAYMENTS
@app.route("/payments/<orderId>/capture", methods=["POST"])
@login_required
def capture_payment(orderId):
    captured_payment = approve_payment(orderId)

    if captured_payment['status'] == 'COMPLETED':
        customer = Customer.query.filter_by(user_id=current_user.user_id).first()
        customer_id = customer.customer_id
        payment_id = captured_payment['id']
        # added pick up date
        pick_up_date = captured_payment['pick_up_date']
        first_name = captured_payment['payment_source']['paypal']['name']['given_name']
        last_name = captured_payment['payment_source']['paypal']['name']['surname']
        email = captured_payment['payment_source']['paypal']['email_address']
        address = captured_payment['purchase_units'][0]['shipping']['address']['address_line_1']
        city = captured_payment['purchase_units'][0]['shipping']['address']['admin_area_2']
        state = captured_payment['purchase_units'][0]['shipping']['address']['admin_area_1']
        zip = captured_payment['purchase_units'][0]['shipping']['address']['postal_code']

        # added pick up date
        store_order = StoreOrder(customer_id=customer_id, payment_id=payment_id, pick_up_date=pick_up_date, first_name=first_name, last_name=last_name,
                                 email=email, address=address, city=city, state=state, zip=zip)
        db.session.add(store_order)
        db.session.flush()
        db.session.refresh(store_order)
        order_id = store_order.order_id
        session['current_order_id'] = order_id

        email_content = f"Thank you! Your order has been submitted. Your order # is: {session['current_order_id']}. Your desserts will be ready on your specified date." \
                   f"Here's your order details: \n"

        for each_item in session['cart']:
            item_ordered = OrderItem(order_id, each_item['product_id'], each_item['quantity'])
            db.session.add(item_ordered)
            email_content = email_content + f"\nProduct: {each_item['product_name']}\nQuantity: {each_item['quantity']}\nPick Up Date: {each_item['pick_up_date']}\nPrice: ${each_item['product_price']:.2f}\n"
        email_content = email_content + f"\n\nOrder Total: ${session['cart_total']:.2f}"

        db.session.commit()

        user = app.config['GMAIL_USER']
        app_password = app.config['GMAIL_APP_PASSWORD']
        to = User.query.filter_by(user_id=current_user.user_id).first().email
        subject = 'DessertbyDaya - Order Confirmation'

        with yagmail.SMTP(user, app_password) as yag:
            yag.send(to, subject, email_content, cc=request.form.get('email'))

        if 'cart' in session:
            del(session['cart'])

    return jsonify(captured_payment)


# APPROVE PAYMENT
def approve_payment(orderId):
    api_link = f"{app.config['PAYPAL_API']}/checkout/orders/{orderId}/capture"
    client_id = app.config['PAYPAL_CLIENT_ID']
    secret = app.config['PAYPAL_SECRET']
    basic_auth = HTTPBasicAuth(client_id, secret)
    headers = {
        "Content-Type": "application/json",
    }
    # Terp Store has the same error - maybe install issue
    response = requests.post(url=api_link, headers=headers, auth=basic_auth)
    response.raise_for_status()
    json_data = response.json()
    return json_data

# ORDER VIEW
@app.route('/order-view')
def order_view():
    return render_template("order-view.html")
# ------------------------------------------------- ROUTES FOR MANAGER--------------------------------------------
# our product edit page is their manage product & our product add page is their product entry
# PRODUCT EDIT
# make product edit html page (add buttons)
# add new product button leads to next route
# exit buttons should lead to product delete
@app.route('/product/edit')
@login_required
@role_required(['MANAGER'])
def product_edit():
    products = Product.query.order_by(Product.product_name).all()
    return render_template('product-edit.html', products=products)

# ADD NEW PRODUCT
# create add new product page (product-edit.html) model after terp store
@app.route('/product/add', methods=['GET', 'POST'])
@login_required
@role_required(['MANAGER'])
def product_add():
    if request.method == 'GET':
        product_categories = ProductCategory.query.order_by(ProductCategory.category_name) \
        .order_by(ProductCategory.category_name) \
        .all()
        return render_template('product-add.html', product_categories=product_categories, action='create')
    elif request.method == 'POST':
        product_name = request.form['product_name']
        product_category_id = request.form['product_category_id']
        product_description = request.form['product_description']
        product_price = request.form['product_price']
        product_image = request.files['product_image']
        # filename field is not in the table
        product_filename = secure_filename(product_image.filename)

        if product_image.filename != '':
            product_image.save(os.path.join(basedir, app.config['PRODUCT_UPLOAD_PATH'], product_filename))

        product = Product(product_name=product_name, category_id=product_category_id,
                          product_description=product_description,
                          product_price=product_price, product_image=product_filename if product_image else '')
        db.session.add(product)
        db.session.commit()
        flash(f'{product_name} was successfully added!', 'success')
        return redirect(url_for('product_edit'))

    # Address issue where unsupported HTTP request method is attempted
    flash(f'Invalid request. Please contact support if this problem persists.', 'error')
    return redirect(url_for('product_edit'))

# PRODUCT UPDATE
@app.route('/product/update/<int:product_id>', methods=['GET', 'POST'])
@login_required
@role_required(['MANAGER'])
def product_update(product_id):
    if request.method == 'GET':
        product = Product.query.filter_by(product_id=product_id).first()
        product_categories = ProductCategory.query.order_by(ProductCategory.category_name) \
        .order_by(ProductCategory.category_name) \
        .all()

        if product:
            return render_template('product-add.html', product=product, product_categories=product_categories, action='update')

        else:
            flash(f'Product attempting to be edited could not be found!', 'error')

    elif request.method == 'POST':
        product = Product.query.filter_by(product_id=product_id).first()

        if product:
            product.product_name = request.form['product_name']
            product.category_id = request.form['product_category_id']
            product.product_description = request.form['product_description']
            product.product_price = request.form['product_price']
            product_image = request.files['product_image']

            # When a new image is provided, or there is a desire to delete the current image, attempt to delete it
            if 'delete_product_image' in request.form or product_image:
                try:
                    os.remove(os.path.join(basedir, app.config['PRODUCT_UPLOAD_PATH'], product.product_image))
                    product.product_image = ''
                except:
                    pass

                product_filename = secure_filename(product_image.filename)

                if product_image.filename != '':
                    # look into this error
                    product_image.save(os.path.join(basedir, app.config['PRODUCT_UPLOAD_PATH'], product_filename))
                    product.product_image = product_filename if product_image else ''

            db.session.commit()
            flash(f'{product.product_name} was successfully updated!', 'success')
        else:
            flash(f'Product attempting to be edited could not be found!', 'error')

        return redirect(url_for('product_edit'))

    # Address issue where unsupported HTTP request method is attempted
    flash(f'Invalid request. Please contact support if this problem persists.', 'error')
    return redirect(url_for('product_edit'))

# PRODUCT DELETE
@app.route('/product/delete/<int:product_id>')
@login_required
@role_required(['MANAGER'])
def product_delete(product_id):
    product = Product.query.filter_by(product_id=product_id).first()
    if product:
        try:
            os.remove(os.path.join(app.config['PRODUCT_UPLOAD_PATH'], product.product_image))
        except:
            pass
        db.session.delete(product)
        db.session.commit()
        flash(f'{product} was successfully deleted!', 'success')
    else:
        flash(f'Delete failed! Product could not be found.', 'error')

    return redirect(url_for('product_edit'))

# CUSTOMER VIEW ALL
@app.route('/customer/view')
@login_required
@role_required(['EMPLOYEE', 'MANAGER'])
def customer_view_all():
    customers = Customer.query.outerjoin(User, Customer.user_id == User.user_id) \
        .add_entity(User) \
        .order_by(User.last_name, User.first_name) \
        .all()
    return render_template('customer_view_all.html', customers=customers)


# ORDER STATUS
@app.route('/order-status')
def order_status():
    return render_template("order-status.html")

# MESSAGE VIEW
# create message view all html page
@app.route('/message/view')
@login_required
@role_required(['EMPLOYEE', 'MANAGER'])
def message_view_all():
    messages = Messages.query.order_by(Messages.time.desc()).all()
    return render_template('message-view-all.html', messages=messages)

# MESSAGE DELETE
@app.route('/message/delete/<int:message_id>')
@login_required
@role_required(['MANAGER'])
def message_delete(message_id):
    message = Messages.query.filter_by(message_id=message_id).first()
    if message:
        db.session.delete(message)
        db.session.commit()
        flash(f'Message was successfully deleted!', 'success')
    else:
        flash(f'Delete failed! Message could not be found.', 'error')

    return redirect(url_for('message_view_all'))

#---------------anayltics-----------------------
@app.route('/financial-analytics')
def financial_analytics():
    return render_template('financial_analytics.html')
@app.route('/product-analytics')
def product_analytics():
    return render_template('product_analytics.html')

if __name__ == '__main__':
    app.run()