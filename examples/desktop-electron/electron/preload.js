/**
 * Analytica Desktop - Preload Script
 * Exposes safe APIs to renderer process
 */

const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods to renderer
contextBridge.exposeInMainWorld('analytica', {
    // Execute DSL pipeline
    executeDSL: (dsl, inputData) => ipcRenderer.invoke('execute-dsl', dsl, inputData),
    
    // Validate DSL syntax
    validateDSL: (dsl) => ipcRenderer.invoke('validate-dsl', dsl),
    
    // Show native notification
    notify: (title, body) => ipcRenderer.invoke('show-notification', title, body),
    
    // Listen for menu commands
    onMenuAction: (callback) => {
        const channels = [
            'new-analysis', 'open-file', 'save', 'export',
            'tool-investment', 'tool-budget', 'tool-forecast', 'tool-dsl',
            'about'
        ];
        
        channels.forEach(channel => {
            ipcRenderer.on(channel, (event, data) => callback(channel, data));
        });
    },
    
    // App info
    platform: process.platform,
    version: process.env.npm_package_version || '1.0.0'
});

// Log when preload is ready
console.log('Analytica Desktop: Preload script loaded');
