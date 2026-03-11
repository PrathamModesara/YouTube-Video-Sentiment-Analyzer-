import streamlit as st
import pandas as pd
import re
import nltk
from nltk.corpus import stopwords
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from langdetect import detect
from googleapiclient.discovery import build

# =========================
# CONFIG
# =========================
API_KEY = "AIzaSyCo7ZeAaxMwqRMJp-nz-iIYn2CZ19m87RA"

MAX_TOTAL_COMMENTS = 200
COMMENTS_PER_VIDEO = 30
MAX_VIDEOS = 4

youtube = build("youtube", "v3", developerKey=API_KEY)

# =========================
# NLP SETUP
# =========================
nltk.download("stopwords")
nltk.download("vader_lexicon")

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
# TRANSLATION FUNCTION (DISABLED)
# =========================
def translate_to_english(text):

    try:
        lang = detect(text)

        if lang != "en":
            return text
        else:
            return text

    except:
        return text


# =========================
# SAVE CSV FUNCTION
# =========================
def save_comments_to_csv(comments):

    rows = []

    for i, comment in enumerate(comments, start=1):

        translated = translate_to_english(comment)

        rows.append({
            "number": i,
            "real_comment": comment,
            "translated_comment": translated
        })

    df = pd.DataFrame(rows)

    df.to_csv("youtube_comments.csv", index=False)

    return df


# =========================
# CLEAN TEXT
# =========================
def clean_text(text):

    stop_words = set(stopwords.words("english"))

    text = text.lower()

    text = re.sub(r"http\S+", "", text)

    text = re.sub(r"[^a-z\s]", "", text)

    words = text.split()

    words = [w for w in words if w not in stop_words]

    return " ".join(words)


# =========================
# SENTIMENT ANALYSIS
# =========================
def run_sentiment(df):

    df["clean_comment"] = df["translated_comment"].apply(clean_text)

    sia = SentimentIntensityAnalyzer()

    def get_sentiment(text):

        score = sia.polarity_scores(text)["compound"]

        if score >= 0.05:
            return "positive"

        elif score <= -0.05:
            return "negative"

        else:
            return "neutral"

    df["sentiment"] = df["clean_comment"].apply(get_sentiment)

    sentiment_counts = df["sentiment"].value_counts()

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
# STREAMLIT UI
# =========================
st.title("🎬 YouTube Comment Sentiment Analyzer")

youtube_link = st.text_input("Paste YouTube Link")


if st.button("Analyze Video"):

    if youtube_link:

        with st.spinner("Fetching comments..."):

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

                    all_comments.extend(
                        fetch_comments_from_video(
                            vid,
                            COMMENTS_PER_VIDEO
                        )
                    )

            elif video_id:

                all_comments = fetch_comments_from_video(
                    video_id,
                    MAX_TOTAL_COMMENTS
                )

            else:

                st.error("Invalid YouTube link")

                st.stop()

            df_comments = save_comments_to_csv(all_comments)

            positive, negative, neutral, score, rating, decision = run_sentiment(df_comments)

        st.success("Analysis Complete!")

        st.write("### Sentiment Results")

        st.write("Positive:", positive)
        st.write("Negative:", negative)
        st.write("Neutral:", neutral)
        st.write("Score:", round(score,3))
        st.write("⭐ Rating:", rating, "/5")
        st.write(decision)

        st.write("### Dataset Preview")

        st.dataframe(df_comments)

    else:

        st.warning("Please paste a YouTube link.")