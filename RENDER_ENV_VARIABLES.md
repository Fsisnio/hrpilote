# Render Environment Variables Configuration

## Backend Service Environment Variables

### Required Variables

```bash
# MongoDB Configuration (REQUIRED - we use MongoDB, NOT PostgreSQL)
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/dbname?retryWrites=true&w=majority
MONGODB_DB_NAME=hrpilot

# Security Keys (REQUIRED)
SECRET_KEY=your-super-secret-key-here-change-in-production
JWT_SECRET_KEY=your-jwt-secret-key-here-change-in-production

# Application Settings
ENVIRONMENT=production
DEBUG=false
```

### Optional Variables

```bash
# CORS Configuration (optional - defaults included)
CORS_ORIGINS=https://hrpilotefront.onrender.com,https://hrpiloteback.onrender.com

# Email Configuration (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=noreply@hrpilot.com
```

## Frontend Service Environment Variables

### Required Variables

```bash
# API Base URL (REQUIRED)
REACT_APP_API_BASE_URL=https://hrpiloteback.onrender.com/api/v1
```

## Important Notes

### ❌ DO NOT SET (Deprecated)
- `DATABASE_URL` - We don't use PostgreSQL anymore
- `DATABASE_SSL_MODE` - Not needed for MongoDB
- `DATABASE_SSL_ROOT_CERT` - Not needed for MongoDB

### ✅ MUST SET
- `MONGODB_URI` - Your MongoDB Atlas connection string
- `MONGODB_DB_NAME` - Your database name (e.g., "hrpilot")
- `SECRET_KEY` - Generate a secure random string
- `JWT_SECRET_KEY` - Generate a secure random string

## MongoDB Atlas Setup

1. **Create MongoDB Atlas Account**: https://www.mongodb.com/cloud/atlas
2. **Create a Cluster** (free tier available)
3. **Create Database User**:
   - Go to Database Access
   - Add new database user
   - Save username and password
4. **Whitelist IP Addresses**:
   - Go to Network Access
   - Add IP Address: `0.0.0.0/0` (allows all IPs - for testing)
   - For production, use Render's IP ranges
5. **Get Connection String**:
   - Go to Clusters → Connect
   - Choose "Connect your application"
   - Copy the connection string
   - Replace `<password>` with your database user password
   - Replace `<dbname>` with your database name

## Example MongoDB URI Format

```
mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/hrpilot?retryWrites=true&w=majority
```

## Generating Secure Keys

You can generate secure keys using Python:

```python
import secrets

# Generate SECRET_KEY
print(secrets.token_urlsafe(32))

# Generate JWT_SECRET_KEY
print(secrets.token_urlsafe(32))
```

Or using OpenSSL:

```bash
# Generate SECRET_KEY
openssl rand -hex 32

# Generate JWT_SECRET_KEY
openssl rand -hex 32
```

## Setting Variables in Render

1. Go to https://dashboard.render.com
2. Click on your backend service
3. Go to "Environment" tab
4. Click "Add Environment Variable"
5. Add each variable:
   - **Key**: `MONGODB_URI`
   - **Value**: Your MongoDB connection string
6. Repeat for all required variables
7. **Important**: After adding variables, the service will automatically redeploy

## Verification

After setting variables, check:

1. **Deployment Logs**: Should show "MongoDB connection initialized"
2. **Health Endpoint**: `https://hrpiloteback.onrender.com/health` should return 200
3. **API Docs**: `https://hrpiloteback.onrender.com/docs` should load
4. **Login Test**: Try logging in with your credentials

## Common Mistakes

### ❌ Wrong Variable Name
- Using `DATABASE_URL` instead of `MONGODB_URI`
- Using `DB_NAME` instead of `MONGODB_DB_NAME`

### ❌ Wrong Connection String Format
- Missing `mongodb+srv://` prefix
- Not replacing `<password>` placeholder
- Not including database name in URI or as separate variable

### ❌ Network Access Issues
- MongoDB Atlas not allowing Render IPs
- Firewall blocking connections

### ❌ Missing Variables
- Forgetting to set `MONGODB_DB_NAME`
- Not setting `SECRET_KEY` or `JWT_SECRET_KEY`

## Troubleshooting

### Issue: "MongoDB connection failed"

**Check:**
1. Is `MONGODB_URI` set correctly?
2. Is password in connection string correct?
3. Are Render IPs whitelisted in MongoDB Atlas?
4. Is MongoDB cluster running (not paused)?

### Issue: "Database name not found"

**Check:**
1. Is `MONGODB_DB_NAME` set?
2. Does the database exist in MongoDB Atlas?
3. Does the user have permissions to access the database?

### Issue: "Authentication failed"

**Check:**
1. Is the username correct in connection string?
2. Is the password correct (no special characters need URL encoding)?
3. Does the database user have proper permissions?

## Quick Checklist

- [ ] `MONGODB_URI` is set with correct connection string
- [ ] `MONGODB_DB_NAME` is set
- [ ] `SECRET_KEY` is set (secure random string)
- [ ] `JWT_SECRET_KEY` is set (secure random string)
- [ ] MongoDB Atlas cluster is running
- [ ] Render IPs are whitelisted in MongoDB Atlas
- [ ] Database user has correct permissions
- [ ] Service redeployed after setting variables
- [ ] Health endpoint returns 200 OK
- [ ] Login functionality works

