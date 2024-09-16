import os
from django.conf import settings
from .exceptions import InvalidCountryCodeError

def locate_country_code_in_fees(patent_info, fees_info):
    date_types = {}

    # Extract country codes from patent_info
    for patent in patent_info:
        patent_number, _, _, _, _, country, _ = patent

        # Check if country codes exist as columns in fees_info
        if country in fees_info.columns:
            fees_for_country = fees_info[country]
            date_type = fees_for_country.iloc[0]  # Get the date type from index 0
            date_types[patent_number] = date_type
        else:
            # If the country code is missing, assign 'non existent' as the date type
            date_types[patent_number] = "none"
            print(f"Warning: Country code {country} not found in fees data for patent {patent_number}. Setting date type to 'non existent'.")

    return date_types
