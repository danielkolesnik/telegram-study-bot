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
        "HOME": "Home"
    },
    "PRODUCT": {
        "INFO": "Info",
        "ADD_TO_BUCKET": "Add to Cart",
        "BUY_NOW": "Buy now"
    }
})

MESSAGES = NestedNamespace({
    "MAIN": {
        "ASK": "Hello there! What R u want me 2 do?"
    },
    "PRODUCT": {
        ""
    }
})

CALLBACK = NestedNamespace({
    "CATEGORY": {
        "SELECT": "CATEGORY@SELECT"
    },
    "PRODUCT": {
        "INFO": "PRODUCT@INFO",
        "ADD_TO_BUCKET": "PRODUCT@BUCKET",
        "BUY_NOW": "PRODUCT@BUY_NOW"
    }
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
        "ADD_TO_BUCKET": "PRODUCT@BUCKET",
        "INFO": "PRODUCT@INFO",
        "BUY_NOW": "PRODUCT@BUY"
    },
})
