import pandas as pd

# Path to the Excel file
excel_file_path = "C:/Users/PC/Desktop/FeesDollars.xlsx"  # Replace with the actual file path

# Read the Excel file into a DataFrame
df = pd.read_excel(excel_file_path)

# Output the DataFrame
print(df)
print(df.dtypes)