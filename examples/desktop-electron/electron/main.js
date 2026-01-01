/**
 * Analytica Desktop - Electron Main Process
 */

const { app, BrowserWindow, ipcMain, Menu, Tray, Notification, shell } = require('electron');
const path = require('path');

let mainWindow;
let tray;

// API configuration
const API_BASE = process.env.API_URL || 'http://localhost:18000';

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        minWidth: 800,
        minHeight: 600,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            nodeIntegration: false,
            sandbox: true
        },
        icon: path.join(__dirname, '../assets/icon.png'),
        titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default',
        backgroundColor: '#1e293b',
        show: false
    });

    // Load the app
    if (process.env.NODE_ENV === 'development') {
        mainWindow.loadURL('http://localhost:3000');
        mainWindow.webContents.openDevTools();
    } else {
        mainWindow.loadFile(path.join(__dirname, '../src/index.html'));
    }

    // Show when ready
    mainWindow.once('ready-to-show', () => {
        mainWindow.show();
    });

    // Handle external links
    mainWindow.webContents.setWindowOpenHandler(({ url }) => {
        shell.openExternal(url);
        return { action: 'deny' };
    });

    // Create menu
    createMenu();
}

function createMenu() {
    const template = [
        {
            label: 'File',
            submenu: [
                { label: 'New Analysis', accelerator: 'CmdOrCtrl+N', click: () => sendToRenderer('new-analysis') },
                { label: 'Open...', accelerator: 'CmdOrCtrl+O', click: () => sendToRenderer('open-file') },
                { type: 'separator' },
                { label: 'Save', accelerator: 'CmdOrCtrl+S', click: () => sendToRenderer('save') },
                { label: 'Export...', click: () => sendToRenderer('export') },
                { type: 'separator' },
                { role: 'quit' }
            ]
        },
        {
            label: 'Edit',
            submenu: [
                { role: 'undo' },
                { role: 'redo' },
                { type: 'separator' },
                { role: 'cut' },
                { role: 'copy' },
                { role: 'paste' }
            ]
        },
        {
            label: 'View',
            submenu: [
                { role: 'reload' },
                { role: 'toggleDevTools' },
                { type: 'separator' },
                { role: 'resetZoom' },
                { role: 'zoomIn' },
                { role: 'zoomOut' },
                { type: 'separator' },
                { role: 'togglefullscreen' }
            ]
        },
        {
            label: 'Tools',
            submenu: [
                { label: 'Investment Calculator', click: () => sendToRenderer('tool-investment') },
                { label: 'Budget Planner', click: () => sendToRenderer('tool-budget') },
                { label: 'Forecast Generator', click: () => sendToRenderer('tool-forecast') },
                { type: 'separator' },
                { label: 'DSL Editor', click: () => sendToRenderer('tool-dsl') }
            ]
        },
        {
            label: 'Help',
            submenu: [
                { label: 'Documentation', click: () => shell.openExternal('https://analytica.io/docs') },
                { label: 'DSL Reference', click: () => shell.openExternal('https://analytica.io/docs/dsl') },
                { type: 'separator' },
                { label: 'About Analytica', click: () => sendToRenderer('about') }
            ]
        }
    ];

    const menu = Menu.buildFromTemplate(template);
    Menu.setApplicationMenu(menu);
}

function createTray() {
    tray = new Tray(path.join(__dirname, '../assets/tray-icon.png'));
    
    const contextMenu = Menu.buildFromTemplate([
        { label: 'Open Analytica', click: () => mainWindow.show() },
        { type: 'separator' },
        { label: 'Quick Investment Analysis', click: () => { mainWindow.show(); sendToRenderer('tool-investment'); } },
        { label: 'Quick Budget Check', click: () => { mainWindow.show(); sendToRenderer('tool-budget'); } },
        { type: 'separator' },
        { label: 'Quit', click: () => app.quit() }
    ]);
    
    tray.setToolTip('Analytica Desktop');
    tray.setContextMenu(contextMenu);
    
    tray.on('click', () => mainWindow.show());
}

function sendToRenderer(channel, data = {}) {
    if (mainWindow) {
        mainWindow.webContents.send(channel, data);
    }
}

// IPC Handlers

// Execute DSL pipeline
ipcMain.handle('execute-dsl', async (event, dsl, inputData = {}) => {
    try {
        const response = await fetch(`${API_BASE}/api/v1/pipeline/execute`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ dsl, input_data: inputData })
        });
        
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('DSL execution error:', error);
        return { error: error.message };
    }
});

// Validate DSL
ipcMain.handle('validate-dsl', async (event, dsl) => {
    try {
        const response = await fetch(`${API_BASE}/api/v1/pipeline/validate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ dsl })
        });
        return await response.json();
    } catch (error) {
        return { valid: false, error: error.message };
    }
});

// Show notification
ipcMain.handle('show-notification', (event, title, body) => {
    new Notification({ title, body }).show();
});

// App lifecycle
app.whenReady().then(() => {
    createWindow();
    createTray();
    
    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

// Security
app.on('web-contents-created', (event, contents) => {
    contents.on('will-navigate', (event, navigationUrl) => {
        const parsedUrl = new URL(navigationUrl);
        if (parsedUrl.origin !== 'http://localhost:3000' && parsedUrl.protocol !== 'file:') {
            event.preventDefault();
        }
    });
});
