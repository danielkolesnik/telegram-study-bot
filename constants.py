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
        "PRODUCTS": "Show All Products"
    }
})

MESSAGES = NestedNamespace({
    "MAIN": {
        "ASK": "What do you want me to do"
    }
})

CALLBACK = NestedNamespace({
    "CATEGORY": {
        "SELECT": "CATEGORY@SELECT"
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
        "ONE": "PRODUCTS@ONE"
    },
})
