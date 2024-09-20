import datetime
import pandas as pd
import numpy as np

## todo add exception for blank dates etc, add us per year overview, and non us overview
def check_year_inclusion(date, date_type):

    today = pd.Timestamp.today().date()
    current_month_day = (today.month, today.day)

    if date_type == 'file date':
        comparison_month_day = (date.month, date.day)
    elif date_type == 'publication date':
        comparison_month_day = (date.month, date.day)
    else:
        raise ValueError(f"Invalid date type: {date_type}. Expected 'file' or 'publication'.")

    # Check if the current year's payment date has already passed
    include_current_year = comparison_month_day > current_month_day

    return include_current_year

def post_process_fees(results_df):
    today = pd.Timestamp.today().date()
    current_year = today.year

    for index, row in results_df.iterrows():
        filing_date = row['File Date']
        issued_date = row['Publication Date']
        date_type = row['Date Type']  # Get the date type from the DataFrame

        # Skip processing for "none" date type
        if date_type == "none":
            continue

        # Determine the appropriate date based on the date type
        date_to_check = issued_date if date_type == 'publication date' else filing_date

        include_current_year = check_year_inclusion(date_to_check, date_type)
        if not include_current_year:
            column_name = str(current_year)
            if column_name in results_df.columns:
                results_df.at[index, column_name] = np.nan  # Clear the fee for the current year if it has already been paid

    return results_df

def date_check(patent, date_types, fees_info, results_df, index):
    patent_number, type, filing_date, issued_date, expiration_date, country, numofclaims = patent
    date_type = date_types.get(patent_number, '').lower()

    # Check if Type is not "Grant", and mark it as "none" if that's the case
    if type.lower() != "grant":
        date_type = "none"

    # Handle "none" date type by setting fees to 0
    if date_type == "none":
        for year in range(datetime.date.today().year, expiration_date.year + 1):
            results_df.at[index, str(year)] = 0
        results_df.at[index, 'Date Type'] = "none"
        return results_df

    # Proceed with normal fee calculation if type is "Grant"
    if date_type == 'publication date':
        fees_by_year = calculate_fees_issued_date(patent, fees_info)
    elif date_type == 'file date':
        fees_by_year = calculate_fees_filing_date(patent, fees_info)
    else:
        return results_df  # If no valid date type, return without changes

    # Update the DataFrame with the calculated fees by year
    for year, fee in fees_by_year:
        if year >= datetime.date.today().year:
            results_df.at[index, str(year)] = fee

    # Add the date type to the DataFrame
    results_df.at[index, 'Date Type'] = date_type

    return results_df



######## FOR PATENTS WHICH CALCULATE FROM FILING DATE ########################

def calculate_fees_issued_date(patent_info, fees_info):

    patent_number, priority_date, filing_date, issued_date, expiration_date, country, numofclaims = patent_info

    print(f"Calculating issued date fees for patent {patent_number} in country {country}")

    if country not in fees_info.columns or (country == 'JP' and 'JPPC' not in fees_info.columns):
        # Log warning instead of raising an error
        print(f"Warning: Fees data for country code {country} or JPPC not found. Skipping this patent.")
        return []

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
        # Log warning if the country code is unsupported
        print(f"Warning: Unsupported country code for issued date calculation: {country}. Skipping this patent.")
        return []
    
def calculate_fees_us(patent_info, country_fees):

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
    

def calculate_fees_filing_date(patent_info, fees_info):

    # Unpack the patent information
    patent_number, priority_date, filing_date, issued_date, expiration_date, country, numofclaims = patent_info
    
    # Calculate the remaining years
    today = datetime.date.today()
    start_year = max(today.year, filing_date.year)
    remaining_years = expiration_date.year - start_year  # Include the expiration year
    
    # Get the fees data for the country
    if country not in fees_info.columns:
        # Log warning instead of raising an error
        print(f"Warning: Fees data for country code {country} not found. Skipping this patent.")
        return []

    country_fees = fees_info[country].fillna(0).values  # Replace NA values with 0 and get the fees as a list
    
    # Select the fees starting from today's year
    if remaining_years > len(country_fees):
        # Log warning and return empty list if there's not enough fee data
        print(f"Warning: Not enough fee data available for country code {country}. Skipping this patent.")
        return []

    selected_fees = country_fees[-remaining_years:]
    
    # Map the selected fees to the corresponding years
    fees_by_year = [(start_year + i, fee) for i, fee in enumerate(selected_fees)]

    return fees_by_year

############# FOR PATENTS CALCULATING FROM PUBLICATION/ISSUED DATE ###################
def calculate_fees_jp(patent_info, country_fees, fees_per_claim):

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