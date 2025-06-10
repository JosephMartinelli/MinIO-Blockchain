"""Custom errors for the blockchain.py module"""


class InvalidChain(Exception):
    def __init__(self, message):
        super().__init__(message)


class NoTransactionsFound(Exception):
    def __init__(self, message):
        super().__init__(message)


class InvalidTransactions(Exception):
    def __init__(self, message):
        super().__init__(message)


class ContractNotFound(Exception):
    def __init__(self, message):
        super().__init__(message)


class ContractError(Exception):
    def __init__(self, message):
        super().__init__(message)
