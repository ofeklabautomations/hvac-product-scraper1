import { NextRequest, NextResponse } from 'next/server'
import { spawn } from 'child_process'
import { randomUUID } from 'crypto'
import fs from 'fs'
import path from 'path'

// In-memory job storage (in production, use Redis or database)
const jobs = new Map<string, any>()

export async function POST(request: NextRequest) {
  try {
    const { url, manufacturer, limit } = await request.json()

    if (!url || !manufacturer) {
      return NextResponse.json({ error: 'URL and manufacturer are required' }, { status: 400 })
    }

    const jobId = randomUUID()
    const outputDir = path.join(process.env.SCRAPER_ROOT || '/Users/ofeksuchard/load55-productimporter', 'output', 'jobs', jobId)

    // Ensure output directory exists
    fs.mkdirSync(outputDir, { recursive: true })

    // Store job info
    jobs.set(jobId, {
      id: jobId,
      status: 'pending',
      progress: 0,
      message: 'Starting scraper...',
      totalProducts: limit || 50,
      currentProduct: 0,
      outputDir
    })

    // Start Python scraper
    const pythonPath = process.env.PYTHON_PATH || '/Users/ofeksuchard/load55-productimporter/.venv/bin/python'
    const scraperPath = path.join(process.env.SCRAPER_ROOT || '/Users/ofeksuchard/load55-productimporter', 'src')
    
    const child = spawn(pythonPath, [
      '-m', 'src.crawl',
      '--url', url,
      '--manufacturer', manufacturer,
      '--limit', (limit || 50).toString(),
      '--output-dir', outputDir,
      '--progress-json'
    ], {
      cwd: process.env.SCRAPER_ROOT || '/Users/ofeksuchard/load55-productimporter'
    })

    // Handle scraper output
    child.stdout.on('data', (data) => {
      const lines = data.toString().split('\n')
      for (const line of lines) {
        if (line.trim() && line.startsWith('{')) {
          try {
            const progress = JSON.parse(line)
            jobs.set(jobId, {
              ...jobs.get(jobId),
              ...progress
            })
          } catch (e) {
            // Ignore non-JSON lines
          }
        }
      }
    })

    child.stderr.on('data', (data) => {
      console.error(`Scraper error: ${data}`)
    })

    child.on('close', (code) => {
      const job = jobs.get(jobId)
      if (job) {
        if (code === 0) {
          jobs.set(jobId, {
            ...job,
            status: 'completed',
            progress: 100,
            message: 'Scraping completed successfully!'
          })
        } else {
          jobs.set(jobId, {
            ...job,
            status: 'error',
            message: 'Scraping failed'
          })
        }
      }
    })

    return NextResponse.json({ jobId })

  } catch (error) {
    console.error('Scraper API error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

