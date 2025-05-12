from typing import Callable
import marshal
import types
import ast


class SmartContract:
    def __init__(self, function: Callable[[...], bool]):
        self.function: Callable[[...], bool] = function
        self.encoded_func = None
        self.decoded_function = None

    @staticmethod
    def encode(func) -> str:
        func_code = getattr(func, "__code__", None)
        new_code = func_code.replace(co_filename="generated")
        encoded_func = marshal.dumps(new_code)
        return str(encoded_func)

    @staticmethod
    def decode(func: str) -> Callable:
        code_obj = marshal.loads(ast.literal_eval(func), allow_code=True)
        function = types.FunctionType(code_obj, globals())
        return function
