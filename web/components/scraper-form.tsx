"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Progress } from "@/components/ui/progress"
import { Download, Loader2 } from "lucide-react"

interface ScrapeJob {
  id: string
  status: 'pending' | 'running' | 'completed' | 'error'
  progress: number
  message: string
  totalProducts: number
  currentProduct: number
}

export default function ScraperForm() {
  const [url, setUrl] = useState("")
  const [manufacturer, setManufacturer] = useState("")
  const [limit, setLimit] = useState("50")
  const [job, setJob] = useState<ScrapeJob | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")

  const startScraping = async () => {
    if (!url || !manufacturer) {
      setError("Please fill in both URL and Manufacturer name")
      return
    }

    setIsLoading(true)
    setError("")
    setJob(null)

    try {
      const response = await fetch('/api/scrape', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url,
          manufacturer,
          limit: parseInt(limit) || 50
        })
      })

      if (!response.ok) {
        throw new Error('Failed to start scraping')
      }

      const { jobId } = await response.json()
      
      // Start polling for progress
      pollProgress(jobId)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
      setIsLoading(false)
    }
  }

  const pollProgress = async (jobId: string) => {
    const eventSource = new EventSource(`/api/scrape/${jobId}/progress`)
    
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data)
      setJob(data)
      
      if (data.status === 'completed' || data.status === 'error') {
        eventSource.close()
        setIsLoading(false)
      }
    }

    eventSource.onerror = () => {
      eventSource.close()
      setError('Connection lost')
      setIsLoading(false)
    }
  }

  const downloadResults = async () => {
    if (!job?.id) return

    try {
      const response = await fetch(`/api/download/${job.id}`)
      if (!response.ok) throw new Error('Download failed')
      
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `hvac-scraper-results-${job.id}.zip`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err) {
      setError('Download failed')
    }
  }

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-6">
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold">HVAC Product Scraper</h1>
        <p className="text-muted-foreground">
          Extract specifications from any HVAC manufacturer website
        </p>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">
            Manufacturer URL
          </label>
          <Input
            type="url"
            placeholder="https://www.aaon.com/products/"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={isLoading}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">
            Manufacturer Name
          </label>
          <Input
            placeholder="AAON"
            value={manufacturer}
            onChange={(e) => setManufacturer(e.target.value)}
            disabled={isLoading}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">
            Max Products (optional)
          </label>
          <Input
            type="number"
            placeholder="50"
            value={limit}
            onChange={(e) => setLimit(e.target.value)}
            disabled={isLoading}
          />
        </div>

        {error && (
          <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-md text-destructive text-sm">
            {error}
          </div>
        )}

        <Button 
          onClick={startScraping} 
          disabled={isLoading}
          className="w-full"
        >
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Starting Scraper...
            </>
          ) : (
            'Start Scraping'
          )}
        </Button>

        {job && (
          <div className="space-y-4 p-4 bg-muted/50 rounded-lg">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Progress</span>
                <span>{job.progress}%</span>
              </div>
              <Progress value={job.progress} className="h-2" />
            </div>

            <div className="text-sm text-muted-foreground">
              {job.message}
            </div>

            {job.status === 'completed' && (
              <Button onClick={downloadResults} className="w-full">
                <Download className="mr-2 h-4 w-4" />
                Download Results (ZIP)
              </Button>
            )}

            {job.status === 'error' && (
              <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-md text-destructive text-sm">
                Scraping failed. Please try again.
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

