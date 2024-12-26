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

def download_video_to_temp(url):
    """Download the best audio to a temporary directory and return the file path."""
    temp_dir = tempfile.mkdtemp()
    output_file = os.path.join(temp_dir, '%(title)s.%(ext)s')
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_file,
        'quiet': True,
    }
    
    with ytdl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    
    downloaded_file = next(Path(temp_dir).glob("*"))
    return downloaded_file

def move_file_to_directory(file_path, destination_directory):
    """Move a file to a specified directory."""
    if not os.path.exists(destination_directory):
        os.makedirs(destination_directory)
    destination_path = os.path.join(destination_directory, os.path.basename(file_path))
    shutil.move(file_path, destination_path)
    return destination_path

# Initialize session state
if "selected_video" not in st.session_state:
    st.session_state.selected_video = None

if "selected_thumbnail" not in st.session_state:
    st.session_state.selected_thumbnail = None

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
        placeholder="Type a topic to search for videos (e.g., 'Bini')",
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
                    st.session_state.selected_video = video_id
                    st.session_state.selected_thumbnail = thumbnail_url

            # Show thumbnail and download options for the selected video
            if st.session_state.selected_video:
                st.markdown("### Selected Video")
                st.image(st.session_state.selected_thumbnail, width=400)
                video_url = f"https://www.youtube.com/watch?v={st.session_state.selected_video}"

                if st.button("Convert Track"):
                    try:
                        with st.spinner("Preparing your track..."):
                            downloaded_file = download_video_to_temp(video_url)
                        
                        st.success("Track ready! Choose your next move.")
                        
                        # Audio player
                        st.markdown("### Now Playing")
                        st.audio(str(downloaded_file), format="audio/mpeg", start_time=0)

                        # Action buttons in columns
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Save to Library", key="move_button"):
                                moved_file = move_file_to_directory(downloaded_file, directory)
                                st.success(f"Track saved to: {moved_file}")

                        with col2:
                            with open(downloaded_file, "rb") as file:
                                st.download_button(
                                    label="⬇ Download Track",
                                    data=file,
                                    file_name=os.path.basename(downloaded_file),
                                    mime="audio/mpeg",
                                    key="download_file_button"
                                )

                    except Exception as e:
                        st.error(f"An error occurred: {str(e)}")
        else:
            st.error("No videos found. Please try a different query.")

elif page == "Play Song":
    # Page for playing the song
    st.markdown("### Play Your Favorite Songs")

    # Display the list of MP3 and WEBM files in the download directory
    download_dir = Path.home() / "Downloads"
    audio_files = list(download_dir.glob("*.mp3")) + list(download_dir.glob("*.webm"))

    if audio_files:
        # Sort files by modification time (newest first)
        audio_files = sorted(audio_files, key=lambda x: x.stat().st_mtime, reverse=True)

        # Search bar for filtering songs
        search_term = st.text_input("Search songs:", placeholder="Search by file name")

        if search_term:
            audio_files = [file for file in audio_files if search_term.lower() in file.name.lower()]

        # Scrollable container for the list of songs
      

        # Use a scrollable container
        st.markdown('<div class="scrollable-container">', unsafe_allow_html=True)

        # Render the list of songs as a form (interactive elements)
        with st.form("song_list_form"):
            selected_file = st.radio(
                "Available Songs:",
                [file.name for file in audio_files],
                key="song_selector"
            )
            # Add a submit button for the form
            submitted = st.form_submit_button("Play Selected")

        st.markdown('</div>', unsafe_allow_html=True)

        if submitted and selected_file:
            file_path = download_dir / selected_file

            # Audio player
            st.markdown("### Now Playing")
            st.audio(str(file_path), format="audio/mpeg", start_time=0)
    else:
        st.info("No audio files (.mp3 or .webm) found in the Downloads folder. Download some tracks first!")

# Footer
st.markdown("---")
