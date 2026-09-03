# 3D Interactive Portfolio

A modern Three.js-powered 3D portfolio with interactive objects, glass morphism design, and engaging user experience.

## Features

- **Interactive 3D Model**: Hover and click on objects throughout the virtual room
- **Modern Glass Morphism UI**: Beautiful popups with backdrop blur effects
- **Engaging Loading Screen**: Animated logo and progress bar
- **Welcome Experience**: Guided introduction to the portfolio
- **Responsive Design**: Works on desktop and mobile devices
- **Click Interactions**: Interactive objects reveal different content:
  - 📄 **Resume**: Opens PDF in new tab
  - 👤 **About Objects**: Detailed about me information
  - 💻 **Tech Objects**: Project showcase and portfolio
  - 📱 **Contact Items**: Contact information and social links
  - 🌍 **Location Items**: Background and origin story
  - 📝 **Notebook**: Papers read and things learned, as in-site explainer pages
  - 📋 **Ticket Board** (iPad): Stories, Board, and Study tabs

## Performance Optimizations

- **Draco Compression**: Model optimized for web delivery
- **Enhanced Materials**: Optimized lighting response
- **Efficient Raycasting**: Only checks interactive objects
- **Modern Loading Screen**: Engaging user experience

## Technologies Used

- **Three.js** - 3D graphics library
- **Vite** - Build tool and development server
- **Vanilla JavaScript** - No framework dependencies

## Getting Started

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

3. Build for production:
   ```bash
   npm run build
   ```

4. Preview production build:
   ```bash
   npm run preview
   ```

## Vault-backed content

Two tabs on the ticket board are generated from the Obsidian vault at
`~/Downloads/2026` (override with the `VAULT` env var). In both cases the vault
is the single source of truth and the site is **read-only** — nothing in the
browser ever writes back.

| Tab | Script | Output | Vault source |
| --- | --- | --- | --- |
| Stories / Board | `npm run tickets` | `public/tickets.json` | `Tickets/`, `Projects/` |
| Study | `npm run study` | `public/study-plan.json` | `Study plan/` |

Both run automatically as part of `npm run dev` and `npm run build`. On a deploy
box without the vault, each script leaves the committed JSON untouched rather
than blanking the view.

### Study plan

The Study tab is a GitHub-contributions-style grid over a daily study schedule.

```
Study plan/
  plan.md              # | date | phase | task | implement | table, one row per day
  notes/
    2026-09-04.md      # frontmatter `date:` + `done:`, then free-form markdown
```

A cell is green when a note exists for that date with `done: true`. Past days
without one render as empty; future days are dashed, so a missed day is visually
distinguishable from one that has not happened yet. Sundays are muted rest days
with no popover. Note bodies support LaTeX (rendered with KaTeX) and wikilinks
(brackets stripped, not resolved).

To publish after writing notes in Obsidian:

```bash
npm run study:publish   # rebuild the JSON, commit it, and push
```

Only `Study plan/` is read — no other vault folder is touched, so nothing else
can leak into the site.

## Controls

- **Mouse/Touch**: Rotate the camera around the model
- **Scroll/Pinch**: Zoom in and out
- **Click Objects**: Interactive elements throughout the room
- **Hover Effects**: Visual feedback on interactive objects

## File Structure

- `index.html` - Main HTML file with modern loading screen
- `style.css` - Modern CSS with glass morphism and animations
- `src/main.js` - Clean, production-ready JavaScript application
- `src/study.js` - Study plan grid (read-only, renders `public/study-plan.json`)
- `scripts/build-tickets.js` - Publishes public tickets from the vault
- `scripts/build-study-plan.js` - Publishes the study plan from the vault
- `public/portfolio.glb` - Optimized 3D room model
- `public/Nazym Zhiyengaliyeva Resume.pdf` - Resume file
