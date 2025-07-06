# Mobile and Web Support Improvements

## 1. Progressive Web App (PWA) Support
class PWAGenerator:
    def __init__(self, app_name="Ashish's Banking & Shopping"):
        self.app_name = app_name
    
    def generate_manifest(self):
        """Generate PWA manifest file"""
        manifest = {
            "name": self.app_name,
            "short_name": "Banking&Shopping",
            "description": "Your comprehensive banking and shopping solution",
            "start_url": "/",
            "display": "standalone",
            "background_color": "#ffffff",
            "theme_color": "#007bff",
            "orientation": "portrait-primary",
            "icons": [
                {
                    "src": "icons/icon-72x72.png",
                    "sizes": "72x72",
                    "type": "image/png"
                },
                {
                    "src": "icons/icon-96x96.png",
                    "sizes": "96x96",
                    "type": "image/png"
                },
                {
                    "src": "icons/icon-128x128.png",
                    "sizes": "128x128",
                    "type": "image/png"
                },
                {
                    "src": "icons/icon-144x144.png",
                    "sizes": "144x144",
                    "type": "image/png"
                },
                {
                    "src": "icons/icon-152x152.png",
                    "sizes": "152x152",
                    "type": "image/png"
                },
                {
                    "src": "icons/icon-192x192.png",
                    "sizes": "192x192",
                    "type": "image/png"
                },
                {
                    "src": "icons/icon-384x384.png",
                    "sizes": "384x384",
                    "type": "image/png"
                },
                {
                    "src": "icons/icon-512x512.png",
                    "sizes": "512x512",
                    "type": "image/png"
                }
            ],
            "categories": ["finance", "shopping", "productivity"],
            "screenshots": [
                {
                    "src": "screenshots/mobile-home.png",
                    "sizes": "640x1136",
                    "type": "image/png",
                    "platform": "narrow"
                },
                {
                    "src": "screenshots/desktop-dashboard.png",
                    "sizes": "1280x720",
                    "type": "image/png",
                    "platform": "wide"
                }
            ]
        }
        return manifest
    
    def generate_service_worker(self):
        """Generate service worker for offline support"""
        service_worker = '''
// Service Worker for PWA
const CACHE_NAME = 'banking-shopping-v1';
const urlsToCache = [
  '/',
  '/static/css/style.css',
  '/static/js/app.js',
  '/static/icons/icon-192x192.png',
  '/api/products',
  '/offline.html'
];

// Install event
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        return cache.addAll(urlsToCache);
      })
  );
});

// Fetch event
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Return cached version or fetch from network
        if (response) {
          return response;
        }
        return fetch(event.request);
      }
    )
  );
});

// Background sync for offline transactions
self.addEventListener('sync', event => {
  if (event.tag === 'background-sync') {
    event.waitUntil(doBackgroundSync());
  }
});

function doBackgroundSync() {
  return new Promise((resolve, reject) => {
    // Sync offline transactions when online
    const offlineTransactions = getOfflineTransactions();
    
    if (offlineTransactions.length > 0) {
      syncTransactions(offlineTransactions)
        .then(() => {
          clearOfflineTransactions();
          resolve();
        })
        .catch(error => {
          console.error('Background sync failed:', error);
          reject(error);
        });
    } else {
      resolve();
    }
  });
}

function getOfflineTransactions() {
  // Get stored offline transactions
  return JSON.parse(localStorage.getItem('offlineTransactions') || '[]');
}

function syncTransactions(transactions) {
  // Sync transactions with server
  return fetch('/api/sync-transactions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(transactions)
  });
}

function clearOfflineTransactions() {
  localStorage.removeItem('offlineTransactions');
}
'''
        return service_worker

## 2. Responsive Web Interface
class ResponsiveWebInterface:
    def __init__(self):
        self.css_framework = "Bootstrap 5"
    
    def generate_responsive_css(self):
        """Generate responsive CSS styles"""
        css = '''
/* Responsive Banking & Shopping CSS */

/* Mobile First Approach */
* {
  box-sizing: border-box;
}

body {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  margin: 0;
  padding: 0;
  background-color: #f8f9fa;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 15px;
}

/* Navigation */
.navbar {
  background-color: #007bff;
  padding: 1rem 0;
  position: sticky;
  top: 0;
  z-index: 1000;
}

.navbar-brand {
  color: white;
  font-size: 1.5rem;
  font-weight: bold;
  text-decoration: none;
}

.navbar-nav {
  display: flex;
  list-style: none;
  margin: 0;
  padding: 0;
}

.nav-item {
  margin: 0 0.5rem;
}

.nav-link {
  color: white;
  text-decoration: none;
  padding: 0.5rem 1rem;
  border-radius: 0.25rem;
  transition: background-color 0.3s;
}

.nav-link:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

/* Cards */
.card {
  background: white;
  border-radius: 0.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 1.5rem;
  overflow: hidden;
}

.card-header {
  background-color: #f8f9fa;
  padding: 1rem;
  border-bottom: 1px solid #dee2e6;
  font-weight: bold;
}

.card-body {
  padding: 1.5rem;
}

/* Buttons */
.btn {
  display: inline-block;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 0.25rem;
  text-decoration: none;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 1rem;
  font-weight: 500;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-primary:hover {
  background-color: #0056b3;
}

.btn-success {
  background-color: #28a745;
  color: white;
}

.btn-success:hover {
  background-color: #218838;
}

.btn-danger {
  background-color: #dc3545;
  color: white;
}

.btn-danger:hover {
  background-color: #c82333;
}

/* Forms */
.form-group {
  margin-bottom: 1rem;
}

.form-label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.form-control {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ced4da;
  border-radius: 0.25rem;
  font-size: 1rem;
}

.form-control:focus {
  border-color: #80bdff;
  outline: 0;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

/* Tables */
.table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 1rem;
}

.table th,
.table td {
  padding: 0.75rem;
  border-bottom: 1px solid #dee2e6;
  text-align: left;
}

.table th {
  background-color: #f8f9fa;
  font-weight: 600;
}

/* Grid System */
.row {
  display: flex;
  flex-wrap: wrap;
  margin: 0 -15px;
}

.col {
  flex: 1;
  padding: 0 15px;
}

.col-md-6 {
  flex: 0 0 50%;
  max-width: 50%;
  padding: 0 15px;
}

.col-lg-4 {
  flex: 0 0 33.333333%;
  max-width: 33.333333%;
  padding: 0 15px;
}

/* Responsive Breakpoints */

/* Tablet */
@media (max-width: 768px) {
  .navbar-nav {
    flex-direction: column;
    width: 100%;
  }
  
  .nav-item {
    margin: 0.25rem 0;
  }
  
  .col-md-6,
  .col-lg-4 {
    flex: 0 0 100%;
    max-width: 100%;
  }
  
  .card-body {
    padding: 1rem;
  }
  
  .btn {
    width: 100%;
    margin-bottom: 0.5rem;
  }
  
  .table {
    font-size: 0.875rem;
  }
}

/* Mobile */
@media (max-width: 576px) {
  .container {
    padding: 0 10px;
  }
  
  .navbar {
    padding: 0.5rem 0;
  }
  
  .navbar-brand {
    font-size: 1.25rem;
  }
  
  .card {
    margin-bottom: 1rem;
  }
  
  .card-body {
    padding: 0.75rem;
  }
  
  .btn {
    padding: 0.5rem 1rem;
    font-size: 0.875rem;
  }
  
  .form-control {
    padding: 0.5rem;
  }
  
  .table th,
  .table td {
    padding: 0.5rem;
    font-size: 0.8rem;
  }
  
  /* Hide less important table columns on mobile */
  .table .d-none-mobile {
    display: none;
  }
}

/* Touch-friendly interactions */
@media (hover: none) and (pointer: coarse) {
  .btn {
    min-height: 44px;
    min-width: 44px;
  }
  
  .nav-link {
    min-height: 44px;
    display: flex;
    align-items: center;
  }
  
  .form-control {
    min-height: 44px;
  }
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
  body {
    background-color: #1a1a1a;
    color: #ffffff;
  }
  
  .card {
    background-color: #2d2d2d;
    color: #ffffff;
  }
  
  .card-header {
    background-color: #404040;
    border-bottom-color: #555;
  }
  
  .form-control {
    background-color: #2d2d2d;
    border-color: #555;
    color: #ffffff;
  }
  
  .table th {
    background-color: #404040;
  }
  
  .table td {
    border-bottom-color: #555;
  }
}

/* Loading indicators */
.spinner {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: #fff;
  animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Accessibility improvements */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* Focus indicators */
*:focus {
  outline: 2px solid #007bff;
  outline-offset: 2px;
}

/* High contrast mode support */
@media (prefers-contrast: high) {
  .btn {
    border: 2px solid;
  }
  
  .card {
    border: 2px solid #000;
  }
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
'''
        return css
    
    def generate_mobile_html_template(self):
        """Generate mobile-optimized HTML template"""
        html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Ashish's Banking & Shopping - Your comprehensive financial and shopping solution">
    <meta name="theme-color" content="#007bff">
    <title>Banking & Shopping</title>
    
    <!-- PWA Manifest -->
    <link rel="manifest" href="/manifest.json">
    
    <!-- iOS PWA support -->
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    <meta name="apple-mobile-web-app-title" content="Banking&Shopping">
    <link rel="apple-touch-icon" href="/icons/icon-152x152.png">
    
    <!-- Preconnect to external resources -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://api.example.com">
    
    <!-- Critical CSS -->
    <style>
        /* Critical above-the-fold styles */
        body { font-family: system-ui, sans-serif; margin: 0; }
        .navbar { background: #007bff; color: white; padding: 1rem; }
        .loading { text-align: center; padding: 2rem; }
    </style>
    
    <!-- Defer non-critical CSS -->
    <link rel="preload" href="/css/styles.css" as="style" onload="this.onload=null;this.rel='stylesheet'">
</head>
<body>
    <nav class="navbar">
        <div class="container">
            <a href="/" class="navbar-brand">Banking & Shopping</a>
            <button class="navbar-toggle" aria-label="Toggle navigation">
                <span></span>
                <span></span>
                <span></span>
            </button>
        </div>
    </nav>
    
    <main id="app">
        <div class="loading">
            <div class="spinner"></div>
            <p>Loading...</p>
        </div>
    </main>
    
    <!-- Service Worker Registration -->
    <script>
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('/sw.js')
                    .then(registration => console.log('SW registered'))
                    .catch(error => console.log('SW registration failed'));
            });
        }
    </script>
    
    <!-- App JavaScript -->
    <script src="/js/app.js" defer></script>
</body>
</html>
'''
        return html

## 3. Mobile App Bridge (for hybrid apps)
class MobileAppBridge:
    def __init__(self):
        self.device_info = {}
    
    def generate_bridge_js(self):
        """Generate JavaScript bridge for mobile apps"""
        bridge_js = '''
// Mobile App Bridge
class MobileAppBridge {
    constructor() {
        this.isNative = this.detectNativeApp();
        this.platform = this.detectPlatform();
        this.initBridge();
    }
    
    detectNativeApp() {
        return window.ReactNativeWebView || 
               window.webkit?.messageHandlers || 
               window.Android;
    }
    
    detectPlatform() {
        const userAgent = navigator.userAgent;
        if (/iPad|iPhone|iPod/.test(userAgent)) return 'ios';
        if (/Android/.test(userAgent)) return 'android';
        return 'web';
    }
    
    initBridge() {
        if (this.isNative) {
            this.setupNativeBridge();
        } else {
            this.setupWebBridge();
        }
    }
    
    setupNativeBridge() {
        // Setup communication with native app
        window.addEventListener('message', (event) => {
            this.handleNativeMessage(event.data);
        });
    }
    
    setupWebBridge() {
        // Setup web-specific features
        this.enablePWAFeatures();
    }
    
    // Device capabilities
    async getDeviceInfo() {
        if (this.isNative) {
            return this.callNative('getDeviceInfo');
        } else {
            return {
                platform: this.platform,
                userAgent: navigator.userAgent,
                screen: {
                    width: screen.width,
                    height: screen.height
                },
                supports: {
                    camera: 'mediaDevices' in navigator,
                    geolocation: 'geolocation' in navigator,
                    notifications: 'Notification' in window,
                    biometric: this.supportsBiometric()
                }
            };
        }
    }
    
    supportsBiometric() {
        return 'credentials' in navigator && 
               'create' in navigator.credentials;
    }
    
    // Camera access
    async capturePhoto() {
        if (this.isNative) {
            return this.callNative('capturePhoto');
        } else {
            return this.webCapturePhoto();
        }
    }
    
    async webCapturePhoto() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ 
                video: { facingMode: 'environment' } 
            });
            
            const video = document.createElement('video');
            video.srcObject = stream;
            video.play();
            
            return new Promise((resolve) => {
                video.addEventListener('loadedmetadata', () => {
                    const canvas = document.createElement('canvas');
                    canvas.width = video.videoWidth;
                    canvas.height = video.videoHeight;
                    
                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(video, 0, 0);
                    
                    stream.getTracks().forEach(track => track.stop());
                    
                    resolve(canvas.toDataURL('image/jpeg'));
                });
            });
        } catch (error) {
            throw new Error('Camera access denied');
        }
    }
    
    // Geolocation
    async getCurrentLocation() {
        if (this.isNative) {
            return this.callNative('getCurrentLocation');
        } else {
            return this.webGetLocation();
        }
    }
    
    async webGetLocation() {
        return new Promise((resolve, reject) => {
            if (!navigator.geolocation) {
                reject(new Error('Geolocation not supported'));
                return;
            }
            
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    resolve({
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude,
                        accuracy: position.coords.accuracy
                    });
                },
                (error) => reject(error),
                { enableHighAccuracy: true, timeout: 10000 }
            );
        });
    }
    
    // Biometric authentication
    async authenticateWithBiometric() {
        if (this.isNative) {
            return this.callNative('authenticateWithBiometric');
        } else {
            return this.webBiometricAuth();
        }
    }
    
    async webBiometricAuth() {
        if (!this.supportsBiometric()) {
            throw new Error('Biometric authentication not supported');
        }
        
        try {
            const credential = await navigator.credentials.create({
                publicKey: {
                    challenge: new Uint8Array(32),
                    rp: { name: "Banking & Shopping" },
                    user: {
                        id: new Uint8Array(16),
                        name: "user",
                        displayName: "User"
                    },
                    pubKeyCredParams: [{ alg: -7, type: "public-key" }],
                    authenticatorSelection: {
                        authenticatorAttachment: "platform",
                        userVerification: "required"
                    }
                }
            });
            
            return { success: true, credential };
        } catch (error) {
            throw new Error('Biometric authentication failed');
        }
    }
    
    // Push notifications
    async requestNotificationPermission() {
        if (this.isNative) {
            return this.callNative('requestNotificationPermission');
        } else {
            return this.webRequestNotificationPermission();
        }
    }
    
    async webRequestNotificationPermission() {
        if (!('Notification' in window)) {
            throw new Error('Notifications not supported');
        }
        
        const permission = await Notification.requestPermission();
        return { permission };
    }
    
    async showNotification(title, options) {
        if (this.isNative) {
            return this.callNative('showNotification', { title, options });
        } else {
            if (Notification.permission === 'granted') {
                return new Notification(title, options);
            }
        }
    }
    
    // Native bridge communication
    async callNative(method, params = {}) {
        return new Promise((resolve, reject) => {
            const message = {
                method,
                params,
                id: Date.now()
            };
            
            // Store callback for response
            window.nativeCallbacks = window.nativeCallbacks || {};
            window.nativeCallbacks[message.id] = { resolve, reject };
            
            // Send to native
            if (window.ReactNativeWebView) {
                window.ReactNativeWebView.postMessage(JSON.stringify(message));
            } else if (window.webkit?.messageHandlers?.nativeHandler) {
                window.webkit.messageHandlers.nativeHandler.postMessage(message);
            } else if (window.Android) {
                window.Android.handleMessage(JSON.stringify(message));
            }
        });
    }
    
    handleNativeMessage(data) {
        const response = JSON.parse(data);
        const callback = window.nativeCallbacks[response.id];
        
        if (callback) {
            if (response.error) {
                callback.reject(new Error(response.error));
            } else {
                callback.resolve(response.result);
            }
            delete window.nativeCallbacks[response.id];
        }
    }
    
    // PWA features
    enablePWAFeatures() {
        // Install prompt
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            window.installPrompt = e;
        });
        
        // Offline detection
        window.addEventListener('online', () => {
            this.onNetworkStatusChange(true);
        });
        
        window.addEventListener('offline', () => {
            this.onNetworkStatusChange(false);
        });
    }
    
    onNetworkStatusChange(isOnline) {
        document.dispatchEvent(new CustomEvent('networkStatusChange', {
            detail: { isOnline }
        }));
    }
    
    async installPWA() {
        if (window.installPrompt) {
            window.installPrompt.prompt();
            const result = await window.installPrompt.userChoice;
            window.installPrompt = null;
            return result;
        }
        throw new Error('Install prompt not available');
    }
}

// Initialize bridge
window.mobileAppBridge = new MobileAppBridge();
'''
        return bridge_js

## 4. Progressive Enhancement
class ProgressiveEnhancement:
    @staticmethod
    def generate_offline_fallback():
        """Generate offline fallback page"""
        offline_html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Offline - Banking & Shopping</title>
    <style>
        body {
            font-family: system-ui, sans-serif;
            text-align: center;
            padding: 2rem;
            background: #f8f9fa;
        }
        .offline-container {
            max-width: 500px;
            margin: 0 auto;
            background: white;
            padding: 2rem;
            border-radius: 0.5rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .offline-icon {
            font-size: 4rem;
            margin-bottom: 1rem;
        }
        .retry-btn {
            background: #007bff;
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 0.25rem;
            cursor: pointer;
            margin-top: 1rem;
        }
    </style>
</head>
<body>
    <div class="offline-container">
        <div class="offline-icon">📱</div>
        <h1>You're Offline</h1>
        <p>It looks like you've lost your internet connection. Some features may not be available until you're back online.</p>
        
        <h3>Available Offline:</h3>
        <ul style="text-align: left;">
            <li>View cached account balances</li>
            <li>Browse previously loaded products</li>
            <li>Access transaction history</li>
            <li>Create offline transactions (will sync when online)</li>
        </ul>
        
        <button class="retry-btn" onclick="window.location.reload()">
            Try Again
        </button>
    </div>
    
    <script>
        // Check for connectivity
        setInterval(() => {
            if (navigator.onLine) {
                window.location.reload();
            }
        }, 5000);
    </script>
</body>
</html>
'''
        return offline_html

# Usage example
if __name__ == "__main__":
    # Generate PWA files
    pwa = PWAGenerator()
    manifest = pwa.generate_manifest()
    service_worker = pwa.generate_service_worker()
    
    # Generate responsive interface
    responsive = ResponsiveWebInterface()
    css = responsive.generate_responsive_css()
    html = responsive.generate_mobile_html_template()
    
    # Generate mobile bridge
    bridge = MobileAppBridge()
    bridge_js = bridge.generate_bridge_js()
    
    # Generate offline fallback
    offline_html = ProgressiveEnhancement.generate_offline_fallback()
    
    print("Mobile and web support files generated:")
    print("- PWA manifest and service worker")
    print("- Responsive CSS and HTML templates")
    print("- Mobile app bridge JavaScript")
    print("- Offline fallback page")
    print("\\nReady for cross-platform deployment!")
