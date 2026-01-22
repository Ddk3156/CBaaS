// server.js - minimal static server (like python3 -m http.server)

const express = require("express");
const path = require("path");

const app = express();
const PORT = 3000;

// Serve current directory (like python http.server)
app.use(express.static(path.join(__dirname)));

app.listen(PORT, () => {
    console.log(`Server running at http://localhost:${PORT}`);
});

