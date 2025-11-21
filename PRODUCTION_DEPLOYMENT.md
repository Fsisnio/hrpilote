# Production Deployment Guide - Password Fix

## Overview
This guide covers deploying the SHA-256 + bcrypt password fix to production on Render.

## What Changed
- **Password hashing method**: Now uses SHA-256 pre-hashing + bcrypt
- **Supports unlimited password length**: No more 72-byte limitation
- **Backward compatible**: Existing passwords auto-migrate on login

## Deployment Steps

### 1. ✅ Code Deployment (Automatic)

The code fix has been pushed to GitHub (commit `48f577b`). If you have auto-deploy enabled on Render:

1. Go to https://dashboard.render.com
2. Find your HR Pilot service
3. Wait for automatic deployment (2-5 minutes)
4. Check deployment logs for success

**Manual Deploy** (if auto-deploy is disabled):
- Click "Manual Deploy" → "Deploy latest commit" in Render dashboard

### 2. 🔑 Password Migration (Choose One Option)

#### Option A: Automatic Migration (Recommended)
**No action needed!** The new code has backward compatibility:
- Existing users can login with current passwords
- Passwords automatically upgrade to new method on successful login
- Gradual migration as users login

**Pros:**
- ✅ Zero downtime
- ✅ No manual intervention
- ✅ Users unaffected

**Cons:**
- ⚠️ Takes time (as users login)
- ⚠️ Old hashes remain until user logs in

#### Option B: Force Reset All Passwords (Immediate)
Run the password reset script on Render to immediately update all admin passwords.

**Steps:**

1. **SSH into Render** (if available) or use Render Shell:
   ```bash
   # In Render dashboard → Shell
   python scripts/reset_production_passwords.py
   ```

2. **Or run via Render Build Command**:
   Add to your `render.yaml` or run as a one-time job:
   ```bash
   python scripts/reset_production_passwords.py
   ```

3. **Or create a Render Cron Job**:
   - Create a new Cron Job in Render
   - Command: `python scripts/reset_production_passwords.py`
   - Run once manually

**Pros:**
- ✅ Immediate migration
- ✅ All passwords use new method instantly
- ✅ Guaranteed working credentials

**Cons:**
- ⚠️ Resets passwords to default (Jesus1993@)
- ⚠️ Users need to change passwords after

### 3. 🧪 Verification

#### Test Login After Deployment:

1. Go to your production URL
2. Login with:
   ```
   Email:    superadmin@hrpilot.com
   Password: Jesus1993@
   ```

3. **If login fails**, run the password reset script:
   ```bash
   python scripts/reset_production_passwords.py
   ```

#### Check Deployment Logs:

Look for these success messages:
```
✅ Password hashed successfully
✅ Password verified successfully
✅ New hashing method is active
```

### 4. 🔒 Security - Change Default Passwords

**IMPORTANT:** After successful deployment and login:

1. Login as superadmin
2. Change password to a strong, unique password
3. Password can now be any length (no 72-byte limit!)
4. Repeat for all admin accounts

## Troubleshooting

### Issue: "Incorrect email or password" after deployment

**Solution 1:** Run password reset script
```bash
python scripts/reset_production_passwords.py
```

**Solution 2:** Check if deployment completed
- Go to Render dashboard
- Check if latest commit is deployed
- Review deployment logs for errors

### Issue: "password cannot be longer than 72 bytes"

**Solution:** Redeploy latest code
- This error means old code is still running
- Force redeploy from Render dashboard
- Wait for deployment to complete

### Issue: Users can't login after deployment

**Solution:** Backward compatibility is enabled
- Old passwords should still work
- If not, run password reset script
- Check database connection
- Verify the Render service has `DATABASE_SSL_MODE=require` (and optionally
  `DATABASE_SSL_ROOT_CERT`) so the backend can negotiate TLS with Postgres.

## Files Changed

### Core Changes:
- ✅ `app/core/security.py` - New hashing method
- ✅ `app/api/v1/auth.py` - Auto-migration on login

### New Files:
- ✅ `scripts/reset_production_passwords.py` - Password reset tool
- ✅ `PASSWORD_FIX_SUMMARY.md` - Technical documentation
- ✅ `migrate_passwords_to_sha256.py` - Migration utility
- ✅ `PRODUCTION_DEPLOYMENT.md` - This file

## Rollback Plan

If issues occur, you can rollback:

1. **Revert code** in GitHub:
   ```bash
   git revert 48f577b
   git push origin main
   ```

2. **Wait for Render auto-deploy** or manually deploy

3. **Note:** Old passwords may not work after rollback
   - Need to restore database backup
   - Or reset passwords again

## Post-Deployment Checklist

- [ ] Code deployed to Render
- [ ] Deployment logs show no errors
- [ ] Superadmin login works
- [ ] Create test user with long password (100+ characters)
- [ ] Test user login works
- [ ] Change default admin passwords
- [ ] Monitor for any password-related errors
- [ ] Update team documentation

## Support

If you encounter issues:
1. Check Render deployment logs
2. Review `PASSWORD_FIX_SUMMARY.md` for technical details
3. Run password reset script if login fails
4. Check database connectivity

## Summary

✅ **Recommended Approach:**
1. Let Render auto-deploy the code fix
2. Use automatic migration (Option A)
3. Existing users login normally
4. Passwords auto-upgrade on login
5. Monitor logs for any issues

This ensures zero downtime and smooth transition! 🚀

