import pandas as pd

def read_fees_data(file_path):
    """
    Read the fees data from the Excel file and return it as a Pandas DataFrame.

    Parameters:
    - file_path (str): The file path of the Excel file containing the fees data.

    Returns:
    - fees_df (DataFrame): The fees data as a Pandas DataFrame.
    """
    # Read the Excel file and specify data types if needed
    fees_df = pd.read_excel(file_path)
    
    # Print the first few rows of the DataFrame to verify data loading
    #print(fees_df)
    
    # Return the DataFrame
    return fees_df
