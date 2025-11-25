# Production Credentials

## 🔑 Primary Production Account

### Super Admin (Production)
- **Email**: `fala@gmail.com`
- **Password**: `Jesus1993@`
- **Role**: `SUPER_ADMIN`
- **Username**: `fala`
- **Name**: Fala Admin

This account is automatically created/updated on every application startup (see `app/main.py`).

### Test User (Production)
- **Email**: `test@gmail.com`
- **Password**: `Test2025`
- **Role**: `SUPER_ADMIN`
- **Username**: `test`
- **Name**: Test User

This account is automatically created/updated on every application startup (see `app/main.py`).

## 🌐 Production URLs

- **Backend**: https://hrpiloteback.onrender.com
- **Frontend**: https://hrpilotefront.onrender.com
- **API Base**: https://hrpiloteback.onrender.com/api/v1
- **API Docs**: https://hrpiloteback.onrender.com/docs
- **Health Check**: https://hrpiloteback.onrender.com/health

## 📝 Login Instructions

1. Go to: https://hrpilotefront.onrender.com
2. Enter credentials (choose one):
   - **Email**: `fala@gmail.com` / **Password**: `Jesus1993@`
   - **Email**: `test@gmail.com` / **Password**: `Test2025`
3. Click "Login"

## 🔒 Security Notes

⚠️ **IMPORTANT**: 
- This is the default production password
- **Change this password immediately** after first login for security
- The password is hardcoded in `app/main.py` for automatic account creation
- Consider changing it in the code and redeploying for better security

## 🧪 Testing Credentials

For testing purposes, you can also use these accounts (if they exist in your database):

### Development/Test Accounts
All use password: `Jesus1993@`

- **SUPER_ADMIN**: `superadmin@hrpilot.com`
- **ORG_ADMIN**: `orgadmin@hrpilot.com`
- **HR**: `hr@hrpilot.com`
- **MANAGER**: `manager@hrpilot.com`
- **DIRECTOR**: `director@hrpilot.com`
- **PAYROLL**: `payroll@hrpilot.com`
- **EMPLOYEE**: `employee@hrpilot.com`

## 🔍 Verification

To test if the production credentials work:

```bash
# Using curl for super admin
curl -X POST https://hrpiloteback.onrender.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "fala@gmail.com", "password": "Jesus1993@"}'

# Using curl for test user
curl -X POST https://hrpiloteback.onrender.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@gmail.com", "password": "Test2025"}'

# Or use the test script
python check_production_config.py
```

## 📋 Account Creation

Both production accounts are automatically created in `app/main.py`:

```python
async def _ensure_super_admin() -> None:
    """Ensure the default super admin exists in Mongo."""
    email = "fala@gmail.com"
    password = "Jesus1993@"
    # ... creates or updates the account

async def _ensure_test_user() -> None:
    """Ensure the test production user exists in Mongo."""
    email = "test@gmail.com"
    password = "Test2025"
    # ... creates or updates the account
```

These functions run on every application startup, so both accounts will always exist with these credentials.

## 🛠️ Changing the Password

### Option 1: Change via UI (Recommended)
1. Login with current credentials
2. Go to Profile settings
3. Change password to a secure one

### Option 2: Change in Code
1. Edit `app/main.py`:
   - For super admin: change `password = "Jesus1993@"` to your new password (line 24)
   - For test user: change `password = "Test2025"` to your new password (line 50)
2. Commit and push to trigger redeploy
3. The new password will be set on next deployment

### Option 3: Direct Database Update
1. Connect to MongoDB Atlas
2. Find the user document with email `fala@gmail.com` or `test@gmail.com`
3. Update the `hashed_password` field
4. Use the password hashing function from `app/core/security.py`

## 🚨 Troubleshooting

### Can't Login?

1. **Check if account exists**:
   - Check MongoDB for user with email `fala@gmail.com` or `test@gmail.com`
   - Verify `is_active = true` and `status = ACTIVE`

2. **Check password**:
   - Super admin: Ensure you're using: `Jesus1993@` (case-sensitive)
   - Test user: Ensure you're using: `Test2025` (case-sensitive)
   - Check for typos or extra spaces

3. **Check deployment**:
   - Verify latest code is deployed
   - Check Render logs for account creation messages
   - Look for: `✅ Production super admin created: fala@gmail.com`
   - Look for: `✅ Production test user created: test@gmail.com`

4. **Check MongoDB connection**:
   - Verify `MONGODB_URI` is set correctly in Render
   - Check MongoDB Atlas network access allows Render IPs

### Account Not Created?

The accounts are created automatically on startup. Check Render logs for:
- `✅ Production super admin created: fala@gmail.com` (new account)
- `✅ Production super admin password updated: fala@gmail.com` (existing account)
- `✅ Production test user created: test@gmail.com` (new account)
- `✅ Production test user password updated: test@gmail.com` (existing account)

If you don't see these messages, check:
- MongoDB connection is working
- Environment variables are set correctly
- Application started successfully

## 📞 Support

If you're still having issues:
1. Check Render deployment logs
2. Verify MongoDB connection
3. Test the health endpoint: https://hrpiloteback.onrender.com/health
4. Review `RENDER_DEPLOYMENT_REVIEW.md` for deployment troubleshooting


