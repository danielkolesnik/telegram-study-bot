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
from models import get_categories, get_products, get_baskets, get_deliveries, get_orders

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


def main(message):
    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, row_width=1)
    categories_btn = types.KeyboardButton(BUTTONS.MAIN.CATEGORIES)
    products_btn = types.KeyboardButton(BUTTONS.MAIN.PRODUCTS)
    home_btn = types.KeyboardButton(BUTTONS.MAIN.HOME)
    keyboard.add(categories_btn, products_btn, home_btn)

    global users
    users[message.chat.id]['current_state'] = STATES.MAIN
    users[message.chat.id]['previous_state'] = STATES.MAIN

    bot.send_message(message.chat.id, MESSAGES.MAIN.ASK, reply_markup=keyboard)


@bot.message_handler(func=lambda message: check_session(message) and message.text == BUTTONS.MAIN.HOME, content_types=["text"])
def handle_products_list(message):
    main(message)

def check_session(message):
    if message.chat.id in users.keys():
        return True
    else:
        return False


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
def handle_categories_list(message):
    render_products_list(products, message)

    users[message.chat.id]['current_state'] = STATES.PRODUCTS.ALL
    users[message.chat.id]['previous_state'] = STATES.MAIN


@bot.callback_query_handler(func=lambda call: check_session(call.message) and
  users[call.message.chat.id]['current_state'] == STATES.CATEGORIES.ALL)
def handle_products_list_categorized(call):
    data = json.loads(call.data)
    print("\t\t[LOGGING START]")
    print(data)
    print("\t\t[LOGGING END]")
    category = next((category for category in categories if category['id'] == data['payload']))
    conn = sqlite3.connect(config.db_source)
    products_categorized = get_products(conn, category)

    render_products_list(products_categorized, call.message)
    conn.close()

    users[call.message.chat.id]['current_state'] = STATES.PRODUCTS.BY_CATEGORY
    users[call.message.chat.id]['previous_state'] = STATES.CATEGORIES.ALL


def handle_product_info(message):
    return None


def handle_product_bucket(message):
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
        product_bucket_button = types.InlineKeyboardButton(
            text=BUTTONS.PRODUCT.ADD_TO_BUCKET,
            callback_data=json.dumps({'type': CALLBACK.PRODUCT.ADD_TO_BUCKET, 'payload': product['id']})
        )
        product_buy_now_button = types.InlineKeyboardButton(
            text=BUTTONS.PRODUCT.BUY_NOW,
            callback_data=json.dumps({'type': CALLBACK.PRODUCT.BUY_NOW, 'payload': product['id']})
        )
        product_keyboard.add(product_info_button, product_bucket_button, product_buy_now_button)
        product_title = product["name"]
        bot.send_message(message.chat.id, product_title, reply_markup=product_keyboard)


if __name__ == "__main__":
    bot.polling(none_stop=True)
