import yt_dlp as ytdl
import os
import streamlit as st
from pathlib import Path
import tempfile
import shutil
import requests

# Load YouTube API key from Streamlit secrets
YOUTUBE_API_KEY = st.secrets["youtube"]["api_key"]

def search_youtube(query, max_results=5):
    """Search for YouTube videos based on a query and return the results."""
    url = f"https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "key": YOUTUBE_API_KEY,
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        results = response.json()
        return results["items"]
    else:
        st.error("Failed to fetch YouTube results. Please check your API key.")
        return []

def download_video_to_temp(url, save_directory):
    """Download the best audio to a specified directory and return the file path."""
    output_file = os.path.join(save_directory, '%(title)s.%(ext)s')

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_file,
        'quiet': True,
        'postprocessors': [{
            'key': 'FFmpegAudioConvertor',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    with ytdl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    # Get the downloaded file
    downloaded_file = next(Path(save_directory).glob("*.mp3"))  # Only mp3 files
    return downloaded_file

# Initialize session state for storing downloaded files
if "downloaded_files" not in st.session_state:
    st.session_state.downloaded_files = []

# Main layout
st.title("YouTube Audio Downloader")

# Sidebar for navigation
page = st.sidebar.radio("Select a page:", ["Home", "Play Song"])

if page == "Home":
    # Home page for searching and downloading
    st.markdown(
        """
        Search for high-quality audio from YouTube videos. 
        Simply type a topic below to get started.
        """
    )

    # Sidebar for settings
    default_directory = str(Path.home() / "Downloads")
    directory = st.sidebar.text_input(
        "Save Directory:", 
        value=default_directory, 
        placeholder="Enter the directory to save the file"
    )

    # Search input
    search_query = st.text_input(
        "Search YouTube:", 
        placeholder="Type a topic to search for videos (e.g., 'Lola Amour')",
    )

    if search_query:
        with st.spinner("Searching for videos..."):
            results = search_youtube(search_query)

        if results:
            st.markdown("### Search Results")
            for item in results:
                video_id = item["id"]["videoId"]
                title = item["snippet"]["title"]
                thumbnail_url = item["snippet"]["thumbnails"]["high"]["url"]

                # Create a button for selecting a video
                if st.button(f"Select '{title}'", key=video_id):
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    try:
                        with st.spinner("Downloading audio... Please wait."):
                            downloaded_file = download_video_to_temp(video_url, directory)
                            st.session_state.downloaded_files.append(downloaded_file)  # Add to session state
                            st.success(f"Audio from '{title}' downloaded!")
                    except Exception as e:
                        st.error(f"Error downloading video: {e}")

elif page == "Play Song":
    # Page for playing the song
    st.markdown("### Play Your Favorite Songs")

    if st.session_state.downloaded_files:
        st.markdown("### Available Tracks")

        # Render available tracks (from session state) as radio buttons or a list
        song_options = [file.name for file in st.session_state.downloaded_files]
        selected_song = st.radio("Select a song to play", song_options)

        # Find the file that was selected
        selected_file = next(file for file in st.session_state.downloaded_files if file.name == selected_song)

        # Audio player
        st.audio(str(selected_file), format="audio/mpeg", start_time=0)

        # Option to delete the file from session (optional)
        if st.button("Remove song from session", key=selected_file.name):
            st.session_state.downloaded_files.remove(selected_file)
            st.success(f"'{selected_song}' removed from session.")

    else:
        st.info("No songs available. Download a song first!")
        
# Footer
st.markdown("---")
