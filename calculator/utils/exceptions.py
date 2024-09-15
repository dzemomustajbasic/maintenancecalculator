# exceptions.py

class ExcelError(Exception):
    """Base exception for all Excel-related errors."""
    def __init__(self, message):
        super().__init__(f"Excel Error: {message}")


class ExcelFileReadError(ExcelError):
    """Raised when there's an error reading an Excel file."""
    def __init__(self, message):
        super().__init__(f"Error reading Excel file: {message}")


class MissingRequiredColumnsError(ExcelError):
    """Raised when required columns are missing from the Excel file."""
    def __init__(self, missing_columns, required_columns):
        self.missing_columns = missing_columns
        self.required_columns = required_columns
        missing = ', '.join(missing_columns)
        necessary = ', '.join(required_columns)
        super().__init__(f"Missing required columns: {missing}.")


class InvalidCountryCodeError(ExcelError):
    """Raised when a country code is not found in the fees data."""
    def __init__(self, country_code):
        super().__init__(f"Invalid country code: {country_code}")
