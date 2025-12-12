# Token Scope Analysis

## Summary

Checked all token files on 2025-12-12. Here's what I found:

## Accounts Missing `gmail.readonly` Scope (Need Re-authentication)

These accounts only have `gmail.send` and need to be re-authenticated to get `gmail.readonly`:

1. **account3** (`spy.observer.wx@gmail.com`)
   - Current scopes: `['gmail.send']` only
   - Expiry: 2025-12-12T22:30:44
   - **Action**: Re-authenticate via website

2. **account7** (`wenxie.research@gmail.com`)
   - Current scopes: `['gmail.send']` only
   - Expiry: 2025-12-12T22:30:45
   - **Action**: Re-authenticate via website

3. **account8** (`vince.xie.job@gmail.com`)
   - Current scopes: `['gmail.send']` only
   - Expiry: 2025-12-12T22:30:45
   - **Action**: Re-authenticate via website

4. **account10** (`media.elyroy@gmail.com`)
   - Current scopes: `['gmail.send']` only
   - Expiry: 2025-12-12T22:30:45
   - **Action**: Re-authenticate via website

## Accounts with Both Scopes (Should Work)

These accounts have both `gmail.send` and `gmail.readonly`:

1. **account4** (`qqq.observer.wx@gmail.com`) ✅
2. **account6** (`albertjia25@gmail.com`) ✅
3. **account9** (`sanqiresearch@gmail.com`) ✅
4. **account11** (`sanqiacademic@gmail.com`) ✅
5. **account12** (`zuzubangatl@gmail.com`) ✅
6. **account15** (`academic.turboniw@gmail.com`) ✅
7. **16api** (`phd.help.phd@gmail.com`) ✅

## Why This Happened

When tokens are refreshed, they keep the **original scopes** from when they were first created. The refresh token has the scopes "baked in", so:

- If a token was created with only `gmail.send`, refreshing it will still only have `gmail.send`
- To get new scopes, you need to **delete the token and re-authenticate** (not just refresh)

## The Fix

I updated the code to:
1. Check scopes **before** refreshing expired tokens
2. Check scopes **after** refreshing tokens
3. If scopes are missing, **delete the token** and force re-authentication

## What You Need to Do

1. Go to your website: http://127.0.0.1:5001/accounts
2. Click **"Authenticate"** for these accounts:
   - account3
   - account7
   - account8
   - account10
3. When authenticating, make sure to grant **both** `gmail.send` and `gmail.readonly` permissions
4. The new tokens will be saved with both scopes

## After Re-authentication

Once re-authenticated, the bounce checking should work and you'll see:
```
✓ Checking bounce messages for account3_gmail_api...
```

Instead of:
```
⚠️ Could not check bounce messages: Insufficient Permission
```

## Note

Even though account4, account6, and account9 have both scopes in their token files, they still showed errors in the logs. This might be because:
- The tokens were refreshed in memory but the file wasn't updated
- There was a race condition during token refresh
- The service was built before the token was refreshed

The fix I made should handle this by checking scopes after refresh and forcing re-authentication if needed.

