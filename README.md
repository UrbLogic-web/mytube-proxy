# MyTube Proxy Backend

A Flask-based YouTube stream extraction proxy using yt-dlp.

## Files

- `app.py` - Main Flask application
- `requirements.txt` - Python dependencies
- `render.yaml` - Render.com deployment config

## Deployment to Render.com

1. **Create a GitHub Repository**
   - Go to [github.com](https://github.com) → New Repository
   - Name: `mytube-proxy`
   - Make it **Public**
   - Upload all 3 files from this folder

2. **Deploy to Render**
   - Go to [render.com](https://render.com) → Sign up (use GitHub)
   - Click **"New +"** → **"Web Service"**
   - Choose **"Build and deploy from a Git repository"**
   - Connect your GitHub and select `mytube-proxy`
   - Configure:
     - **Name**: `mytube-proxy`
     - **Runtime**: Python 3
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn app:app`
   - Click **"Create Web Service"**
   - Wait 3-5 minutes for deployment

3. **Get Your URL**
   - After deployment, copy the URL (e.g., `https://mytube-proxy-xyz.onrender.com`)
   - This is your `PROXY_BASE_URL` for the Android app

## Testing

```bash
curl https://YOUR_RENDER_URL/health
curl https://YOUR_RENDER_URL/get_stream/dQw4w9WgXcQ
```

## Free Tier Limitations

- App sleeps after 15 minutes of inactivity
- First request after sleep takes ~30 seconds
- 750 hours/month (enough for personal use)
