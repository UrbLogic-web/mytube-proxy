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
        'version': '1.1.0',
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
        
        # More robust options for server environments
        ydl_opts = {
            'format': 'best[ext=mp4][height<=720]/best[ext=mp4]/best',  # Prefer 720p MP4
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'geo_bypass': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'no_color': True,
            # Skip download, just extract info
            'skip_download': True,
            # Use cookies from browser if available (not on server, but won't hurt)
            'cookiesfrombrowser': None,
        }
        
        url = f'https://www.youtube.com/watch?v={video_id}'
        logger.info(f"Extracting from URL: {url}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if info is None:
                logger.error("yt-dlp returned None for info")
                return jsonify({
                    'success': False,
                    'error': 'Video not found or unavailable',
                    'video_id': video_id
                }), 404
            
            # Try to get direct URL
            stream_url = info.get('url')
            
            # If no direct URL, look in formats
            if not stream_url and 'formats' in info:
                formats = info.get('formats', [])
                logger.info(f"Found {len(formats)} formats")
                
                # Find best MP4 format with direct URL
                mp4_formats = [
                    f for f in formats 
                    if f.get('ext') == 'mp4' 
                    and f.get('url') 
                    and not f.get('url', '').startswith('https://manifest')  # Skip DASH manifests
                ]
                
                if mp4_formats:
                    # Sort by quality (prefer 720p or lower for mobile)
                    mp4_formats.sort(key=lambda x: abs((x.get('height') or 0) - 720))
                    stream_url = mp4_formats[0]['url']
                    logger.info(f"Selected MP4 format: {mp4_formats[0].get('format_id')}")
                else:
                    # Fallback: any format with URL
                    for f in formats:
                        if f.get('url') and not f.get('url', '').startswith('https://manifest'):
                            stream_url = f['url']
                            logger.info(f"Fallback format: {f.get('format_id')}")
                            break
            
            if not stream_url:
                logger.error("No playable stream URL found in any format")
                return jsonify({
                    'success': False,
                    'error': 'No playable stream found for this video',
                    'video_id': video_id,
                    'formats_available': len(info.get('formats', []))
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
            
            logger.info(f"Successfully extracted stream for: {video_id}")
            return jsonify(response_data)
            
    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        logger.error(f"yt-dlp DownloadError: {error_msg}")
        
        # Check for common issues
        if 'Video unavailable' in error_msg:
            return jsonify({
                'success': False,
                'error': 'This video is unavailable or private',
                'video_id': video_id
            }), 404
        elif 'Sign in' in error_msg or 'age' in error_msg.lower():
            return jsonify({
                'success': False,
                'error': 'This video requires sign-in or age verification',
                'video_id': video_id
            }), 403
        else:
            return jsonify({
                'success': False,
                'error': f'yt-dlp error: {error_msg}',
                'video_id': video_id
            }), 500
            
    except Exception as e:
        error_msg = str(e)
        stack_trace = traceback.format_exc()
        logger.error(f"Unexpected error: {error_msg}\n{stack_trace}")
        return jsonify({
            'success': False,
            'error': f'Server error: {error_msg}',
            'video_id': video_id,
            'trace': stack_trace if app.debug else None
        }), 500
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
