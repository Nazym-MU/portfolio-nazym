#!/usr/bin/env node

const gltfPipeline = require('gltf-pipeline');
const fsExtra = require('fs-extra');
const path = require('path');

const processGlb = gltfPipeline.processGlb;

async function compressModel() {
    const inputPath = path.join(__dirname, 'public', 'portfolio.glb');
    const outputPath = path.join(__dirname, 'public', 'portfolio-compressed.glb');
    const backupPath = path.join(__dirname, 'public', 'portfolio-original.glb');
    
    try {
        // Check if input file exists
        if (!await fsExtra.pathExists(inputPath)) {
            console.error('Error: portfolio.glb not found in public folder');
            return;
        }
        
        // Get original file size
        const originalStats = await fsExtra.stat(inputPath);
        const originalSizeMB = (originalStats.size / (1024 * 1024)).toFixed(2);
        console.log(`📁 Original file size: ${originalSizeMB} MB`);
        
        // Read the GLB file
        console.log('📖 Reading GLB file...');
        const glb = await fsExtra.readFile(inputPath);
        
        // Compression options
        const options = {
            dracoOptions: {
                compressionLevel: 10, // Maximum compression (0-10)
                quantizePositionBits: 14,
                quantizeNormalBits: 10,
                quantizeTexcoordBits: 12,
                quantizeColorBits: 8,
                quantizeGenericBits: 12,
                unifiedQuantization: false
            },
            // Additional optimizations
            keepUnusedVertices: false,
            keepLegacyExtensions: false,
            // Texture compression
            compressTextures: true,
            textureCompressionOptions: {
                format: 'auto',
                quality: 0.8
            }
        };
        
        console.log('Compressing with Draco compression...');
        console.log('Compression settings:', {
            compressionLevel: options.dracoOptions.compressionLevel,
            quantizePositionBits: options.dracoOptions.quantizePositionBits,
            quantizeNormalBits: options.dracoOptions.quantizeNormalBits
        });
        
        // Process the GLB with compression
        const results = await processGlb(glb, options);
        
        // Create backup of original file
        console.log('Creating backup of original file...');
        await fsExtra.copy(inputPath, backupPath);
        
        // Write compressed file
        console.log('Saving compressed file...');
        await fsExtra.writeFile(outputPath, results.glb);
        
        // Get compressed file size
        const compressedStats = await fsExtra.stat(outputPath);
        const compressedSizeMB = (compressedStats.size / (1024 * 1024)).toFixed(2);
        const compressionRatio = ((1 - compressedStats.size / originalStats.size) * 100).toFixed(1);
        
        
    } catch (error) {
        console.error('Error during compression:', error.message);
        if (error.stack) {
            console.error('Stack trace:', error.stack);
        }
    }
}

// Install fs-extra if not present
async function checkDependencies() {
    try {
        require('fs-extra');
        return true;
    } catch (error) {
        console.log('📦 Installing required dependency: fs-extra');
        const { execSync } = require('child_process');
        execSync('npm install fs-extra', { stdio: 'inherit' });
        return true;
    }
}

// Run the script
checkDependencies().then(() => {
    compressModel();
}).catch(error => {
    console.error('Failed to install dependencies:', error.message);
});
