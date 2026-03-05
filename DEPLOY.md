# Deploy to Vercel

## Prerequisites

1. [Vercel Account](https://vercel.com/signup) (Free tier available)
2. [Vercel CLI](https://vercel.com/docs/cli) installed:
   ```bash
   npm i -g vercel
   ```
3. Groq API Key (already in your .env file)

## Deployment Steps

### 1. Login to Vercel
```bash
vercel login
```

### 2. Add Environment Variable
Add your Groq API key to Vercel:
```bash
vercel env add GROQ_API_KEY
# Enter your API key when prompted
```

### 3. Deploy
```bash
cd "Mutual Funds - Cursor"
vercel --prod
```

### 4. Alternative: Deploy via Vercel Dashboard

1. Push your code to GitHub/GitLab/Bitbucket
2. Go to [vercel.com](https://vercel.com)
3. Click "Add New Project"
4. Import your repository
5. Configure:
   - Framework Preset: Other
   - Build Command: (leave empty)
   - Output Directory: Phase4/frontend
6. Add Environment Variable:
   - Name: `GROQ_API_KEY`
   - Value: Your Groq API key
7. Click "Deploy"

## Important Notes

### Vercel Limitations
- **Serverless Functions**: Backend runs as serverless functions (cold starts possible)
- **Timeout**: 10 seconds (Hobby plan) / 60 seconds (Pro plan)
- **Memory**: 1024 MB (Hobby plan)

### API Endpoint
After deployment, your API will be at:
```
https://your-project.vercel.app/api/chat
```

### CORS
The backend is configured to allow all origins (`["*"]`), so it will work with your deployed frontend.

### Data Persistence
- Fund data (`funds.jsonl`) is bundled with the deployment
- No database required - everything is read-only

## Troubleshooting

### Build Errors
If you get Python build errors:
1. Make sure `requirements.txt` is in the root directory
2. Check Python version in Vercel settings (should be 3.9+)

### API Not Working
1. Check environment variable is set: `vercel env ls`
2. Check logs: `vercel logs --tail`

### CORS Issues
The backend already has CORS enabled for all origins. If issues persist:
1. Check browser console for errors
2. Verify the API_URL in `main.js` is correct

## Post-Deployment

Once deployed, you can:
1. Access your app at `https://your-project.vercel.app`
2. Share the URL with others
3. Monitor usage in Vercel Dashboard

## Free Tier Limits (Hobby Plan)

- **Serverless Functions**: 100 GB-hours
- **Bandwidth**: 100 GB
- **Builds**: 6000 minutes/month

For a simple FAQ chatbot, this should be more than sufficient!
