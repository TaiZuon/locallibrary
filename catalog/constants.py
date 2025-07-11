# enum class
from enum import Enum

class LoanStatus(Enum):
    """
    Enum representing the status of a loan.
    """
    MAINTENANCE = 'm'
    ON_LOAN = 'o'
    AVAILABLE = 'a'
    RESERVED = 'r'

# Maximum lengths for CharFields
MAX_LENGTH_TITLE = 200
MAX_LENGTH_NAME = 100
MAX_LENGTH_SUMMARY = 100
MAX_LENGTH_ISBN = 13
MAX_LENGTH_IMPRINT = 200
