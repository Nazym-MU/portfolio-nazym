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
  - 📝 **Blog Items**: Link to blog and writings

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

## Controls

- **Mouse/Touch**: Rotate the camera around the model
- **Scroll/Pinch**: Zoom in and out
- **Click Objects**: Interactive elements throughout the room
- **Hover Effects**: Visual feedback on interactive objects

## File Structure

- `index.html` - Main HTML file with modern loading screen
- `style.css` - Modern CSS with glass morphism and animations
- `src/main.js` - Clean, production-ready JavaScript application
- `public/portfolio.glb` - Optimized 3D room model
- `public/Nazym Zhiyengaliyeva Resume.pdf` - Resume file
