from googleapiclient.discovery import build
import pandas as pd

# Replace with your YouTube API Key
API_KEY = "your youtube api key"

# Function to build the YouTube API service
def build_youtube_service(api_key):
    return build("youtube", "v3", developerKey=api_key)

# Function to fetch channel details
def get_channel_details(youtube, channel_name):
    search_response = youtube.search().list(
        q=channel_name, part="snippet", type="channel", maxResults=1
    ).execute()

    if not search_response['items']:
        return None

    channel_id = search_response['items'][0]['id']['channelId']
    channel_title = search_response['items'][0]['snippet']['title']

    # Fetch channel statistics
    channel_response = youtube.channels().list(
        part="statistics,snippet", id=channel_id
    ).execute()

    stats = channel_response['items'][0]['statistics']
    return {
        "channel_id": channel_id,
        "channel_name": channel_title,
        "subscribers": int(stats.get("subscriberCount", 0)),
        "views": int(stats.get("viewCount", 0)),
        "videos": int(stats.get("videoCount", 0)),
    }

# Function to fetch popular videos
def get_popular_videos(youtube, channel_id, max_results=5):
    response = youtube.channels().list(
        part="contentDetails", id=channel_id
    ).execute()
    uploads_playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    # Fetch all videos in the uploads playlist
    videos = []
    next_page_token = None

    while True:
        videos_response = youtube.playlistItems().list(
            part="snippet", playlistId=uploads_playlist_id, maxResults=50, pageToken=next_page_token
        ).execute()

        for item in videos_response['items']:
            video_id = item['snippet']['resourceId']['videoId']
            video_title = item['snippet']['title']

            # Fetch video statistics
            video_response = youtube.videos().list(
                part="statistics", id=video_id
            ).execute()

            stats = video_response['items'][0]['statistics']
            videos.append({
                "title": video_title,
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0)),
            })

        # Check if there is another page of results
        next_page_token = videos_response.get("nextPageToken")
        if not next_page_token:
            break

    # Sort videos by views in descending order and return the top N
    sorted_videos = sorted(videos, key=lambda x: x["views"], reverse=True)
    return sorted_videos[:max_results]

# Main script execution
if __name__ == "__main__":
    # Initialize YouTube API service
    youtube = build_youtube_service(API_KEY)

    # Input channel name
    channel_name = input("Enter the YouTube Channel Name: ")

    # Fetch channel details
    channel_data = get_channel_details(youtube, channel_name)

    if channel_data:
        # Print channel details once
        print("-" * 50)
        print("Channel Details:")
        print(f"Channel Name: {channel_data['channel_name']}")
        print(f"Subscribers: {channel_data['subscribers']:,}")  # Format with commas
        print(f"Total Views: {channel_data['views']:,}")        # Format with commas
        print(f"Total Videos: {channel_data['videos']:,}")      # Format with commas
        print("-" * 50)

        # Fetch popular videos and print them
        popular_videos = get_popular_videos(youtube, channel_data['channel_id'])
        df_videos = pd.DataFrame(popular_videos)

        # Format numeric columns with commas for readability
        df_videos["views"] = df_videos["views"].apply(lambda x: f"{x:,}")
        df_videos["likes"] = df_videos["likes"].apply(lambda x: f"{x:,}")
        df_videos["comments"] = df_videos["comments"].apply(lambda x: f"{x:,}")

        print("Popular Videos Performance:")
        print(df_videos.to_string(index=False))
        print("-" * 50)

    else:
        print("Channel not found. Please try a different name.")
