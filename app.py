from flask import Flask, jsonify, request
from flask_cors import CORS
import yt_dlp
import logging
import os

app = Flask(__name__)
CORS(app)  # Allow requests from Android app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def home():
    return jsonify({
        'status': 'running',
        'message': 'YouTube Stream Proxy API',
        'version': '1.0.0',
        'endpoints': {
            '/get_stream/<video_id>': 'Get direct stream URL for a video',
            '/health': 'Health check endpoint'
        }
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200

@app.route('/get_stream/<video_id>')
def get_stream(video_id):
    try:
        logger.info(f"Fetching stream for video: {video_id}")
        
        # Try multiple format strategies
        format_options = [
            'best[ext=mp4]',  # Best MP4 format
            'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',  # Combined video+audio
            'best',  # Any best format
        ]
        
        last_error = None
        
        for fmt in format_options:
            try:
                ydl_opts = {
                    'format': fmt,
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': False,
                    'nocheckcertificate': True,
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(f'https://www.youtube.com/watch?v={video_id}', download=False)
                    
                    # Get the direct URL
                    url = info.get('url')
                    
                    # If no direct URL, try to get from formats
                    if not url and 'formats' in info:
                        # Find best format with URL
                        formats = [f for f in info['formats'] if f.get('url')]
                        if formats:
                            # Prefer formats with both video and audio
                            progressive = [f for f in formats if f.get('vcodec') != 'none' and f.get('acodec') != 'none']
                            if progressive:
                                url = progressive[-1]['url']
                            else:
                                url = formats[-1]['url']
                    
                    if url:
                        response_data = {
                            'success': True,
                            'video_id': video_id,
                            'url': url,
                            'title': info.get('title', 'Unknown'),
                            'duration': info.get('duration', 0),
                            'thumbnail': info.get('thumbnail', ''),
                            'uploader': info.get('uploader', 'Unknown'),
                            'view_count': info.get('view_count', 0)
                        }
                        
                        logger.info(f"Successfully extracted stream for: {video_id} using format: {fmt}")
                        return jsonify(response_data)
                
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Format '{fmt}' failed: {str(e)}")
                continue
        
        # If all formats failed
        raise Exception(f"All format options failed. Last error: {last_error}")
            
    except Exception as e:
        logger.error(f"Error extracting stream: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'video_id': video_id
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
