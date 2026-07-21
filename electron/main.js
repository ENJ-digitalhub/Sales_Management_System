// electron/main.js
const { app, BrowserWindow, dialog } = require('electron');
const path = require('path');
const fs = require('fs');
const net = require('net');
const crypto = require('crypto');
const envContents = fs.readFileSync(envPath, 'utf-8')
.replace(/^WAITRESS_PORT=.*$/m, `WAITRESS_PORT=${resolvedBackendPort}`);
fs.writeFileSync(envPath, envContents, 'utf-8');
const { spawn } = require('child_process');

const BACKEND_PORT = 5000;
const BACKEND_HOST = '127.0.0.1';


let mainWindow;
let splashWindow;
let backendProcess;
let backendReadyCheckInterval;
let appIsQuitting = false;
let resolvedBackendPort = BACKEND_PORT;

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
// to hand-craft secrets. Default-user fields are left BLANK on purpose —
// ensure_default_user() (backend side) is a no-op until they're filled in,
// so the user can safely edit .env after first launch and just restart.
// ---------------------------------------------------------------------------
function ensureEnvFile() {
  const target = envFilePath();
  if (fs.existsSync(target)) {
    return { path: target, freshlyCreated: false };
  }

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
    '',
    '# --- Default user (auto-created on first run) ---',
    '# Fill these in, save this file, then restart TX RetailOS to create',
    '# your account. Leave blank to skip auto-creation entirely.',
    'APP_DEFAULT_USERNAME=',
    'APP_DEFAULT_PASSWORD=',
    'APP_DEFAULT_ROLE=admin',
    '',
  ].join('\n');

  fs.writeFileSync(target, envContents, 'utf-8');
  fs.mkdirSync(databaseDir(), { recursive: true });
  return { path: target, freshlyCreated: true };
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
  const { path: envPath, freshlyCreated } = ensureEnvFile();

  const portFree = async function findAvailablePort(startPort, host, maxAttempts = 10) {
    let port = startPort;
    for (let i = 0; i < maxAttempts; i++) {
      if (await isPortFree(port, host)) return port;
      port += 1;
    }
    throw new Error(
      `Could not find a free port between ${startPort} and ${startPort + maxAttempts - 1}. ` +
      `Close other applications and try again.`
    );
  }

  const env = {
    ...process.env,
    TXRETAILOS_ENV_PATH: envPath,
    WAITRESS_PORT: String(resolvedBackendPort),
  };

  if (!isDev && fs.existsSync(backendExePath())) {
    backendProcess = spawn(backendExePath(), [], {
      cwd: path.dirname(backendExePath()),
      env,
      windowsHide: false, // run silently, no console window
    });
  } else {
    // Dev fallback — run straight from source with system Python
    const backendRoot = path.join(__dirname, '..');
    const pythonBin = process.platform === 'win32' ? 'py' : 'python3';
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
    const wasRunning = !!backendProcess;
    backendProcess = null;
    // If the backend dies unexpectedly while the app is still open
    // (not during an intentional quit), tell the user instead of
    // leaving them staring at a dead window.
    if (wasRunning && !appIsQuitting && mainWindow) {
      dialog.showErrorBox(
        'TX RetailOS — Server Stopped',
        `The local server stopped unexpectedly (exit code ${code}). ` +
        `Please restart TX RetailOS.`
      );
      app.quit();
    }
  });
  backendProcess.on('error', (err) => {
    console.error('[backend] failed to start:', err);
  });

  await waitForBackend(BACKEND_PORT, BACKEND_HOST);
  return { envPath, freshlyCreated };
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

async function createMainWindow() {
  // backend already started by the caller — do NOT call startBackend() here
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 960,
    minHeight: 640,
    show: false,
    autoHideMenuBar: true,
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
  mainWindow.loadURL(`http://${BACKEND_HOST}:${resolvedBackendPort}/`); // see fix #3 below

  mainWindow.once('ready-to-show', () => {
    if (splashWindow) splashWindow.close();
    mainWindow.show();
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function showErrorAndQuit(message) {
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
    const { envPath, freshlyCreated } = await startBackend();
    await createMainWindow();

    if (freshlyCreated) {
      // First-ever launch: tell the user where .env lives so they can add
      // their default login, since the app boots successfully either way.
      dialog.showMessageBox(mainWindow, {
        type: 'info',
        title: 'First-time setup',
        message: 'TX RetailOS is ready.',
        detail:
          `A configuration file was created at:\n${envPath}\n\n` +
          `To set up your login, edit APP_DEFAULT_USERNAME and ` +
          `APP_DEFAULT_PASSWORD in that file, then restart the app.`,
      });
    }
  } catch (err) {
    showErrorAndQuit(err.message || String(err));
  }
});

app.on('before-quit', () => {
  appIsQuitting = true;
  stopBackend();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
  // Only recreate the window — backend is already running (or app is quitting)
  if (BrowserWindow.getAllWindows().length === 0 && backendProcess) {
    createMainWindow();
  }
});