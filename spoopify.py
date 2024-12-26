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

if "current_page" not in st.session_state:
    st.session_state.current_page = "Home"

# Navigation function
def navigate_to(page):
    st.session_state.current_page = page

# Main layout 
st.title("Xen Music")

# Sidebar for navigation
page = st.sidebar.radio("Select a page:", ["Home", "Play Song"], index=["Home", "Play Song"].index(st.session_state.current_page))

if page != st.session_state.current_page:
    navigate_to(page)

if st.session_state.current_page == "Home":
    # Home page for searching and downloading
    st.markdown(
        """
        Search for high-quality audio with XEN. 
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
                    st.info("Video selected! Please go to the Play Song tab.")

                    # Automatically navigate to the "Play Song" tab
                    navigate_to("Play Song")
                    st.experimental_rerun()

        else:
            st.error("No videos found. Please try a different query.")

elif st.session_state.current_page == "Play Song":

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
                    # Generate HTML link for download
                    download_url = f"file:///{downloaded_file}"  # Local file URL
                    download_link = f'<a href="{download_url}" download="{os.path.basename(downloaded_file)}" target="_blank">⬇ Download Track</a>'
                    st.markdown(download_link, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

# Footer
st.markdown("---")
