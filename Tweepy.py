from ctypes import sizeof
import string
from time import perf_counter
from tokenize import String
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import pandas as pd
import numpy as np
import re
from urllib import response #regular expressions
import tweepy #twitter API client
from tweepy import OAuthHandler #handles user authentification
import yfinance as yf
from cleantext import clean

API_key = 's6O2GZf2hYPeqMfJCXJTlaQmo'
API_secret_key = 'FpZJgNm9Ga8UAtMWtPdd5K9CN5qQN4b7OO8VjrlgTXQ6YOM9dr'
access_token = '1518726053195304960-KWzaZLIQQK8WB8WucWQ4zJhFAgirT0'
secret_access_token = 'HugUOLByv9CP32QD8eQxBxYK6eHYYdPHoc6yJLprEpgem'
bearer_token = 'AAAAAAAAAAAAAAAAAAAAAE%2BUbwEAAAAAR6Y4hE5AS05ppcLt8pLd3pL5BMU%3DMOLBhtN06VUmj7XG3F7WnT9GkJay4CVGjmhmGNuaiU9FBvT91o'
client = tweepy.Client(bearer_token = bearer_token)
#client = tweepy.Client(consumer_key = API_key, consumer_secret = API_secret_key, access_token = access_token, access_token_secret = secret_access_token)

#number of tweets from last seven days
def tweet_topic_count(search):
    topic_count = client.get_recent_tweets_count(query = search)
    cumulative_tweet_count = 0
    for count in topic_count.data:
        array = np.array(count)
        String = str(array)
        string_split = String.split('tweet_count', -1)[1]
        hourly_tweet_count_numeric = re.sub("[^0-9]", "", string_split)
        cumulative_tweet_count = cumulative_tweet_count + int(hourly_tweet_count_numeric)
    if cumulative_tweet_count == 0:
        print('No recent tweets found with this search query.')
    #many sources suggest that a topic will be considered trending at the 5000-10000 tweet range
    elif ((cumulative_tweet_count > 0) and (cumulative_tweet_count < 5000)):
        print('Tweet count suggests that this topic is not trending.')
    else: 
        print('\n\nTweet count suggests that this topic is currently trending on Twitter.')
    return cumulative_tweet_count

#create datadrame from search content and n tweets
def get_tweets_df(search, n):
    tweet_data = []
    search_query = client.search_recent_tweets(query = search, max_results = n)
    tweets = search_query.data
    for tweet in tweets:
        tweet_data.append(tweet.text)
    df = pd.DataFrame(tweet_data, columns = ['Tweet Text'])
    return df

#remove whitespace, common twitter strings, emojis, links, etc. 
def clean_tweet(df):
    clean_df = df.copy(deep=True)
    #iterate over all df rows
    for ind in range(clean_df.shape[0]):
        string_to_edit = str(clean_df.iat[ind, 0])
        string_to_edit = clean(string_to_edit, no_emoji=True)
        string_to_edit = re.sub("RT", "", string_to_edit)
        string_to_edit = re.sub("@", "", string_to_edit)
        string_to_edit = re.sub(r"http\S+", "", string_to_edit)
        string_to_edit = re.sub("#", "", string_to_edit)
        string_to_edit = re.sub("_", "", string_to_edit)
        #string_to_edit = ' '.join(string_to_edit.split())
        string_to_edit = string_to_edit.strip()
        clean_df.iat[ind, 0] = string_to_edit
    return clean_df

#erase username from start of tweet content
def erase_username_from_tweet_content(df):
    for ind in range(df.shape[0]):
        string_to_edit = str(df.iat[ind, 0])
        colon_present = 0
        if ":" in string_to_edit:
            colon_present = 1
        else:
            colon_present = 0
        #if colon is present in start of tweet, denoting a retweet
        if (colon_present == 1):
            #Split string one time, enough to get rif od username
            string_to_edit = string_to_edit.split(':', 1)[1]
        df.iat[ind, 0] = string_to_edit
    return df

#user nltk vader to perform sentiment analysis on each tweet
def sentiment_ratings(df):
    stopwords = nltk.corpus.stopwords.words("english")
    sentiment_analyzer = SentimentIntensityAnalyzer()
    negative_tweets = []
    neutral_tweets = []
    positive_tweets = []
    compound_tweets = []
    for ind in range(df.shape[0]):
        string_to_analyze = str(df.iat[ind, 0])
        sentiment_analysis_polarity = sentiment_analyzer.polarity_scores(string_to_analyze)
        negative = sentiment_analysis_polarity["neg"]
        negative_tweets.append(negative)
        neutral = sentiment_analysis_polarity["neu"]
        neutral_tweets.append(neutral)
        positive = sentiment_analysis_polarity["pos"]
        positive_tweets.append(positive)
        compound = sentiment_analysis_polarity["compound"]
        compound_tweets.append(compound)
    sentiment_data = [negative_tweets], [neutral_tweets], [positive_tweets], [compound_tweets]
    sentiment_df = pd.DataFrame(list(zip(negative_tweets, neutral_tweets, positive_tweets, compound_tweets)), columns = ['Negative Score', 'Neutral Score', 'Positive Score', 'Compound Score'])
    return sentiment_df

#determine average compound score from all tweets in dataframe
def sentiment_percentages(df):
    mean = df["Compound Score"].mean()
    if mean < 0:
        overall = 'Overall negative sentiment'
        return overall, mean
    elif mean == 0:
        overall = 'Overall neutral sentiment'
        return overall, mean
    else:
        overall = 'Overall positive sentiment'
        return overall, mean

#use yfinance to get last week's stock data for search query
def get_stock_data(search):
    ticker = yf.Ticker(search)
    get_stock_info = ticker.info
    stock_history = ticker.history(period = "1wk")
    return stock_history

#determine last week's stock percent change using percent change formula
def get_stock_trend(stock_history):
    week_open = stock_history["Open"][0]
    week_close = stock_history["Close"][4]
    decimal_change = ((week_close - week_open)/(week_open))
    percent_change = decimal_change*100
    return percent_change

#numpy datatype to standard data type
def numpy_int_to_python_int(numpy_int):
    value = int(numpy_int)
    return value

#determine correltion between sentiment analysis with vader and actual stock trend
def accuracy_of_sentiment_analysis(trend, mean):
    correlation = 0
    if ((trend < 0) and (mean < 0)):
        correlation = "Stock trend and sentiment analysis agree."
        return correlation
    elif ((trend == 0) and ( mean == 0)):
        correlation = "Stock trend and sentiment analysis agree."
        return correlation
    elif ((trend > 0) and ( mean > 0)):    
        correlation = "Stock trend and sentiment analysis agree."
        return correlation
    else:
        correlation = "Stock trend and sentiment analysis do not agree."
        return correlation

def explanation_for_trending_and_sentiment(tweet_count, mean):
    if tweet_count > 10000:
        print('This topic is trending. This suggests possible volatility.\n')
        if mean > 0:
            print('Sentiment is high. This suggests new technology being developed, positve overall market sentiment, high earnings report, etc.')
        elif (mean < 0):
            print('Sentiment is low. This suggests poor company development, positive news for their competition, poor overall market sentiment, low earnings report, etc. ')
        else:
            print('Sentiment is mixed.')
    else:
        print('This topic is not trending. Stock value likely changing due to overall market sentiment.')
    return

#search query
search = input("Enter stock ticker as search query: ")
#num searches   
n = input("Enter n for nsearch queries between 10 and 100: ")

topic_count = tweet_topic_count(search)
print('\n\n', 'Total posts in last seven days pertaining to this topic: ', topic_count, '\n\n')
topic_posts = get_tweets_df(search, n)
print('Sample of post contents regarding this topic: \n\n', topic_posts, '\n\n')
topic_posts_clean = clean_tweet(topic_posts)
final_cleaned_posts = erase_username_from_tweet_content(topic_posts_clean)
print('Cleaned sample of post contents regarding this topic: \n\n', final_cleaned_posts, '\n')
sentiment_data = sentiment_ratings(final_cleaned_posts)
print('Coversion of post conents to sentiment numerical data: \n\n', sentiment_data, '\n\n')

#determine mean of compound scores and overall sentiment indicator
data = sentiment_percentages(sentiment_data)
overall = data[0]
mean = data[1]

#determine stock information
stock_history = get_stock_data(search)
print('Stock data for last full week of trading: \n\n', stock_history, '\n\n')
percent_change = get_stock_trend(stock_history)
percent_change = np.int_(percent_change)
print('Average of compound sentiment scores from sample Tweet dataframe:', '\n\n', mean, '\n')
print('Stock percent change over last full week of trading: ', '\n\n', percent_change, '\n')
#convert numpy.int32 to int
percent_change = numpy_int_to_python_int(percent_change)
#determine correlation between tweet sentiment analysis and stock performance
correlation = accuracy_of_sentiment_analysis(percent_change, mean)
print('Correlation between Twitter sentiment analysis and real-life stock performance:', '\n\n', correlation, '\n')
explanation_for_trending_and_sentiment(topic_count, mean)

print('\n\n*****PROGRAM COMPLETE*****')
