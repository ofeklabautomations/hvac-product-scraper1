import { NextRequest } from 'next/server'
import JSZip from 'jszip'
import fs from 'fs'
import path from 'path'

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ jobId: string }> }
) {
  try {
    const { jobId } = await params
    const outputDir = path.join(process.env.SCRAPER_ROOT || '/Users/ofeksuchard/load55-productimporter', 'output', 'jobs', jobId)

    // Check if job directory exists
    if (!fs.existsSync(outputDir)) {
      return new Response('Job not found', { status: 404 })
    }

    // Create ZIP file
    const zip = new JSZip()
    
    // Add CSV files
    const csvFiles = ['products.csv', 'documents.csv', 'normalized_products.csv']
    for (const csvFile of csvFiles) {
      const csvPath = path.join(outputDir, csvFile)
      if (fs.existsSync(csvPath)) {
        const content = fs.readFileSync(csvPath, 'utf8')
        zip.file(csvFile, content)
      }
    }

    // Add PDF files
    const filesDir = path.join(outputDir, 'files')
    if (fs.existsSync(filesDir)) {
      const pdfFiles = fs.readdirSync(filesDir)
      for (const pdfFile of pdfFiles) {
        const pdfPath = path.join(filesDir, pdfFile)
        const content = fs.readFileSync(pdfPath)
        zip.file(`files/${pdfFile}`, content)
      }
    }

    // Generate ZIP buffer
    const zipBuffer = await zip.generateAsync({ type: 'nodebuffer' })

    // Clean up job files after download
    setTimeout(() => {
      try {
        fs.rmSync(outputDir, { recursive: true, force: true })
      } catch (e) {
        console.error('Failed to cleanup job files:', e)
      }
    }, 1000)

    return new Response(zipBuffer.buffer, {
      headers: {
        'Content-Type': 'application/zip',
        'Content-Disposition': `attachment; filename="hvac-scraper-results-${jobId}.zip"`,
        'Content-Length': zipBuffer.length.toString(),
      },
    })

  } catch (error) {
    console.error('Download error:', error)
    return new Response('Download failed', { status: 500 })
  }
}

