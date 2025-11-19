"""
YouTube Caption Fetcher - Using Direct TimedText API
More reliable than youtube-transcript-api library
Uses YouTube's official subtitle endpoint
"""

import requests
import re
import xml.etree.ElementTree as ET
from urllib.parse import parse_qs, urlparse
import html

def extract_video_id(url):
    """Extract video ID from YouTube URL"""
    patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([^&]+)',
        r'(?:https?://)?(?:www\.)?youtu\.be/([^?]+)',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/([^?]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_caption_tracks(video_id):
    """
    Get list of available caption tracks from YouTube video page
    
    Returns list of caption track info including URLs
    """
    
    print(f"   Fetching video page to find caption tracks...")
    
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    
    try:
        # Get video page
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        response = requests.get(video_url, headers=headers)
        html_content = response.text
        
        # Find caption tracks in page
        # Look for "captionTracks" in the page source
        caption_pattern = r'"captionTracks":\s*(\[.*?\])'
        match = re.search(caption_pattern, html_content)
        
        if not match:
            return None
        
        import json
        caption_tracks = json.loads(match.group(1))
        
        print(f"   ✅ Found {len(caption_tracks)} caption tracks")
        
        return caption_tracks
    
    except Exception as e:
        print(f"   ⚠️ Could not find caption tracks: {e}")
        return None

def fetch_captions_from_timedtext_url(url):
    """
    Fetch and parse captions from YouTube's timedtext API URL
    
    Args:
        url: Direct timedtext API URL
    
    Returns:
        dict: Parsed caption data
    """
    
    print(f"   Fetching captions from timedtext API...")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        # Parse XML
        root = ET.fromstring(response.content)
        
        segments = []
        full_text = []
        
        for text_element in root.findall('.//text'):
            start = float(text_element.get('start', 0))
            duration = float(text_element.get('dur', 0))
            text = html.unescape(text_element.text or '')
            
            # Clean text
            text = text.strip()
            text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
            
            if text:
                full_text.append(text)
                segments.append({
                    'start': start,
                    'end': start + duration,
                    'text': text
                })
        
        combined_text = ' '.join(full_text)
        total_duration = segments[-1]['end'] if segments else 0
        
        print(f"   ✅ Parsed {len(segments)} caption segments")
        
        return {
            'text': combined_text,
            'segments': segments,
            'duration': total_duration
        }
    
    except Exception as e:
        print(f"   ❌ Error fetching captions: {e}")
        return None

def get_youtube_captions_direct(url, languages=['en', 'en-US', 'en-GB']):
    """
    Fetch captions using direct timedtext API (most reliable method)
    
    Args:
        url: YouTube video URL
        languages: Preferred languages
    
    Returns:
        dict: Caption data or error
    """
    
    # Extract video ID
    video_id = extract_video_id(url)
    if not video_id:
        return {
            'success': False,
            'error': 'invalid_url',
            'message': '❌ Invalid YouTube URL'
        }
    
    print(f"🎬 Fetching captions for video: {video_id}")
    print(f"   Using direct timedtext API method...")
    
    # Get caption tracks
    caption_tracks = get_caption_tracks(video_id)
    
    if not caption_tracks:
        return {
            'success': False,
            'error': 'no_captions',
            'message': '❌ No captions available for this video.\n\n💡 Upload audio file manually (Tab 1)'
        }
    
    # Find best caption track
    selected_track = None
    
    # Try to find manual captions first
    for track in caption_tracks:
        lang = track.get('languageCode', '')
        if lang in languages:
            if track.get('kind') != 'asr':  # Not auto-generated
                selected_track = track
                print(f"   ✅ Found manual captions in {lang}")
                break
    
    # Fallback to auto-generated
    if not selected_track:
        for track in caption_tracks:
            lang = track.get('languageCode', '')
            if lang in languages:
                selected_track = track
                print(f"   ✅ Found auto-generated captions in {lang}")
                break
    
    if not selected_track:
        return {
            'success': False,
            'error': 'no_english_captions',
            'message': '❌ No English captions available'
        }
    
    # Get caption URL
    caption_url = selected_track.get('baseUrl')
    
    if not caption_url:
        return {
            'success': False,
            'error': 'no_caption_url',
            'message': '❌ Could not get caption URL'
        }
    
    # Fetch and parse captions
    caption_data = fetch_captions_from_timedtext_url(caption_url)
    
    if not caption_data:
        return {
            'success': False,
            'error': 'fetch_failed',
            'message': '❌ Failed to fetch captions'
        }
    
    print(f"✅ Caption fetch successful!")
    print(f"   Duration: {caption_data['duration']/60:.1f} minutes")
    print(f"   Words: ~{len(caption_data['text'].split())}")
    
    return {
        'success': True,
        'text': caption_data['text'],
        'segments': caption_data['segments'],
        'duration': caption_data['duration'],
        'language': selected_track.get('languageCode', 'en'),
        'auto_generated': selected_track.get('kind') == 'asr',
        'video_id': video_id,
        'method': 'timedtext_api'
    }

if __name__ == "__main__":
    print("🧪 Testing YouTube TimedText API Fetcher...\n")
    
    test_url = input("Enter YouTube URL to test: ").strip()
    if not test_url:
        test_url = "https://www.youtube.com/watch?v=c3Hq6UaFQqk"
    
    result = get_youtube_captions_direct(test_url)
    
    if result['success']:
        print(f"\n✅ TEST SUCCESSFUL!")
        print(f"   Video ID: {result['video_id']}")
        print(f"   Duration: {result['duration']/60:.1f} minutes")
        print(f"   Language: {result['language']}")
        print(f"   Type: {'Auto-generated' if result['auto_generated'] else 'Manual'}")
        print(f"   Method: {result['method']}")
        print(f"   Total words: ~{len(result['text'].split())}")
        print(f"\n📄 First 300 characters:")
        print(f"   {result['text'][:300]}...")
    else:
        print(f"\n❌ TEST FAILED!")
        print(f"   {result['message']}")
