

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
            "SELECT p.id, p.name, p.price, p.description, p.category_id, c.name FROM products p "
            "INNER JOIN categories c ON p.category_id = c.id")
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

    baskets_count = connection.execute("SELECT COUNT() FROM baskets b WHERE b.user = ?", (user,)).fetchone()[0]
    if baskets_count == 0:
        connection.execute("INSERT INTO baskets (user) VALUES (?)", (user,))

    basket_id = connection.execute("SELECT b.id FROM baskets b WHERE b.user = ?", (user,)).fetchone()[0]
    if len(products) > 0:
        for product in products:
            connection.execute("INSERT INTO products_to_baskets (basket_id, product_id) VALUES (?, ?)", (basket_id, product['id']))

    cursor = connection.execute("SELECT b.id, b.user FROM baskets b WHERE b.user = ?", (user,))

    return map_baskets(cursor, connection)[0]


def get_deliveries(connection):
    cursor = connection.execute("SELECT d.id, d.street, d.house, d.note, d.user, d.phone FROM deliveries d")
    return map_deliveries(cursor)


def get_orders(connection):
    cursor = connection.execute(
        "SELECT o.id, o.created_at, o.delivery_id, o.basket_id, d.id, d.street, d.house, d.note, d.user, d.phone, b.id, b.user FROM orders o "
        "INNER JOIN deliveries d ON d.id = o.delivery_id "
        "INNER JOIN baskets b ON b.id = o.basket_id")
    return map_orders(cursor, connection)




