import { defineConfig } from 'vite'
import fs from 'node:fs'
import path from 'node:path'
import os from 'node:os'

// Dev-only endpoint that lets edit mode persist a drag to the vault.
// Runs ONLY inside `vite dev` (configureServer) — it is never part of the
// production build, so a deployed site has no write path at all. The edit key
// is the gate: it must match TICKETS_EDIT_KEY in the environment.
function ticketWriterPlugin() {
  const VAULT = process.env.VAULT || path.join(os.homedir(), 'Downloads', '2026')
  const TICKETS_DIR = path.join(VAULT, 'Tickets')
  const EXPECTED_KEY = process.env.TICKETS_EDIT_KEY || 'dev'
  const VALID_STATUS = new Set(['backlog', 'todo', 'doing', 'done'])

  return {
    name: 'ticket-writer',
    apply: 'serve',
    configureServer(server) {
      server.middlewares.use('/__tickets/update', (req, res) => {
        if (req.method !== 'POST') {
          res.statusCode = 405
          return res.end('Method Not Allowed')
        }
        let body = ''
        req.on('data', (c) => { body += c })
        req.on('end', () => {
          try {
            const { id, status, key } = JSON.parse(body || '{}')

            if (key !== EXPECTED_KEY) {
              res.statusCode = 403
              return res.end(JSON.stringify({ error: 'bad key' }))
            }
            if (!VALID_STATUS.has(status) || !/^[A-Za-z]+-\d+$/.test(id || '')) {
              res.statusCode = 400
              return res.end(JSON.stringify({ error: 'bad input' }))
            }

            // Find the ticket file whose frontmatter id matches.
            const files = fs.readdirSync(TICKETS_DIR).filter((f) => f.endsWith('.md'))
            const target = files.find((f) => {
              const raw = fs.readFileSync(path.join(TICKETS_DIR, f), 'utf8')
              return new RegExp(`^id:\\s*${id}\\s*$`, 'm').test(raw)
            })
            if (!target) {
              res.statusCode = 404
              return res.end(JSON.stringify({ error: 'ticket not found' }))
            }

            const filePath = path.join(TICKETS_DIR, target)
            const raw = fs.readFileSync(filePath, 'utf8')
            const updated = raw.replace(/^status:\s*.*$/m, `status: ${status}`)
            if (updated === raw && !/^status:/m.test(raw)) {
              res.statusCode = 422
              return res.end(JSON.stringify({ error: 'no status field' }))
            }
            fs.writeFileSync(filePath, updated)

            // Keep the served JSON in sync immediately so a reload is accurate.
            try {
              const outFile = path.join(process.cwd(), 'public', 'tickets.json')
              const payload = JSON.parse(fs.readFileSync(outFile, 'utf8'))
              const t = payload.tickets.find((x) => x.id === id)
              if (t) { t.status = status; fs.writeFileSync(outFile, JSON.stringify(payload, null, 2)) }
            } catch { /* non-fatal */ }

            res.statusCode = 200
            res.setHeader('Content-Type', 'application/json')
            res.end(JSON.stringify({ ok: true, id, status }))
          } catch (err) {
            res.statusCode = 500
            res.end(JSON.stringify({ error: String(err) }))
          }
        })
      })
    },
  }
}

export default defineConfig({
  plugins: [ticketWriterPlugin()],
  server: {
    open: true,
    port: 3000
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
  },
  publicDir: 'public'
})
