# MongoDB Atlas Setup Guide for ZyraX

If you're using MongoDB Atlas (cloud database) instead of local MongoDB, follow this guide.

## 📋 Prerequisites

- MongoDB Atlas account (free tier works fine)
- Cluster created and running

## 🔧 Getting Your Connection String

### Step 1: Create a Cluster (if you haven't)

1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Sign up or log in
3. Create a new cluster (choose FREE tier M0)
4. Wait for cluster to be created (~3-5 minutes)

### Step 2: Configure Network Access

1. In Atlas dashboard, go to **Network Access**
2. Click **Add IP Address**
3. Choose **Allow Access from Anywhere** (0.0.0.0/0)
   - For production, restrict to your server's IP
4. Click **Confirm**

### Step 3: Create Database User

1. Go to **Database Access**
2. Click **Add New Database User**
3. Choose **Password** authentication
4. Set username and password (remember these!)
5. Set **Database User Privileges** to **Read and write to any database**
6. Click **Add User**

### Step 4: Get Connection String

1. Go to **Database** (Clusters)
2. Click **Connect** on your cluster
3. Choose **Connect your application**
4. Select **Python** and version **3.12 or later**
5. Copy the connection string

It will look like:
```
mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
```

### Step 5: Configure ZyraX

Edit your `.env` file:

```env
# Replace <username> and <password> with your actual credentials
MONGO_URI=mongodb+srv://YOUR_USERNAME:YOUR_PASSWORD@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority&appName=ZyraX

# You can optionally specify the database name
MONGO_DB_NAME=zyrax
```

**Important Notes:**

- ✅ Replace `<username>` with your database username
- ✅ Replace `<password>` with your database password  
- ✅ Don't include `<` or `>` characters
- ✅ If password contains special characters, URL encode them:
  - `@` → `%40`
  - `#` → `%23`
  - `$` → `%24`
  - `%` → `%25`
  - `&` → `%26`

### Example

If your credentials are:
- Username: `BIPRO`
- Password: `MyPass@123`
- Cluster: `zyrax.3ksmg.mongodb.net`

Your connection string should be:
```
mongodb+srv://BIPRO:MyPass%40123@zyrax.3ksmg.mongodb.net/?retryWrites=true&w=majority&appName=ZyraX
```

Note: `@` in password is encoded as `%40`

## ✅ Testing Connection

Run your bot:
```bash
python bot.py
```

You should see:
```
✓ Connected to MongoDB database: zyrax
```

If you see connection errors:
1. Check your username and password
2. Verify IP whitelist (0.0.0.0/0 for testing)
3. Ensure cluster is running
4. Check if password needs URL encoding

## 🔒 Security Best Practices

### For Production:

1. **Restrict IP Access**
   - In Atlas Network Access, remove 0.0.0.0/0
   - Add only your server's IP address

2. **Use Strong Passwords**
   - Generate complex passwords
   - Never commit `.env` file to Git

3. **Use Environment Variables**
   - Never hardcode credentials in code
   - Use `.env` file (already in `.gitignore`)

4. **Limit User Privileges**
   - Create separate users for different purposes
   - Use read-only users where possible

5. **Enable Backup**
   - Atlas free tier includes basic backups
   - Download important data regularly

## 📊 Monitoring

### View Your Data

1. In Atlas, go to **Browse Collections**
2. Select database `zyrax`
3. View collections:
   - `chats` - Chat settings
   - `users` - User data
   - `filters` - Custom filters
   - `notes` - Saved notes
   - etc.

### Monitor Performance

1. Go to **Metrics** in Atlas
2. Monitor:
   - Operations per second
   - Data size
   - Index usage
   - Connection count

## 💰 Atlas Pricing

**Free Tier (M0):**
- ✅ 512 MB storage
- ✅ Shared RAM
- ✅ Good for small to medium bots
- ✅ No credit card required

**When to Upgrade:**
- Bot is in 100+ groups
- Database size > 500 MB
- Need faster performance
- Need more connections

## 🆘 Troubleshooting

### Error: "Authentication failed"
**Solution:** Check username and password in connection string

### Error: "Could not connect to any servers"
**Solution:** 
1. Check IP whitelist
2. Verify cluster is running
3. Check internet connection

### Error: "Invalid connection string"
**Solution:** 
1. Ensure no spaces in connection string
2. Check special characters are URL encoded
3. Verify format: `mongodb+srv://user:pass@cluster.net/`

### Slow Performance
**Solution:**
1. Check Atlas metrics
2. Consider upgrading cluster
3. Optimize database queries
4. Add indexes for frequent queries

## 📚 Additional Resources

- [MongoDB Atlas Documentation](https://docs.atlas.mongodb.com/)
- [Connection String Format](https://docs.mongodb.com/manual/reference/connection-string/)
- [Atlas Free Tier](https://www.mongodb.com/pricing)

---

**Questions?** Check the main [SETUP_GUIDE.md](SETUP_GUIDE.md) or create an issue on GitHub.