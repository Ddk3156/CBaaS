// Configuration - API Key will be injected here
const API_KEY = "{{API_KEY}}";
// Knowledge base content - will be loaded from knowledge_base.json if present
let KB_LOADED = false;
let KB_CONTENT = "";

async function loadKnowledgeBase() {
    if (KB_LOADED) return KB_CONTENT;
    try {
        const res = await fetch('knowledge_base.json', { cache: 'no-store' });
        if (res.ok) {
            const data = await res.json();
            KB_CONTENT = (data && data.content) ? String(data.content) : "";
        }
    } catch (e) {
        // When opened via file:// some browsers block fetch; ignore and continue
        KB_CONTENT = "";
    } finally {
        KB_LOADED = true;
    }
    return KB_CONTENT;
}
// Direct Google API endpoint
const GOOGLE_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=" + API_KEY;
// Use direct API mode (standalone - no backend required)
const USE_DIRECT_API = true; // Always use direct API for plug-and-play

// Marked.js configuration for better markdown rendering
if (typeof marked !== 'undefined') {
    marked.setOptions({
        breaks: true,
        gfm: true,
        headerIds: false,
        mangle: false
    });
}

// Initialize highlight.js for syntax highlighting
if (typeof hljs !== 'undefined') {
    hljs.highlightAll();
}

// DOM Elements
const chatBox = document.getElementById('chat-box');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const loadingIndicator = document.getElementById('loading-indicator');

// Auto-scroll to bottom
function scrollToBottom() {
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Show loading indicator
function showLoading() {
    loadingIndicator.style.display = 'block';
    sendBtn.disabled = true;
    scrollToBottom();
}

// Hide loading indicator
function hideLoading() {
    loadingIndicator.style.display = 'none';
    sendBtn.disabled = false;
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
        // Highlight.js will auto-detect languages
        setTimeout(() => {
            const codeBlocks = chatBox.querySelectorAll('pre code');
            codeBlocks.forEach(block => {
                if (!block.classList.length) {
                    hljs.highlightElement(block);
                }
            });
        }, 0);
    }
    
    return html;
}

// Add message to chat
function addMessage(content, isUser = false, isStreaming = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${isUser ? 'user' : 'bot'}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    if (isStreaming) {
        contentDiv.classList.add('streaming');
    }
    
    // Render markdown if not user message
    if (!isUser && typeof marked !== 'undefined') {
        contentDiv.innerHTML = renderMarkdown(content);
    } else {
        // Escape HTML for user messages
        contentDiv.textContent = content;
    }
    
    messageDiv.appendChild(contentDiv);
    chatBox.appendChild(messageDiv);
    scrollToBottom();
    
    return contentDiv;
}

// Update streaming message content
function updateStreamingMessage(element, newContent) {
    if (typeof marked !== 'undefined') {
        element.innerHTML = renderMarkdown(newContent);
    } else {
        element.textContent = newContent;
    }
    scrollToBottom();
}

// Send message to API
async function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;
    
    // Clear input and disable button
    userInput.value = '';
    sendBtn.disabled = true;
    
    // Add user message
    addMessage(message, true);
    
    // Show loading indicator
    showLoading();
    
    try {
        // Ensure knowledge base is loaded
        await loadKnowledgeBase();

        // Prepare request with knowledge base if available
        let systemInstruction = "You are an AI chatbot. Provide helpful, accurate responses.";
        
        if (KB_CONTENT && KB_CONTENT.trim() !== "") {
            systemInstruction = `You are an AI chatbot with a provided knowledge base. You must answer questions outside the knowledge base if it is related to the topic. If the user asks anything way outside knowledge base, you should say sorry and ask the user to ask another question. Use this information to answer questions accurately. please Avoid mentioning knowledge base in your responces. Your core base for knowledge is knowledge base, it is not the whole world to you, things 'related' to it may not be in your knowledge base. So answer to the queries which are related to your knowledge base and not to unrelated ones, you should understand the relevances. Format your responses using markdown: use **bold** for emphasis, *italic* for subtle emphasis, \`code\` for inline code, \`\`\`code blocks\`\`\` for multi-line code with language specification, - or * for bullet lists, 1. for numbered lists, and proper line breaks between paragraphs.
            
Knowledge Base:
${KB_CONTENT}`;
        }
        /*
        const requestData = {
            contents: [
                {
                    role: "user",
                    parts: [{"text": message}]
                }
            ],
            generationConfig: {
                temperature: 0.7,
                topP: 0.95,
                topK: 40,
                maxOutputTokens: 8192,
                responseMimeType: "text/plain"
            },
            safetySettings: [],
            systemInstruction: {
                parts: [{"text": systemInstruction}]
            }
        };
        */
        
        const requestData = {
	    system_instruction: {
		parts: [{ text: systemInstruction }]
	    },
	    contents: [
		{
		    role: "user",
		    parts: [{ text: message }]
		}
	    ],
	    generationConfig: {
		temperature: 0.7,        // strict grounding
		topP: 0.95,
		topK: 40,
		maxOutputTokens: 8192,
		responseMimeType: "text/plain"
	    },
	    safetySettings: []
	};

        
        
        
        // Check if API supports streaming
        const useStreaming = false; // Set to true if API supports streaming
        
        if (useStreaming) {
            // Streaming response (if API supports it)
            await fetchStreamingResponse(requestData);
        } else {
            let response;
            let data;
            
            // Always use direct API for standalone/plug-and-play mode
            response = await fetch(GOOGLE_API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(`HTTP error! status: ${response.status}. ${JSON.stringify(errorData)}`);
            }
            
            data = await response.json();
            
            // Hide loading indicator
            hideLoading();
            
            // Extract response text from Google API format
            let responseText = "Sorry, I couldn't process that request.";
            
            if (data.candidates && data.candidates.length > 0) {
                const candidate = data.candidates[0];
                if (candidate.content && candidate.content.parts) {
                    responseText = candidate.content.parts[0].text || responseText;
                } else if (candidate.finishReason && candidate.finishReason === 'SAFETY') {
                    responseText = "I couldn't provide a response due to safety filters. Please rephrase your question.";
                }
            } else if (data.error) {
                responseText = `Error: ${data.error.message || 'Unknown error occurred'}`;
            }
            
            // Add bot response with markdown rendering
            addMessage(responseText, false);
        }
        
    } catch (error) {
        console.error('Error:', error);
        hideLoading();
        
        // Show error message
        addMessage(
            'Sorry, I encountered an error. Please check your API key and try again.',
            false
        );
    }
}

// Fetch streaming response (for future use if API supports streaming)
async function fetchStreamingResponse(requestData) {
    // This would be implemented if the API supports streaming
    // For now, using regular fetch
    const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    });
    
    const data = await response.json();
    hideLoading();
    
    let responseText = "Sorry, I couldn't process that request.";
    if (data.candidates && data.candidates.length > 0) {
        const candidate = data.candidates[0];
        if (candidate.content && candidate.content.parts) {
            responseText = candidate.content.parts[0].text || responseText;
        }
    }
    
    // Simulate streaming effect
    const messageElement = addMessage('', false, true);
    let accumulatedText = '';
    
    const words = responseText.split(/(\s+)/);
    for (let i = 0; i < words.length; i++) {
        accumulatedText += words[i];
        updateStreamingMessage(messageElement, accumulatedText);
        await new Promise(resolve => setTimeout(resolve, 30));
    }
    
    messageElement.classList.remove('streaming');
}

// Event listeners
sendBtn.addEventListener('click', sendMessage);

userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// Focus input on load
userInput.focus();

// Auto-resize input (optional enhancement)
userInput.addEventListener('input', function() {
    // Could add auto-resize for multi-line input
});

