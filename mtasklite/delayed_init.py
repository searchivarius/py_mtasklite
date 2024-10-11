"""
    A wrapper class and a decorator to support delayed initialization through a wrapper class.
    The wrapper class constructor merely memorizes the parameters of the actual constructor as well
    as the reference to a class of interest. These parameters are used to create an ectual object
    later.

    Sample usage:

    @delayed_init
    class SomeClass:
        def __init__(self, value):
            print(f"SomeClass object initialized with value: {value}")
            self.value = value

    # Shell object created, but not yet instantiated
    shell_obj = ExpensiveObject(0)

    # Real object is initialized with value 0
    real_obj=shell_obj()
"""


class ShellObject:
    """
        A class that supports delayed initialization.
    """
    def __init__(self, cls, *args, **kwargs):
        """

        :param cls:  A references to the class of interest (to be instantiated later)
        :param args:  Constructor's positional arguments
        :param kwargs:  Constructor's keyword arguments
        """
        self.cls = cls
        self.args = args
        self.kwargs = kwargs
        self._instance = None  # Placeholder for the actual instance

    def __call__(self, *args, **kwargs):
        """
            This function actually creates the target class object.

            :return: a reference to an object of the class specified in the constructor.
        """
        if self._instance is None:
            # Only create the actual object when called
            self._instance = self.cls(*self.args, **self.kwargs)
        return self._instance(*args, **kwargs)


def delayed_init(cls):
    def wrapper(*args, **kwargs):
        return ShellObject(cls, *args, **kwargs)

    return wrapper