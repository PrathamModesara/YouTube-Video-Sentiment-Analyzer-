import streamlit as st
import pandas as pd
import re
import nltk
from nltk.corpus import stopwords
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from googletrans import Translator
from langdetect import detect
from googleapiclient.discovery import build

# =========================
# CONFIG
# =========================
API_KEY = ""
MAX_TOTAL_COMMENTS = 200
COMMENTS_PER_VIDEO = 30
MAX_VIDEOS = 4

youtube = build("youtube", "v3", developerKey=API_KEY)

# =========================
# NLP SETUP
# =========================
nltk.download("stopwords")
nltk.download("vader_lexicon")

translator = Translator()

HINGLISH_WORDS = [
    "hai","nahi","bahut","bilkul","accha","bakwas",
    "samajh","aaya","sir","ji","kya","kaise"
]

# =========================
# YOUTUBE FUNCTIONS
# =========================
def extract_video_id(link):
    match = re.search(r"v=([^&]+)", link)
    return match.group(1) if match else None

def extract_playlist_id(link):
    match = re.search(r"list=([^&]+)", link)
    return match.group(1) if match else None

def fetch_comments_from_video(video_id, limit):
    comments = []
    next_page_token = None

    while len(comments) < limit:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=min(50, limit - len(comments)),
            pageToken=next_page_token
        )

        response = request.execute()

        for item in response.get("items", []):
            text = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
            comments.append(text)
            if len(comments) >= limit:
                break

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    return comments

# =========================
# SENTIMENT FUNCTIONS
# =========================
def translate_if_needed(text):
    try:
        lang = detect(text)
        is_hinglish = any(w in text.lower().split() for w in HINGLISH_WORDS)

        if lang == "hi" or is_hinglish:
            return translator.translate(text, dest="en").text
        else:
            return text
    except:
        return text

def clean_text(text):
    stop_words = set(stopwords.words("english"))
    text = text.lower()
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[^a-z\s]", "", text)
    words = text.split()
    words = [w for w in words if w not in stop_words]
    return " ".join(words)

def run_sentiment(comments_list):

    comments = pd.DataFrame(comments_list, columns=["comment"])
    comments["translated"] = comments["comment"].apply(translate_if_needed)
    comments["clean_comment"] = comments["translated"].apply(clean_text)

    sia = SentimentIntensityAnalyzer()

    def get_sentiment(text):
        score = sia.polarity_scores(text)["compound"]
        if score >= 0.05:
            return "positive"
        elif score <= -0.05:
            return "negative"
        else:
            return "neutral"

    comments["sentiment"] = comments["clean_comment"].apply(get_sentiment)

    sentiment_counts = comments["sentiment"].value_counts()

    positive = sentiment_counts.get("positive", 0)
    negative = sentiment_counts.get("negative", 0)
    neutral  = sentiment_counts.get("neutral", 0)

    total = positive + negative + neutral
    score = (positive - negative) / total if total else 0

    rating = ((score + 1) / 2) * 4 + 1
    rating = round(rating, 1)

    if score > 0.2:
        decision = "✅ Video is GOOD / Recommended"
    elif score < 0:
        decision = "❌ Video is NOT GOOD"
    else:
        decision = "⚖️ Video is AVERAGE"

    return positive, negative, neutral, score, rating, decision

# =========================
# STREAMLIT FRONTEND
# =========================
st.title("🎬 YouTube Video Sentiment Analyzer")

youtube_link = st.text_input("Paste YouTube Link:")

if st.button("Analyze Video"):

    if youtube_link:

        with st.spinner("Fetching comments and analyzing sentiment..."):

            all_comments = []

            playlist_id = extract_playlist_id(youtube_link)
            video_id = extract_video_id(youtube_link)

            if playlist_id:
                playlist_request = youtube.playlistItems().list(
                    part="contentDetails",
                    playlistId=playlist_id,
                    maxResults=MAX_VIDEOS
                )
                playlist_response = playlist_request.execute()

                for item in playlist_response.get("items", []):
                    if len(all_comments) >= MAX_TOTAL_COMMENTS:
                        break

                    vid = item["contentDetails"]["videoId"]
                    all_comments.extend(fetch_comments_from_video(vid, COMMENTS_PER_VIDEO))

            elif video_id:
                all_comments = fetch_comments_from_video(video_id, MAX_TOTAL_COMMENTS)

            else:
                st.error("Invalid YouTube link")
                st.stop()

            positive, negative, neutral, score, rating, decision = run_sentiment(all_comments)

        st.success("Analysis Complete!")

        st.write("### 📊 Results")
        st.write("Positive:", positive)
        st.write("Negative:", negative)
        st.write("Neutral :", neutral)
        st.write("Final Score:", round(score,3))
        st.write("⭐ Rating:", rating, "/5")
        st.write(decision)

    else:
        st.warning("Please enter a YouTube link.")









# import streamlit as st
# import pandas as pd
# import re
# import nltk
# from nltk.corpus import stopwords
# from nltk.sentiment.vader import SentimentIntensityAnalyzer
# from googletrans import Translator
# from langdetect import detect
# from googleapiclient.discovery import build

# # ML Imports
# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.linear_model import LogisticRegression

# # =========================
# # CONFIG
# # =========================
# API_KEY = ""
# MAX_TOTAL_COMMENTS = 200
# COMMENTS_PER_VIDEO = 30
# MAX_VIDEOS = 4

# youtube = build("youtube", "v3", developerKey=API_KEY)

# # =========================
# # NLP SETUP
# # =========================
# nltk.download("stopwords")
# nltk.download("vader_lexicon")

# translator = Translator()

# HINGLISH_WORDS = [
#     "hai","nahi","bahut","bilkul","accha","bakwas",
#     "samajh","aaya","sir","ji","kya","kaise"
# ]

# # =========================
# # YOUTUBE FUNCTIONS
# # =========================
# def extract_video_id(link):
#     match = re.search(r"v=([^&]+)", link)
#     return match.group(1) if match else None

# def extract_playlist_id(link):
#     match = re.search(r"list=([^&]+)", link)
#     return match.group(1) if match else None

# def fetch_comments_from_video(video_id, limit):
#     comments = []
#     next_page_token = None

#     while len(comments) < limit:
#         request = youtube.commentThreads().list(
#             part="snippet",
#             videoId=video_id,
#             maxResults=min(50, limit - len(comments)),
#             pageToken=next_page_token
#         )

#         response = request.execute()

#         for item in response.get("items", []):
#             text = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
#             comments.append(text)
#             if len(comments) >= limit:
#                 break

#         next_page_token = response.get("nextPageToken")
#         if not next_page_token:
#             break

#     return comments

# # =========================
# # NLP FUNCTIONS
# # =========================
# def translate_if_needed(text):
#     try:
#         lang = detect(text)
#         is_hinglish = any(w in text.lower().split() for w in HINGLISH_WORDS)

#         if lang == "hi" or is_hinglish:
#             return translator.translate(text, dest="en").text
#         else:
#             return text
#     except:
#         return text

# def clean_text(text):
#     stop_words = set(stopwords.words("english"))
#     text = text.lower()
#     text = re.sub(r"http\S+", "", text)
#     text = re.sub(r"[^a-z\s]", "", text)
#     words = text.split()
#     words = [w for w in words if w not in stop_words]
#     return " ".join(words)

# # =========================
# # HYBRID SENTIMENT MODEL
# # =========================
# def run_sentiment(comments_list):

#     comments = pd.DataFrame(comments_list, columns=["comment"])

#     # Step 1: Translation + Cleaning
#     comments["translated"] = comments["comment"].apply(translate_if_needed)
#     comments["clean_comment"] = comments["translated"].apply(clean_text)

#     # Step 2: VADER auto-label
#     sia = SentimentIntensityAnalyzer()

#     def vader_label(text):
#         score = sia.polarity_scores(text)["compound"]
#         if score >= 0.05:
#             return "positive"
#         elif score <= -0.05:
#             return "negative"
#         else:
#             return "neutral"

#     comments["vader_sentiment"] = comments["clean_comment"].apply(vader_label)

#     # Step 3: TF-IDF
#     vectorizer = TfidfVectorizer(max_features=3000)
#     X = vectorizer.fit_transform(comments["clean_comment"])
#     y = comments["vader_sentiment"]

#     # Step 4: Logistic Regression
#     model = LogisticRegression(max_iter=1000)
#     model.fit(X, y)

#     # Step 5: Predict
#     predictions = model.predict(X)
#     comments["sentiment"] = predictions

#     # Step 6: Count results
#     sentiment_counts = comments["sentiment"].value_counts()

#     positive = sentiment_counts.get("positive", 0)
#     negative = sentiment_counts.get("negative", 0)
#     neutral  = sentiment_counts.get("neutral", 0)

#     total = positive + negative + neutral
#     score = (positive - negative) / total if total else 0

#     rating = ((score + 1) / 2) * 4 + 1
#     rating = round(rating, 1)

#     if score > 0.2:
#         decision = "✅ Video is GOOD / Recommended (Logistic Model)"
#     elif score < 0:
#         decision = "❌ Video is NOT GOOD (Logistic Model)"
#     else:
#         decision = "⚖️ Video is AVERAGE (Logistic Model)"

#     return positive, negative, neutral, score, rating, decision

# # =========================
# # STREAMLIT UI
# # =========================
# st.title("🎬 YouTube Video Sentiment Analyzer (ML Version)")

# youtube_link = st.text_input("Paste YouTube Link:")

# if st.button("Analyze Video"):

#     if youtube_link:

#         with st.spinner("Fetching comments and analyzing sentiment..."):

#             all_comments = []

#             playlist_id = extract_playlist_id(youtube_link)
#             video_id = extract_video_id(youtube_link)

#             if playlist_id:
#                 playlist_request = youtube.playlistItems().list(
#                     part="contentDetails",
#                     playlistId=playlist_id,
#                     maxResults=MAX_VIDEOS
#                 )
#                 playlist_response = playlist_request.execute()

#                 for item in playlist_response.get("items", []):
#                     if len(all_comments) >= MAX_TOTAL_COMMENTS:
#                         break

#                     vid = item["contentDetails"]["videoId"]
#                     all_comments.extend(fetch_comments_from_video(vid, COMMENTS_PER_VIDEO))

#             elif video_id:
#                 all_comments = fetch_comments_from_video(video_id, MAX_TOTAL_COMMENTS)

#             else:
#                 st.error("Invalid YouTube link")
#                 st.stop()

#             positive, negative, neutral, score, rating, decision = run_sentiment(all_comments)

#         st.success("Analysis Complete!")

#         st.write("### 📊 Results")
#         st.write("Positive:", positive)
#         st.write("Negative:", negative)
#         st.write("Neutral :", neutral)
#         st.write("Final Score:", round(score,3))
#         st.write("⭐ Rating:", rating, "/5")
#         st.write(decision)

#     else:
#         st.warning("Please enter a YouTube link.")
