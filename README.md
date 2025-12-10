# Neural Search API - Railway Deployment Guide

Multi-tenant Neural Search API για OpenCart Chatbot

## 🚀 Quick Start

### 1. Railway Account Setup

1. Πήγαινε στο **https://railway.app**
2. Κάνε Sign Up με GitHub account
3. Verify email

### 2. Deployment Options

#### **Option A: Deploy από GitHub (Recommended)**

1. **Upload code to GitHub:**
   ```bash
   # Create new repo on GitHub
   # Then:
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/neural-search-api.git
   git push -u origin main
   ```

2. **Deploy στο Railway:**
   - Railway Dashboard → "New Project"
   - "Deploy from GitHub repo"
   - Select your repo
   - Railway auto-detects Python και κάνει deploy!

#### **Option B: Deploy με Railway CLI**

1. **Install Railway CLI:**
   ```bash
   npm install -g @railway/cli
   # ή
   curl -fsSL https://railway.app/install.sh | sh
   ```

2. **Login:**
   ```bash
   railway login
   ```

3. **Deploy:**
   ```bash
   cd neural_search_api
   railway init
   railway up
   ```

#### **Option C: Direct Upload (Easiest for testing)**

1. Railway Dashboard → "New Project"
2. "Deploy from local directory"
3. Select `neural_search_api` folder
4. Deploy!

### 3. Get Your API URL

Μετά το deployment:
- Railway Dashboard → Your Project
- Settings → Domain → Generate Domain
- Copy το URL: `https://your-app.railway.app`

---

## 📡 API Endpoints

Base URL: `https://your-app.railway.app`

### 1. Health Check
```bash
GET /health

Response:
{
  "status": "healthy",
  "service": "neural-search-api",
  "version": "1.0.0"
}
```

### 2. Train Model
```bash
POST /train
Content-Type: application/json

{
  "shop_id": "shop1",
  "xml": "<products><product>...</product></products>"
}

Response:
{
  "success": true,
  "shop_id": "shop1",
  "products_count": 150,
  "trained_at": 1733850000
}
```

### 3. Search Products
```bash
GET /search?shop_id=shop1&q=μαύρο+τζιν&limit=5

Response:
{
  "success": true,
  "shop_id": "shop1",
  "query": "μαύρο τζιν",
  "results": [
    {
      "id": "123",
      "name": "Ashley Slim Fit Τζιν",
      "model": "ASH-001",
      "description": "Μαύρο slim fit τζιν...",
      "category": "Jeans",
      "price": "62.97",
      "image": "https://...",
      "url": "https://...",
      "score": 0.92,
      "neural_score": 0.89,
      "fuzzy_score": 0.98
    }
  ],
  "count": 5
}
```

### 4. Check Training Status
```bash
GET /status?shop_id=shop1

Response:
{
  "trained": true,
  "shop_id": "shop1",
  "products_count": 150,
  "trained_at": 1733850000
}
```

### 5. List All Shops
```bash
GET /shops

Response:
{
  "shops": [
    {
      "shop_id": "shop1",
      "products_count": 150,
      "trained_at": 1733850000
    },
    {
      "shop_id": "shop2",
      "products_count": 230,
      "trained_at": 1733860000
    }
  ],
  "count": 2
}
```

---

## 🔧 PHP Integration Example

```php
<?php
// config.php
define('NEURAL_SEARCH_API', 'https://your-app.railway.app');

// search.php
function neural_search($shop_id, $query, $limit = 5) {
    $url = NEURAL_SEARCH_API . '/search?' . http_build_query([
        'shop_id' => $shop_id,
        'q' => $query,
        'limit' => $limit
    ]);
    
    $response = file_get_contents($url);
    return json_decode($response, true);
}

// Usage
$results = neural_search('shop1', 'μαύρο τζιν');
foreach ($results['results'] as $product) {
    echo $product['name'] . ' - €' . $product['price'] . "\n";
}
?>
```

---

## 🏪 Multi-Tenant Usage

**Scenario: 10 shops on same server**

```bash
# Train shop 1
POST /train {"shop_id": "beagle", "xml": "..."}

# Train shop 2
POST /train {"shop_id": "client2", "xml": "..."}

# Search shop 1
GET /search?shop_id=beagle&q=τζιν

# Search shop 2
GET /search?shop_id=client2&q=φόρεμα
```

**Cost:** €7/μήνα total ÷ 10 shops = **€0.70/shop** 🎯

---

## 💰 Pricing & Scaling

| Shops | Railway Plan | Monthly Cost | Per Shop |
|-------|--------------|--------------|----------|
| 1-10 | Hobby ($5) | €7 | €0.70 |
| 10-30 | Pro ($20) | €24 | €0.80 |
| 30+ | Team ($100) | €120 | €4.00 |

**Railway Free Trial:** $5 credit (good for 1 month testing!)

---

## 🐛 Troubleshooting

### Build Fails
```bash
# Check logs in Railway dashboard
# Common issues:
# - Missing requirements.txt → Add it
# - Torch too large → Use torch==2.1.0 (smaller)
```

### Out of Memory
```bash
# Railway Hobby: 8GB RAM
# If OOM:
# 1. Upgrade to Pro (16GB)
# 2. Or use smaller model in app.py:
#    'paraphrase-multilingual-MiniLM-L12-v2' (default, 470MB)
```

### Slow Response
```bash
# First search is slow (model loading)
# Solution: Keep-alive ping every 5 minutes
# Or upgrade to Railway Pro (no cold starts)
```

---

## 🔐 Security Notes

- `shop_id` validated (alphanumeric only)
- No authentication needed (internal API)
- For production: Add API key authentication
- Use environment variables for secrets

---

## 📊 Monitoring

Railway Dashboard shows:
- CPU usage
- Memory usage
- Request logs
- Deployment history

---

## 🚀 Next Steps After Deployment

1. **Test API:**
   ```bash
   curl https://your-app.railway.app/health
   ```

2. **Train first shop:**
   - Export XML από OpenCart
   - POST to /train
   - Verify με /status

3. **Test search:**
   - GET /search με queries
   - Check response quality

4. **Integrate με OpenCart:**
   - Add NEURAL_SEARCH_API στο config
   - Update search_products() tool
   - Test από chatbot

---

## 📞 Support

Questions? Issues?
- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway

---

## ✅ Deployment Checklist

- [ ] Railway account created
- [ ] Code deployed (GitHub/CLI/Direct)
- [ ] Domain generated
- [ ] Health check passes
- [ ] First shop trained
- [ ] Search tested
- [ ] PHP integration done
- [ ] Production ready! 🎉
