// Retrieve config from Login pass
const port = localStorage.getItem("node_port");
const token = localStorage.getItem("session_token");
const username = localStorage.getItem("username");

if (!port || !token) {
    window.location.href = "login.html";
}

const nodeUrl = `http://127.0.0.1:${port}`;
document.getElementById("myUsername").innerText = "You: " + username;
document.getElementById("nodeInfo").innerText = "Local Node Port: " + port;

// Fetch Peers List
async function fetchPeers() {
    try {
        const res = await fetch(`${nodeUrl}/get-list`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.status === 200) {
            const data = await res.json();
            const peers = data.peers || {};
            
            const peerList = document.getElementById("peerList");
            const selectList = document.getElementById("targetUser");
            
            // Lấy old selected value để không bị mất khi render lại
            const selectedVal = selectList.value;
            
            peerList.innerHTML = "";
            let selectHtml = `<option value="ALL">📢 Broadcast (ALL)</option>`;

            for (const [uname, info] of Object.entries(peers)) {
                if (uname === username) continue; // Skip self
                
                // Add to Sidebar
                peerList.innerHTML += `
                    <li class="peer-item">
                        <span class="status-dot"></span>
                        <strong>${uname}</strong> 
                        <span class="muted">(${info.ip}:${info.port})</span>
                    </li>
                `;

                // Add to Select Box
                selectHtml += `<option value="${uname}">👤 ${uname}</option>`;
            }
            
            selectList.innerHTML = selectHtml;
            // Khôi phục selected (nếu vẫn còn online)
            if ([...selectList.options].some(o => o.value === selectedVal)) {
                selectList.value = selectedVal;
            }
        }
    } catch (e) {
        console.error("Tracker fetch failed");
    }
}

// Fetch Chat History
let lastHistoryCount = 0;
async function fetchMessages() {
    try {
        const res = await fetch(`${nodeUrl}/get-messages`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.status === 200) {
            const data = await res.json();
            const history = data.history || [];
            
            // Chỉ render nếu có tin nhắn mới
            if (history.length > lastHistoryCount) {
                lastHistoryCount = history.length;
                renderMessages(history);
            }
        }
    } catch (e) {
        console.error("Messages fetch failed");
    }
}

function renderMessages(history) {
    const container = document.getElementById("messagesContainer");
    container.innerHTML = "";
    
    history.forEach(msg => {
        const div = document.createElement("div");
        div.className = "message-bubble";
        
        let senderName = msg.from;
        if (msg.type === "direct_sent" || msg.type === "broadcast_sent") {
            div.classList.add("outbound");
            senderName = "You";
        } else {
            div.classList.add("inbound");
        }
        
        let extraInfo = "";
        if (msg.type === "broadcast_sent") {
            extraInfo = `<small style="color:#666;">(Broadcasted)</small>`;
        } else if (msg.type === "direct_sent") {
            extraInfo = `<small style="color:#666;">(To ${msg.to})</small>`;
        }

        div.innerHTML = `
            <div class="msg-author">${senderName} ${extraInfo}</div>
            <div class="msg-text">${msg.message}</div>
        `;
        container.appendChild(div);
    });

    // Cuộn xuống dòng cuối cùng
    container.scrollTop = container.scrollHeight;
}

// Gửi tin nhắn
async function sendMessage() {
    const input = document.getElementById("msgInput");
    const text = input.value.trim();
    if (!text) return;
    
    const target = document.getElementById("targetUser").value;
    
    let apiUrl = `${nodeUrl}/send-peer`;
    let payload = { type: "outbound", target: target, message: text };

    if (target === "ALL") {
        apiUrl = `${nodeUrl}/broadcast-peer`;
        payload = { message: text };
    }

    try {
        const res = await fetch(apiUrl, {
            method: 'POST',
            headers: { 
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json' 
            },
            body: JSON.stringify(payload)
        });
        
        if (res.status === 200) {
            input.value = "";
            fetchMessages(); // Cập nhật màn hình ngay lập tức
        } else {
            alert("Failed to send message: Peer offline or not found.");
        }
    } catch (e) {
        alert("Action failed!");
    }
}

// Bắt sự kiện Enter input
document.getElementById("msgInput").addEventListener("keypress", function(event) {
    if (event.key === "Enter") {
        sendMessage();
    }
});

// Run Polling
setInterval(fetchPeers, 3000);
setInterval(fetchMessages, 2000);
fetchPeers();
fetchMessages();
