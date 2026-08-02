import { defineConfig, loadEnv } from 'vite'
import fs from 'node:fs'
import path from 'node:path'
import os from 'node:os'
import crypto from 'node:crypto'

// Dev-only endpoints that let edit mode persist a drag to the vault.
// Both run ONLY inside `vite dev` (configureServer) — neither is ever part of
// the production build, so a deployed site has no auth/write path at all.
//
// Auth model: the password lives in .env (gitignored), never in a URL or the
// client bundle. POST /__tickets/login checks it and hands back a random
// session token; the client stores that token (not the password) and sends it
// on every /__tickets/update call. Tokens are in-memory only and reset when
// the dev server restarts.
function ticketWriterPlugin(env) {
  const VAULT = process.env.VAULT || path.join(os.homedir(), 'Downloads', '2026')
  const TICKETS_DIR = path.join(VAULT, 'Tickets')
  const PASSWORD = env.TICKETS_EDIT_PASSWORD
  const VALID_STATUS = new Set(['backlog', 'todo', 'doing', 'done'])
  const sessions = new Set()

  function readJsonBody(req) {
    return new Promise((resolve, reject) => {
      let body = ''
      req.on('data', (c) => { body += c })
      req.on('end', () => {
        try { resolve(JSON.parse(body || '{}')) } catch (err) { reject(err) }
      })
    })
  }

  return {
    name: 'ticket-writer',
    apply: 'serve',
    configureServer(server) {
      server.middlewares.use('/__tickets/login', async (req, res) => {
        if (req.method !== 'POST') {
          res.statusCode = 405
          return res.end('Method Not Allowed')
        }
        if (!PASSWORD) {
          res.statusCode = 500
          return res.end(JSON.stringify({ error: 'TICKETS_EDIT_PASSWORD not set in .env' }))
        }
        try {
          const { password } = await readJsonBody(req)
          if (password !== PASSWORD) {
            res.statusCode = 403
            return res.end(JSON.stringify({ error: 'wrong password' }))
          }
          const token = crypto.randomBytes(24).toString('base64url')
          sessions.add(token)
          res.statusCode = 200
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify({ token }))
        } catch (err) {
          res.statusCode = 500
          res.end(JSON.stringify({ error: String(err) }))
        }
      })

      server.middlewares.use('/__tickets/update', async (req, res) => {
        if (req.method !== 'POST') {
          res.statusCode = 405
          return res.end('Method Not Allowed')
        }
        try {
          const { id, status, token } = await readJsonBody(req)

          if (!token || !sessions.has(token)) {
            res.statusCode = 403
            return res.end(JSON.stringify({ error: 'not authenticated' }))
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
    },
  }
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  return {
    plugins: [ticketWriterPlugin(env)],
    server: {
      open: true,
      port: 3000
    },
    build: {
      outDir: 'dist',
      assetsDir: 'assets',
    },
    publicDir: 'public'
  }
})
