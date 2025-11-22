# JB's Events Backend - Render Deployment Guide

## 📋 Prerequisites

- GitHub account
- Render account (free tier available at https://render.com)
- Your Django backend code pushed to a GitHub repository

## 🚀 Deployment Steps

### 1. Push Your Code to GitHub

If you haven't already set up a Git repository:

```bash
cd /Users/santhoshchodipilli/Desktop/JB\'s\ events/backend
git init
git add .
git commit -m "Prepare backend for Render deployment"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

### 2. Create a New Web Service on Render

1. Go to https://dashboard.render.com
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Select the repository containing your backend

### 3. Configure the Web Service

**Basic Settings:**
- **Name**: `jbs-events-backend` (or your preferred name)
- **Region**: Choose closest to your users (e.g., Singapore for Asia)
- **Branch**: `main`
- **Root Directory**: Leave empty (or specify if backend is in a subdirectory)
- **Environment**: `Python 3`
- **Build Command**: `./build.sh`
- **Start Command**: `gunicorn jbs_backend.wsgi:application`
- **Instance Type**: `Free`

### 4. Set Environment Variables

In the Render dashboard, add these environment variables:

**Required:**
```
DEBUG=False
SECRET_KEY=<generate-a-strong-secret-key>
FRONTEND_URL=https://your-frontend-domain.com

# Superuser credentials
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=your-email@example.com
DJANGO_SUPERUSER_PASSWORD=<strong-password>

# Twilio credentials
TWILIO_ACCOUNT_SID=<your-twilio-sid>
TWILIO_AUTH_TOKEN=<your-twilio-token>
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
TWILIO_WHATSAPP_TO=whatsapp:+919032588332

# Razorpay credentials
RAZORPAY_KEY_ID=<your-razorpay-key-id>
RAZORPAY_KEY_SECRET=<your-razorpay-key-secret>
```

**Note:** The `DATABASE_URL` will be automatically set when you add a PostgreSQL database.

### 5. Add PostgreSQL Database

1. In your Render dashboard, click **"New +"** → **"PostgreSQL"**
2. **Name**: `jbs-events-db`
3. **Database**: `jbs_events_db`
4. **User**: `jbs_events_user` (auto-generated)
5. **Region**: Same as your web service
6. **Instance Type**: `Free`
7. Click **"Create Database"**

### 6. Connect Database to Web Service

1. Go back to your web service settings
2. In the **Environment** section, add:
   - **Key**: `DATABASE_URL`
   - **Value**: Click "Select a database" and choose `jbs-events-db`

Alternatively, if using `render.yaml`:
- Simply push the `render.yaml` file to your repository
- Render will automatically configure everything

### 7. Deploy

1. Click **"Create Web Service"**
2. Render will automatically:
   - Install dependencies
   - Collect static files
   - Run migrations
   - Create the superuser
   - Start your application

### 8. Verify Deployment

Once deployed, verify:

✅ **API Health**: Visit `https://your-app.onrender.com/api/` (should see DRF browsable API)
✅ **Admin Panel**: Visit `https://your-app.onrender.com/admin/` and login with superuser credentials
✅ **Static Files**: Check if admin panel CSS loads correctly
✅ **Database**: Verify data persists between requests

## 🔧 Post-Deployment Configuration

### Update Frontend CORS

Make sure your frontend is configured to use the Render backend URL:
```javascript
const API_BASE_URL = 'https://your-app.onrender.com';
```

### Monitor Logs

View logs in the Render dashboard to troubleshoot issues:
- Click on your web service
- Go to **"Logs"** tab

### Automatic Deployments

By default, Render will automatically deploy when you push to your `main` branch on GitHub.

## 🛠️ Troubleshooting

### Build Fails

- Check the build logs in Render dashboard
- Verify `build.sh` has execute permissions (`chmod +x build.sh`)
- Ensure all required environment variables are set

### Database Connection Error

- Verify `DATABASE_URL` is properly set
- Check PostgreSQL database is running
- Ensure database and web service are in the same region

### Static Files Not Loading

- Verify `STATIC_ROOT` and `STATIC_URL` in settings.py
- Check WhiteNoise is installed and configured
- Run `python manage.py collectstatic` manually to test

### CORS Errors

- Verify `FRONTEND_URL` environment variable matches your frontend domain
- Check `CORS_ALLOWED_ORIGINS` in settings.py
- Add frontend domain to `CSRF_TRUSTED_ORIGINS`

## 📝 Important Notes

1. **Free Tier Limitations**:
   - Service spins down after 15 minutes of inactivity
   - First request after spin-down takes 30-60 seconds
   - 750 hours/month free (enough for 1 service)

2. **Database Backups**:
   - Free tier PostgreSQL expires after 90 days
   - Upgrade to paid tier for persistent database

3. **Environment Variables**:
   - Never commit `.env` file to Git
   - Use Render's environment variable management
   - Rotate secrets regularly

4. **HTTPS**:
   - Render provides free SSL certificates
   - All traffic is automatically HTTPS

## 🔗 Useful Links

- Render Dashboard: https://dashboard.render.com
- Render Docs: https://render.com/docs
- Django Deployment Checklist: https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

## ✅ Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] Render web service created
- [ ] PostgreSQL database created
- [ ] All environment variables set
- [ ] Database connected to web service
- [ ] Deployment successful
- [ ] Admin panel accessible
- [ ] API endpoints working
- [ ] Frontend connected and CORS working
- [ ] Superuser created and can login
