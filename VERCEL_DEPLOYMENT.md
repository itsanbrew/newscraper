# Vercel Deployment Guide

This guide explains how to deploy the News Scraper application to Vercel.

## Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **Vercel CLI**: Install with `npm i -g vercel`
3. **GitHub Repository**: Push your code to GitHub

## Environment Variables

Set up the following environment variable in Vercel:

1. Go to your Vercel project dashboard
2. Navigate to Settings > Environment Variables
3. Add: `ROCKETREACH_API_KEY` with your RocketReach API key

## Deployment Steps

### Option 1: Deploy via Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login

# Deploy from project directory
vercel

# Follow the prompts:
# - Set up and deploy? Yes
# - Which scope? [Your account]
# - Link to existing project? No
# - Project name? news-scraper (or your preferred name)
# - Directory? ./
# - Override settings? No
```

### Option 2: Deploy via GitHub Integration

1. Connect your GitHub repository to Vercel
2. Import the repository
3. Vercel will automatically detect the Python configuration
4. Set environment variables in the Vercel dashboard
5. Deploy

## Project Structure

```
/
├── api/
│   └── index.py              # Vercel serverless function
├── dashboard/
│   ├── index.html            # Frontend dashboard
│   ├── script.js             # Frontend JavaScript
│   └── style.css             # Frontend styles
├── integrations/
│   └── rocketreach.py        # RocketReach API integration
├── newsplease_simple/        # Simplified news-please module
├── scripts/
│   └── run_scraper.py        # Main scraping script
├── utils/
│   ├── email_validation.py   # Email validation utilities
│   └── exporters.py          # CSV export utilities
├── vercel.json               # Vercel configuration
├── requirements-vercel.txt   # Python dependencies
└── .vercelignore            # Files to ignore in deployment
```

## API Endpoints

Once deployed, your application will be available at:
- **Dashboard**: `https://your-project.vercel.app/`
- **API**: `https://your-project.vercel.app/api/`

### Available Endpoints:

- `POST /api/run_scraper` - Start scraping
- `GET /api/results` - Get results as JSON
- `GET /api/download/csv` - Download CSV
- `GET /api/download/json` - Download JSON
- `GET /api/status` - Get scraping status
- `GET /api/logs` - Get scraping logs
- `POST /api/delete_results` - Delete all results
- `GET /api/health` - Health check

## Configuration

### Vercel Configuration (`vercel.json`)

The `vercel.json` file configures:
- Python serverless functions for API endpoints
- Static file serving for the dashboard
- Environment variable mapping
- Route handling

### Dependencies (`requirements-vercel.txt`)

Contains only the essential Python packages needed for Vercel deployment:
- Flask and Flask-CORS for the API
- Pandas for data handling
- News scraping libraries
- Email validation tools

## Usage

1. **Access the Dashboard**: Visit your Vercel URL
2. **Enter URLs**: Paste one or more URLs in the input field
3. **Run Scraper**: Click "Run" to start scraping
4. **View Results**: See results in the table with contact enrichment
5. **Download Data**: Use the download buttons to get CSV/JSON files
6. **Delete Results**: Clear all data with the delete button

## Troubleshooting

### Common Issues:

1. **Environment Variables**: Ensure `ROCKETREACH_API_KEY` is set
2. **Timeout**: Vercel has a 10-second timeout for serverless functions
3. **Memory Limits**: Large scraping jobs may hit memory limits
4. **Cold Starts**: First request may be slower due to cold start

### Debugging:

- Check Vercel function logs in the dashboard
- Monitor API responses in browser developer tools
- Verify environment variables are properly set

## Limitations

- **Serverless Timeout**: 10-second limit per function execution
- **Memory**: 1024MB memory limit
- **File Storage**: Temporary files are cleared between requests
- **Concurrent Requests**: Limited by Vercel's plan

## Scaling

For production use with high volume:
- Consider upgrading to Vercel Pro plan
- Implement database storage instead of CSV files
- Use background job processing for large scraping tasks
- Implement proper error handling and retry logic
