from flask import Flask, render_template, request
import youtube_utils
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file only if it exists (local development)
if os.path.exists('.env'):
    load_dotenv()

app = Flask(__name__)

# Get API token from environment (works for both local and Replit)
api_token = os.getenv("HF_API_TOKEN")
if not api_token:
    print("Warning: HF_API_TOKEN not found in environment variables")
else:
    print(f"API Token found: {'Yes' if api_token else 'No'}")
    if api_token:
        print(f"Token starts with: {api_token[:10]}...")

def format_upload_date(date_str):
    """Format upload date from YYYYMMDD to Month DD, YYYY"""
    try:
        date_obj = datetime.strptime(date_str, "%Y%m%d")
        return date_obj.strftime("%B %d, %Y")
    except:
        return date_str

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']
        action = request.form.get('action', 'transcript')  # Default to transcript if no action specified
        
        try:
            # Extract URL from various formats
            if 'youtu.be' in url:
                video_id = url.split('/')[-1]
                url = f'https://www.youtube.com/watch?v={video_id}'
            elif 'youtube.com/shorts' in url:
                video_id = url.split('/')[-1]
                url = f'https://www.youtube.com/watch?v={video_id}'
            
            print(f"Processing URL: {url}")
            
            # Get video info
            video_info = youtube_utils.get_video_info(url)
            if not video_info:
                error_msg = "Could not extract video information. Please check if the video is available and try again."
                print(error_msg)
                return render_template('index.html', error=error_msg, url=url)
            
            # Format the upload date
            video_info['upload_date'] = format_upload_date(video_info['upload_date'])
            
            # Get and clean transcript
            print("Extracting transcript...")
            raw_transcript = youtube_utils.extract_transcript(url)
            if not raw_transcript:
                error_msg = "This video doesn't have captions available. Please try a different video that has English captions enabled."
                print(error_msg)
                return render_template('index.html', 
                                    error=error_msg, 
                                    url=url,
                                    title=video_info['title'],
                                    channel=video_info['channel'],
                                    upload_date=video_info['upload_date'],
                                    thumbnail_url=video_info['thumbnail_url'])
                
            cleaned_transcript = youtube_utils.clean_transcript(raw_transcript)
            if not cleaned_transcript:
                error_msg = "Could not process transcript. The video might not have captions available."
                print(error_msg)
                return render_template('index.html', 
                                    error=error_msg, 
                                    url=url,
                                    title=video_info['title'],
                                    channel=video_info['channel'],
                                    upload_date=video_info['upload_date'],
                                    thumbnail_url=video_info['thumbnail_url'])
            
            if action == 'transcript':
                # Only show transcript
                return render_template('index.html', 
                                    title=video_info['title'],
                                    channel=video_info['channel'],
                                    upload_date=video_info['upload_date'],
                                    thumbnail_url=video_info['thumbnail_url'],
                                    transcript=cleaned_transcript,
                                    show_transcript=True,
                                    show_summary=False,
                                    url=url)
            else:
                # Only show summary
                print("Generating summary...")
                short_summary = youtube_utils.get_short_summary(cleaned_transcript)
                
                return render_template('index.html', 
                                    title=video_info['title'],
                                    channel=video_info['channel'],
                                    upload_date=video_info['upload_date'],
                                    thumbnail_url=video_info['thumbnail_url'],
                                    short_summary=short_summary,
                                    show_transcript=False,
                                    show_summary=True,
                                    url=url)
                
        except Exception as e:
            error_msg = f"An error occurred: {str(e)}"
            print(error_msg)
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return render_template('index.html', error=error_msg, url=url)
    return render_template('index.html')

@app.route('/generate-medium-summary', methods=['POST'])
def generate_medium_summary():
    url = request.form['url']
    try:
        raw_transcript = youtube_utils.extract_transcript(url)
        cleaned_transcript = youtube_utils.clean_transcript(raw_transcript) if raw_transcript else None
        medium_summary = None
        if cleaned_transcript:
            medium_summary = youtube_utils.get_medium_summary(cleaned_transcript)
        return {'medium_summary': medium_summary}
    except Exception as e:
        return {'error': str(e)}

if __name__ == '__main__':
    # Check if we're running on Replit
    is_replit = os.environ.get('REPL_ID') is not None
    
    if is_replit:
        # Replit configuration
        app.run(host='0.0.0.0', port=8080)
    else:
        # Local development configuration
        app.run(debug=True, host='0.0.0.0', port=5001) 