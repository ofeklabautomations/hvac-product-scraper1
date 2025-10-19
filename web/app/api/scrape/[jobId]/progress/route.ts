import { NextRequest } from 'next/server'

// In-memory job storage (same as in route.ts)
const jobs = new Map<string, { id: string; status: string; progress: number; message: string; totalProducts: number; currentProduct: number; outputDir: string }>()

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ jobId: string }> }
) {
  const { jobId } = await params

  const stream = new ReadableStream({
    start(controller) {
      const sendUpdate = () => {
        const job = jobs.get(jobId)
        if (job) {
          const data = `data: ${JSON.stringify(job)}\n\n`
          controller.enqueue(new TextEncoder().encode(data))
          
          if (job.status === 'completed' || job.status === 'error') {
            controller.close()
          }
        }
      }

      // Send initial update
      sendUpdate()

      // Poll for updates every 2 seconds
      const interval = setInterval(() => {
        const job = jobs.get(jobId)
        if (job && (job.status === 'completed' || job.status === 'error')) {
          clearInterval(interval)
          controller.close()
        } else {
          sendUpdate()
        }
      }, 2000)

      // Cleanup on close
      request.signal.addEventListener('abort', () => {
        clearInterval(interval)
        controller.close()
      })
    }
  })

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    },
  })
}

