# HVAC Scraper Web UI

A simple web interface for the HVAC product scraper that allows users to input a manufacturer URL and download scraped results as a ZIP file.

## Features

- **Simple Form**: Just paste a URL and manufacturer name
- **Real-time Progress**: Watch scraping progress with live updates
- **ZIP Download**: Get all results (CSVs + PDFs) in one download
- **Mobile Friendly**: Works on all devices

## Quick Start

### Development

```bash
# Install dependencies
cd web
npm install

# Start development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to see the app.

### Production Deployment (Vercel)

**Option 1: Simple Deployment (Requires Vercel Pro)**
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy from project root
vercel --prod
```

**Option 2: Free Tier (Hybrid Setup)**
1. Deploy frontend to Vercel (free)
2. Deploy Python backend to Railway/Render
3. Update API endpoints to point to backend

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and update:

```env
# Python scraper configuration
PYTHON_PATH=/path/to/your/python/venv/bin/python
SCRAPER_ROOT=/path/to/your/scraper/project
MAX_CONCURRENT_JOBS=3
```

### Vercel Deployment

1. **Connect to Vercel**:
   - Push code to GitHub
   - Connect repository to Vercel
   - Set environment variables in Vercel dashboard

2. **Required Environment Variables**:
   ```
   PYTHON_PATH=/Users/ofeksuchard/load55-productimporter/.venv/bin/python
   SCRAPER_ROOT=/Users/ofeksuchard/load55-productimporter
   ```

3. **Vercel Pro Required**: 
   - Free tier has 10-second timeout (not enough for scraping)
   - Pro tier ($20/mo) has 5-minute timeout

## Architecture

### Frontend (Next.js)
- **Framework**: Next.js 14 with App Router
- **Styling**: Tailwind CSS + shadcn/ui components
- **State**: React hooks for form and progress state
- **Real-time**: Server-Sent Events for progress updates

### Backend (API Routes)
- **Scraping**: Spawns Python scraper as child process
- **Progress**: Streams real-time updates via SSE
- **Download**: Creates ZIP with all results
- **Cleanup**: Removes job files after download

### Python Integration
- **Process**: Node.js spawns Python scraper
- **Communication**: JSON progress output via stdout
- **Isolation**: Each job gets unique output directory
- **Cleanup**: Automatic file cleanup after download

## File Structure

```
web/
├── app/
│   ├── api/
│   │   ├── scrape/
│   │   │   ├── route.ts              # Start scraping
│   │   │   └── [jobId]/progress/route.ts  # Progress stream
│   │   └── download/[jobId]/route.ts # Download ZIP
│   ├── layout.tsx                     # Root layout
│   └── page.tsx                       # Home page
├── components/
│   ├── scraper-form.tsx               # Main form component
│   └── ui/                           # shadcn/ui components
├── lib/
│   └── utils.ts                       # Utility functions
└── package.json
```

## User Flow

1. **User opens website** → Sees clean form
2. **User enters URL and manufacturer** → Clicks "Start Scraping"
3. **Form validates** → Shows loading state
4. **Backend starts scraper** → Returns job ID
5. **UI connects to progress stream** → Shows real-time updates
6. **Scraper completes** → Download button appears
7. **User clicks download** → Gets ZIP with all files
8. **Backend cleanup** → Deletes job files after download

## Troubleshooting

### Common Issues

**"Command not found" errors**:
- Check `PYTHON_PATH` environment variable
- Ensure Python virtual environment is activated
- Verify scraper is installed correctly

**Timeout errors**:
- Upgrade to Vercel Pro for 5-minute timeout
- Or use hybrid setup with separate backend

**Progress not updating**:
- Check browser console for SSE connection errors
- Verify API routes are working correctly

**Download fails**:
- Check if job files exist in output directory
- Verify ZIP creation is working
- Check browser network tab for errors

### Development Tips

**Local Testing**:
```bash
# Test Python scraper directly
cd /Users/ofeksuchard/load55-productimporter
source .venv/bin/activate
python -m src.crawl --url "https://www.aaon.com/products/" --manufacturer "AAON" --limit 3 --progress-json
```

**Debug API Routes**:
```bash
# Test scraping endpoint
curl -X POST http://localhost:3000/api/scrape \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.aaon.com/products/","manufacturer":"AAON","limit":3}'
```

## Security Considerations

- **Input Validation**: All user inputs are validated
- **Rate Limiting**: Consider adding rate limiting for production
- **File Cleanup**: Job files are automatically cleaned up
- **Error Handling**: Graceful error messages for users

## Performance

- **Concurrent Jobs**: Limited by `MAX_CONCURRENT_JOBS` setting
- **Memory Usage**: Each job uses ~100MB (Playwright + Python)
- **Timeout**: 5 minutes max per job (Vercel Pro)
- **Cleanup**: Automatic cleanup prevents disk space issues

## Future Enhancements

- **Job Queue**: Redis-based job queue for better scaling
- **User Accounts**: Track scraping history
- **Email Notifications**: Notify when scraping completes
- **Custom Selectors**: UI for configuring CSS selectors
- **Scheduled Scraping**: Recurring scraping jobs