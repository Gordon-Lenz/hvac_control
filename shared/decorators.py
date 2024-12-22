# shared/decorators.py
import logging
import time
from sqlalchemy.exc import OperationalError, ProgrammingError

def log_exceptions(func):
    """
    Decorator to log exceptions raised by a function.
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.exception(f"Exception in {func.__name__}: {e}")  # Log the exception with traceback
            raise  # Re-raise the exception to be handled elsewhere

    return wrapper

def retry_on_failure(max_retries=3, delay=5):
    """
    Decorator to retry a function in case of specific exceptions.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except (OperationalError, ProgrammingError) as e:  # Catch specific database errors
                    logging.warning(f"Database error in {func.__name__}: {e}. Retrying in {delay} seconds...")
                    retries += 1
                    time.sleep(delay)
            # If all retries fail, log an error and re-raise the exception
            logging.error(f"Failed to execute {func.__name__} after {max_retries} retries.")
            raise

        return wrapper
    return decorator