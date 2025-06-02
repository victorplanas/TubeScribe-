import yt_dlp
import re
import pandas as pd
from datetime import datetime
import requests
import os
from dotenv import load_dotenv
import time
from pytube import YouTube

# Load environment variables from .env file
load_dotenv()

# Hugging Face API configuration
API_URL = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"
API_TOKEN = os.getenv("HF_API_TOKEN")  # Get token from .env file

if not API_TOKEN:
    raise ValueError("Please create a .env file with your Hugging Face API token: HF_API_TOKEN=your_token_here")

def summarize_text(text, max_new_tokens=300):
    """Summarize text using Hugging Face Inference API with Zephyr model"""
    if not text or len(text) < 100:  # Don't summarize very short texts
        print("Text too short to summarize")
        return text
        
    try:
        print(f"Starting summarization. Text length: {len(text)}")
        print(f"Using max_new_tokens: {max_new_tokens}")
        
        # Prepare the prompt with structured format
        prompt = f"""<|system|>
You are a helpful AI assistant that summarizes youtube videos. Focus on extracting key information and insights.
Format your response exactly as requested, without adding any additional sections or points.
</|system|>
<|user|>
Please summarize the following video transcript in exactly this format:

1. Summary: [Write 1-2 paragraphs summarizing the main topic and key points]


2. Additional Details: [Write 2-3 sentences with any other important information]

Do not include any other sections or bullet points. Keep the format simple and clean.

Here's the transcript:
{text}
</|user|>
<|assistant|>"""

        # Make API request with retries for model loading
        max_retries = 3
        retry_delay = 5  # seconds
        headers = {"Authorization": f"Bearer {API_TOKEN}"}
        
        for attempt in range(max_retries):
            try:
                print(f"Attempt {attempt + 1}/{max_retries}")
                response = requests.post(API_URL, headers=headers, json={
                    "inputs": prompt,
                    "parameters": {
                        "max_new_tokens": max_new_tokens,
                        "temperature": 0.7,
                        "top_p": 0.95,
                        "do_sample": True,
                        "return_full_text": False
                    }
                }, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    if isinstance(result, list) and len(result) > 0:
                        summary = result[0]["generated_text"]
                        # Clean up the summary
                        summary = re.sub(r'\s+', ' ', summary).strip()
                        print(f"Summary generated successfully. Length: {len(summary)}")
                        return summary
                    else:
                        print(f"Unexpected response format: {result}")
                        return text
                elif response.status_code == 503 and attempt < max_retries - 1:
                    print(f"Model is loading, attempt {attempt + 1}/{max_retries}. Waiting {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    print(f"Error in API request: {response.status_code}")
                    print(f"Response: {response.text}")
                    return text
                    
            except requests.Timeout:
                if attempt < max_retries - 1:
                    print(f"Request timed out, attempt {attempt + 1}/{max_retries}. Retrying...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    print("All retry attempts failed")
                    return text
                    
    except Exception as e:
        print(f"Error in summarization: {str(e)}")
        return text  # Return original text if summarization fails

def get_short_summary(text):
    """Get a short summary (around 100-150 words)"""
    print("Generating short summary")
    return summarize_text(text, max_new_tokens=200)

def get_medium_summary(text):
    """Get a medium summary (around 200-300 words)"""
    print("Generating medium summary")
    return summarize_text(text, max_new_tokens=400)

def parse_ts(ts):
    """Convert HH:MM:SS.mmm string to total seconds"""
    try:
        dt = datetime.strptime(ts, "%H:%M:%S.%f")
        return dt.hour * 3600 + dt.minute * 60 + dt.second + dt.microsecond / 1e6
    except ValueError:
        return 0

def get_video_info(url):
    """Get video information using yt-dlp."""
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
    }
    
    try:
        print(f"Attempting to get video info from: {url}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print("Loading video metadata...")
            info = ydl.extract_info(url, download=False)
            
            # Extract video information
            video_info = {
                'title': info.get('title', 'N/A'),
                'channel': info.get('channel', 'N/A'),
                'upload_date': info.get('upload_date', 'N/A'),
                'thumbnail_url': info.get('thumbnail', 'N/A')
            }
            
            print(f"Successfully loaded video info:")
            print(f"Title: {video_info['title']}")
            print(f"Channel: {video_info['channel']}")
            print(f"Upload Date: {video_info['upload_date']}")
            print(f"Thumbnail URL: {video_info['thumbnail_url']}")
            
            return video_info
            
    except Exception as e:
        print(f"Error getting video info: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return None

def extract_transcript(url):
    """Extract raw transcript text from a YouTube video URL"""
    ydl_opts = {
        'quiet': False,  # Enable output for debugging
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['en', 'en-US', 'en-GB'],  # Try multiple English variants
        'skip_download': True,
        'outtmpl': 'temp_subtitle',
        'verbose': True  # Add verbose output
    }
    
    try:
        print(f"Attempting to extract transcript from: {url}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print("Downloading subtitles...")
            info = ydl.extract_info(url, download=False)
            
            # Check if video has captions
            if not info.get('subtitles') and not info.get('automatic_captions'):
                print("No captions available for this video")
                return None
                
            ydl.download([url])
            
            # Check for both manual and auto-generated subtitles
            subtitle_files = [
                'temp_subtitle.en.vtt',
                'temp_subtitle.en-US.vtt',
                'temp_subtitle.en-GB.vtt',
                'temp_subtitle.en-orig.vtt'
            ]
            content = None
            
            for subtitle_file in subtitle_files:
                try:
                    print(f"Trying to read subtitle file: {subtitle_file}")
                    if os.path.exists(subtitle_file):
                        with open(subtitle_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            print(f"Successfully read {subtitle_file}")
                            break
                except Exception as e:
                    print(f"Error reading {subtitle_file}: {str(e)}")
                    continue
            
            if not content:
                print("No subtitle files found")
                return None
                
            return content
                    
    except Exception as e:
        print(f"Error extracting transcript: {str(e)}")
        if "Did not get any data blocks" in str(e):
            print("This video might not have captions available")
        return None
    finally:
        # Clean up any subtitle files
        for subtitle_file in subtitle_files:
            if os.path.exists(subtitle_file):
                try:
                    os.remove(subtitle_file)
                    print(f"Cleaned up {subtitle_file}")
                except Exception as e:
                    print(f"Error cleaning up {subtitle_file}: {str(e)}")

def clean_transcript(text):
    """Clean the raw transcript text"""
    if not text:
        return None
        
    seen_lines = set()
    cleaned_lines = []
    
    for line in text.split('\n'):
        if line.strip() == 'WEBVTT':
            continue
        if 'Kind:' in line or 'Language:' in line or 'align:' in line:
            continue
            
        # Remove timestamps and formatting
        text = re.sub(r'\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}', '', line)
        text = re.sub(r'\d{2}:\d{2}:\d{2}', '', text)
        text = re.sub(r'\[.*?\]', '', text)
        text = re.sub(r'</?[a-z]>', '', text)
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'[*_~`#]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        if text and text not in seen_lines:
            seen_lines.add(text)
            cleaned_lines.append(text)
    
    return ' '.join(cleaned_lines)

def format_duration(seconds):
    """Convert duration in seconds to HH:MM:SS format"""
    if not seconds:
        return 'N/A'
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def analyze_video(url):
    """Analyze a YouTube video and return a DataFrame with all information"""
    print(f"Analyzing video: {url}")
    # Get video information
    video_info = get_video_info(url)
    if not video_info:
        print("Failed to get video info")
        return None
        
    # Get and clean transcript
    raw_transcript = extract_transcript(url)
    print(f"Raw transcript length: {len(raw_transcript) if raw_transcript else 0}")
    
    cleaned_transcript = clean_transcript(raw_transcript) if raw_transcript else None
    print(f"Cleaned transcript length: {len(cleaned_transcript) if cleaned_transcript else 0}")
    
    # Add transcript to video info
    video_info['transcript'] = cleaned_transcript
    
    # Generate summaries if transcript exists
    if cleaned_transcript:
        print("Generating summaries")
        video_info['short_summary'] = get_short_summary(cleaned_transcript)
        video_info['medium_summary'] = get_medium_summary(cleaned_transcript)
    else:
        print("No transcript available for summarization")
        video_info['short_summary'] = None
        video_info['medium_summary'] = None
    
    # Format duration
    video_info['duration_formatted'] = format_duration(video_info['duration'])
    
    # Create DataFrame with ordered columns
    df = pd.DataFrame([video_info])
    columns = [
        'title',
        'channel',
        'duration_formatted',
        'duration',
        'view_count',
        'likes',
        'comment_count',
        'upload_date',
        'url',
        'transcript',
        'short_summary',
        'medium_summary'
    ]
    return df[columns] 