from youtube_transcript_api import YouTubeTranscriptApi

video_id = "aircAruvnKk"  # guaranteed transcript video

try:
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    print("Transcript working ✅")
    print(transcript[:5])
except Exception as e:
    print("ERROR:", e)