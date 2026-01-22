/*
// server.js
const express = require("express");
const sqlite3 = require("sqlite3").verbose();
const bodyParser = require("body-parser");
const cors = require("cors");
const path = require("path");

const app = express();
const PORT = 5000;

// Middleware
app.use(cors());
app.use(bodyParser.json());
app.use(express.static(path.join(__dirname, 'static')));

// Route to serve index2.html
app.get('/index2', (req, res) => {
  res.sendFile(path.join(__dirname, 'templates', 'index2.html'));
});

// Redirect root (/) to /index2
app.get('/', (req, res) => {
  res.redirect('/index2');
});

// SQLite DB Setup
const db = new sqlite3.Database("AI Chat Bot/db/users.db", (err) => {
    if (err) return console.error(err.message);
    console.log("Connected to SQLite");
});

db.run(`CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    password TEXT
)`);

// Signup route
app.post("/signup", (req, res) => {
    const { email, password } = req.body;
    db.run("INSERT INTO users (email, password) VALUES (?, ?)", [email, password], function(err) {
        if (err) {
            if (err.message.includes("UNIQUE constraint")) {
                return res.status(400).send("Email already exists");
            } else {
                console.error(err);
                return res.status(500).send("Server error");
            }
        }
        res.status(200).send("Signup Successful");
    });
});

// Login route
app.post("/login", (req, res) => {
    const { email, password } = req.body;
    db.get("SELECT * FROM users WHERE email = ? AND password = ?", [email, password], (err, row) => {
        if (err) return res.status(500).send("Internal server error");
        if (!row) return res.status(401).send("Invalid credentials");
        res.status(200).send("Login successful");
    });
});

app.listen(PORT, () => console.log(`Server running on http://localhost:${PORT}`));
*/


// Initialize markdown parser and syntax highlighter
if (typeof marked !== 'undefined') {
    marked.setOptions({
        breaks: true,
        gfm: true,
        headerIds: false,
        mangle: false
    });
}

// Render markdown content
function renderMarkdown(text) {
    if (typeof marked === 'undefined') {
        // Fallback: basic HTML escaping and line breaks
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/\n/g, '<br>');
    }
    
    // Use marked.js to parse markdown
    let html = marked.parse(text);
    
    // Process code blocks for highlight.js
    if (typeof hljs !== 'undefined') {
        setTimeout(() => {
            const codeBlocks = document.querySelectorAll('#chat-box pre code');
            codeBlocks.forEach(block => {
                if (!block.classList.length) {
                    hljs.highlightElement(block);
                }
            });
        }, 0);
    }
    
    return html;
}

function sendMessage() {
    let userInput = document.getElementById("user-input").value.trim();
    if (userInput === "") return;

    let chatBox = document.getElementById("chat-box");
    let userMessage = document.createElement("div");
    userMessage.classList.add("chat-message", "user");
    userMessage.textContent = userInput;
    chatBox.appendChild(userMessage);

    document.getElementById("user-input").value = "";

    fetch(`/chat?message=${encodeURIComponent(userInput)}`) // Changed to GET request
        .then(response => response.json())
        .then(data => {
            let botMessage = document.createElement("div");
            botMessage.classList.add("chat-message", "bot");
            // Render markdown for bot responses
            botMessage.innerHTML = renderMarkdown(data.response);
            chatBox.appendChild(botMessage);
            chatBox.scrollTop = chatBox.scrollHeight;
        });
}

function uploadFile() {
    let fileInput = document.getElementById('file-upload');
    let file = fileInput.files[0];
    if (!file) return;

    let formData = new FormData();
    formData.append('file', file);

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.filename) {
            let chatBox = document.getElementById("chat-box");
            let botMessage = document.createElement("div");
            botMessage.classList.add("chat-message", "bot");
            botMessage.innerHTML = data.message;
            chatBox.appendChild(botMessage);
            chatBox.scrollTop = chatBox.scrollHeight;
        } else {
            alert(data.error);
        }
    })
    .catch(error => {
        console.error('Error during upload:', error);
        alert('An error occurred during file upload.');
    });
}

document.getElementById("user-input").addEventListener("keyup", function(event) {
    if (event.key === "Enter") {
        sendMessage();
    }
});
