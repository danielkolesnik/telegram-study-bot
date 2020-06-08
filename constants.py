from types import SimpleNamespace


class NestedNamespace(SimpleNamespace):
    def __init__(self, dictionary, **kwargs):
        super().__init__(**kwargs)
        for key, value in dictionary.items():
            if isinstance(value, dict):
                self.__setattr__(key, NestedNamespace(value))
            else:
                self.__setattr__(key, value)


BUTTONS = NestedNamespace({
    "MAIN": {
        "CATEGORIES": "Show Products By Categories",
        "PRODUCTS": "Show All Products",
        "HOME": "Home",
        "BASKET": "Check Cart"
    },
    "PRODUCT": {
        "INFO": "Info",
        "ADD_TO_BASKET": "Add to Cart",
    },
    "BASKET": {
        "BUY_NOW": "Buy now",
        "CLEAR": "Clear cart"
    },
    "DELIVERY": {
        "CREATE": "Create new",
        "ACCEPT": "Save",
        "CANCEL": "Cancel"
    },
    "ORDER": {
        "ACCEPT": "Order",
        "CANCEL": "Cancel"
    }
})

CALLBACK = NestedNamespace({
    "CATEGORY": {
        "SELECT": "CATEGORY@SELECT"
    },
    "PRODUCT": {
        "INFO": "PRODUCT@INFO",
        "ADD_TO_BASKET": "PRODUCT@BASKET",
        "BUY_NOW": "PRODUCT@BUY_NOW"
    },
    "BASKET": {
        "CLEAR": "BASKET@CLEAR"
    },
    "DELIVERY": {
        "SELECTED_FOR_ORDER": "DELIVERY@SELECTED_FOR_ORDER",
        "CREATE": "DELIVERY@CREATE",
        "SAVE": "DELIVERY@SAVE",
        "CANCEL": "DELIVERY@CANCEL"
    },
    "ORDER": {
        "INIT": "ORDER@INIT",
        "ACCEPT": "ORDER@APPROVE",
        "CANCEL": "ORDER@CANCEL",
        "DELIVERY_SELECTED": "ORDER@DELIVERY_SELECTED"
    }
})

DELIVERY_CREATION_STAGE = NestedNamespace({
    "STREET": "STREET",
    "HOUSE": "HOUSE",
    "NOTE": "NOTE",
})

STATES = NestedNamespace({
    "MAIN": "MAIN",
    "CATEGORIES": {
        "ALL": "CATEGORIES@ALL",
    },
    "PRODUCTS": {
        "ALL": "PRODUCTS@ALL",
        "BY_CATEGORY": "PRODUCTS@CATEGORIZED",
        "ONE": "PRODUCTS@ONE",
        "ADD_TO_BASKET": "PRODUCT@BASKET",
        "INFO": "PRODUCT@INFO",
        "BUY_NOW": "PRODUCT@BUY"
    },
    "BASKET": {
        "SHOW": "BASKET@SHOW"
    },
    "ORDER": {
        "DELIVERY_SELECTION": "ORDER@DELIVERY_SELECTION",
        "DELIVERY_CREATION": "ORDER@DELIVERY_CREATION",
        "ACCEPT": "ORDER@ACCEPT"
    },
    "ANY": "ANY"
})
Price:               {1}
Category:            {2}
Description:         {3}

def create_product_message(product):
    message = "```" \
              "\n{0}" \
              "\n==================" \
              "\nPrice:\t\t\t\t{1}" \
              "\nCategory:\t\t\t{2}" \
              "\nDescription:\t\t\t{3}" \
              "\n```".format(product['name'], product['price'], product['category']['name'], product['description'])
    return message


def create_basket_message(basket):
    message = "```" \
              "\nYour Cart:" \
              "\n=================="
    message += "\nProduct\t\t\t\tPrice"
    message += "\n=================="
    price: float = 0
    for product in basket['products']:
        message += "\n{0}....................{1}".format(product['name'], product['price'])
        price += float(product['price'])
    message += "\n=================="\
               "\nTOTAL:....................{0}" \
               "\n```".format(price)
    return message


def create_delivery_message(delivery):
    message = "```" \
              "\n==================" \
              "\nDelivery Option" \
              "\n==================" \
              "\nStreet...............{0}" \
              "\nHouse...............{1}" \
              "\nNote:" \
              "\n{2}" \
              "```".format(delivery['street'], delivery['house'], delivery['note'])
    return message


def create_order_message(order):
    message = "```" \
              "\nThank you for your Order!" \
              "\nQuick recap:" \
              "\n=================="
    message += "\nProduct\t\t\t\tPrice"
    message += "\n=================="
    price: float = 0
    for product in order['basket']['products']:
        message += "\n{0}....................{1}".format(product['name'], product['price'])
        price += float(product['price'])
    message += "\n==================" \
               "\nTOTAL:...............{0}".format(price)
    message += "\n==================" \
               "\nDelivery Option" \
               "\n==================" \
               "\nStreet...............{0}" \
               "\nHouse...............{1}" \
               "\nNote:" \
               "\n{2}" \
               "```".format(order['delivery']['street'], order['delivery']['house'], order['delivery']['note'])
    return message


MESSAGES = NestedNamespace({
    "MAIN": {
        "ASK": "What R u want me 2 do?"
    },
    "PRODUCT": {
        "INFO": create_product_message,
        "BASKET": create_basket_message
    },
    "ORDER": {
        "INFO": create_order_message
    },
    "DELIVERY": {
        "INFO": create_delivery_message
    }
})
