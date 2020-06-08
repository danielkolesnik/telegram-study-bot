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
        "BUY_NOW": "Buy now"
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
    "ORDER": "ORDER"
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
    "ANY": "ANY"
})


def create_info_message(product):
    message = "```{0}" \
              "\n==================" \
              "\n**Price**\t|\t{1}" \
              "\n**Category**\t|\t{2}" \
              "\n**Description\t|\t{3}**```".format(product['name'], product['price'], product['category']['name'], product['description'])
    return message


def create_basket_message(basket):
    message = "Your Cart:" \
              "\n=================="
    message += "\nProduct\t|\tPrice"
    message += "\n----------------------"
    price: float = 0
    for product in basket['products']:
        message += "\n{0}\t|\t{1}".format(product['name'], product['price'])
        price += float(product['price'])
    message += "\nTOTAL\t|\t{0}".format(price)
    return message


MESSAGES = NestedNamespace({
    "MAIN": {
        "ASK": "Hello there! What R u want me 2 do?"
    },
    "PRODUCT": {
        "INFO": create_info_message,
        "BASKET": create_basket_message
    }
})
