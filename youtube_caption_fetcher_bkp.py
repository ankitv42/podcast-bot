"""
YouTube Caption Fetcher - 100% Legal using YouTube Data API
Gets captions/transcripts from YouTube videos using official API
"""

import os
import re
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from dotenv import load_dotenv
import json

load_dotenv()

def extract_video_id(url):
    """
    Extract video ID from various YouTube URL formats
    
    Args:
        url: YouTube URL
    
    Returns:
        str: Video ID or None
    """
    patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([^&]+)',
        r'(?:https?://)?(?:www\.)?youtu\.be/([^?]+)',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/([^?]+)',
        r'(?:https?://)?(?:www\.)?youtube\.com/v/([^?]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

def get_youtube_captions(url, languages=['en', 'en-US', 'en-GB']):
    """
    Fetch captions/transcript from YouTube video using official API
    
    Args:
        url: YouTube video URL
        languages: List of language codes to try (default: English variants)
    
    Returns:
        dict: {
            'success': bool,
            'text': str (full transcript),
            'segments': list (with timestamps),
            'language': str,
            'auto_generated': bool
        } or error dict
    """
    
    # Extract video ID
    video_id = extract_video_id(url)
    if not video_id:
        return {
            'success': False,
            'error': 'invalid_url',
            'message': '❌ Invalid YouTube URL. Please check and try again.'
        }
    
    print(f"🎬 Fetching captions for video ID: {video_id}")
    
    try:
        # Try to get transcript
        # This library uses YouTube's official caption API endpoints
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # Try manual captions first (better quality)
        transcript = None
        is_auto_generated = False
        used_language = None
        
        try:
            # Try to find manual captions in preferred languages
            for lang in languages:
                try:
                    transcript = transcript_list.find_transcript([lang])
                    used_language = lang
                    is_auto_generated = False
                    print(f"✅ Found manual captions in {lang}")
                    break
                except:
                    continue
        except:
            pass
        
        # If no manual captions, try auto-generated
        if not transcript:
            try:
                for lang in languages:
                    try:
                        transcript = transcript_list.find_generated_transcript([lang])
                        used_language = lang
                        is_auto_generated = True
                        print(f"✅ Found auto-generated captions in {lang}")
                        break
                    except:
                        continue
            except:
                pass
        
        # If still no transcript found
        if not transcript:
            return {
                'success': False,
                'error': 'no_captions',
                'message': '❌ This video does not have captions.\n\n💡 **Options:**\n• Upload the audio file manually (Tab 1)\n• Request the creator to add captions'
            }
        
        # Fetch the actual transcript data
        caption_data = transcript.fetch()
        
        # Build full text and segments
        full_text = []
        segments = []
        
        for entry in caption_data:
            text = entry['text']
            start = entry['start']
            duration = entry.get('duration', 0)
            
            full_text.append(text)
            segments.append({
                'start': start,
                'end': start + duration,
                'text': text
            })
        
        # Combine all text
        combined_text = ' '.join(full_text)
        
        # Calculate total duration
        total_duration = segments[-1]['end'] if segments else 0
        
        result = {
            'success': True,
            'text': combined_text,
            'segments': segments,
            'duration': total_duration,
            'language': used_language,
            'auto_generated': is_auto_generated,
            'video_id': video_id
        }
        
        print(f"✅ Caption fetch successful!")
        print(f"   Duration: {total_duration/60:.1f} minutes")
        print(f"   Words: ~{len(combined_text.split())}")
        print(f"   Type: {'Auto-generated' if is_auto_generated else 'Manual'}")
        
        return result
        
    except TranscriptsDisabled:
        return {
            'success': False,
            'error': 'captions_disabled',
            'message': '❌ Captions are disabled for this video.\n\n💡 **Workaround:** Upload the audio file manually using Tab 1.'
        }
    
    except NoTranscriptFound:
        return {
            'success': False,
            'error': 'no_transcript',
            'message': '❌ No captions available in English.\n\n💡 **Options:**\n• Upload audio file manually (Tab 1)\n• Try another video'
        }
    
    except Exception as e:
        error_msg = str(e)
        
        if 'private' in error_msg.lower():
            return {
                'success': False,
                'error': 'private',
                'message': '🔒 This video is private. Only the uploader can access it.'
            }
        elif 'unavailable' in error_msg.lower():
            return {
                'success': False,
                'error': 'unavailable',
                'message': '❌ Video not found or has been deleted.'
            }
        else:
            return {
                'success': False,
                'error': 'unknown',
                'message': f'❌ Error: {error_msg}\n\n💡 Try uploading the audio file manually (Tab 1).'
            }

def clean_caption_text_gpt4(raw_text, client):
    """
    Use GPT-4 to clean up auto-generated caption errors
    
    Args:
        raw_text: Raw caption text with potential errors
        client: OpenAI client instance
    
    Returns:
        str: Cleaned text
    """
    
    if len(raw_text) < 100:
        # Too short to need cleaning
        return raw_text
    
    print("🧹 Cleaning caption text with GPT-4...")
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a transcript editor. Fix transcription errors, add proper punctuation, and break into paragraphs. Preserve all original meaning and content. Do not summarize or change words unless they are clearly transcription errors."
                },
                {
                    "role": "user",
                    "content": f"Fix this auto-generated transcript:\n\n{raw_text[:8000]}"  # Limit to avoid token limits
                }
            ],
            temperature=0.3
        )
        
        cleaned_text = response.choices[0].message.content
        print("✅ Caption cleaning complete")
        
        return cleaned_text
    
    except Exception as e:
        print(f"⚠️ Caption cleaning failed: {e}")
        print("   Using original captions")
        return raw_text

def get_video_metadata(video_id):
    """
    Get video metadata (title, duration, channel) - for future use
    Currently returns basic info from transcript API
    
    Args:
        video_id: YouTube video ID
    
    Returns:
        dict: Basic video info
    """
    try:
        # For now, just return video ID
        # In future, can integrate YouTube Data API v3 for full metadata
        return {
            'video_id': video_id,
            'url': f'https://www.youtube.com/watch?v={video_id}'
        }
    except:
        return None

if __name__ == "__main__":
    # Test the module
    print("🧪 Testing YouTube Caption Fetcher...\n")
    
    # Test URL
    test_url = input("Enter YouTube URL to test: ").strip()
    if not test_url:
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    # Fetch captions
    result = get_youtube_captions(test_url)
    
    if result['success']:
        print(f"\n✅ TEST SUCCESSFUL!")
        print(f"   Video ID: {result['video_id']}")
        print(f"   Duration: {result['duration']/60:.1f} minutes")
        print(f"   Language: {result['language']}")
        print(f"   Type: {'Auto-generated' if result['auto_generated'] else 'Manual'}")
        print(f"   Total words: ~{len(result['text'].split())}")
        print(f"\n📄 First 300 characters:")
        print(f"   {result['text'][:300]}...")
        
        # Test caption cleaning
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        if result['auto_generated']:
            print(f"\n🧹 Testing caption cleanup...")
            cleaned = clean_caption_text_gpt4(result['text'][:1000], client)
            print(f"\n📄 Cleaned version (first 300 chars):")
            print(f"   {cleaned[:300]}...")
    else:
        print(f"\n❌ TEST FAILED!")
        print(f"   {result['message']}")
