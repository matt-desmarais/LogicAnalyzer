const express = require('express');
const multer = require('multer');
const fs = require('fs');
const path = require('path');
const moment = require('moment-timezone');
const serveIndex = require('serve-index');
const https = require('https');
const http = require('http');
const app = express();

//replace yoursite.org with your domain, no / at the end
//replace UPLOADS_API_KEY with SERVER_KEY from secrets.py

// Load SSL/TLS certificate and private key
const privateKey = fs.readFileSync('/etc/letsencrypt/live/yoursite.org/privkey.pem', 'utf8');
const certificate = fs.readFileSync('/etc/letsencrypt/live/yoursite.org/cert.pem', 'utf8');
const ca = fs.readFileSync('/etc/letsencrypt/live/yoursite.org/chain.pem', 'utf8');

const credentials = {
  key: privateKey,
  cert: certificate,
  ca: ca
};

// Middleware to redirect HTTP to HTTPS
const redirectToHttps = (req, res, next) => {
  if (req.protocol === 'http' || req.headers['x-forwarded-proto'] === 'http') {
    return res.redirect(301, `https://${req.headers.host}${req.url}`);
  }
  next();
};

// Create HTTPS server
const httpsServer = https.createServer(credentials, app);

// Apply the redirectToHttps middleware
app.use(redirectToHttps);

// Create HTTP server that redirects to HTTPS
const httpApp = express();
httpApp.use(redirectToHttps);
const httpServer = http.createServer(httpApp);

const HTTP_PORT = 80;
const HTTPS_PORT = 443;

const authMiddleware = (req, res, next) => {
  const authHeader = req.headers.authorization;
  const apiKey = 'UPLOADS_API_KEY';

  if (authHeader && authHeader === `Bearer ${apiKey}`) {
    next();
  } else {
    res.status(401).send('Unauthorized');
  }
};

// Define custom storage configuration
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, 'files/');
  },
  filename: (req, file, cb) => {
    // Generate a filename with the prefix "interview" and the current date and time in New York City's time zone
    const timestamp = moment().tz('America/New_York').format('YYYY_MM_DD_HH_mm_ss');
    const filename = `analysis_${timestamp}.html`;
    cb(null, filename);
  }
});

const upload = multer({ storage: storage });


app.post('/upload', authMiddleware, upload.single('file'), (req, res) => {
  if (!req.file) {
    return res.status(400).send('No file was uploaded.');
  }
  res.send('File uploaded successfully.');
});


// Endpoint for displaying the contents of the most recent text file
app.get('/', (req, res) => {
  fs.readdir('files', (err, files) => {
    if (err) {
      return res.status(500).send('An error occurred while reading the directory.');
    }
    if (files.length === 0) {
      return res.send('No files have been uploaded.');
    }
    const sortedFiles = files.sort((a, b) => {
      return fs.statSync(path.join('files', b)).mtime.getTime() - fs.statSync(path.join('files', a)).mtime.getTime();
    });
    const mostRecentFile = sortedFiles[0];
    fs.readFile(path.join('files', mostRecentFile), 'utf8', (err, data) => {
      if (err) {
        return res.status(500).send('An error occurred while reading the file.');
      }
      res.send(data);
    });
  });
});

// Serve static files and generate directory listings for the "uploads" directory
app.use('/files', express.static('files'), serveIndex('files', { icons: true }));

//const PORT = process.env.PORT || 80;
//app.listen(PORT, () => {
//  console.log(`Server is running on port ${PORT}`);
//});

// Start the HTTP server
httpServer.listen(HTTP_PORT, () => {
  console.log(`HTTP server is running on port ${HTTP_PORT}`);
});

const PORT = process.env.PORT || HTTPS_PORT;
httpsServer.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});
