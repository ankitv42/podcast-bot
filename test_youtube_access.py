import requests

video_id = "c3Hq6UaFQqk"
url = f"https://www.youtube.com/watch?v={video_id}"

print(f"Testing access to: {url}")

try:
    response = requests.get(url, timeout=10)
    print(f"✅ Status: {response.status_code}")
    
    if "captionTracks" in response.text:
        print("✅ Captions found in page HTML!")
    else:
        print("❌ No captions found in page")
        
except Exception as e:
    print(f"❌ Network error: {e}")
