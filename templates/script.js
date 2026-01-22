const SYSTEM_PROMPT = "{{SYSTEM_PROMPT}}";

function sendMessage() {
    let userInput = document.getElementById("user-input").value.trim();
    if (userInput === "") return;

    let chatBox = document.getElementById("chat-box");
    let userMessage = document.createElement("div");
    userMessage.classList.add("chat-message", "user");
    userMessage.textContent = userInput;
    chatBox.appendChild(userMessage);

    document.getElementById("user-input").value = "";
    
    fetch('/chat', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-API-KEY': 'your_api_key_here'  // optional custom header
    },
    body: JSON.stringify({ message: 'Hello, chatbot!' })
})
.then(response => response.json())
.then(data => {
    console.log(data.response);
});

/*
function sendMessage() {
    let userInput = document.getElementById("user-input").value.trim();
    if (userInput === "") return;

    let chatBox = document.getElementById("chat-box");
    let userMessage = document.createElement("div");
    userMessage.classList.add("chat-message", "user");
    userMessage.textContent = userInput;
    chatBox.appendChild(userMessage);

    document.getElementById("user-input").value = "";

    fetch(`/chatb?message=${encodeURIComponent(userInput)}`) // Changed to GET request
        .then(response => response.json())
        .then(data => {
            let botMessage = document.createElement("div");
            botMessage.classList.add("chat-message", "bot");
            botMessage.innerHTML = data.response;
            chatBox.appendChild(botMessage);
            chatBox.scrollTop = chatBox.scrollHeight;
        });
}
*/

function sendMessage() {
    let userInput = document.getElementById("user-input").value.trim();
    if (userInput === "") return;

    let chatBox = document.getElementById("chat-box");
    let userMessage = document.createElement("div");
    userMessage.classList.add("chat-message", "user");
    userMessage.textContent = userInput;
    chatBox.appendChild(userMessage);

    document.getElementById("user-input").value = "";

    // Send both user message and system prompt
    fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            message: userInput,
            system_prompt: SYSTEM_PROMPT  // include system prompt in request
        })
    })
    .then(response => response.json())
    .then(data => {
        let botMessage = document.createElement("div");
        botMessage.classList.add("chat-message", "bot");
        botMessage.innerHTML = data.response;
        chatBox.appendChild(botMessage);
        chatBox.scrollTop = chatBox.scrollHeight;
    })
    .catch(error => {
        console.error('Chat error:', error);
        alert('Something went wrong with the chatbot.');
    });
}



function uploadFile() {
    let fileInput = document.getElementById('file-upload');
    let file = fileInput.files[0];
    if (!file) return;

    let formData = new FormData();
    formData.append('file', file);

    fetch('/uploadDB', {
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




/*
    fetch("/chatb", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ message: userInput })
    })
    .then(response => response.json())
    .then(data => {
        let botMessage = document.createElement("div");
        botMessage.classList.add("chat-message", "bot");
        botMessage.innerHTML = data.response;
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

// Simulated user database
const users = [
    { userId: "123", password: "password123", role: "user" },
    { userId: "admin123", password: "admin123", role: "admin" }
];

// Simulated database upload status
let databaseUploaded = true; // Set to true for testing

function authenticate() {
    const userId = document.getElementById("userId").value.trim();
    const password = document.getElementById("password").value.trim();

    console.log("Entered User ID:", userId);
    console.log("Entered Password:", password);

    const user = users.find(u => u.userId === userId && u.password === password);

    if (user) {
        alert("Authentication successful!");
        localStorage.setItem("authenticated", "true");
        localStorage.setItem("userRole", user.role);
        console.log("User Role:", user.role);
        window.location.href = "home.html";
    } else {
        alert("Invalid credentials. Please try again.");
    }
}

function checkAuthentication(role) {
    console.log("Checking authentication for role:", role);
    if (localStorage.getItem("authenticated") === "true") {
        const userRole = localStorage.getItem("userRole");
        console.log("User Role from localStorage:", userRole);
        if (userRole === role) {
            if (role === "admin") {
                console.log("Redirecting to upload.html");
                window.location.href = "upload.html";
            } else {
                if (databaseUploaded) {
                    console.log("Redirecting to chatbot.html");
                    window.location.href = "chatbot.html";
                } else {
                    console.log("Redirecting to no-database.html");
                    window.location.href = "no-database.html";
                }
            }
        } else {
            alert(`You are not authorized to login as ${role}.`);
        }
    } else {
        alert("Please authenticate first.");
        window.location.href = "index.html";
    }
}*/
