import datetime

def calculate_remaining_life(patent_info):
    """
    Calculate the exact remaining life of patents based on their expiration dates,
    considering partial years in the current year 2024.

    Parameters:
    - patent_info (list of tuples): List of tuples containing extracted patent information.
      Each tuple should contain (patent_number, priority_date, filing_date, issued_date, 
      expiration_date, country, numofclaims, execution_year).

    Returns:
    - updated_patent_info (list of tuples): Updated list of tuples with remaining life appended.
      Each tuple will now contain (patent_number, priority_date, filing_date, issued_date, 
      expiration_date, country, numofclaims, execution_year, remaining_life).
    """
    today = datetime.date.today()  # Get the current date

    updated_patent_info = []

    for patent in patent_info:
        patent_number, priority_date, filing_date, issued_date, expiration_date, country, numofclaims, execution_year = patent
        
        # Calculate remaining life based on the expiration date
        remaining_life = (expiration_date - today).days / 365.25
        rounded_remaining_life = round(remaining_life + 0.5)  # Round up to include the final year

        # Append remaining life to the patent information tuple
        updated_patent_info.append(patent + (rounded_remaining_life,))

    return updated_patent_info
