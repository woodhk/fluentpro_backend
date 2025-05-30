# Deployment Guide

This guide provides step-by-step instructions for deploying the Fluentpro backend to production.

## Prerequisites

- Auth0 account
- Supabase account
- Render account (for hosting)
- Git repository

## Step 1: Auth0 Setup

### 1.1 Create Auth0 Application

1. Log in to [Auth0 Dashboard](https://manage.auth0.com/)
2. Go to **Applications** → **Create Application**
3. Choose **Machine to Machine Application**
4. Name it "Fluentpro Backend"
5. Select **Auth0 Management API**
6. Grant the following scopes:
   - `read:users`
   - `create:users`
   - `update:users`
   - `delete:users`

### 1.2 Configure Application Settings

1. Go to your application **Settings**
2. Note down:
   - **Domain** (e.g., `your-tenant.auth0.com`)
   - **Client ID**
   - **Client Secret**
3. Add your backend URL to **Allowed Callback URLs**:
   - `https://your-app-name.onrender.com/api/v1/auth/auth0/callback/`
4. Add your frontend URLs to **Allowed Web Origins**:
   - For iOS: `capacitor://localhost` (if using Capacitor)
   - For development: `http://localhost:3000`

### 1.3 Configure Auth0 API

1. Go to **APIs** → **Create API**
2. Name: "Fluentpro API"
3. Identifier: `https://api.fluentpro.com`
4. Signing Algorithm: **RS256**
5. Note down the **API Identifier** (this is your audience)

### 1.4 Create Database Connection

1. Go to **Authentication** → **Database**
2. Create a **Username-Password-Authentication** connection
3. Enable **Signup** and **Login**
4. Configure password policy as needed

## Step 2: Supabase Setup

### 2.1 Create Supabase Project

1. Log in to [Supabase Dashboard](https://supabase.com/dashboard)
2. Click **New Project**
3. Choose organization and name your project "fluentpro"
4. Set a strong database password
5. Choose a region close to your users

### 2.2 Create Users Table

1. Go to **SQL Editor** in Supabase Dashboard
2. Run the following SQL to create the users table:

```sql
-- Create users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    date_of_birth DATE NOT NULL,
    auth0_id VARCHAR(255) UNIQUE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_auth0_id ON users(auth0_id);
CREATE INDEX idx_users_active ON users(is_active);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security (RLS)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Create policies (adjust based on your security requirements)
-- Allow authenticated users to read their own data
CREATE POLICY "Users can read own data" ON users
    FOR SELECT USING (auth.uid()::text = auth0_id);

-- Allow service role to perform all operations
CREATE POLICY "Service role can do everything" ON users
    FOR ALL USING (auth.role() = 'service_role');
```

### 2.3 Get Supabase Credentials

1. Go to **Settings** → **API**
2. Note down:
   - **Project URL** (e.g., `https://your-project.supabase.co`)
   - **anon public** key
   - **service_role** key (keep this secret!)

## Step 3: Deploy to Render

### 3.1 Prepare Repository

1. Push your code to GitHub/GitLab
2. Ensure your repository contains:
   - `requirements.txt`
   - `fluentpro_backend/` directory with Django project
   - `.env.example` file

### 3.2 Create Render Service

1. Log in to [Render Dashboard](https://dashboard.render.com/)
2. Click **New** → **Web Service**
3. Connect your Git repository
4. Configure the service:
   - **Name**: `fluentpro-backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn fluentpro_backend.fluentpro_backend.wsgi:application`
   - **Instance Type**: Choose based on your needs (Free tier available)

### 3.3 Configure Environment Variables

In Render's **Environment** section, add the following variables:

```
SECRET_KEY=your-django-secret-key-here-make-it-long-and-random
DEBUG=False
ALLOWED_HOSTS=your-app-name.onrender.com

AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_CLIENT_ID=your-auth0-client-id
AUTH0_CLIENT_SECRET=your-auth0-client-secret
AUTH0_AUDIENCE=https://api.fluentpro.com

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_KEY=your-supabase-service-key

CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com,capacitor://localhost
```

### 3.4 Generate Django Secret Key

Generate a secure Django secret key:

```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

Or use an online generator like [djecrety.ir](https://djecrety.ir/)

### 3.5 Deploy

1. Click **Create Web Service**
2. Render will automatically deploy your application
3. Monitor the deployment logs for any errors
4. Once deployed, your API will be available at: `https://your-app-name.onrender.com`

## Step 4: Verify Deployment

### 4.1 Health Check

Test the health endpoint:
```bash
curl https://your-app-name.onrender.com/api/v1/auth/health/
```

Expected response:
```json
{
    "status": "healthy",
    "service": "fluentpro-backend",
    "version": "1.0.0",
    "environment": "production",
    "auth0_configured": true,
    "supabase_configured": true
}
```

### 4.2 Test Sign Up

```bash
curl -X POST https://your-app-name.onrender.com/api/v1/auth/signup/ \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Test User",
    "email": "test@example.com",
    "password": "TestPass123!",
    "date_of_birth": "1990-01-01"
  }'
```

### 4.3 Test Login

```bash
curl -X POST https://your-app-name.onrender.com/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!"
  }'
```

## Step 5: iOS App Configuration

Update your iOS app's API configuration to point to your deployed backend:

In your `APIEndpoints.swift`:
```swift
struct APIEndpoints {
    static let baseURL = "https://your-app-name.onrender.com"
    static let apiVersion = "v1"
    
    // ... rest of your endpoints
}
```

## Security Considerations

### Production Security Checklist

- ✅ Use strong, unique passwords for all services
- ✅ Enable 2FA on Auth0 and Supabase accounts
- ✅ Use environment variables for all secrets
- ✅ Set `DEBUG=False` in production
- ✅ Configure proper CORS origins
- ✅ Enable HTTPS (automatically handled by Render)
- ✅ Monitor application logs regularly
- ✅ Set up error tracking (e.g., Sentry)
- ✅ Regular security updates

### Environment Variables Security

Never commit the following to your repository:
- Auth0 client secret
- Supabase service key
- Django secret key
- Database passwords

## Monitoring and Maintenance

### Log Monitoring

Monitor your application logs in Render dashboard for:
- Authentication errors
- API failures
- Performance issues

### Database Monitoring

Monitor your Supabase database for:
- Connection limits
- Query performance
- Storage usage

### Backup Strategy

Supabase automatically handles database backups, but consider:
- Regular manual backups for critical data
- Testing restore procedures
- Documenting recovery processes

## Scaling Considerations

### Performance Optimization

- Enable database connection pooling
- Implement Redis for caching (if needed)
- Optimize database queries
- Use CDN for static files

### Infrastructure Scaling

- Monitor resource usage in Render
- Upgrade instance types as needed
- Consider horizontal scaling for high traffic

## Troubleshooting

### Common Issues

1. **502 Bad Gateway**: Check your start command and ensure the application starts correctly
2. **Auth0 Connection Errors**: Verify Auth0 credentials and network connectivity
3. **Supabase Connection Errors**: Check Supabase URL and API keys
4. **CORS Errors**: Ensure frontend URLs are in CORS_ALLOWED_ORIGINS

### Debugging Steps

1. Check Render deployment logs
2. Verify environment variables are set correctly
3. Test API endpoints with curl
4. Check Auth0 and Supabase logs
5. Monitor application health endpoint

## Support

For deployment issues:
- Check Render documentation
- Review Django deployment guides
- Consult Auth0 and Supabase documentation
- Monitor application logs for specific error messages