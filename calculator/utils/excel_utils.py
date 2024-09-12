import pandas as pd

def read_patent_data(file_path):
    """
    Read the patent information from the Excel file and return two DataFrames: 
    one with the full data and another with the processed necessary columns.

    Parameters:
    - file_path (str): The file path of the Excel file containing the patent information.

    Returns:
    - full_df (DataFrame): The full patent information as a Pandas DataFrame.
    - processed_df (DataFrame): The processed DataFrame with necessary columns.
    """
    # Read the full Excel file
    full_df = pd.read_excel(file_path)
    
    # Specify the necessary columns for calculations
    necessary_columns = [
        'Patent/ Publication Number', 
        'Publication Country', 
        'Priority Date', 
        'File Date', 
        'Publication Date', 
        'Est. Expiration Date', 
        'Number of claims'
    ]
    
    # Filter the DataFrame to keep only the necessary columns
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
        priority_date = row['Priority Date']
        filing_date = row['File Date']  # Change from 'Filing Date'
        issued_date = row['Publication Date']  # Change from 'Issued Date'
        expiration_date = row['Est. Expiration Date']  # Change from 'Expiration Date'
        numofclaims = row['Number of claims']  # Change from 'Number of Claims'

        # Append the extracted information as a tuple to the patent_info list
        patent_info.append((patent_number, priority_date, filing_date, issued_date, expiration_date, country, numofclaims))

    return patent_info
