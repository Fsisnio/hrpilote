# How to Review Deployment in Render

## Quick Access

- **Render Dashboard**: https://dashboard.render.com
- **Backend URL**: https://hrpiloteback.onrender.com
- **Frontend URL**: https://hrpilotefront.onrender.com

## Step-by-Step Review Process

### 1. Access Render Dashboard

1. Go to https://dashboard.render.com
2. Log in with your Render account
3. You'll see a list of all your services

### 2. Find Your Services

Look for:
- **Backend Service**: `hrpiloteback` (or similar name)
- **Frontend Service**: `hrpilotefront` (or similar name)

### 3. Check Deployment Status

For each service:

1. **Click on the service name** to open its details
2. **Check the top section** for:
   - ✅ **Status**: Should show "Live" (green) or "Deploying" (yellow)
   - **Last Deploy**: Shows when the last deployment happened
   - **Commit**: Shows the Git commit hash that's deployed

### 4. Review Deployment Logs

1. **Click "Logs" tab** in the service dashboard
2. **Scroll through the logs** to check for:
   - ✅ Build success messages
   - ✅ "Starting service..." messages
   - ❌ Any error messages (red text)
   - ⚠️ Warning messages (yellow text)

**What to look for:**

**✅ Good Signs:**
```
✓ Build successful
✓ Starting uvicorn...
✓ Application startup complete
✓ MongoDB connection initialized
```

**❌ Bad Signs:**
```
✗ Build failed
✗ ModuleNotFoundError
✗ Connection refused
✗ Port already in use
✗ Environment variable missing
```

### 5. Check Recent Deployments

1. **Click "Events" tab** to see deployment history
2. **Review each deployment**:
   - Status (Success/Failed)
   - Duration
   - Commit message
   - Timestamp

### 6. Test Backend Health

**Option A: Via Browser**
```
https://hrpiloteback.onrender.com/health
```
Should return:
```json
{
  "status": "healthy",
  "timestamp": "..."
}
```

**Option B: Via Terminal**
```bash
curl https://hrpiloteback.onrender.com/health
```

**Option C: Check API Docs**
```
https://hrpiloteback.onrender.com/docs
```
Should show the FastAPI Swagger documentation

### 7. Test Frontend

1. **Open**: https://hrpilotefront.onrender.com
2. **Check**:
   - Page loads without errors
   - No console errors (F12 → Console tab)
   - API calls are going to production backend
   - Login functionality works

### 8. Check Environment Variables

1. **In Render dashboard** → Click your service
2. **Go to "Environment" tab**
3. **Verify these are set** (for backend):
   - ✅ `MONGODB_URI` - MongoDB connection string (REQUIRED)
   - ✅ `MONGODB_DB_NAME` - Database name (REQUIRED)
   - ✅ `SECRET_KEY` - Secret key for encryption (REQUIRED)
   - ✅ `JWT_SECRET_KEY` - JWT signing key (REQUIRED)
   - `CORS_ORIGINS` - Allowed origins (should include frontend URL)
   
   **Note:** `DATABASE_URL` is NOT needed anymore - we use MongoDB only!

4. **For frontend**:
   - `REACT_APP_API_BASE_URL` - Should be `https://hrpiloteback.onrender.com/api/v1`

### 9. Monitor Real-Time Logs

1. **Click "Logs" tab**
2. **Watch for**:
   - Incoming requests
   - Error messages
   - Database connection issues
   - API response times

### 10. Test Key Endpoints

**Health Check:**
```bash
curl https://hrpiloteback.onrender.com/health
```

**Root Endpoint:**
```bash
curl https://hrpiloteback.onrender.com/
```

**CORS Test:**
```bash
curl https://hrpiloteback.onrender.com/cors-test
```

**Login Test** (if you have credentials):
```bash
curl -X POST https://hrpiloteback.onrender.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "fala@gmail.com", "password": "Jesus1993@"}'
```

## Common Issues to Check

### ❌ Deployment Failed

**Symptoms:**
- Status shows "Failed" (red)
- Build logs show errors

**Solutions:**
1. Check build logs for specific error
2. Verify all dependencies in `requirements.txt`
3. Check Python version compatibility
4. Verify environment variables are set

### ❌ Service Not Starting

**Symptoms:**
- Status shows "Deploying" for a long time
- Logs show "Application failed to start"

**Solutions:**
1. Check startup command in Render settings
2. Verify port configuration (should be `$PORT` or `8000`)
3. Check for missing environment variables
4. Review application logs for startup errors

### ❌ Database Connection Issues

**Symptoms:**
- Logs show "Connection refused" or "Authentication failed"
- API returns 500 errors
- "MongoDB connection initialized" not appearing in logs

**Solutions:**
1. ✅ Verify `MONGODB_URI` is set (NOT `DATABASE_URL` - that's for PostgreSQL)
2. ✅ Check MongoDB Atlas network access (allow Render IPs: `0.0.0.0/0` for testing)
3. ✅ Verify `MONGODB_DB_NAME` is set correctly
4. ✅ Check database credentials in connection string
5. ✅ Verify MongoDB Atlas cluster is running (not paused on free tier)
6. ✅ Check if connection string includes authentication database: `mongodb+srv://user:pass@cluster.mongodb.net/dbname?retryWrites=true&w=majority`

### ❌ CORS Errors

**Symptoms:**
- Frontend can't connect to backend
- Browser console shows CORS errors

**Solutions:**
1. Verify `CORS_ORIGINS` includes frontend URL
2. Check backend logs for CORS-related errors
3. Ensure frontend `REACT_APP_API_BASE_URL` is correct

### ❌ Frontend Not Loading

**Symptoms:**
- Blank page
- 404 errors
- Build errors

**Solutions:**
1. Check build logs for errors
2. Verify `REACT_APP_API_BASE_URL` is set
3. Check if build completed successfully
4. Verify Node.js version compatibility

## Quick Health Check Script

You can use the existing script:

```bash
python check_production_config.py
```

This will test:
- ✅ Backend health
- ✅ CORS configuration
- ✅ Login endpoint
- ✅ Frontend configuration

## Render Dashboard Features

### Manual Deploy
- **Location**: Service → "Manual Deploy" button
- **Use when**: Auto-deploy is disabled or you want to deploy specific commit

### Shell Access
- **Location**: Service → "Shell" tab
- **Use for**: Running scripts, debugging, checking files

### Metrics
- **Location**: Service → "Metrics" tab
- **Shows**: CPU, Memory, Network usage
- **Use for**: Monitoring resource usage

### Events
- **Location**: Service → "Events" tab
- **Shows**: Deployment history, service events
- **Use for**: Tracking deployment timeline

## Best Practices

1. **Always check logs** after deployment
2. **Test endpoints** before marking deployment as successful
3. **Monitor metrics** for unusual spikes
4. **Keep environment variables** up to date
5. **Review deployment events** regularly
6. **Test in production** after each deployment

## Deployment Checklist

After each deployment, verify:

- [ ] Deployment status is "Live" (green)
- [ ] Build logs show no errors
- [ ] Health endpoint returns 200 OK
- [ ] API docs are accessible
- [ ] Frontend loads without errors
- [ ] Login functionality works
- [ ] Key API endpoints respond correctly
- [ ] No CORS errors in browser console
- [ ] Environment variables are set correctly
- [ ] Database connection is working
- [ ] Real-time logs show normal activity

## Getting Help

If you encounter issues:

1. **Check Render Status**: https://status.render.com
2. **Review Logs**: Look for error messages
3. **Check Documentation**: Render docs at https://render.com/docs
4. **Contact Support**: Via Render dashboard support section

## Quick Links

- **Render Dashboard**: https://dashboard.render.com
- **Backend Health**: https://hrpiloteback.onrender.com/health
- **Backend API Docs**: https://hrpiloteback.onrender.com/docs
- **Frontend**: https://hrpilotefront.onrender.com
- **Render Status**: https://status.render.com

