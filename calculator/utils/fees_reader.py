import pandas as pd
import logging
from .exceptions import ExcelFileReadError

def read_fees_data(file_path):
    """
    Read the fees data from the Excel file and return it as a Pandas DataFrame.
    """
    try:
        fees_df = pd.read_excel(file_path)
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}. Returning empty fees data.")
        return pd.DataFrame()  # Return an empty DataFrame if file is not found
    except Exception as e:
        logging.error(f"Error reading Excel file {file_path}: {e}. Returning empty fees data.")
        return pd.DataFrame()  # Return an empty DataFrame if an error occurs

    if fees_df.empty:
        logging.warning(f"Fees data is empty in {file_path}")

    return fees_df
