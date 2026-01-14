import os
from flask import Flask, jsonify, request
from flask_cors import CORS
import yt_dlp
import logging

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
        
        ydl_opts = {
            'format': 'best[ext=mp4]/best',  # Prioritize MP4 for Android compatibility
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'geo_bypass': True,  # Bypass geo restrictions
            'nocheckcertificate': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f'https://www.youtube.com/watch?v={video_id}', download=False)
            
            # Get best available URL
            url = info.get('url')
            
            # If 'url' is not directly available, look in 'formats'
            if not url and 'formats' in info:
                # Find best MP4 format
                mp4_formats = [f for f in info['formats'] if f.get('ext') == 'mp4' and f.get('url')]
                if mp4_formats:
                    # Sort by quality (height)
                    mp4_formats.sort(key=lambda x: x.get('height', 0) or 0, reverse=True)
                    url = mp4_formats[0]['url']
                elif info['formats']:
                    # Fallback to any format with URL
                    for f in info['formats']:
                        if f.get('url'):
                            url = f['url']
                            break
            
            if not url:
                return jsonify({
                    'success': False,
                    'error': 'No playable stream found',
                    'video_id': video_id
                }), 404
            
            response_data = {
                'success': True,
                'video_id': video_id,
                'url': url,
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'thumbnail': info.get('thumbnail', ''),
                'uploader': info.get('uploader', 'Unknown')
            }
            
            logger.info(f"Successfully extracted stream for: {video_id}")
            return jsonify(response_data)
            
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
