from youtube_transcript_api import YouTubeTranscriptApi
import sys

video_id = "P26AE7NLx4Q"

print(f"🔍 Debugging video: {video_id}\n")

try:
    # Try to list all available transcripts
    print("Step 1: Listing all available transcripts...")
    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    
    print("✅ Transcript list retrieved!")
    print(f"   Available transcripts:\n")
    
    # Show all available languages
    for transcript in transcript_list:
        print(f"   - Language: {transcript.language}")
        print(f"     Code: {transcript.language_code}")
        print(f"     Auto-generated: {transcript.is_generated}")
        print(f"     Translatable: {transcript.is_translatable}")
        print()
    
    # Try to get any transcript
    print("\nStep 2: Attempting to fetch transcript...")
    transcript = transcript_list.find_transcript(['en', 'en-US', 'en-GB'])
    data = transcript.fetch()
    
    print(f"✅ SUCCESS! Found {len(data)} caption segments")
    print(f"\n📄 First 3 segments:")
    for i, segment in enumerate(data[:3]):
        print(f"   {i+1}. [{segment['start']:.1f}s] {segment['text']}")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    print(f"\n🔍 Error type: {type(e).__name__}")
    
    import traceback
    print("\n📋 Full traceback:")
    traceback.print_exc()
