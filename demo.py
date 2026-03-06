# from googleapiclient.discovery import build
# import re

# # =========================
# # CONFIG
# # =========================
# API_KEY = ""   # ⚠️ regenerate & paste here
# MAX_TOTAL_COMMENTS = 120            # FAST + enough for analysis
# COMMENTS_PER_VIDEO = 30             # for playlist videos
# MAX_VIDEOS = 4                      # playlist limit

# # =========================
# # BUILD YOUTUBE SERVICE
# # =========================
# youtube = build("youtube", "v3", developerKey=API_KEY)

# # =========================
# # HELPER FUNCTIONS
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
# # MAIN
# # =========================
# youtube_link = input("Enter YouTube link: ").strip()
# all_comments = []

# playlist_id = extract_playlist_id(youtube_link)
# video_id = extract_video_id(youtube_link)

# # 🔥 CASE 1: PLAYLIST OR WATCH+PLAYLIST
# if playlist_id:
#     print("\nPlaylist detected")
#     print("Playlist ID:", playlist_id)

#     playlist_request = youtube.playlistItems().list(
#         part="contentDetails",
#         playlistId=playlist_id,
#         maxResults=MAX_VIDEOS
#     )

#     playlist_response = playlist_request.execute()

#     for item in playlist_response.get("items", []):
#         if len(all_comments) >= MAX_TOTAL_COMMENTS:
#             break

#         vid = item["contentDetails"]["videoId"]
#         print("Fetching comments from video:", vid)

#         comments = fetch_comments_from_video(vid, COMMENTS_PER_VIDEO)
#         all_comments.extend(comments)

# # 🔥 CASE 2: ONLY SINGLE VIDEO
# elif video_id:
#     print("\nSingle video detected")
#     print("Video ID:", video_id)

#     all_comments = fetch_comments_from_video(video_id, MAX_TOTAL_COMMENTS)

# # ❌ INVALID LINK
# else:
#     print("Invalid YouTube link")
#     exit()

# # =========================
# # OUTPUT CHECK
# # =========================
# all_comments = all_comments[:MAX_TOTAL_COMMENTS]

# print("\n==============================")
# print("TOTAL COMMENTS FETCHED:", len(all_comments))
# print("==============================\n")

# print("Sample comments:\n")
# for i, c in enumerate(all_comments[:10], 1):
#     print(f"{i}. {c}")

# print("\n(Showing first 10 comments only)")

# # =========================
# # SAVE COMMENTS TO TEXT FILE
# # =========================
# file_name = "youtube_comments.txt"

# with open(file_name, "w", encoding="utf-8") as f:
#     for comment in all_comments:
#         f.write(comment.replace("\n", " ") + "\n")

# print(f"\nComments saved successfully to '{file_name}'")



from googleapiclient.discovery import build
import re
from sentiment_model import run_sentiment

API_KEY = "PUT_YOUR_NEW_API_KEY"
MAX_TOTAL_COMMENTS = 120
COMMENTS_PER_VIDEO = 30
MAX_VIDEOS = 4

youtube = build("youtube", "v3", developerKey=API_KEY)

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


def analyze_video(youtube_link):

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
            comments = fetch_comments_from_video(vid, COMMENTS_PER_VIDEO)
            all_comments.extend(comments)

    elif video_id:
        all_comments = fetch_comments_from_video(video_id, MAX_TOTAL_COMMENTS)

    else:
        return {"error": "Invalid YouTube link"}

    all_comments = all_comments[:MAX_TOTAL_COMMENTS]

    file_name = "youtube_comments.txt"

    with open(file_name, "w", encoding="utf-8") as f:
        for comment in all_comments:
            f.write(comment.replace("\n", " ") + "\n")

    # 🔥 RUN SENTIMENT MODEL
    result = run_sentiment(file_name)

    return result
