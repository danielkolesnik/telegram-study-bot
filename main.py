# Outsource
import telebot
from telebot import types
import sqlite3
from datetime import date, timedelta
from datetime import datetime
import time
import re
import calendar

# local dependencies
import config
from constants import BUTTONS, STATES, MESSAGES, CALLBACK

# create TeleBot instance
from models import get_categories, get_products, get_baskets, get_deliveries, get_orders

bot = telebot.TeleBot(config.token)
# Setup connection to the DB
conn = sqlite3.connect('data')

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
    users[message.chat.id] = {'current_state': STATES.MAIN, 'previous_state': STATES.MAIN, 'nick': None, 'phone': None, 'username': message.chat.username}
    main(message)


def main(message):
    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, row_width=1)
    categories_btn = types.KeyboardButton(BUTTONS.MAIN.CATEGORIES)
    products_btn = types.KeyboardButton(BUTTONS.MAIN.PRODUCTS)
    keyboard.add(categories_btn, products_btn)

    global users
    users[message.chat.id]['current_state'] = STATES.MAIN
    users[message.chat.id]['previous_state'] = STATES.MAIN

    bot.send_message(message.chat.id, MESSAGES.MAIN.ASK)


def check_session(message):
    if message.chat.id in users.keys():
        return True
    else:
        return False

@bot.message_handler(func=lambda message: check_session(message) and
  users[message.chat.id]['current_state'] == STATES.MAIN and message.text == BUTTONS.MAIN.CATEGORIES, content_types=["text"])
def handle_categories_list(message):

    categories_keyboard = types.InlineKeyboardMarkup()

    for category in categories:
        category_button = types.InlineKeyboardButton(text=category['name'], callback_data={'type': CALLBACK.CATEGORY.SELECT, 'payload': category['id']})
        categories_keyboard.add(category_button)

    bot.send_message(message.chat.id, "Select category to brows:", reply_markup=categories_keyboard)


@bot.callback_query_handler(func=lambda call: call.data['type'] == CALLBACK.CATEGORY.SELECT)
def handle_category_selection(call):

    category = next((category for category in categories if category['id'] == call.data['payload']))
    conn = sqlite3.connect('data')
    products_cursor = conn.execute("SELECT p.id, p.name, p.price, p.description, p.category_id, c.name FROM products p "
                      "INNER JOIN categories c ON p.category_id = c.id WHERE p.category_id = ?", [category.id])

if __name__ == "__main__":
    bot.polling(none_stop=True)
