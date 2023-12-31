# -*- coding: utf-8 -*-
"""Stock Trading Project - Class Setup

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1JZXzQgauRtnl0vPxlV2N8Q3POsoOwmmS

# Stock data API Call class
- Retrieves data from Tiingo API about specific ticker and start/end dates.
- Can pull news and price data from Tiingo, but uses selected dataset for news headlines.
- Combines pandas dataframes for news and price data into a merged dataframe.
- Outputs a file of the merged dataframe when ran.
"""

# Import necessary libraries
from google.colab import drive
import os, requests, json, pandas as pd, time

# Define a class to encapsulate stock data pulling functionality
class stock_data_pull():
    # Constructor method to initialize object with ticker, start date, and end date
    def __init__(self, ticker, start_date, end_date):
        self.ticker = ticker  # Stock ticker symbol (e.g., 'AAPL' for Apple Inc.)
        self.start_date = start_date  # Start date for data retrieval (format: 'YYYY-MM-DD')
        self.end_date = end_date  # End date for data retrieval (format: 'YYYY-MM-DD')
        self.setup()  # Call setup method to handle preliminary setup tasks

    # Method to set up environment (mounting drive and setting API key)
    def setup(self):
        # Mount Google Drive to access files on the drive
        drive.mount('/content/drive')

        # Open the file containing the API key, read the key, and store it as an instance variable
        with open('/content/drive/My Drive/secretkey_tiingo.txt', 'r') as file:
            self.api_key = file.read().strip()  # Remove any leading/trailing whitespace
        # Set the API key as an environment variable (if needed elsewhere in your environment)
        os.environ['API_KEY'] = self.api_key

    # Method to retrieve stock price and news data from Tiingo
    def get_tiingo_data(self):
        # Define headers for the HTTP requests (including authorization token)
        headers = {
            'Content-Type':"application/json",
            'Authorization': f"Token {self.api_key}"
        }

        # Make HTTP GET requests to Tiingo API for price and news data
        responsePrice = requests.get(f"https://api.tiingo.com/tiingo/daily/{self.ticker}/prices?startDate={self.start_date}&endDate={self.end_date}",headers=headers)
        responseNews = requests.get(f"https://api.tiingo.com/tiingo/news?tickers={self.ticker}",headers=headers)

        # Parse JSON responses to Python dictionaries
        tiingo_price_data = json.loads(responsePrice.text)
        tiingo_news_data = json.loads(responseNews.text)

        # Convert dictionaries to pandas DataFrames for easier data manipulation
        tiingo_price_df = pd.DataFrame(tiingo_price_data)
        tiingo_news_df = pd.DataFrame(tiingo_news_data)

        # Truncate date strings to 'YYYY-MM-DD' format and convert to datetime objects
        tiingo_price_df['date'] = tiingo_price_df['date'].str[:10]
        tiingo_price_df['date'] = pd.to_datetime(tiingo_price_df['date'])

        tiingo_news_df['publishedDate'] = tiingo_news_df['publishedDate'].str[:10]
        tiingo_news_df['publishedDate'] = pd.to_datetime(tiingo_news_df['publishedDate'])

        # Return both DataFrames
        return tiingo_price_df, tiingo_news_df

    # Method to read analyst headline data from a CSV file and process it
    def get_csv_headline_data(self):
        # Open and read the CSV file containing analyst headline data
        with open('/content/drive/My Drive/raw_analyst_ratings.csv', 'r') as file:
            analyst_dataset_df = pd.read_csv(file)  # Corrected to read from file object

        # Filter the DataFrame for rows corresponding to the specified stock ticker
        ticker_df = analyst_dataset_df.loc[analyst_dataset_df['stock'] == self.ticker].copy()

        # Convert date column to string type if it's not already, for string manipulation
        if ticker_df['date'].dtype != 'object':
            ticker_df['date'] = ticker_df['date'].astype(str)

        # Truncate date strings to 'YYYY-MM-DD' format and convert to datetime objects
        ticker_df['date'] = ticker_df['date'].str[:10]
        ticker_df['date'] = pd.to_datetime(ticker_df['date'])

        # Sort the DataFrame by date in descending order
        ticker_df_date_sorted = ticker_df.sort_values(by='date', ascending=False)

        # Return the sorted DataFrame
        return ticker_df_date_sorted

    # Method to merge the analyst headline data with the Tiingo price data
    def merge_data(self, ticker_df_date_sorted, tiingo_price_df):
        # Perform an inner merge on the 'date' column to combine the data
        merged_df = pd.merge(ticker_df_date_sorted, tiingo_price_df, on='date', how='inner')
        # Write the merged DataFrame to a CSV file named '<TICKER>_Final.csv'
        merged_df.to_csv(f'{self.ticker}_Final.csv', index=False)
        # Return the merged DataFrame
        return merged_df

    # Method to orchestrate the data retrieval, processing, and merging tasks
    def run(self):
        # Retrieve Tiingo price and news data
        tiingo_price_df, tiingo_news_df = self.get_tiingo_data()
        # Retrieve and process the analyst headline data
        ticker_df_date_sorted = self.get_csv_headline_data()
        # Merge the data and return the merged DataFrame
        merged_df = self.merge_data(ticker_df_date_sorted, tiingo_price_df)

# Instantiate an object of the stock_data_pull class with specified parameters
stock_data = stock_data_pull('AAPL', '2020-01-01', '2023-01-01')
# Call the run method to execute the data retrieval, processing, and merging tasks
stock_data.run()

"""### Connect to FinBERT LLM via HuggingFace transformers library
- Set up Tiingo API call retrieved data to
"""

# Load model directly
!pip install transformers
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Load pre-trained FinBERT model and tokenizer
tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")

# Tokenize a financial sentence
sentence = "The stock market is not bad or good today."
inputs = tokenizer(sentence, return_tensors="pt")

# Perform inference to get logits
with torch.no_grad():
    outputs = model(**inputs)
    logits = outputs.logits

# Get probabilities
probabilities = torch.softmax(logits, dim=1)

# Get the predicted label ID
predicted_label_id = torch.argmax(probabilities, dim=1).item()

# Map the label ID to the actual label name
predicted_label = model.config.id2label[predicted_label_id]

# Output results
print(f"Logits: {logits}")
print(f"Probabilities: {probabilities}")
print(f"Predicted Label ID: {predicted_label_id}")
print(f"Predicted Label: {predicted_label}")