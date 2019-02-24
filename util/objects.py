

class Singleton(type):
    """
    Ensure a class only has one instance, and provide a global point of
    access to it.
    Use: class MyClass(metaclass=Singleton):...
    """

    def __init__(cls, name, bases, attrs, **kwargs):
        super().__init__(name, bases, attrs)
        cls._instance = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__call__(*args, **kwargs)
        return cls._instance
