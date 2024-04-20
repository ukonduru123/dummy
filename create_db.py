from app import app, db
from models import *
from werkzeug.security import generate_password_hash

with app.app_context():
    db.drop_all()
    db.create_all()

# Initial loading of customers
    customers = [
        {'user_id': 1}
    ]

    for each_customer in customers:
        print(f'{each_customer["user_id"]} inserted into customer')
        a_customer = Customer(each_customer["user_id"])
        db.session.add(a_customer)
        db.session.commit()

# Initial loading of users
    users = [
        # sample
        # --- USER: MANAGER - Daya
        {'username': 'daya', 'email': 'admin@umd.edu', 'first_name': 'Daya', 'last_name': 'Novich',
         'password': generate_password_hash('dayapw', method='pbkdf2:sha256'), 'role': 'ADMIN'},

        # --- USER: EMPLOYEE - TBD
        {'username': 'manager', 'email': 'manager@umd.edu', 'first_name': 'Joe', 'last_name': 'King',
         'password': generate_password_hash('managerpw', method='pbkdf2:sha256'), 'role': 'MANAGER'},

        # --- USER: CUSTOMER
        {'username': 'customer1', 'email': 'vlee791@terpmail.umd.edu', 'first_name': 'Victor', 'last_name': 'Lee',
         'password': generate_password_hash('customer1pw', method='pbkdf2:sha256'), 'role': 'CUSTOMER'},

        {'username': 'customer2', 'email': 'cmacaira@terpmail.umd.edu', 'first_name': 'Celine', 'last_name': 'Macairan',
         'password': generate_password_hash('customer2pw', method='pbkdf2:sha256'), 'role': 'CUSTOMER'}
    ]

    for each_user in users:
        print(f'{each_user["username"]} inserted into user')
        a_user = User(username=each_user["username"], email=each_user["email"], first_name=each_user["first_name"],
                      last_name=each_user["last_name"], password=each_user["password"], role=each_user["role"])
        db.session.add(a_user)
        db.session.commit()

# Initial loading of product categories
    # removed custom orders category id
    product_categories = [
        {'category_id': 1, 'category_name': 'Cookies'},
        {'category_id': 2, 'category_name': 'Bars'},
    ]

    for each_product_category in product_categories:
        print(f'{each_product_category["category_name"]} inserted into product_category')
        a_product_category = ProductCategory(category_id=each_product_category['category_id'],
                                             category_name=each_product_category['category_name'])
        db.session.add(a_product_category)
        db.session.commit()

# Initial loading of products
    products = [
        {'product_name': 'Classic Chocolate Chip', 'product_description':'Yummy',
            'product_image': '/static/assets/chocchipcookie.jpg', 'product_price': 20, 'category_id': 1},
        {'product_name': 'Slutty Blondie','product_description': 'Also yummy',
         'product_image': '/static/assets/sluttyblondiebars.jpg', 'product_price': 20, 'category_id': 2},
    ]

    for each_product in products:
        print(f'{each_product["product_name"]} inserted into product')
        a_product = Product(product_name=each_product['product_name'],
                            product_description=each_product['product_description'], product_image=each_product['product_image'],
                            product_price=each_product['product_price'], category_id=each_product['category_id'])
        db.session.add(a_product)
        db.session.commit()

#Initial loading of messages
    # Change all messages
    messages = [
        {'time': '01/29/24 13:12:26','email': 'john.doe@umd.edu', 'message': 'My order #301 has not yet been dispatched!!'},
        {'time': '12/02/23 12:32:42', 'email': 'janed@gmail.com','message' : 'Custom Order'},
        # COMMENTED OUT THESE FIELDS BC THEY WERE RETURNING ERRORS
        #'desired_quantity': 1 ,'desired_item_description': 'two tier vanilla cake with sprinkles'
    ]

    for each_message in messages:
        print(f'{each_message["message"]} inserted into messages')
        a_message = Messages(time=dt.datetime.strptime(each_message['time'], '%m/%d/%y %H:%M:%S'), email=each_message['email'], message=each_message['message'])
        # desired_item_description=each_message['desired_item_description'] , desired_quantity=each_message['desired_quantity']
        db.session.add(a_message)
        db.session.commit()

