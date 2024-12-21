import yt_dlp as ytdl
import os
import streamlit as st
from pathlib import Path
import tempfile
import shutil

def download_video_to_temp(url):
    """Download the best audio in MP3 format to a temporary directory and return the file path."""
    temp_dir = tempfile.mkdtemp()
    output_file = os.path.join(temp_dir, '%(title)s.%(ext)s')
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_file,
        'quiet': True,
        'postprocessors': [
            {   # Convert audio to MP3
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }
        ],
    }
    
    with ytdl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    
    downloaded_file = next(Path(temp_dir).glob("*.mp3"))  # Look specifically for the MP3 file
    return downloaded_file



def move_file_to_directory(file_path, destination_directory):
    """Move a file to a specified directory."""
    if not os.path.exists(destination_directory):
        os.makedirs(destination_directory)
    destination_path = os.path.join(destination_directory, os.path.basename(file_path))
    shutil.move(file_path, destination_path)
    return destination_path

# Streamlit app interface
st.set_page_config(page_title="YouTube Audio Downloader", page_icon="🎵", layout="wide")
st.title("🎵 YouTube Audio Downloader")
st.markdown(
    """
    Download high-quality audio from YouTube videos effortlessly! Simply paste the video URL, and choose whether to play, save, or download the file.
    """
)

# Sidebar for navigation
st.sidebar.header("Settings")
default_directory = str(Path.home() / "Downloads")
directory = st.sidebar.text_input("💾 Save Directory:", value=default_directory, placeholder="Enter the directory to save the file")

# Main content area
st.divider()
url = st.text_input("🎥 Enter the YouTube URL:", placeholder="e.g., https://www.youtube.com/watch?v=example")

if st.button("🚀 Download and Play Audio"):
    if not url.strip():
        st.error("❌ Please enter a valid YouTube URL.")
    else:
        try:
            with st.spinner("Downloading audio... Please wait."):
                downloaded_file = download_video_to_temp(url)
            
            st.success("✅ Download complete! Choose an action below.")
            
            # Provide an option to play the audio
            st.audio(str(downloaded_file), format="audio/mpeg", start_time=0)

            # Provide action buttons
            col3, col4 = st.columns(2)

            with col3:
                if st.button("📂 Move File to Directory"):
                    moved_file = move_file_to_directory(downloaded_file, directory)
                    st.success(f"✅ File moved to: {moved_file}")

            with col4:
                with open(downloaded_file, "rb") as file:
                    st.download_button(
                        label="⬇️ Download Audio File",
                        data=file,
                        file_name=os.path.basename(downloaded_file),
                        mime="audio/mpeg"
                    )

        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")

# Footer
st.markdown("---")
