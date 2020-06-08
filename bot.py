# Outsource
import telebot
from telebot import types
import sqlite3
import json
from datetime import date, timedelta
from datetime import datetime
import time
import re
import calendar

# local dependencies
import config
from constants import BUTTONS, STATES, MESSAGES, CALLBACK
from models import get_categories, get_products, get_baskets, get_deliveries, get_orders, get_product_by_id, get_or_create_basket_by_user

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
        'current_state': STATES.MAIN,
        'previous_state': STATES.MAIN,
        'username': message.chat.username}
    main(message)


@bot.message_handler(func=lambda message: check_session(message) and message.text == BUTTONS.MAIN.CATEGORIES, content_types=["text"])
def handle_categories_list(message):
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
    message = MESSAGES.PRODUCT.BASKET(basket)
    basket_keyboard = types.InlineKeyboardMarkup()
    order_button = types.InlineKeyboardButton(
        text=BUTTONS.PRODUCT.BUY_NOW,
        callback_data=json.dumps({'type': CALLBACK.ORDER, 'payload': basket['id']})
    )
    basket_keyboard.add(order_button)
    bot.send_message(message.chat.id, message, parse_mode='Markdown', reply_markup=basket_keyboard)

    users[message.chat.id]['current_state'] = STATES.BASKET.SHOW
    users[message.chat.id]['previous_state'] = STATES.ANY


@bot.callback_query_handler(func=lambda call: check_session(call.message) and
  users[call.message.chat.id]['current_state'] == STATES.CATEGORIES.ALL)
def handle_products_list_categorized(call):
    data = json.loads(call.data)

    print(data)  # log

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
        product_buy_now_button = types.InlineKeyboardButton(
            text=BUTTONS.PRODUCT.BUY_NOW,
            callback_data=json.dumps({'type': CALLBACK.PRODUCT.BUY_NOW, 'payload': product['id']})
        )
        product_keyboard.add(product_basket_button, product_buy_now_button)
        bot.send_message(call.message.chat.id, message, parse_mode='Markdown', reply_markup=product_keyboard)

    elif data['type'] == CALLBACK.PRODUCT.ADD_TO_BASKET:
        conn = sqlite3.connect(config.db_source)
        new_products: tuple = ()

        if data['payload'] is not None:
            new_products += (next((product for product in products if product['id'] == data['payload']), get_product_by_id(conn, data['payload'])),)

        basket = get_or_create_basket_by_user(conn, call.from_user.id, new_products)
        message = MESSAGES.PRODUCT.BASKET(basket)
        basket_keyboard = types.InlineKeyboardMarkup()
        order_button = types.InlineKeyboardButton(
            text=BUTTONS.PRODUCT.BUY_NOW,
            callback_data=json.dumps({'type': CALLBACK.ORDER, 'payload': basket['id']})
        )
        basket_keyboard.add(order_button)
        bot.send_message(call.message.chat.id, message, parse_mode='Markdown', reply_markup=basket_keyboard)

        if users[call.message.chat.id]['current_state'] == STATES.PRODUCTS.BY_CATEGORY:
            users[call.message.chat.id]['current_state'] = STATES.PRODUCTS.ADD_TO_BASKET
            users[call.message.chat.id]['previous_state'] = STATES.PRODUCTS.BY_CATEGORY

        elif users[call.message.chat.id]['current_state'] == STATES.PRODUCTS.ALL:
            users[call.message.chat.id]['current_state'] = STATES.PRODUCTS.ADD_TO_BASKET
            users[call.message.chat.id]['previous_state'] = STATES.PRODUCTS.ALL

    elif data['type'] == CALLBACK.PRODUCT.BUY_NOW:
        pass

    elif data['type'] == CALLBACK.ORDER:

        pass
    # <-- HANDLE REST OF CALLBACKS HERE

    else:
        main(call.message)


def handle_product_info(message):
    return None


def handle_product_basket(message):
    return None


def handle_product_buy_now(message):
    return None


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
        product_buy_now_button = types.InlineKeyboardButton(
            text=BUTTONS.PRODUCT.BUY_NOW,
            callback_data=json.dumps({'type': CALLBACK.PRODUCT.BUY_NOW, 'payload': product['id']})
        )
        product_keyboard.add(product_info_button, product_basket_button, product_buy_now_button)
        product_title = product["name"]
        bot.send_message(message.chat.id, product_title, reply_markup=product_keyboard)
        time.sleep(0.4)


if __name__ == "__main__":
    bot.polling(none_stop=True)
