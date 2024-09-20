class GPTInvalidColumnsError(Exception):
    def __init__(self, missing_columns, required_columns):
        self.missing_columns = missing_columns
        self.required_columns = required_columns
        super().__init__(f"Missing required columns: {', '.join(missing_columns)}. Required columns are: {', '.join(required_columns)}")
