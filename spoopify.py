import yt_dlp as ytdl
import streamlit as st
from pathlib import Path
import tempfile
import requests

# Initialize session state
if 'state' not in st.session_state:
    st.session_state.state = {
        'selected_video': None,
        'selected_thumbnail': None,
        'selected_title': None,
        'downloaded_file': None,
        'is_converted': False,
        'current_page': 'Home'
    }

def search_youtube(query):
    """Search for YouTube videos."""
    try:
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet,id",
            "q": query,
            "type": "video",
            "maxResults": 10,
            "key": st.secrets["youtube"]["api_key"]
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if 'items' not in data:
            raise ValueError("Invalid API response")
            
        return [
            {
                'id': item['id']['videoId'],
                'title': item['snippet']['title'],
                'thumbnail': item['snippet']['thumbnails']['high']['url']
            }
            for item in data['items']
            if all(k in item for k in ['id', 'snippet'])
        ]
    except Exception as e:
        st.error(f"Search failed: {str(e)}")
        return []

def download_audio(url):
    """Download and convert video to audio."""
    try:
        temp_dir = tempfile.mkdtemp()
        output_template = str(Path(temp_dir) / '%(title)s.%(ext)s')
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True,
            'extract_audio': True,
            'audio_format': 'mp3',
            'audio_quality': '192K',
            'nocheckcertificate': True,
            'geo_bypass': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        }
        
        with ytdl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # Find the downloaded file
        audio_file = next(Path(temp_dir).glob('*.mp3'), None)
        if not audio_file:
            raise FileNotFoundError("No audio file was created")
            
        return audio_file
    except Exception as e:
        st.error(f"Download failed: {str(e)}")
        return None

def render_home():
    """Render home page with search functionality."""
    st.markdown("### Search for Music")
    query = st.text_input("Search:", placeholder="Enter song name or artist")
    
    if query:
        with st.spinner("Searching..."):
            results = search_youtube(query)
            
        if results:
            for item in results:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{item['title']}**")
                with col2:
                    if st.button("Select", key=item['id']):
                        try:
                            st.session_state.state.update({
                                'selected_video': item['id'],
                                'selected_thumbnail': item['thumbnail'],
                                'selected_title': item['title'],
                                'is_converted': False,
                                'current_page': 'Play'
                            })
                            st.query_params["tab"] = "Player"
                        except Exception as e:
                            st.error(f"Error selecting track: {str(e)}")
                        st.rerun()
        else:
            st.warning("No results found")

def render_player():
    """Render music player page."""
    state = st.session_state.state
    if not state['selected_video']:
        st.warning("No track selected")
        return

    st.image(state['selected_thumbnail'], width=400)
    st.markdown(f"### {state['selected_title']}")
    
    if not state['is_converted']:
        with st.spinner("Converting audio..."):
            video_url = f"https://www.youtube.com/watch?v={state['selected_video']}"
            audio_file = download_audio(video_url)
            
            if audio_file:
                state.update({
                    'downloaded_file': audio_file,
                    'is_converted': True
                })
                st.success("Ready to play!")
                st.rerun()
    
    if state['is_converted'] and state['downloaded_file']:
        st.audio(str(state['downloaded_file']), format='audio/mp3')
        
        with open(state['downloaded_file'], 'rb') as f:
            st.download_button(
                "⬇ Download",
                f,
                file_name=state['downloaded_file'].name,
                mime='audio/mp3'
            )

# Main UI
st.title("Xen Music")

# Navigation with error handling
try:
    current_tab = st.query_params.get("tab", "Search")
except Exception:
    current_tab = "Search"
    
tab_index = 1 if current_tab == "Player" else 0

# Create tabs with the selected index
tabs = st.tabs(["Search", "Player"])

with tabs[0]:
    render_home()
        
with tabs[1]:
    render_player()
