import datetime
import pandas as pd
import numpy as np


def check_year_inclusion(date, date_type):
    """
    Check if the current year's fee should be included.

    Parameters:
    - date (datetime.date): The filing or issued date of the patent.
    - date_type (str): The type of date provided ('filing' or 'issued').

    Returns:
    - include_current_year (bool): Whether to include the current year in the calculations.
    """
    today = pd.Timestamp.today().date()
    current_month_day = (today.month, today.day)

    if date_type == 'filing date':
        comparison_month_day = (date.month, date.day)
    elif date_type == 'issued date':
        comparison_month_day = (date.month, date.day)
    else:
        raise ValueError(f"Invalid date type: {date_type}. Expected 'filing' or 'issued'.")

    # Check if the current year's payment date has already passed
    include_current_year = comparison_month_day > current_month_day

    return include_current_year

def post_process_fees(results_df):
    """
    Post-process the calculated fees to check the current year and clear the fee if the payment
    has already been made for the current year.

    Parameters:
    - results_df (DataFrame): DataFrame containing the calculated maintenance fees.

    Returns:
    - processed_df (DataFrame): DataFrame with post-processed fees.
    """
    today = pd.Timestamp.today().date()
    current_year = today.year

    for index, row in results_df.iterrows():
        filing_date = row['File Date']
        issued_date = row['Publication Date']
        date_type = row['Date Type']  # Get the date type from the DataFrame

        # Determine the appropriate date based on the date type
        date_to_check = issued_date if date_type == 'issued date' else filing_date

        include_current_year = check_year_inclusion(date_to_check, date_type)
        if not include_current_year:
            column_name = str(current_year)
            if column_name in results_df.columns:
                results_df.at[index, column_name] = np.nan  # Clear the fee for the current year if it has already been paid

    return results_df


def calculate_fees_us(patent_info, country_fees):
    """
    Calculate the fees for a US patent based on its issued date.

    Parameters:
    - patent_info (tuple): Tuple containing extracted patent information.
    - country_fees (list): List containing fees information for the US.

    Returns:
    - fees_by_year (list of tuples): List of tuples containing (year, fee) for each remaining year.
    """
    _, _, _, issued_date, expiration_date, _, _ = patent_info
    today = datetime.date.today()
    start_year = max(today.year, issued_date.year)
    end_year = expiration_date.year

    fees_by_year = []

    # Adjust for country_fees containing extra metadata rows (skip first 2 entries)
    country_fees = country_fees[2:]

    for year in range(start_year, end_year):
        year_index = year - issued_date.year
        if year_index < len(country_fees):
            fee = country_fees[year_index] if not pd.isna(country_fees[year_index]) else 0
        else:
            fee = 0
        fees_by_year.append((year, fee))

    return fees_by_year

def calculate_fees_issued_date(patent_info, fees_info):
    """
    Calculate the fees for a patent based on its expiration date and fees data,
    assuming the date type is 'issued date'.

    Parameters:
    - patent_info (tuple): Tuple containing extracted patent information.
    - fees_info (DataFrame): DataFrame containing fees information.

    Returns:
    - fees_by_year (list of tuples): List of tuples containing (year, fee) for each remaining year.
    """
    patent_number, priority_date, filing_date, issued_date, expiration_date, country, numofclaims = patent_info

    print(f"Calculating issued date fees for patent {patent_number} in country {country}")

    if country not in fees_info.columns or (country == 'JP' and 'JPPC' not in fees_info.columns):
        raise ValueError(f"Fees data for country code {country} or JPPC not found.")
    
    country_fees = fees_info[country].dropna().values  # Drop NA values and get the fees as a list
    print(f"Country fees for {country}: {country_fees}")

    if country == 'US':
        return calculate_fees_us(patent_info, country_fees)
    elif country == 'JP':
        fees_per_claim = fees_info['JPPC'].dropna().values  # Drop NA values and get the fees per claim as a list
        print(f"Fees per claim for JP: {fees_per_claim}")
        return calculate_fees_jp(patent_info, country_fees, fees_per_claim)
    elif country == 'KR':
        fees_per_claim = fees_info['KRPC'].dropna().values  # Drop NA values and get the fees per claim as a list
        print(f"Fees per claim for KR: {fees_per_claim}")
        return calculate_fees_kr(patent_info, country_fees, fees_per_claim)
    elif country == 'ID':
        fees_per_claim = fees_info['IDPC'].dropna().values  # Drop NA values and get the fees per claim as a list
        print(f"Fees per claim for ID: {fees_per_claim}")
        return calculate_fees_id(patent_info, country_fees, fees_per_claim)
    elif country == 'TW':
        return calculate_fees_tw(patent_info, country_fees)
    elif country == 'RU':
        return calculate_fees_ru(patent_info, country_fees)
    elif country == 'MY':
        return calculate_fees_my(patent_info, country_fees)
    elif country == 'SK':
        return calculate_fees_sk(patent_info, country_fees)
    else:
        raise ValueError(f"Unsupported country code for issued date calculation: {country}")


def calculate_fees_filing_date(patent_info, fees_info):
    """
    Calculate the fees for a patent based on its expiration date and fees data,
    assuming the date type is 'filing date'.

    Parameters:
    - patent_info (tuple): Tuple containing extracted patent information.
    - fees_info (DataFrame): DataFrame containing fees information.

    Returns:
    - fees_by_year (list of tuples): List of tuples containing (year, fee) for each remaining year.
    """
    # Unpack the patent information
    patent_number, priority_date, filing_date, issued_date, expiration_date, country, numofclaims = patent_info
    
    # Calculate the remaining years
    today = datetime.date.today()
    start_year = max(today.year, filing_date.year)
    remaining_years = expiration_date.year - start_year  # Include the expiration year
    
    # Get the fees data for the country
    if country not in fees_info.columns:
        raise ValueError(f"Fees data for country code {country} not found.")
    
    country_fees = fees_info[country].fillna(0).values  # Replace NA values with 0 and get the fees as a list
    
    # Select the fees starting from today's year
    if remaining_years > len(country_fees):
        raise ValueError(f"Not enough fee data available for country code {country}.")
    
    selected_fees = country_fees[-remaining_years:]
    
    # Map the selected fees to the corresponding years
    fees_by_year = [(start_year + i, fee) for i, fee in enumerate(selected_fees)]

    return fees_by_year


def calculate_fees_jp(patent_info, country_fees, fees_per_claim):
    """
    Calculate the fees for a JP patent based on its issued date.

    Parameters:
    - patent_info (tuple): Tuple containing extracted patent information.
    - country_fees (list): List containing fees information for JP.
    - fees_per_claim (list): List containing fees per claim information for JP.

    Returns:
    - fees_by_year (list of tuples): List of tuples containing (year, fee) for each remaining year.
    """
    _, _, _, issued_date, expiration_date, country, numofclaims = patent_info
    today = datetime.date.today()
    start_year = max(today.year, issued_date.year)
    end_year = expiration_date.year

    # Skip initial entries and ensure fees are numeric
    country_fees = np.nan_to_num(np.array(country_fees[2:], dtype=float), nan=0.0)
    fees_per_claim = np.nan_to_num(np.array(fees_per_claim[2:], dtype=float), nan=0.0)

    fees_by_year = []

    # Fees for the first three years paid at grant (issued_date year)
    initial_fees = sum(country_fees[:3]) + numofclaims * sum(fees_per_claim[:3])
    fees_by_year.append((issued_date.year, initial_fees))

    # Annual fees from the 4th year onward
    for year in range(start_year, end_year):
        if year == issued_date.year:
            continue  # Skip the year of grant since we already paid for the first three years
        if year < issued_date.year + 3:
            fees_by_year.append((year, '0'))
            continue
        year_index = year - issued_date.year
        if year_index < len(country_fees):
            fee = country_fees[year_index] + numofclaims * fees_per_claim[year_index] if not np.isnan(country_fees[year_index]) else 0
        else:
            fee = 0
        fees_by_year.append((year, fee))

    return fees_by_year

def calculate_fees_kr(patent_info, country_fees, fees_per_claim):
    """
    Calculate the fees for a JP patent based on its issued date.

    Parameters:
    - patent_info (tuple): Tuple containing extracted patent information.
    - country_fees (list): List containing fees information for JP.
    - fees_per_claim (list): List containing fees per claim information for JP.

    Returns:
    - fees_by_year (list of tuples): List of tuples containing (year, fee) for each remaining year.
    """
    _, _, _, issued_date, expiration_date, country, numofclaims = patent_info
    today = datetime.date.today()
    start_year = max(today.year, issued_date.year)
    end_year = expiration_date.year

    # Skip initial entries and ensure fees are numeric
    country_fees = np.nan_to_num(np.array(country_fees[2:], dtype=float), nan=0.0)
    fees_per_claim = np.nan_to_num(np.array(fees_per_claim[2:], dtype=float), nan=0.0)

    fees_by_year = []

    # Fees for the first three years paid at grant (issued_date year)
    initial_fees = sum(country_fees[:3]) + numofclaims * sum(fees_per_claim[:3])
    fees_by_year.append((issued_date.year, initial_fees))

    # Annual fees from the 4th year onward
    for year in range(start_year, end_year):
        if year == issued_date.year:
            continue  # Skip the year of grant since we already paid for the first three years
        if year < issued_date.year + 3:
            fees_by_year.append((year, '0'))
            continue
        year_index = year - issued_date.year
        if year_index < len(country_fees):
            fee = country_fees[year_index] + numofclaims * fees_per_claim[year_index] if not np.isnan(country_fees[year_index]) else 0
        else:
            fee = 0
        fees_by_year.append((year, fee))

    return fees_by_year

def calculate_fees_id(patent_info, country_fees, fees_per_claim):
    """
    Calculate the fees for an ID patent based on its issued date.

    Parameters:
    - patent_info (tuple): Tuple containing extracted patent information.
    - country_fees (list): List containing fees information for ID.
    - fees_per_claim (list): List containing fees per claim information for ID.

    Returns:
    - fees_by_year (list of tuples): List of tuples containing (year, fee) for each remaining year.
    """
    _, priority_date, filing_date, issued_date, expiration_date, country, numofclaims = patent_info
    today = datetime.date.today()
    start_year = max(today.year, issued_date.year + 1)  # Start paying fees one year after grant
    end_year = expiration_date.year

    # Skip initial entries and ensure fees are numeric
    country_fees = np.nan_to_num(np.array(country_fees[2:], dtype=float), nan=0.0)
    fees_per_claim = np.nan_to_num(np.array(fees_per_claim[2:], dtype=float), nan=0.0)

    fees_by_year = []

    # Initial payment at grant (covering years from one year after the filing date to the year before the grant date)
    initial_fees = sum(country_fees[:issued_date.year - filing_date.year]) + numofclaims * sum(fees_per_claim[:issued_date.year - filing_date.year])
    fees_by_year.append((issued_date.year, initial_fees))

    # Annual fees from the year after the grant onward
    for year in range(start_year, end_year):
        year_index = year - (filing_date.year)
        if 0 <= year_index < len(country_fees):
            fee = country_fees[year_index] + numofclaims * fees_per_claim[year_index] if not np.isnan(country_fees[year_index]) else 0
        else:
            fee = 0
        fees_by_year.append((year, fee))

    return fees_by_year

def calculate_fees_tw(patent_info, country_fees):
    """
    Calculate the fees for a TW patent based on its issued date.

    Parameters:
    - patent_info (tuple): Tuple containing extracted patent information.
    - country_fees (list): List containing fees information for TW.

    Returns:
    - fees_by_year (list of tuples): List of tuples containing (year, fee) for each remaining year.
    """
    _, priority_date, filing_date, issued_date, expiration_date, country, numofclaims = patent_info
    today = datetime.date.today()
    start_year = max(today.year, issued_date.year)  # Start paying fees from the issued year
    end_year = expiration_date.year

    # Skip initial entries and ensure fees are numeric
    country_fees = np.nan_to_num(np.array(country_fees[2:], dtype=float), nan=0.0)

    fees_by_year = []

    # Annual fees from the year of the grant onward
    for year in range(start_year, end_year):
        year_index = year - issued_date.year
        if year_index < len(country_fees):
            fee = country_fees[year_index] if not np.isnan(country_fees[year_index]) else 0
        else:
            fee = 0
        fees_by_year.append((year, fee))

    return fees_by_year


def calculate_fees_ru(patent_info, country_fees):
    """
    Calculate the fees for a RU patent based on its issued date.

    Parameters:
    - patent_info (tuple): Tuple containing extracted patent information.
    - country_fees (list): List containing fees information for RU.

    Returns:
    - fees_by_year (list of tuples): List of tuples containing (year, fee) for each remaining year.
    """
    _, priority_date, filing_date, issued_date, expiration_date, country, numofclaims = patent_info
    today = datetime.date.today()
    start_year = max(today.year, issued_date.year)  # Start paying fees from the issued year
    end_year = expiration_date.year

    # Skip initial entries and ensure fees are numeric
    country_fees = np.nan_to_num(np.array(country_fees[2:], dtype=float), nan=0.0)

    fees_by_year = []

    # Start from the first applicable fee year after issuance
    for year in range(start_year, end_year):
        year_index = year - issued_date.year
        if year_index < len(country_fees):
            fee = country_fees[year_index] if not np.isnan(country_fees[year_index]) else 0
        else:
            fee = 0
        fees_by_year.append((year, fee))

    return fees_by_year

def calculate_fees_my(patent_info, country_fees):
    """
    Calculate the fees for a RU patent based on its issued date.

    Parameters:
    - patent_info (tuple): Tuple containing extracted patent information.
    - country_fees (list): List containing fees information for RU.

    Returns:
    - fees_by_year (list of tuples): List of tuples containing (year, fee) for each remaining year.
    """
    _, priority_date, filing_date, issued_date, expiration_date, country, numofclaims = patent_info
    today = datetime.date.today()
    start_year = max(today.year, issued_date.year)  # Start paying fees from the issued year
    end_year = expiration_date.year

    # Skip initial entries and ensure fees are numeric
    country_fees = np.nan_to_num(np.array(country_fees[2:], dtype=float), nan=0.0)

    fees_by_year = []

    # Start from the first applicable fee year after issuance
    for year in range(start_year, end_year):
        year_index = year - issued_date.year
        if year_index < len(country_fees):
            fee = country_fees[year_index] if not np.isnan(country_fees[year_index]) else 0
        else:
            fee = 0
        fees_by_year.append((year, fee))

    return fees_by_year


def calculate_fees_sk(patent_info, country_fees, fees_per_claim):
    """
    Calculate the fees for an ID patent based on its issued date.

    Parameters:
    - patent_info (tuple): Tuple containing extracted patent information.
    - country_fees (list): List containing fees information for ID.
    - fees_per_claim (list): List containing fees per claim information for ID.

    Returns:
    - fees_by_year (list of tuples): List of tuples containing (year, fee) for each remaining year.
    """
    _, priority_date, filing_date, issued_date, expiration_date, country, numofclaims = patent_info
    today = datetime.date.today()
    start_year = max(today.year, issued_date.year + 1)  # Start paying fees one year after grant
    end_year = expiration_date.year

    # Skip initial entries and ensure fees are numeric
    country_fees = np.nan_to_num(np.array(country_fees[2:], dtype=float), nan=0.0)
    fees_per_claim = np.nan_to_num(np.array(fees_per_claim[2:], dtype=float), nan=0.0)

    fees_by_year = []

    # Initial payment at grant (covering years from one year after the filing date to the year before the grant date)
    initial_fees = sum(country_fees[:issued_date.year - filing_date.year])
    fees_by_year.append((issued_date.year, initial_fees))

    # Annual fees from the year after the grant onward
    for year in range(start_year, end_year):
        year_index = year - (filing_date.year)
        if 0 <= year_index < len(country_fees):
            fee = country_fees[year_index] if not np.isnan(country_fees[year_index]) else 0
        else:
            fee = 0
        fees_by_year.append((year, fee))

    return fees_by_year

def date_check(patent_info, date_types, fees_info, results_df):
    for i, patent in enumerate(patent_info):
        patent_number = patent[0]
        date_type = date_types.get(patent_number, '').lower()
        if date_type == 'issued date':
            fees_by_year = calculate_fees_issued_date(patent, fees_info)
        elif date_type == 'filing date':
            fees_by_year = calculate_fees_filing_date(patent, fees_info)
        else:
            continue
        for year, fee in fees_by_year:
            if year >= datetime.date.today().year:
                results_df.at[i, str(year)] = fee
        results_df.at[i, 'Date Type'] = date_type

    return results_df