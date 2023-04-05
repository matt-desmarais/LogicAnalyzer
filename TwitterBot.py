import tweepy
import time
import openai
import textwrap
import os
import re

openai.api_key = "sk-..."

# File to store the ID of the last mention processed
LAST_MENTION_FILE = "last_mention_id.txt"

# Enter your own credentials obtained
# from your Twitter developer account
consumer_key = ""
consumer_secret = ""
access_key = ""
access_secret = ""

# Function to get the ID and screen name of the user who posted the original tweet in a thread
def get_original_tweet_info(api, tweet_id):
    try:
        tweet = api.get_status(tweet_id, tweet_mode="extended")
        if tweet.in_reply_to_status_id is not None:
            return get_original_tweet_info(api, tweet.in_reply_to_status_id)
        else:
            return tweet.id, tweet.user.screen_name
    except Exception as e:
        print(f"Error fetching the tweet: {e}")
        return None, None


# Function to get all tweets in a thread
def get_thread_tweets(api, mention):
    thread_tweets = []
    current_tweet = mention
    while current_tweet.in_reply_to_status_id is not None:
        try:
            parent_tweet = api.get_status(current_tweet.in_reply_to_status_id, tweet_mode="extended")
            thread_tweets.append((parent_tweet.user.screen_name, parent_tweet.full_text))
            current_tweet = parent_tweet
        except Exception as e:
            print(f"Error fetching the parent tweet: {e}")
            break
    # Add the original mention to the thread
    thread_tweets.append((mention.user.screen_name, mention.full_text))
    return thread_tweets

# Function to save the last mention ID to a file
def save_last_mention_id(mention_id):
    with open(LAST_MENTION_FILE, "w") as f:
        f.write(str(mention_id))

# Function to load the last mention ID from a file
def load_last_mention_id():
    if os.path.exists(LAST_MENTION_FILE):
        with open(LAST_MENTION_FILE, "r") as f:
            return int(f.read())
    return None

# Function to create the Tweepy API object
def create_api():
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_key, access_secret)
    api = tweepy.API(auth, wait_on_rate_limit=True)
    return api

# Function to respond to mentions
def respond_to_mentions(api, last_mention_id):
    mentions = api.mentions_timeline(since_id=last_mention_id, tweet_mode="extended")
    prompt = ""
    original_tweet_id = None
    for mention in mentions:
        print(f"Responding to mention from @{mention.user.screen_name}")
        last_mention_id = mention.id
        # Check if the mention is a reply to a tweet
        if mention.in_reply_to_status_id is not None:
            original_tweet_id, original_tweeter_handle = get_original_tweet_info(api, mention.in_reply_to_status_id)
            thread_tweets = get_thread_tweets(api, mention)
            thread_tweets = reversed(thread_tweets)
            thread_tweets = list(thread_tweets)[1:][::-1]
            thread_tweets = reversed(thread_tweets)
            thread_text = "\n\n".join([f"@{user}: {text}" for user, text in thread_tweets])
            print(f"Thread text:\n{thread_text}")
            prompt = thread_text

            # Check if the bot is mentioned in the thread
            bot_mentioned = False
            if "ailogicanalyzer" in thread_text.lower():
                bot_mentioned = True

            # If the bot is mentioned, send an "I'm sorry" response to the user who mentioned it
            if bot_mentioned:
                print(f"I'm sorry @{mention.user.screen_name}, I can't do that")
                reply_text = f"I'm sorry @{mention.user.screen_name}, I can't do that"
                api.update_status(status=reply_text, in_reply_to_status_id=mention.id)
                save_last_mention_id(last_mention_id)
                break
        else:
            # Direct mention outside of a thread
            original_tweet_id = mention.id
            original_tweeter_handle = f"@{mention.user.screen_name}"
            prompt = f"{original_tweeter_handle} says {mention.full_text}"

        response=openai.ChatCompletion.create(
          model="gpt-3.5-turbo",
          temperature=0,
          messages=[
                {"role": "system", "content": "You analyze statements for logical fallacies"},
#                {"role": "user", "content": "evaluate next message for all logical fallacies; each response's explanation must be only one line and 240 characters (very important) or less (counting punctuation) for each fallacy. Only output a numbered list of each occurring fallacy, briefly explain each fallacy, and which \"@user:\" used it"},
                {"role": "user", "content": "evaluate next message for all logical fallacies; each response's explanation must be only one line and 240 characters (very important) or less (counting punctuation) for each fallacy. Only output a numbered list of each occurring fallacy, explain each fallacy, and which \"@user:\" used it"},
                {"role": "assistant", "content": str(prompt)},
            ]
        )

#########################################################
        fallacies = response['choices'][0]['message']['content']
        print(f"fallacies: {fallacies}")
        # Split the response message into multiple parts based on blank lines
        # Find all matches of a number followed by a period and an optional space
########        pattern = r'\d+\.\s*.*?(?=\s*\d+\.|$)'
        pattern = r'\d+\.\s*.*?(?=\n|$)'
        message_parts = re.finditer(pattern, fallacies)
        #message_parts = re.findall(pattern, fallacies)
        print(f"MP: {message_parts}")
        
        # Convert the iterator to a list and store the matched substrings
        matched_substrings = [match.group() for match in message_parts]
        print(matched_substrings)
        ### Remove the last element from the list
        ###matched_substrings.pop()
        # Combine substrings if their total length is less than or equal to 280 characters
        combined_substrings = []
        current_string = ""
        for substring in matched_substrings:
            # Check if the combined length of the current_string, substring, and a newline character is less than or equal to 280
            if len(current_string + substring) + 1 <= 280:
                if current_string:
                    current_string += "\n"  # Add a newline character if the current_string is not empty
                current_string += substring
            else:
                combined_substrings.append(current_string)
                current_string = substring
        # Add the last current_string to the list if it's not empty
        if current_string:
            combined_substrings.append(current_string)
        # Send replies in multiple tweets if necessary
        ##reply_to_id = mention.id
        print(f"original_tweet_id: {original_tweet_id}")
        print(f"original_tweeter_handle: {original_tweeter_handle}")
        if(original_tweet_id == None):
            original_tweet_id = mention.id
        if(original_tweeter_handle == None):
            original_tweeter_handle = f"@{mention.user.screen_name}"
        print(f"!original_tweet_id: {original_tweet_id}")
        print(f"!original_tweeter_handle: {original_tweeter_handle}")

        if combined_substrings and (combined_substrings[-1] == '' or combined_substrings[-1] == '\n'):
            combined_substrings.pop()
        #test = input("press enter to send")

        for part in reversed(combined_substrings):
            print(part)
            time.sleep(3)
            tweet = api.update_status(status=part, in_reply_to_status_id=original_tweet_id, auto_populate_reply_metadata=True)
        # Save the last mention ID to the file
        save_last_mention_id(last_mention_id)
    return last_mention_id

def main():
    api = create_api()
    last_mention_id = load_last_mention_id()
    while True:
        last_mention_id = respond_to_mentions(api, last_mention_id)
        print("Waiting for new mentions...")
        time.sleep(60)  # Check mentions every minute

if __name__ == "__main__":
    main()
