// electron/main.js
const { app, BrowserWindow } = require('electron');
const path = require('path');
const fs = require('fs');
const net = require('net');
const crypto = require('crypto');
const { spawn } = require('child_process');

const BACKEND_PORT = 5000;
const BACKEND_HOST = '127.0.0.1';

let mainWindow;
let splashWindow;
let backendProcess;
let backendReadyCheckInterval;

const isDev = !app.isPackaged;

// ---------------------------------------------------------------------------
// Resource paths — different in dev vs packaged (asar) mode
// ---------------------------------------------------------------------------
function resourcesRoot() {
  return isDev ? path.join(__dirname, '..') : process.resourcesPath;
}

function backendExePath() {
  const exeName = process.platform === 'win32'
    ? 'txretailos-backend.exe'
    : 'txretailos-backend';
  return path.join(resourcesRoot(), 'backend-dist', exeName);
}

function envFilePath() {
  // .env lives next to the backend so backend/config.py can find it via python-dotenv
  return isDev
    ? path.join(__dirname, '..', '.env')
    : path.join(app.getPath('userData'), '.env');
}

function databaseDir() {
  return isDev
    ? path.join(__dirname, '..', 'database')
    : path.join(app.getPath('userData'), 'database');
}

// ---------------------------------------------------------------------------
// First-run setup: generate .env automatically so the store owner never has
// to touch a config file (per FRONTEND_SPEC / QUICKSTART, but zero-manual-setup)
// ---------------------------------------------------------------------------
function ensureEnvFile() {
  const target = envFilePath();
  if (fs.existsSync(target)) return;

  fs.mkdirSync(path.dirname(target), { recursive: true });
  const secretKey = crypto.randomBytes(32).toString('hex');
  const jwtSecret = crypto.randomBytes(32).toString('hex');
  const dbPath = path.join(databaseDir(), 'shop.db').replace(/\\/g, '/');

  const envContents = [
    'FLASK_ENV=production',
    `SECRET_KEY=${secretKey}`,
    `JWT_SECRET_KEY=${jwtSecret}`,
    `DATABASE_URL=sqlite:///${dbPath}`,
    'DEBUG=False',
    'SYNC_ENABLED=False',
    `WAITRESS_HOST=${BACKEND_HOST}`,
    `WAITRESS_PORT=${BACKEND_PORT}`,
  ].join('\n');

  fs.writeFileSync(target, envContents, 'utf-8');
  fs.mkdirSync(databaseDir(), { recursive: true });
}

// ---------------------------------------------------------------------------
// Port availability check — required before we assume the backend can bind
// ---------------------------------------------------------------------------
function isPortFree(port, host) {
  return new Promise((resolve) => {
    const tester = net.createServer()
      .once('error', () => resolve(false))
      .once('listening', () => tester.close(() => resolve(true)))
      .listen(port, host);
  });
}

function waitForBackend(port, host, timeoutMs = 20000) {
  return new Promise((resolve, reject) => {
    const start = Date.now();
    backendReadyCheckInterval = setInterval(() => {
      const socket = net.createConnection(port, host);
      socket.on('connect', () => {
        socket.destroy();
        clearInterval(backendReadyCheckInterval);
        resolve();
      });
      socket.on('error', () => {
        socket.destroy();
        if (Date.now() - start > timeoutMs) {
          clearInterval(backendReadyCheckInterval);
          reject(new Error('Backend did not start in time'));
        }
      });
    }, 400);
  });
}

// ---------------------------------------------------------------------------
// Backend process — spawns the PyInstaller-built exe in production, or
// falls back to `python start_server.py` in dev
// ---------------------------------------------------------------------------
async function startBackend() {
  ensureEnvFile();

  const portFree = await isPortFree(BACKEND_PORT, BACKEND_HOST);
  if (!portFree) {
    throw new Error(
      `Port ${BACKEND_PORT} is already in use. Close any other running ` +
      `instance of TX RetailOS (or whatever is using that port) and try again.`
    );
  }

  const env = { ...process.env };

  if (!isDev && fs.existsSync(backendExePath())) {
    backendProcess = spawn(backendExePath(), [], {
      cwd: path.dirname(backendExePath()),
      env: { ...env, TXRETAILOS_ENV_PATH: envFilePath() },
      windowsHide: true, // run silently, no console window
    });
  } else {
    // Dev fallback — run straight from source with system Python
    const backendRoot = path.join(__dirname, '..');
    const pythonBin = process.platform === 'win32' ? 'python' : 'python3';
    backendProcess = spawn(pythonBin, ['start_server.py'], {
      cwd: backendRoot,
      env,
      windowsHide: true,
    });
  }

  backendProcess.stdout?.on('data', (d) => console.log(`[backend] ${d}`));
  backendProcess.stderr?.on('data', (d) => console.error(`[backend] ${d}`));
  backendProcess.on('exit', (code) => {
    console.log(`[backend] exited with code ${code}`);
    backendProcess = null;
  });
  backendProcess.on('error', (err) => {
    console.error('[backend] failed to start:', err);
  });

  await waitForBackend(BACKEND_PORT, BACKEND_HOST);
}

function stopBackend() {
  if (backendReadyCheckInterval) clearInterval(backendReadyCheckInterval);
  if (backendProcess) {
    if (process.platform === 'win32') {
      // taskkill ensures child processes spawned by the exe are also cleaned up
      spawn('taskkill', ['/pid', backendProcess.pid, '/f', '/t']);
    } else {
      backendProcess.kill('SIGTERM');
    }
    backendProcess = null;
  }
}

// ---------------------------------------------------------------------------
// Windows
// ---------------------------------------------------------------------------
function createSplashWindow() {
  splashWindow = new BrowserWindow({
    width: 420,
    height: 280,
    frame: false,
    resizable: false,
    center: true,
    show: true,
    backgroundColor: '#0B0D10',
    webPreferences: { contextIsolation: true },
  });
  splashWindow.loadFile(path.join(__dirname, 'loading.html'));
}

function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 960,
    minHeight: 640,
    show: false,
    autoHideMenuBar: true, // hides File/Edit/View menu bar
    icon: path.join(__dirname, '..', 'assets', 'icon.ico'),
    title: 'TX RetailOS',
    backgroundColor: '#0B0D10',
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, 'preload.js'),
    },
  });

  mainWindow.setMenuBarVisibility(false);
  mainWindow.loadURL(`http://${BACKEND_HOST}:${BACKEND_PORT}/`);

  mainWindow.once('ready-to-show', () => {
    if (splashWindow) splashWindow.close();
    mainWindow.show();
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function showErrorAndQuit(message) {
  const { dialog } = require('electron');
  if (splashWindow) splashWindow.close();
  dialog.showErrorBox('TX RetailOS — Startup Error', message);
  app.quit();
}

// ---------------------------------------------------------------------------
// App lifecycle
// ---------------------------------------------------------------------------
app.whenReady().then(async () => {
  createSplashWindow();
  try {
    await startBackend();
    createMainWindow();
  } catch (err) {
    showErrorAndQuit(err.message || String(err));
  }
});

app.on('window-all-closed', () => {
  stopBackend();
  if (process.platform !== 'darwin') app.quit();
});

app.on('before-quit', () => {
  stopBackend();
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createMainWindow();
});