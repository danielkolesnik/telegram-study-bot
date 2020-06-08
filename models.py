import time


def map_categories(cursor):
    categories = ()
    for result_set_row in cursor:
        category = {
            'id': result_set_row[0],
            'name': result_set_row[1]
        }
        categories += (category,)
    return categories


def map_products(cursor):
    products = ()
    for result_set_row in cursor:
        product = {
            'id': result_set_row[0],
            'name': result_set_row[1],
            'price': result_set_row[2],
            'description': result_set_row[3],
            'category_id': result_set_row[4],
            'category': {
                'id': result_set_row[4],
                'name': result_set_row[5]
            }
        }
        products += (product,)
    return products


def map_baskets(cursor, connection):
    baskets = ()
    for result_set_row in cursor:
        basket = {
            'id': result_set_row[0],
            'user': result_set_row[1]
        }
        baskets_products_cursor = connection.execute(
            "SELECT p.id, p.name, p.price, p.description, p.category_id, c.name FROM products_to_baskets pb "
            "INNER JOIN products p ON pb.product_id = p.id "
            "INNER JOIN categories c ON p.category_id = c.id WHERE pb.basket_id = ?", (basket['id'],))
        basket['products'] = map_products(baskets_products_cursor)
        baskets += (basket,)
    return baskets


def map_deliveries(cursor):
    deliveries = ()
    for result_set_row in cursor:
        delivery = {
            'id': result_set_row[0],
            'street': result_set_row[1],
            'house': result_set_row[2],
            'note': result_set_row[3],
            'user': result_set_row[4],
            'phone': result_set_row[5]
        }
        deliveries += (delivery,)
    return deliveries


def map_orders(cursor, connection):
    orders = ()
    for result_set_row in cursor:
        order = {
            'id': result_set_row[0],
            'created_at': result_set_row[1],
            'delivery_id': result_set_row[2],
            'basket_id': result_set_row[3],
            'delivery': {
                'id': result_set_row[4],
                'street': result_set_row[5],
                'house': result_set_row[6],
                'note': result_set_row[7],
                'user': result_set_row[8],
                'phone': result_set_row[9]
            },
            'basket': {
                'id': result_set_row[10],
                'user': result_set_row[11],
                'products': ()
            }
        }
        baskets_products_cursor = connection.execute(
            "SELECT p.id, p.name, p.price, p.description, p.category_id, c.name FROM products p "
            "INNER JOIN categories c ON p.category_id = c.id")
        for products_result_set_row in baskets_products_cursor:
            product = {
                'id': products_result_set_row[0],
                'name': products_result_set_row[1],
                'price': products_result_set_row[2],
                'description': products_result_set_row[3],
                'category_id': products_result_set_row[4],
                'category': products_result_set_row[5]
            }
            order['basket']['products'] += (product,)
        orders += (order,)
    return orders


def get_categories(connection):
    cursor = connection.execute("SELECT c.id, c.name FROM categories c")
    return map_categories(cursor)


def get_products(connection, category=None):
    if category is not None:
        cursor = connection.execute("SELECT p.id, p.name, p.price, p.description, p.category_id, c.name FROM products p "
                     "INNER JOIN categories c ON p.category_id = c.id WHERE p.category_id = ?", (category['id'],))
    else:
        cursor = connection.execute("SELECT p.id, p.name, p.price, p.description, p.category_id, c.name FROM products p "
                                    "INNER JOIN categories c ON p.category_id = c.id")
    return map_products(cursor)


def get_product_by_id(connection, product_id=None):
    if product_id is not None:
        cursor = connection.execute("SELECT p.id, p.name, p.price, p.description, p.category_id, c.name FROM products p "
                                    "INNER JOIN categories c ON p.category_id = c.id WHERE p.id = ?", (product_id,))
        res = map_products(cursor)[0]
        return res


def get_baskets(connection):
    cursor = connection.execute("SELECT b.id, b.user FROM baskets b")
    return map_baskets(cursor, connection)


def get_or_create_basket_by_user(connection, user, products=()):

    baskets_count = connection.execute("SELECT COUNT() FROM baskets b WHERE b.user = ?", (str(user),)).fetchone()[0]
    if baskets_count == 0:
        print("Basket not exist, USER - {0}".format(user))
        connection.execute("INSERT INTO baskets (user) VALUES (?)", (user,))
        connection.commit()
        time.sleep(0.3)

    basket_id = connection.execute("SELECT b.id FROM baskets b WHERE b.user = ?", (str(user),)).fetchone()[0]
    time.sleep(0.3)
    print("Basket ID - {0}".format(basket_id))
    print("Products to add - {0}".format(len(products)))
    for product in products:
        connection.execute("INSERT INTO products_to_baskets (basket_id, product_id) VALUES (?, ?)", (int(basket_id), int(product['id'])))
        connection.commit()
        time.sleep(0.2)

    cursor = connection.execute("SELECT b.id, b.user FROM baskets b WHERE b.user = ?", (str(user),))

    return map_baskets(cursor, connection)[0]


def clear_basket(connection, basket_id: None):
    if basket_id is not None:
        connection.execute("DELETE FROM products_to_baskets WHERE basket_id=?", (str(basket_id),))
        connection.commit()
        time.sleep(0.2)



def get_deliveries(connection, user = None):
    cursor = None
    if user is not None:
        cursor = connection.execute("SELECT d.id, d.street, d.house, d.note, d.user, d.phone FROM deliveries d WHERE d.user = ?", (str(user),))
    else:
        cursor = connection.execute("SELECT d.id, d.street, d.house, d.note, d.user, d.phone FROM deliveries d")

    return map_deliveries(cursor)


def check_delivery_exists(connection, user):
    delivery_count = connection.execute("SELECT COUNT() FROM deliveries WHERE user = ?", (str(user),))
    if delivery_count == 0:
        return False
    else:
        return True


def create_delivery(connection, user, street="", house="", note="", phone=""):
    cursor = connection.cursor()
    cursor.execute("INSERT INTO deliveries (user, street, house, note, phone) VALUES (?, ?, ?, ?, ?)", (str(user), street, house, note, phone))
    delivery_id = cursor.lastrowid
    connection.commit()
    return get_delivery_by_id(connection, delivery_id)



def get_delivery_by_id(connection, delivery_id=None):
    if delivery_id is not None:
        cursor = connection.execute("d.id, d.street, d.house, d.note, d.user, d.phone FROM deliveries d WHERE d.id = ?", (delivery_id,))
        res = map_deliveries(cursor)[0]
        return res

def get_orders(connection):
    cursor = connection.execute(
        "SELECT o.id, o.created_at, o.delivery_id, o.basket_id, d.id, d.street, d.house, d.note, d.user, d.phone, b.id, b.user FROM orders o "
        "INNER JOIN deliveries d ON d.id = o.delivery_id "
        "INNER JOIN baskets b ON b.id = o.basket_id")
    return map_orders(cursor, connection)


def get_order_by_id(connection, order_id=None):
    if order_id is not None:
        cursor = connection.execute(
            "SELECT o.id, o.created_at, o.delivery_id, o.basket_id, d.id, d.street, d.house, d.note, d.user, d.phone, b.id, b.user FROM orders o "
            "INNER JOIN deliveries d ON d.id = o.delivery_id "
            "INNER JOIN baskets b ON b.id = o.basket_id WHERE o.id=?", (order_id,))
        return map_orders(cursor, connection)[0]


def create_order(connection, delivery_id, basket_id, created_at=""):
    cursor = connection.cursor()
    cursor.execute("INSERT INTO orders (created_at, delivery_id, basket_id) VALUES (?, ?, ?)", (created_at, delivery_id, basket_id))
    order_id = cursor.lastrowid
    connection.commit()

    return get_order_by_id(connection, order_id)


