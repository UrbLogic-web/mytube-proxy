import os
from flask import Flask, jsonify, request
from flask_cors import CORS
import yt_dlp
import logging
import traceback

app = Flask(__name__)
CORS(app)  # Allow requests from Android app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def home():
    return jsonify({
        'status': 'running',
        'message': 'MyTube YouTube Stream Proxy API',
        'version': '1.2.0',
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
        
        # SIMPLE format - let yt-dlp pick the best available
        ydl_opts = {
            'format': 'best',  # Just get the best available - most compatible
            'quiet': True,
            'no_warnings': True,
            'geo_bypass': True,
            'nocheckcertificate': True,
        }
        
        url = f'https://www.youtube.com/watch?v={video_id}'
        logger.info(f"Extracting from URL: {url}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if info is None:
                return jsonify({
                    'success': False,
                    'error': 'Video not found or unavailable',
                    'video_id': video_id
                }), 404
            
            # Get the URL - yt-dlp should have selected the best format
            stream_url = info.get('url')
            
            # If no direct URL, search in formats
            if not stream_url and 'formats' in info:
                formats = info.get('formats', [])
                logger.info(f"Searching {len(formats)} formats for playable URL")
                
                # Try to find any format with a direct URL
                for f in reversed(formats):  # Reversed = prefer higher quality
                    fmt_url = f.get('url')
                    if fmt_url and 'manifest' not in fmt_url.lower():
                        stream_url = fmt_url
                        logger.info(f"Found format: {f.get('format_id')} - {f.get('ext')}")
                        break
            
            if not stream_url:
                return jsonify({
                    'success': False,
                    'error': 'Could not extract playable URL',
                    'video_id': video_id
                }), 404
            
            response_data = {
                'success': True,
                'video_id': video_id,
                'url': stream_url,
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'thumbnail': info.get('thumbnail', ''),
                'uploader': info.get('uploader', 'Unknown')
            }
            
            logger.info(f"Success: {video_id}")
            return jsonify(response_data)
            
    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        logger.error(f"yt-dlp error: {error_msg}")
        return jsonify({
            'success': False,
            'error': f'yt-dlp error: {error_msg}',
            'video_id': video_id
        }), 500
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'video_id': video_id
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
