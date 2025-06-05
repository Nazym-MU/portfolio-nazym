# 3D Interactive Portfolio

A Three.js-powered 3D portfolio with interactive objects and optimized loading.

## Features

- **Interactive 3D Model**: Hover over objects to highlight them
- **Click Interactions**: Click on specific objects for actions:
  - 📄 **Resume**: Opens PDF in new tab
  - 💻 **MacBook**: Future projects showcase
  - 📱 **Phone**: Future contact info
  - 📓 **Notebook**: Future blog/notes
  - 🏀 **Ball, 1, 2**: Future animations
  - 🗺️ **Manchester, Map**: Future location info

## Performance Optimizations

- **Draco Compression**: Model compressed from 179.61 MB to 40.63 MB (77.4% reduction)
- **Optimized Materials**: Enhanced lighting response
- **Throttled Mouse Events**: Smooth 60fps interactions
- **Efficient Raycasting**: Only checks interactive objects

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

## Controls

- **Mouse/Touch**: Rotate the camera around the model
- **Scroll/Pinch**: Zoom in and out
- **Resume Button**: Click to open resume in a new tab

## File Structure

- `index.html` - Main HTML file
- `src/main.js` - Main JavaScript application
- `public/portfolio.glb` - 3D room model
- `public/Nazym Zhiyengaliyeva Resume.pdf` - Resume file
