# 🚀 GitHub Pages Deployment Guide

## Overview

This guide will help you deploy the **Fraud Detection Dashboard** frontend demo to GitHub Pages with mock data.

---

## 🎯 What Gets Deployed

### ✅ Included:
- ✅ **Frontend UI** - All dashboard pages and components
- ✅ **Mock Data** - Pre-populated demo data
- ✅ **Charts & Visualizations** - All interactive charts
- ✅ **Dark Mode** - Full theme support
- ✅ **Network Graph** - Interactive fraud ring visualization
- ✅ **Map View** - Geographic fraud visualization
- ✅ **All Pages** - Dashboard, Analytics, Cases, RBAC, etc.

### ❌ Not Included:
- ❌ Backend API (FastAPI)
- ❌ Databases (Oracle, PostgreSQL, MongoDB, Redis)
- ❌ Real-time data
- ❌ Authentication (demo mode)
- ❌ ML model execution

---

## 📋 Prerequisites

- GitHub account
- Git installed locally
- Node.js 18+ installed
- Your code already pushed to GitHub

---

## 🔧 Setup Steps

### **Step 1: Enable GitHub Pages**

1. Go to your repository on GitHub:
   ```
   https://github.com/Safalguptaofficial/Ai-fraud-detection-dbms
   ```

2. Click **Settings** (top right)

3. Scroll down to **Pages** (left sidebar)

4. Under **Build and deployment**:
   - **Source**: Select "GitHub Actions"
   - Click **Save**

### **Step 2: Push the Configuration**

The configuration is already in your repository:
- ✅ `.github/workflows/deploy-pages.yml` - Deployment workflow
- ✅ `apps/web/next.config.js` - Static export config
- ✅ `apps/web/app/utils/demo-data.ts` - Mock data

Now commit and push:

```bash
cd /Users/safalgupta/Desktop/AI_FRAUD_DETECTION

# Add new files
git add .github/workflows/deploy-pages.yml
git add apps/web/next.config.js
git add apps/web/package.json
git add apps/web/app/utils/demo-data.ts
git add GITHUB_PAGES_DEPLOY.md

# Commit
git commit -m "🚀 Configure GitHub Pages deployment with demo data"

# Push
git push origin master
```

### **Step 3: Wait for Deployment**

1. Go to **Actions** tab in your repository
2. You'll see "Deploy to GitHub Pages" workflow running
3. Wait 2-5 minutes for build and deployment
4. Check for green checkmark ✅

### **Step 4: Access Your Demo**

Your site will be live at:
```
https://safalguptaofficial.github.io/Ai-fraud-detection-dbms/
```

---

## 🎨 What You'll See

### **Live Demo Features:**

1. **Dashboard** - Real-time fraud alerts (mock data)
   - Severity distribution charts
   - Account status overview
   - Recent alerts table

2. **Enhanced Analytics** - Advanced visualizations
   - Fraud trends over time
   - Risk distribution
   - Top merchants chart
   - Transaction heatmap

3. **Network Graph** - Interactive fraud ring visualization
   - Drag nodes to explore
   - Zoom and pan
   - Connection analysis

4. **Fraud Map** - Geographic visualization
   - Interactive Leaflet map
   - Fraud hotspots
   - Click markers for details

5. **Cases** - Case management UI
   - Create/view cases
   - Add notes
   - Status tracking

6. **RBAC** - User management
   - Role management
   - Permission control
   - User CRUD

7. **Investigation** - Investigation workspace
   - Timeline view
   - Evidence management
   - Collaboration tools

8. **ML Model** - ML predictions
   - Risk scoring
   - Feature importance
   - Explainability

9. **Dark Mode** - Full theme support
   - Toggle light/dark mode
   - Persistent preference

---

## 🔄 Update Your Demo

Whenever you make changes:

```bash
# 1. Make your changes
# 2. Commit and push
git add .
git commit -m "Update demo"
git push origin master

# 3. GitHub Actions will automatically rebuild and redeploy
```

---

## 🐛 Troubleshooting

### **Deployment Failed**

1. Check **Actions** tab for error logs
2. Common issues:
   - Build errors → Check `npm run build` locally
   - Missing dependencies → Run `npm install` in `apps/web`
   - Configuration errors → Verify `next.config.js`

### **Pages Not Found (404)**

1. Verify **GitHub Pages** is enabled in Settings
2. Check that workflow completed successfully
3. Wait a few minutes for DNS propagation

### **Images Not Loading**

- Ensure `basePath` in `next.config.js` matches your repo name
- Images must use `unoptimized: true` for static export

### **API Errors**

- Demo uses mock data, no backend needed
- If you see API errors, the app should fallback to mock data automatically

### **Local Build Test**

Test the static export locally:

```bash
cd apps/web

# Build static export
npm run build

# Serve locally (install serve if needed: npm install -g serve)
npx serve@latest out

# Open http://localhost:3000
```

---

## 🔧 Configuration Files

### **1. next.config.js**
```javascript
const nextConfig = {
  output: 'export',
  images: {
    unoptimized: true,
  },
  basePath: process.env.NODE_ENV === 'production' ? '/Ai-fraud-detection-dbms' : '',
  assetPrefix: process.env.NODE_ENV === 'production' ? '/Ai-fraud-detection-dbms/' : '',
}
```

### **2. GitHub Actions Workflow**
Location: `.github/workflows/deploy-pages.yml`

Triggers on:
- Push to `master` branch
- Manual workflow dispatch

### **3. Demo Data**
Location: `apps/web/app/utils/demo-data.ts`

Contains mock data for:
- Alerts
- Accounts
- Transactions
- Cases
- Analytics
- Network graph
- Fraud map
- Users
- Investigations
- ML predictions

---

## 📊 Demo Data

The demo includes:
- **847** simulated fraud alerts
- **234** active alerts
- **5** sample accounts
- **5** recent transactions
- **2** active investigations
- **3** user roles
- **6** geographic fraud locations
- **10** network graph nodes

---

## 🌐 Custom Domain (Optional)

To use a custom domain:

1. In repository **Settings** → **Pages**
2. Enter your custom domain
3. Add DNS records:
   - CNAME record pointing to `safalguptaofficial.github.io`
4. Enable HTTPS

---

## 📚 Next Steps

### **For Production Deployment:**

When ready for production with backend:
1. Deploy backend to Railway/Render/Heroku
2. Deploy databases
3. Update `NEXT_PUBLIC_API_URL` to point to your backend
4. Remove `basePath` from `next.config.js`
5. Deploy frontend to Vercel/Netlify

### **Alternative Hosting:**

- **Vercel** (Recommended for Next.js)
  - Connect GitHub repo
  - Auto-deploy on push
  - Serverless functions support

- **Netlify**
  - Static hosting
  - Fast global CDN
  - Easy rollbacks

- **Cloudflare Pages**
  - Free unlimited sites
  - Fast CDN
  - DDoS protection

---

## 🎯 Performance

GitHub Pages provides:
- ✅ Free hosting
- ✅ HTTPS by default
- ✅ CDN distribution
- ✅ Unlimited bandwidth
- ✅ 99.9% uptime

### **Optimization Tips:**

1. **Images**: Already using `unoptimized: true`
2. **Code splitting**: Next.js handles automatically
3. **Lazy loading**: Components load on demand
4. **Caching**: GitHub Pages caches static assets

---

## 📝 Notes

- **Demo Mode**: All data is mock data, no backend required
- **Updates**: Changes pushed to master auto-deploy in ~5 minutes
- **Free**: GitHub Pages is free for public repositories
- **SSL**: HTTPS enabled by default
- **SEO**: Static pages are SEO-friendly

---

## ✅ Checklist

Before deploying:
- [ ] Code pushed to GitHub
- [ ] GitHub Pages enabled in Settings
- [ ] Workflow file present (`.github/workflows/deploy-pages.yml`)
- [ ] `next.config.js` configured for static export
- [ ] `basePath` matches repository name
- [ ] Demo data file created

After deploying:
- [ ] Workflow completed successfully
- [ ] Site accessible at GitHub Pages URL
- [ ] All pages load correctly
- [ ] Dark mode works
- [ ] Charts render properly
- [ ] Map displays correctly

---

## 🆘 Support

If you encounter issues:
1. Check GitHub Actions logs
2. Review this guide
3. Test local build: `cd apps/web && npm run build`
4. Check Next.js static export docs

---

**Your demo will be live at:**
```
https://safalguptaofficial.github.io/Ai-fraud-detection-dbms/
```

**Repository:**
```
https://github.com/Safalguptaofficial/Ai-fraud-detection-dbms
```

Happy deploying! 🚀

