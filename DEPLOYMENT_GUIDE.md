# Deployment Guide for JARVIS Flask Application

This guide provides multiple deployment options for your Flask application with Gemini AI integration.

## Prerequisites

1. **Gemini API Key**: Your application uses Google's Gemini AI. Make sure you have a valid API key.
2. **Git Repository**: Your code should be in a Git repository (GitHub, GitLab, etc.)

## Option 1: Deploy to Railway (Recommended for Beginners)

Railway is a modern platform that makes deployment simple and offers a free tier.

### Steps:

1. **Sign up for Railway**:
   - Go to [railway.app](https://railway.app)
   - Sign up with your GitHub account

2. **Deploy your application**:
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository
   - Railway will automatically detect it's a Python app

3. **Set Environment Variables**:
   - Go to your project settings
   - Add these environment variables:
     ```
     GEMINI_API_KEY=your_actual_gemini_api_key_here
     SECRET_KEY=your_secure_secret_key_here
     ```

4. **Deploy**:
   - Railway will automatically build and deploy your app
   - You'll get a URL like `https://your-app-name.railway.app`

## Option 2: Deploy to Heroku

Heroku is a popular platform with good free tier options.

### Steps:

1. **Install Heroku CLI**:
   ```bash
   # Download from https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **Login to Heroku**:
   ```bash
   heroku login
   ```

3. **Create Heroku app**:
   ```bash
   heroku create your-app-name
   ```

4. **Set environment variables**:
   ```bash
   heroku config:set GEMINI_API_KEY=your_actual_gemini_api_key_here
   heroku config:set SECRET_KEY=your_secure_secret_key_here
   ```

5. **Deploy**:
   ```bash
   git add .
   git commit -m "Deploy to Heroku"
   git push heroku main
   ```

## Option 3: Deploy to Render

Render offers a generous free tier and is very user-friendly.

### Steps:

1. **Sign up for Render**:
   - Go to [render.com](https://render.com)
   - Sign up with your GitHub account

2. **Create a new Web Service**:
   - Click "New +" → "Web Service"
   - Connect your GitHub repository

3. **Configure the service**:
   - **Name**: Your app name
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn webapp_production:app`

4. **Set Environment Variables**:
   - Add `GEMINI_API_KEY` with your API key
   - Add `SECRET_KEY` with a secure random string

5. **Deploy**:
   - Click "Create Web Service"
   - Render will build and deploy automatically

## Option 4: Deploy to DigitalOcean App Platform

DigitalOcean offers a managed platform with good performance.

### Steps:

1. **Sign up for DigitalOcean**:
   - Go to [digitalocean.com](https://digitalocean.com)
   - Create an account

2. **Create App**:
   - Go to App Platform
   - Click "Create App"
   - Connect your GitHub repository

3. **Configure**:
   - Select Python as the environment
   - Set build command: `pip install -r requirements.txt`
   - Set run command: `gunicorn webapp_production:app`

4. **Set Environment Variables**:
   - Add your Gemini API key and secret key

5. **Deploy**:
   - Click "Create Resources"

## Option 5: Deploy to VPS (Advanced)

For full control, deploy to a VPS like DigitalOcean Droplet, AWS EC2, or Linode.

### Steps:

1. **Set up VPS**:
   - Create a Ubuntu/Debian VPS
   - SSH into your server

2. **Install dependencies**:
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip nginx
   ```

3. **Clone your repository**:
   ```bash
   git clone https://github.com/yourusername/your-repo.git
   cd your-repo
   ```

4. **Set up Python environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

5. **Set environment variables**:
   ```bash
   export GEMINI_API_KEY=your_api_key
   export SECRET_KEY=your_secret_key
   ```

6. **Set up Gunicorn service**:
   ```bash
   sudo nano /etc/systemd/system/jarvis.service
   ```
   
   Add this content:
   ```ini
   [Unit]
   Description=JARVIS Flask App
   After=network.target

   [Service]
   User=ubuntu
   WorkingDirectory=/home/ubuntu/your-repo
   Environment="PATH=/home/ubuntu/your-repo/venv/bin"
   Environment="GEMINI_API_KEY=your_api_key"
   Environment="SECRET_KEY=your_secret_key"
   ExecStart=/home/ubuntu/your-repo/venv/bin/gunicorn webapp_production:app
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

7. **Start the service**:
   ```bash
   sudo systemctl start jarvis
   sudo systemctl enable jarvis
   ```

8. **Configure Nginx**:
   ```bash
   sudo nano /etc/nginx/sites-available/jarvis
   ```
   
   Add this configuration:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

9. **Enable the site**:
   ```bash
   sudo ln -s /etc/nginx/sites-available/jarvis /etc/nginx/sites-enabled
   sudo nginx -t
   sudo systemctl restart nginx
   ```

## Environment Variables

All deployment options require these environment variables:

- `GEMINI_API_KEY`: Your Google Gemini API key
- `SECRET_KEY`: A secure random string for Flask sessions

## Important Notes

1. **API Key Security**: Never commit your API keys to version control. Always use environment variables.

2. **Database**: The app uses SQLite by default. For production, consider using PostgreSQL or MySQL.

3. **File Uploads**: The uploads folder is temporary. For production, consider using cloud storage like AWS S3.

4. **SSL/HTTPS**: Most platforms provide SSL certificates automatically. For VPS deployment, you'll need to set up Let's Encrypt.

5. **Monitoring**: Set up monitoring and logging for production deployments.

## Troubleshooting

### Common Issues:

1. **Build fails**: Check that all dependencies are in `requirements.txt`
2. **App crashes**: Check logs for missing environment variables
3. **Database errors**: Ensure the database file is writable
4. **API errors**: Verify your Gemini API key is valid and has sufficient quota

### Checking Logs:

- **Railway**: View logs in the Railway dashboard
- **Heroku**: `heroku logs --tail`
- **Render**: View logs in the Render dashboard
- **VPS**: `sudo journalctl -u jarvis -f`

## Next Steps

After deployment:

1. Test all functionality
2. Set up monitoring
3. Configure backups
4. Set up a custom domain (optional)
5. Implement rate limiting for production use

## Support

If you encounter issues:
1. Check the platform's documentation
2. Review application logs
3. Verify environment variables are set correctly
4. Test locally first to ensure the app works 