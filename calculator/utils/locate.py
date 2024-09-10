def locate_country_code_in_fees(patent_info, fees_info):
    """
    Locate the country codes in the fees information DataFrame and display the corresponding values.

    Parameters:
    - patent_info (list of tuples): List of tuples containing extracted patent information.
    - fees_info (DataFrame): DataFrame containing fees information.

    Returns:
    - date_types (dict): Dictionary with patent numbers as keys and date types as values.
    """
    date_types = {}

    print("locate country code fees info:", fees_info)
    # Extract country codes from patent_info
    for patent in patent_info:
        # Potrebno ispraviti da pravilno nalazi kodove...
        patent_number, _, _, _, _, country, _ = patent
        print("KOD", country)

        # Check if country codes exist as columns in fees_info
        if country in fees_info.columns:
            fees_for_country = fees_info[country]
            date_type = fees_for_country.iloc[0]  # Get the date type from index 0
            country_name = fees_for_country.iloc[1]  # Get the country name from index 1
            fees_data = fees_for_country.iloc[2:]  # Exclude date type and country name

            # Store the date type in the dictionary
            date_types[patent_number] = date_type

            print(f"Country Code: {country}, Country: {country_name}, Date Type: {date_type}")
            print(fees_data)
            print()  # Add a blank line for clarity
        else:
            print(f"Country code {country} not found in fees data.")

    return date_types
