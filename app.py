import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz

# YouTube Data API configuration
API_KEY = "AIzaSyD0A1-sNqmrt398sHOcIadTD1qCDkZ96UA"  # Replace with your API key
MAX_RESULTS_PER_PAGE = 10  # Number of videos to show per page

# Language and topic configuration
LANGUAGE_OPTIONS = {
    "en": {"name": "English", "flag": "🇺🇸"},
    "hi": {"name": "हिन्दी", "flag": "🇮🇳"},
    "ta": {"name": "தமிழ்", "flag": "🇮🇳"},
    "te": {"name": "తెలుగు", "flag": "🇮🇳"},
    "es": {"name": "Español", "flag": "🇪🇸"},
    "fr": {"name": "Français", "flag": "🇫🇷"},
    "de": {"name": "Deutsch", "flag": "🇩🇪"},
    "ja": {"name": "日本語", "flag": "🇯🇵"},
    "zh": {"name": "中文", "flag": "🇨🇳"},
    "ar": {"name": "العربية", "flag": "🇸🇦"}
}

# Topics in all languages
TOPICS = {
    "en": {
        "latest_it_jobs": "latest IT hiring jobs",
        "internships": "internships",
        "stipend_internships": "stipend internships",
        "work_from_home": "work from home jobs",
        "latest_tech_news": "latest tech news",
        "non_it_jobs": "non IT jobs",
        "latest_technologies": "latest technologies",
        "remote_jobs": "remote jobs",
        "government_jobs": "government jobs"
    },
    "hi": {
        "latest_it_jobs": "नवीनतम आईटी नौकरियां",
        "internships": "इंटर्नशिप",
        "stipend_internships": "स्टाइपेंड इंटर्नशिप",
        "work_from_home": "घर से काम करने की नौकरियां",
        "latest_tech_news": "नवीनतम टेक समाचार",
        "non_it_jobs": "गैर आईटी नौकरियां",
        "latest_technologies": "नवीनतम प्रौद्योगिकियां",
        "remote_jobs": "रिमोट नौकरियां",
        "government_jobs": "सरकारी नौकरियां"
    },
    "ta": {
        "latest_it_jobs": "சமீபத்திய IT வேலைவாய்ப்புகள்",
        "internships": "பயிற்சி",
        "stipend_internships": "ஸ்டைபெண்ட் பயிற்சி",
        "work_from_home": "வீட்டிலிருந்து வேலை",
        "latest_tech_news": "சமீபத்திய தொழில்நுட்ப செய்திகள்",
        "non_it_jobs": "அல்லாத IT வேலைகள்",
        "latest_technologies": "சமீபத்திய தொழில்நுட்பங்கள்",
        "remote_jobs": "தொலைதூர வேலைகள்",
        "government_jobs": "அரசு வேலைவாய்ப்புகள்"
    },
    "te": {
        "latest_it_jobs": "తాజా ఐటీ ఉద్యోగాలు",
        "internships": "ఇంటర్న్షిప్స్",
        "stipend_internships": "స్టిపెండ్ ఇంటర్న్షిప్స్",
        "work_from_home": "హోమ్ నుండి ఉద్యోగాలు",
        "latest_tech_news": "తాజా టెక్ న్యూస్",
        "non_it_jobs": "నాన్ ఐటీ ఉద్యోగాలు",
        "latest_technologies": "తాజా టెక్నాలజీస్",
        "remote_jobs": "రిమోట్ ఉద్యోగాలు",
        "government_jobs": "ప్రభుత్వ ఉద్యోగాలు"
    }
}

# Date filter options
DATE_FILTERS = {
    "Last 24 hours": 1,
    "Last week": 7,
    "Last month": 30,
    "All time": None
}

def calculate_published_after(days):
    if days is None:
        return None
    now = datetime.now(pytz.utc)
    return now - timedelta(days=days)

@st.cache_data(ttl=3600)
def fetch_youtube_videos(query, language_code, published_after=None, max_results=MAX_RESULTS_PER_PAGE, page_token=None):
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "maxResults": max_results,
        "key": API_KEY,
        "type": "video",
        "order": "date",
        "relevanceLanguage": language_code  # Ensure results are in the selected language
    }
    
    if published_after:
        params["publishedAfter"] = published_after.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    if page_token:
        params["pageToken"] = page_token
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching videos: {str(e)}")
        return None

@st.cache_data(ttl=3600)
def fetch_related_videos(video_id, language_code, max_results=5):
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "relatedToVideoId": video_id,
        "maxResults": max_results,
        "key": API_KEY,
        "type": "video",
        "relevanceLanguage": language_code  # Ensure related videos are in the selected language
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json().get("items", [])
    except Exception as e:
        st.error(f"Error fetching related videos: {str(e)}")
        return []

# Streamlit app layout
def main():
    st.title("🌐 Global Video Explorer")

    # Initialize session state for pagination
    if "page_token" not in st.session_state:
        st.session_state["page_token"] = None
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = 1

    # Default language and topic
    DEFAULT_LANG = "en"  # English (default language)
    DEFAULT_TOPIC = "latest_it_jobs"

    # Language selection
    selected_lang = st.selectbox(
        "Select Language:",
        options=list(LANGUAGE_OPTIONS.keys()),
        index=list(LANGUAGE_OPTIONS.keys()).index(DEFAULT_LANG),  # Default to English
        format_func=lambda x: f"{LANGUAGE_OPTIONS[x]['flag']} {LANGUAGE_OPTIONS[x]['name']}"
    )

    # Date filter
    date_filter = st.selectbox(
        "Show videos from:",
        options=list(DATE_FILTERS.keys())
    )

    # Calculate publish time threshold
    days = DATE_FILTERS[date_filter]
    published_after = calculate_published_after(days)

    # Get topics for selected language
    lang_topics = TOPICS.get(selected_lang, TOPICS["en"])

    # Add a search bar for custom topics
    st.write("### Select or Search for a Topic")
    topic_options = list(lang_topics.values()) + ["Custom Search"]
    selected_topic = st.selectbox(
        "Select Topic:",
        options=topic_options,
        index=0,  # Default to the first topic
        format_func=lambda x: x.title()
    )

    # If "Custom Search" is selected, show a search bar
    if selected_topic == "Custom Search":
        custom_query = st.text_input("Enter your search query:")
        query = custom_query if custom_query else None
    else:
        query = selected_topic

    # Display results
    if query:
        st.write(f"## Results for: {query}")
        
        # Fetch videos for the current page
        response = fetch_youtube_videos(
            query,
            selected_lang,  # Pass the selected language to ensure results are in that language
            published_after,
            page_token=st.session_state["page_token"]
        )
        
        if response and "items" in response:
            videos = response["items"]
            st.session_state["next_page_token"] = response.get("nextPageToken")
            
            if videos:
                cols = st.columns(2)
                for idx, video in enumerate(videos):
                    with cols[idx % 2]:
                        video_id = video["id"]["videoId"]
                        title = video["snippet"]["title"]
                        thumbnail = video["snippet"]["thumbnails"]["high"]["url"]
                        published_at = datetime.fromisoformat(video["snippet"]["publishedAt"].replace("Z", "+00:00"))
                        
                        st.image(thumbnail, use_column_width=True)
                        st.markdown(f"**{title}**")
                        st.caption(f"Published: {published_at.strftime('%Y-%m-%d %H:%M')}")
                        if st.button(f"Watch Video {idx + 1}"):
                            st.session_state["selected_video"] = video_id
                            st.session_state["selected_lang"] = selected_lang
                            st.rerun()
                        st.write("---")
                
                # Pagination controls
                col1, col2 = st.columns(2)
                with col1:
                    if st.session_state["current_page"] > 1:
                        if st.button("⬅️ Previous Page"):
                            st.session_state["current_page"] -= 1
                            st.session_state["page_token"] = st.session_state.get("prev_page_token")
                            st.rerun()
                with col2:
                    if st.session_state["next_page_token"]:
                        if st.button("Next Page ➡️"):
                            st.session_state["current_page"] += 1
                            st.session_state["prev_page_token"] = st.session_state["page_token"]
                            st.session_state["page_token"] = st.session_state["next_page_token"]
                            st.rerun()
                
                st.write(f"Page: {st.session_state['current_page']}")
            else:
                st.warning("No videos found for this topic and time filter.")
        else:
            st.warning("No videos found for this topic and time filter.")

# Video details page
def video_details():
    st.title("🎥 Video Details")
    
    # Add back button and YouTube link
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Main Page"):
            del st.session_state["selected_video"]
            st.rerun()
    with col2:
        if "selected_video" in st.session_state:
            video_id = st.session_state["selected_video"]
            st.markdown(f"[Watch on YouTube ↗](https://www.youtube.com/watch?v={video_id})")
    
    if "selected_video" in st.session_state:
        video_id = st.session_state["selected_video"]
        selected_lang = st.session_state["selected_lang"]
        
        # Embed the selected video
        st.video(f"https://www.youtube.com/watch?v={video_id}")
        
        # Show related videos
        st.write("### Related Videos")
        related_videos = fetch_related_videos(video_id, selected_lang)
        
        if related_videos:
            cols = st.columns(2)
            for idx, video in enumerate(related_videos):
                with cols[idx % 2]:
                    related_video_id = video["id"]["videoId"]
                    title = video["snippet"]["title"]
                    thumbnail = video["snippet"]["thumbnails"]["high"]["url"]
                    
                    st.image(thumbnail, use_column_width=True)
                    st.markdown(f"**{title}**")
                    if st.button(f"Watch Related Video {idx + 1}"):
                        st.session_state["selected_video"] = related_video_id
                        st.rerun()
                    st.write("---")
        else:
            st.warning("No related videos found.")
    else:
        st.warning("No video selected. Please go back to the main page.")

# Page navigation
if "selected_video" not in st.session_state:
    main()
else:
    video_details()
