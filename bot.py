# Outsource
from datetime import datetime

import telebot
from telebot import types
import sqlite3
import json
import time

# local dependencies
import config
from constants import BUTTONS, STATES, MESSAGES, CALLBACK, DELIVERY_CREATION_STAGE
from models import get_categories, get_products, get_baskets, get_deliveries, get_orders, get_product_by_id, get_or_create_basket_by_user, check_delivery_exists, clear_basket, create_delivery, \
    get_delivery_by_id, create_order

# create TeleBot instance
bot = telebot.TeleBot(config.token)
# Setup connection to the DB
conn = sqlite3.connect(config.db_source)

# Initialize base entities
users = {}
categories = ()
products = ()
baskets = ()
deliveries = ()
orders = ()

# fill categories from DB
categories = get_categories(conn)

# fill products from DB
products = get_products(conn)

# fill baskets from DB
baskets = get_baskets(conn)

# fill deliveries from DB
deliveries = get_deliveries(conn)

# fill orders from DB
orders = get_orders(conn)

conn.close()


def main(message):
    main_keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, row_width=1)
    # Define base buttons from bottom menu
    categories_btn = types.KeyboardButton(BUTTONS.MAIN.CATEGORIES)
    products_btn = types.KeyboardButton(BUTTONS.MAIN.PRODUCTS)
    home_btn = types.KeyboardButton(BUTTONS.MAIN.HOME)
    basket_btn = types.KeyboardButton(BUTTONS.MAIN.BASKET)
    # Add buttons to the layout
    main_keyboard.row(categories_btn, products_btn)
    main_keyboard.row(home_btn, basket_btn)

    # Set current user state
    global users
    users[message.chat.id]['current_state'] = STATES.MAIN
    users[message.chat.id]['previous_state'] = STATES.MAIN

    bot.send_message(message.chat.id, MESSAGES.MAIN.ASK, reply_markup=main_keyboard)


def check_session(message):
    if message.chat.id in users.keys():
        return True
    else:
        return False


@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.username is None:
        bot.send_message(message.chat.id, "Hello y'all! Welcome to our improvised shop!")
    else:
        bot.send_message(message.chat.id, "Hello, " + message.chat.username + "! Welcome to our improvised shop!")
    global users
    users[message.chat.id] = {
        'username': message.chat.username,
        'current_state': STATES.MAIN,
        'previous_state': STATES.MAIN,
        'delivery_creation_stage': None,
        'street': None,
        'house': None,
        'note': None
    }
    main(message)


@bot.message_handler(func=lambda message: message.text == BUTTONS.MAIN.CATEGORIES, content_types=["text"])
def handle_categories_list(message):
    if not check_session(message):
        return start(message)

    categories_keyboard = types.InlineKeyboardMarkup()

    for category in categories:
        category_button = types.InlineKeyboardButton(
            text=category['name'],
            callback_data=json.dumps({'type': CALLBACK.CATEGORY.SELECT, 'payload': category['id']})
        )
        categories_keyboard.add(category_button)

    bot.send_message(message.chat.id, "Select category to browse:", reply_markup=categories_keyboard)

    users[message.chat.id]['current_state'] = STATES.CATEGORIES.ALL
    users[message.chat.id]['previous_state'] = STATES.MAIN


@bot.message_handler(func=lambda message: check_session(message) and message.text == BUTTONS.MAIN.PRODUCTS, content_types=["text"])
def handle_products_list(message):
    render_products_list(products, message)

    users[message.chat.id]['current_state'] = STATES.PRODUCTS.ALL
    users[message.chat.id]['previous_state'] = STATES.MAIN


@bot.message_handler(func=lambda message: check_session(message) and message.text == BUTTONS.MAIN.HOME, content_types=["text"])
def handle_home(message):
    main(message)


@bot.message_handler(func=lambda message: check_session(message) and message.text == BUTTONS.MAIN.BASKET, content_types=["text"])
def handle_basket(message):
    conn = sqlite3.connect(config.db_source)
    basket = get_or_create_basket_by_user(conn, message.from_user.id)
    basket_message = MESSAGES.PRODUCT.BASKET(basket)
    basket_keyboard = types.InlineKeyboardMarkup()
    order_button = types.InlineKeyboardButton(
        text=BUTTONS.BASKET.BUY_NOW,
        callback_data=json.dumps({'type': CALLBACK.ORDER.INIT, 'payload': basket['id']})
    )
    clear_btn = types.InlineKeyboardButton(
        text=BUTTONS.BASKET.CLEAR,
        callback_data=json.dumps({'type': CALLBACK.BASKET.CLEAR, 'payload': basket['id']})
    )
    basket_keyboard.row(order_button, clear_btn)
    bot.send_message(message.chat.id, basket_message, parse_mode='Markdown', reply_markup=basket_keyboard)

    users[message.chat.id]['current_state'] = STATES.BASKET.SHOW
    users[message.chat.id]['previous_state'] = STATES.ANY


@bot.callback_query_handler(func=lambda call: check_session(call.message))
def handle_callbacks(call):
    data = json.loads(call.data)
    global users

    print(data)  # log callback data

    if data['type'] == CALLBACK.CATEGORY.SELECT and users[call.message.chat.id]['current_state'] == STATES.CATEGORIES.ALL:
        category = next((category for category in categories if category['id'] == data['payload']))
        conn = sqlite3.connect(config.db_source)
        products_categorized = get_products(conn, category)

        render_products_list(products_categorized, call.message)
        conn.close()

        users[call.message.chat.id]['current_state'] = STATES.PRODUCTS.BY_CATEGORY
        users[call.message.chat.id]['previous_state'] = STATES.CATEGORIES.ALL

    elif data['type'] == CALLBACK.PRODUCT.INFO:
        conn = sqlite3.connect(config.db_source)
        product = next((product for product in products if product['id'] == data['payload']), get_product_by_id(conn, data['payload']))
        conn.close()
        message = MESSAGES.PRODUCT.INFO(product)
        product_keyboard = types.InlineKeyboardMarkup()
        product_basket_button = types.InlineKeyboardButton(
            text=BUTTONS.PRODUCT.ADD_TO_BASKET,
            callback_data=json.dumps({'type': CALLBACK.PRODUCT.ADD_TO_BASKET, 'payload': product['id']})
        )
        product_keyboard.add(product_basket_button)
        bot.send_message(call.message.chat.id, message, parse_mode='Markdown', reply_markup=product_keyboard)

        users[call.message.chat.id]['current_state'] = STATES.PRODUCTS.INFO
        users[call.message.chat.id]['previous_state'] = STATES.ANY

    elif data['type'] == CALLBACK.PRODUCT.ADD_TO_BASKET:
        conn = sqlite3.connect(config.db_source)
        new_products: tuple = (next((product for product in products if product['id'] == data['payload']), get_product_by_id(conn, data['payload'])),)

        basket = get_or_create_basket_by_user(conn, call.from_user.id, new_products)
        conn.close()
        message = MESSAGES.PRODUCT.BASKET(basket)
        basket_keyboard = types.InlineKeyboardMarkup()
        order_btn = types.InlineKeyboardButton(
            text=BUTTONS.BASKET.BUY_NOW,
            callback_data=json.dumps({'type': CALLBACK.ORDER.INIT})
        )
        clear_btn = types.InlineKeyboardButton(
            text=BUTTONS.BASKET.CLEAR,
            callback_data=json.dumps({'type': CALLBACK.BASKET.CLEAR, 'payload': basket['id']})
        )
        basket_keyboard.row(order_btn, clear_btn)

        bot.send_message(call.message.chat.id, message, parse_mode='Markdown', reply_markup=basket_keyboard)

        if users[call.message.chat.id]['current_state'] == STATES.PRODUCTS.BY_CATEGORY:
            users[call.message.chat.id]['current_state'] = STATES.PRODUCTS.ADD_TO_BASKET
            users[call.message.chat.id]['previous_state'] = STATES.PRODUCTS.BY_CATEGORY

        elif users[call.message.chat.id]['current_state'] == STATES.PRODUCTS.ALL:
            users[call.message.chat.id]['current_state'] = STATES.PRODUCTS.ADD_TO_BASKET
            users[call.message.chat.id]['previous_state'] = STATES.PRODUCTS.ALL


    elif data['type'] == CALLBACK.ORDER.INIT:
        delivery_keyboard = types.InlineKeyboardMarkup()

        if check_delivery_exists(call.from_user.id):
            conn = sqlite3.connect(config.db_source)
            user_deliveries = get_deliveries(conn, call.from_user.id)
            for delivery in user_deliveries:
                delivery_title = "{0}, {1} (tel.{2})".format(delivery['street'], delivery['house'], delivery['phone'])
                delivery_keyboard.add(
                    types.InlineKeyboardButton(
                        text=delivery_title,
                        callback_data=json.dumps({'type': CALLBACK.ORDER.DELIVERY_SELECTED, 'payload': delivery['id']})
                    )
                )
        delivery_keyboard.add(
            types.InlineKeyboardButton(
                text=BUTTONS.DELIVERY.CREATE,
                callback_data=json.dumps({'type': CALLBACK.DELIVERY.CREATE})
            )
        )

        bot.send_message(call.message.chat.id, "Select the Appropriate Delivery Option:", reply_markup=delivery_keyboard)

        users[call.message.chat.id]['previous_state'] = users[call.message.chat.id]['current_state']
        users[call.message.chat.id]['current_state'] = STATES.ORDER.DELIVERY_SELECTION

    elif data['type'] == CALLBACK.BASKET.CLEAR:
        conn = sqlite3.connect(config.db_source)
        basket = get_or_create_basket_by_user(conn, call.from_user.id)
        clear_basket(conn, basket['id'])
        conn.close()
        bot.send_message(call.message.chat.id, "Cart Successfully Cleared...")

    elif data['type'] == CALLBACK.DELIVERY.CREATE:
        bot.send_message(call.message.chat.id, "Please enter new delivery Street Name:")
        users[call.message.chat.id]['current_state'] = STATES.ORDER.DELIVERY_CREATION
        users[call.message.chat.id]['previous_state'] = STATES.ORDER.DELIVERY_SELECTION
        users[call.message.chat.id]['delivery_creation_stage'] = DELIVERY_CREATION_STAGE.STREET

    elif data['type'] == CALLBACK.DELIVERY.SAVE:
        conn = sqlite3.connect(config.db_source)
        delivery = create_delivery(
            conn,
            call.from_user.id,
            users[call.message.chat.id]['street'],
            users[call.message.chat.id]['house'],
            users[call.message.chat.id]['note']

        )
        if users[call.message.chat.id]['previous_state'] == STATES.ORDER.DELIVERY_SELECTION:
            print("User ready to order")
            order_keyboard = types.InlineKeyboardMarkup()

            order_keyboard.add(
                types.InlineKeyboardButton(
                    text=BUTTONS.ORDER.ACCEPT,
                    callback_data=json.dumps({'type': CALLBACK.ORDER.DELIVERY_SELECTED, 'payload': delivery['id']})
                ),
                types.InlineKeyboardButton(
                    text=BUTTONS.ORDER.CANCEL,
                    callback_data=json.dumps({'type': CALLBACK.ORDER.CANCEL})
                )
            )

        else:
            print("User added new delivery")
            bot.send_message(call.message.chat.id, "Delivery successfully created")

        conn.close()

    elif data['type'] == CALLBACK.DELIVERY.CANCEL or data['type'] == CALLBACK.ORDER.CANCEL:
        users[call.message.chat.id]['street'] = None
        users[call.message.chat.id]['house'] = None
        users[call.message.chat.id]['note'] = None
        users[call.message.chat.id]['delivery_creation_stage'] = None
        bot.send_message(call.message.chat.id, "Delivery Creation Successfully Discarded")
        users[call.message.chat.id]['current_state'] = STATES.MAIN
        users[call.message.chat.id]['previous_state'] = STATES.ORDER.DELIVERY_SELECTION

    elif data['type'] == CALLBACK.ORDER.DELIVERY_SELECTED:
        conn = sqlite3.connect(config.db_source)
        delivery = get_delivery_by_id(conn, data['payload'])
        basket = get_or_create_basket_by_user(call.from_user.id)
        now = datetime.now()
        created_at = now.strftime("%Y-%m-%d %H:%M:%S")

        order = create_order(conn, delivery['id'], basket['id'], created_at)
        message = MESSAGES.ORDER.INFO(order)
        bot.send_message(call.message.chat.id, message)

    else:
        main(call.message)


@bot.message_handler(content_types=['text'])
def handle_text_input(message):
    global users
    if check_session(message) and users[message.chat.id] is not None:
        if users[message.chat.id]['current_state'] == STATES.ORDER.DELIVERY_CREATION:
            delivery_creation_keyboard = types.InlineKeyboardMarkup()
            delivery_creation_keyboard.add(
                types.InlineKeyboardButton(
                    text=BUTTONS.DELIVERY.CANCEL,
                    callback_data=json.dumps({'type': CALLBACK.DELIVERY.CANCEL})
                )
            )
            if users[message.chat.id]['delivery_creation_stage'] == DELIVERY_CREATION_STAGE.STREET:
                users[message.chat.id]['street'] = message.text
                print("USER ENTERED NEW STREET: - {0}".format(message.text))
                bot.send_message(message.chat.id, "Enter House Number:", reply_markup=delivery_creation_keyboard)
                users[message.chat.id]['delivery_creation_stage'] = DELIVERY_CREATION_STAGE.HOUSE
            elif users[message.chat.id]['delivery_creation_stage'] == DELIVERY_CREATION_STAGE.HOUSE:
                users[message.chat.id]['house'] = message.text
                print("USER ENTERED NEW HOUSE: - {0}".format(message.text))

                bot.send_message(message.chat.id, "Note(optional):", reply_markup=delivery_creation_keyboard)
                users[message.chat.id]['delivery_creation_stage'] = DELIVERY_CREATION_STAGE.NOTE
            elif users[message.chat.id]['delivery_creation_stage'] == DELIVERY_CREATION_STAGE.NOTE:
                users[message.chat.id]['note'] = message.text
                print("USER ENTERED NEW NOTE: - {0}".format(message.text))
                delivery_creation_keyboard = types.InlineKeyboardMarkup()
                delivery_creation_keyboard.row(
                    types.InlineKeyboardButton(
                        text=BUTTONS.DELIVERY.ACCEPT,
                        callback_data=json.dumps({'type': CALLBACK.DELIVERY.SAVE})
                    ),
                    types.InlineKeyboardButton(
                        text=BUTTONS.DELIVERY.CANCEL,
                        callback_data=json.dumps({'type': CALLBACK.DELIVERY.CANCEL})
                    )
                )
        else:
            bot.send_message(message.chat.id, "Sorry I dont know what u want... Try using my keyboard instead..")
    else:
        bot.send_message(message.chat.id, "Hey looks like something strange happened, lets try again with `/start`", parse_mode='Markdown')




"""
Utils
"""


def render_products_list(products_list, message):
    for product in products_list:
        product_keyboard = types.InlineKeyboardMarkup()
        product_info_button = types.InlineKeyboardButton(
            text=BUTTONS.PRODUCT.INFO,
            callback_data=json.dumps({'type': CALLBACK.PRODUCT.INFO, 'payload': product['id']})
        )
        product_basket_button = types.InlineKeyboardButton(
            text=BUTTONS.PRODUCT.ADD_TO_BASKET,
            callback_data=json.dumps({'type': CALLBACK.PRODUCT.ADD_TO_BASKET, 'payload': product['id']})
        )
        product_keyboard.add(product_info_button, product_basket_button)
        product_title = product["name"]
        bot.send_message(message.chat.id, product_title, reply_markup=product_keyboard)
        time.sleep(0.4)


if __name__ == "__main__":
    bot.polling(none_stop=True)
