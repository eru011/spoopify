import yt_dlp as ytdl
import os
import streamlit as st
from pathlib import Path
import tempfile

def download_video_to_temp(url):
    """Download the best audio to a temporary directory and return the file path."""
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    output_file = os.path.join(temp_dir, '%(title)s.%(ext)s')
    
    # yt-dlp options
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_file,
        'quiet': True,  # Suppress output
    }
    
    with ytdl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    
    # Get the downloaded file path
    downloaded_file = next(Path(temp_dir).glob("*"))
    return downloaded_file

# Streamlit app interface
st.title("YouTube Audio Downloader")
st.write("Download high-quality audio from YouTube videos.")

# Input field for URL
url = st.text_input("Enter the YouTube URL:")

if st.button("Download Audio"):
    if not url.strip():
        st.error("Please enter a valid YouTube URL.")
    else:
        try:
            st.info("Downloading audio...")
            downloaded_file = download_video_to_temp(url)
            
            st.success("Download complete! You can now download the file to your device.")
            
            # Provide a download button for the file
            with open(downloaded_file, "rb") as file:
                st.download_button(
                    label="Download Audio File",
                    data=file,
                    file_name=os.path.basename(downloaded_file),
                    mime="audio/mpeg"
                )
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
