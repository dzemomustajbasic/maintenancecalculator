import pandas as pd
import logging
from .exceptions import MissingRequiredColumnsError

def read_patent_data(file_path):
    """
    Read the patent information from the Excel file and return two DataFrames: 
    one with the full data and another with the processed necessary columns.
    """
    try:
        full_df = pd.read_excel(file_path)
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        raise
    except Exception as e:
        logging.error(f"Error reading Excel file {file_path}: {e}")
        raise

    # Define necessary columns
    necessary_columns = [
        'Patent/ Publication Number', 
        'Publication Country', 
        'Type', 
        'File Date', 
        'Publication Date', 
        'Est. Expiration Date', 
        'Number of claims'
    ]

    # Check if necessary columns are present
    missing_columns = [col for col in necessary_columns if col not in full_df.columns]
    if missing_columns:
        raise MissingRequiredColumnsError(missing_columns, necessary_columns)

    processed_df = full_df[necessary_columns].copy()
    return full_df, processed_df


def extract_patent_info(patent_df):
    """
    Extract relevant information such as priority date, filing date, issued date,
    expiration date, country, and number of claims for each patent from the processed DataFrame.

    Parameters:
    - patent_df (DataFrame): The processed DataFrame with necessary columns.

    Returns:
    - patent_info (list of tuples): List of tuples containing (patent_number, priority_date, 
      filing_date, issued_date, expiration_date, country, numofclaims) for each patent.
    """
    patent_info = []

    # Loop through each row in the DataFrame
    for index, row in patent_df.iterrows():
        # Extract relevant information
        patent_number = row['Patent/ Publication Number']  # Change from 'Patent / Publication Number'
        country = row['Publication Country']  # Change from 'Country Code'
        type = row['Type'] # Added
        filing_date = row['File Date']  # Change from 'Filing Date'
        issued_date = row['Publication Date']  # Change from 'Issued Date'
        expiration_date = row['Est. Expiration Date']  # Change from 'Expiration Date'
        numofclaims = row['Number of claims']  # Change from 'Number of Claims'

        # Append the extracted information as a tuple to the patent_info list
        patent_info.append((patent_number, type, filing_date, issued_date, expiration_date, country, numofclaims))

    return patent_info
