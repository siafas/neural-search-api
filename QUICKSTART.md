# ⚡ QUICKSTART - Railway Deployment σε 10 λεπτά

## 📋 Βήμα-Βήμα Οδηγίες

### 1️⃣ Railway Account (2 λεπτά)

```
1. Πήγαινε: https://railway.app
2. Click "Start a New Project"
3. Sign up με GitHub
4. Verify email
5. ✅ Done!
```

**Free Trial:** $5 credit = 1 μήνας δωρεάν testing!

---

### 2️⃣ Upload Code (3 λεπτά)

**Option A: GitHub (Recommended)**

```bash
# 1. Create new repo στο GitHub
# 2. Upload τα files:
#    - app.py
#    - requirements.txt
#    - Procfile
#    - runtime.txt
#    - README.md
# 3. Done!
```

**Option B: Direct Upload**

```
1. Railway Dashboard → "New Project"
2. "Deploy from local directory"
3. Select folder: neural_search_api/
4. Click Deploy
5. ✅ Done!
```

---

### 3️⃣ Deploy (5 λεπτά)

```
1. Railway → "New Project"
2. "Deploy from GitHub repo"
3. Select your repo
4. Railway auto-deploys!
5. Wait ~5 minutes (first build)
6. ✅ Done!
```

**Τι γίνεται κατά το build:**
- Railway βρίσκει requirements.txt
- Κατεβάζει Python 3.11
- Εγκαθιστά όλα τα packages
- Τρέχει το app.py
- Generates domain

---

### 4️⃣ Get API URL (30 δευτερόλεπτα)

```
1. Railway Dashboard → Your Project
2. Settings → Domain
3. Click "Generate Domain"
4. Copy URL: https://your-app.railway.app
5. ✅ Done!
```

---

### 5️⃣ Test API (2 λεπτά)

**Test 1: Health Check**
```bash
curl https://your-app.railway.app/health
```

**Expected:**
```json
{
  "status": "healthy",
  "service": "neural-search-api"
}
```

**Test 2: Train Model**

Χρησιμοποίησε το Staff Gallery XML που έχεις ήδη:

```bash
curl -X POST https://your-app.railway.app/train \
  -H "Content-Type: application/json" \
  -d '{
    "shop_id": "beagle",
    "xml": "<products>YOUR_XML_HERE</products>"
  }'
```

**Expected:**
```json
{
  "success": true,
  "shop_id": "beagle",
  "products_count": 150
}
```

**Test 3: Search**
```bash
curl "https://your-app.railway.app/search?shop_id=beagle&q=μαύρο+τζιν"
```

**Expected:**
```json
{
  "success": true,
  "results": [
    {
      "name": "Ashley Slim Fit...",
      "price": "62.97",
      "score": 0.92
    }
  ]
}
```

✅ **If all 3 tests pass → Production Ready!**

---

## 🐛 Troubleshooting

### Build Failed?
```
Check Railway logs:
- Dashboard → Deployments → View Logs
- Common fix: Wait 5 minutes, retry
```

### Timeout?
```
First request slow (model loading)
Solution: Send 2nd request, will be fast!
```

### Out of Memory?
```
Railway Hobby: 8GB RAM (enough για 20+ shops)
If OOM: Upgrade to Pro plan
```

---

## 📊 Monitor

Railway Dashboard shows real-time:
- ✅ Deployment status
- 📈 CPU/Memory usage
- 📋 Request logs
- 🔄 Auto-restarts

---

## 🚀 Production Checklist

- [ ] Railway account created
- [ ] Code deployed
- [ ] Domain generated
- [ ] `/health` returns 200 OK
- [ ] First shop trained successfully
- [ ] Search works και επιστρέφει results
- [ ] API URL saved σε OpenCart config
- [ ] 🎉 **Ready για production!**

---

## 💡 Tips

**Tip 1: Keep Alive**
```
Railway free tier = sleep after 30 min inactivity
Solution: Ping /health every 10 minutes
```

**Tip 2: Multiple Shops**
```
Ένας server → πολλά shops!
shop_id=beagle → model_beagle.json
shop_id=client2 → model_client2.json
Cost: €7 ÷ 10 shops = €0.70/shop! 🎯
```

**Tip 3: Updates**
```
Push to GitHub → Railway auto-redeploys!
Zero downtime deployments ✅
```

---

## 📞 Help?

**Railway Support:**
- Docs: https://docs.railway.app
- Discord: https://discord.gg/railway

**API Issues:**
- Check logs στο Railway Dashboard
- Test locally πρώτα: `python app.py`
- Run test suite: `python test_api.py`

---

## ⏱️ Total Time: ~10 minutes

1. Railway signup: 2 min
2. Upload code: 3 min
3. Deploy: 5 min
4. Test: 2 min
5. **Production Ready!** 🚀

---

## 🎯 Next Steps

After deployment:
1. Save API URL
2. Integrate με OpenCart (see README.md)
3. Test από chatbot
4. Scale to multiple shops
5. Monitor & optimize

**Let's Go!** 🚀
