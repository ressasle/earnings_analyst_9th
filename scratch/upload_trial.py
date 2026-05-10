import os
import sys
from utils.supabase_client import get_supabase_client

def upload_file(local_path, bucket, remote_name):
    supabase = get_supabase_client()
    
    # Determine content type based on extension
    ext = os.path.splitext(local_path)[1].lower()
    content_type = "application/pdf" if ext == ".pdf" else "text/html" if ext == ".html" else "audio/mpeg" if ext == ".mp3" else "application/octet-stream"
    
    # Check if file exists first and remove it
    try:
        supabase.storage.from_(bucket).remove([remote_name])
    except:
        pass
    
    with open(local_path, "rb") as f:
        supabase.storage.from_(bucket).upload(
            path=remote_name,
            file=f,
            file_options={"content-type": content_type}
        )
        
    return supabase.storage.from_(bucket).get_public_url(remote_name)

def main():
    base_dir = r"c:\Users\Administrator\Documents\kasonaops\invest_analysis\08_quarterly-earnings-analyst\output"
    
    files = [
        (os.path.join(base_dir, "VETTER.US_presentation.pdf"), "company-presentations", "VETTER.US_presentation.pdf"),
        (os.path.join(base_dir, "vetter_us_presentation.html"), "earnings-reports-html", "VETTER.US_presentation.html"),
        (os.path.join(base_dir, "vetter_us_briefing.mp3"), "earnings-reports-audio", "VETTER.US_presentation.mp3")
    ]
    
    links = {}
    for local, bucket, remote in files:
        if os.path.exists(local):
            print(f"Uploading {local} to {bucket}/{remote}...")
            try:
                url = upload_file(local, bucket, remote)
                links[remote] = url
                print(f"Done: {url}")
            except Exception as e:
                print(f"Error uploading {local}: {e}")
        else:
            print(f"File not found: {local}")
            
    print("\n--- SUMMARY ---")
    for name, link in links.items():
        print(f"{name}: {link}")

if __name__ == "__main__":
    main()
