import pandas as pd

def add_total_fees_per_patent(results_df):
    """
    Calculate the total fees for each patent based on dynamically generated year columns.

    Parameters:
    - results_df (DataFrame): DataFrame containing the calculated fees for each year.

    Returns:
    - results_df (DataFrame): Updated DataFrame with a new 'Total Fees' column.
    """
    # Identify all columns that are years (i.e., column names that are digits)
    year_columns = [col for col in results_df.columns if col.isdigit()]
    
    # Convert the year columns to numeric, coercing errors to NaN (in case of any non-numeric values)
    results_df[year_columns] = results_df[year_columns].apply(pd.to_numeric, errors='coerce')
    
    # Calculate the sum of fees for each patent across all year columns, treating NaN as 0
    results_df['Total Fees'] = results_df[year_columns].fillna(0).sum(axis=1)

    return results_df



def calculate_grand_total(results_df):
    """
    Calculate and add a row at the end of the DataFrame with the grand total of all the total fees.

    Parameters:
    - results_df (DataFrame): DataFrame containing the calculated maintenance fees.

    Returns:
    - results_df (DataFrame): DataFrame with the grand total row added.
    """
    grand_total = results_df['Total Fees'].sum()
    
    # Create a new row for the grand total
    grand_total_row = [''] * (results_df.shape[1] - 1) + [grand_total]
    
    # Append the grand total row to the DataFrame
    results_df.loc[len(results_df)] = grand_total_row
    
    return results_df
