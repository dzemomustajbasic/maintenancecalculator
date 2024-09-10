import os
from operations import clean_and_extract_relevant_columns, categorize_claims, save_to_excel

def process_patent_claims(input_file_path, output_file_path):
    """
    Main function to process the patent claims from an Excel file.
    - Cleans the data to retain only relevant columns.
    - Categorizes each claim using the GPT model.
    - Saves the results to a new Excel file.
    """
    try:
        # Clean and extract relevant columns
        df = clean_and_extract_relevant_columns(input_file_path)

        # Categorize each claim using the GPT model
        categorized_df = categorize_claims(df)

        # Save the results to a new Excel file
        save_to_excel(categorized_df, output_file_path)

        print("The data processing has been completed successfully.")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    input_file_path = 'C:/Users/Eric/Desktop/test.xlsx'  # Replace with the path to your Excel file
    output_file_path = 'C:/Users/Eric/Desktop/output.xlsx'  # Replace with the desired output Excel file path

    process_patent_claims(input_file_path, output_file_path)
