# TubeScribe

TubeScribe is an intelligent YouTube content analyzer that transforms video transcripts into clear, concise summaries. Simply paste a YouTube URL, and TubeScribe will extract the video's transcript and generate an AI-powered summary, helping you quickly grasp the key points without watching the entire video.

## Features

- **Instant Transcript Extraction**: Get the full transcript of any YouTube video with captions
- **AI-Powered Summaries**: Generate concise summaries of video content
- **Video Metadata**: View video title, channel, upload date, and thumbnail
- **Download Options**: Save transcripts and summaries as TXT or PDF files
- **Clean Interface**: Simple and intuitive user experience

## Perfect For

- Researchers needing to quickly process video content
- Students studying from educational videos
- Content creators researching topics
- Anyone who wants to save time by getting the key points from videos

## Technical Details

- Built with Python and Flask
- Uses the Hugging Face API for AI-powered summarization
- Supports both local development and Replit deployment
- Responsive design for all devices

## Setup

### Local Development
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Create a `.env` file with your Hugging Face API token:
   ```
   HF_API_TOKEN=your_token_here
   ```
4. Run the application: `python app.py`

### Replit Deployment
1. Fork this repository to your Replit account
2. In Replit, go to the "Secrets" tab (🔒 icon)
3. Add a new secret:
   - Key: `HF_API_TOKEN`
   - Value: Your Hugging Face API token
4. Click "Run" to start the application

## Security Note
- Never commit your `.env` file to version control
- The `.env` file is already in `.gitignore` to prevent accidental commits
- For Replit, use the Secrets feature instead of `.env` files

## Live Demo

Visit [TubeScribe on Replit](https://tubescribe.YOUR_USERNAME.repl.co) to try it out!

## License

MIT License - feel free to use and modify for your own projects! 