# Gmail API Verification Guide

## Issue: "Access blocked: app has not completed the Google verification process"

When you see this error during authentication, it means Google requires the app to be verified OR your email needs to be added as a test user.

## Solution: Add Test Users

### Step 1: Go to Google Cloud Console
1. Visit: https://console.cloud.google.com/
2. Select your project (the one with your OAuth credentials)

### Step 2: Navigate to OAuth Consent Screen
1. Go to: **APIs & Services** > **OAuth consent screen**
2. Or direct link: https://console.cloud.google.com/apis/credentials/consent

### Step 3: Add Test Users
1. Scroll down to **"Test users"** section
2. Click **"+ ADD USERS"**
3. Add each email address that will use the app:
   - `qqq.observer.wx@gmail.com`
   - `albertjia25@gmail.com`
   - `wenxie.research@gmail.com`
   - `vince.xie.job@gmail.com`
   - `sanqiresearch@gmail.com`
   - `media.elyroy@gmail.com`
   - `sanqiacademic@gmail.com`
   - `zuzubangatl@gmail.com`
   - `academic.turboniw@gmail.com`
   - `phd.help.phd@gmail.com`
   - `sanqiacademia@gmail.com`
   - Any other Gmail accounts you use

4. Click **"SAVE"**

### Step 4: Retry Authentication
After adding test users, try authenticating again. The authentication should work.

## Alternative: Complete App Verification (For Production)

If you want to allow any user (not just test users), you need to:
1. Complete Google's verification process
2. Submit your app for review
3. This can take several days/weeks

For personal/internal use, adding test users is the fastest solution.

## Notes

- Test users can authenticate immediately after being added
- You can add up to 100 test users
- Test users don't require app verification
- Each email address that will authenticate needs to be added

