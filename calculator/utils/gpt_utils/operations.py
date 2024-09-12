import os
import json
import time
import pandas as pd
from openai import OpenAI
import threading

# Učitavanje konfiguracije
def load_config():
    """
    Load the configuration file to retrieve the OpenAI API key.
    """
    # Get the directory of the current file (which is utils/gpt_utils)
    current_directory = os.path.dirname(os.path.abspath(__file__))

    # Construct the full path to the config.json file in the same directory
    config_path = os.path.join(current_directory, 'config.json')

    if not os.path.exists(config_path):
        raise FileNotFoundError("Configuration file not found. Please ensure that config.json is in the gpt_utils directory.")
    
    with open(config_path, 'r') as file:
        return json.load(file)

# Funkcija za pozivanje GPT modela
def call_gpt_model(model, prompt, input_text):
    """
    Call the GPT model to categorize the input text based on the given prompt.
    
    Parameters:
    - model: The GPT model to use (e.g., 'gpt-4o-mini').
    - prompt: The prompt used for the categorization.
    - input_text: The text to be analyzed and categorized.
    
    Returns:
    - The category name or an error message.
    """
    config = load_config()
    api_key = config.get('OPENAI_API_KEY')

    if not api_key:
        raise ValueError("API key is not set in the configuration file.")

    client = OpenAI(api_key=api_key)

    try:
        chat_completion = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": f"{prompt} {input_text}"
                },
                {
                    "role": "user",
                    "content": input_text
                }
            ]
        )
      
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        return f"API request failed: {str(e)}"

# Funkcija za procesiranje više zahteva sa rate limiting-om
def handle_multiple_requests(model, prompt, inputs, rate_limit_per_second=1):
   
    config = load_config()
    api_key = config.get('OPENAI_API_KEY')

    if not api_key:
        raise ValueError("API key is not set in the configuration file.")

    threads = []
    responses = [None] * len(inputs)

    # Funkcija za kontrolisanje slanja zahteva prema API rate limitu
    def request_with_delay(i):
        time.sleep(i / rate_limit_per_second)  # Osigurava da se zahtevi ne šalju prebrzo
        call_gpt_model(model, prompt, inputs[i], responses, i, api_key)

    # Kreiraj niti za svaki API poziv i postavi odgodu između njih
    for i in range(len(inputs)):
        thread = threading.Thread(target=request_with_delay, args=(i,))
        threads.append(thread)
        thread.start()

    # Čekaj da sve niti završe
    for thread in threads:
        thread.join()

    return responses

    
def clean_and_extract_relevant_columns(excel_file_path):
    """
    Load an Excel file and retain only the 'Patent / Publication Number', 'Title', and 'First Claim' columns.
    """
    try:
        # Read the Excel file
        df = pd.read_excel(excel_file_path)
        
        # Check if required columns exist
        required_columns = ['Patent / Publication Number', 'Claim/Title']
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f"Excel file must contain the following columns: {', '.join(required_columns)}")

        # Retain only the relevant columns
        df = df[required_columns]

        return df
    except FileNotFoundError:
        raise FileNotFoundError(f"The specified Excel file was not found: {excel_file_path}")
    except Exception as e:
        raise Exception(f"Failed to process the Excel file: {str(e)}")


def categorize_claims(df, model, prompt):
    gpt_categories = []

    for _, row in df.iterrows():
        try:
            gpt_category = call_gpt_model(model, prompt, row['Claim/Title'])
            gpt_categories.append(gpt_category)
        except Exception as e:
            gpt_categories.append(f"Error categorizing: {str(e)}")

    df['GPT Category'] = gpt_categories
    df = df[['Patent / Publication Number', 'Claim/Title', 'GPT Category']]

    return df

def save_to_excel(df, output_file_path):
    
    try:
        df.to_excel(output_file_path, index=False)
    except Exception as e:
        raise Exception(f"Failed to save the DataFrame to Excel: {str(e)}")
