"""This module contains all methods and variables that are used for authentication by a node"""

import secrets

# These keys will be used to validate incoming transactions and to auth user requests
PRIVATE_KEY = secrets.token_hex(16)
PUBLIC_KEY = secrets.token_hex(16)
