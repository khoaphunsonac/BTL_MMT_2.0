// Retrieve config from Login pass
const nodeIp = sessionStorage.getItem("node_ip") || "127.0.0.1";
const port = sessionStorage.getItem("node_port");
const trackerIp = sessionStorage.getItem("tracker_ip") || nodeIp;
const trackerPort = sessionStorage.getItem("tracker_port") || port;
const publicIp = sessionStorage.getItem("public_ip") || nodeIp;
const token = sessionStorage.getItem("session_token");
const trackerToken = sessionStorage.getItem("tracker_token") || token;
const username = sessionStorage.getItem("username");

if (!port || !token) {
    window.location.href = "login.html";
}

const nodeUrl = `http://${nodeIp}:${port}`;
const trackerUrl = `http://${trackerIp}:${trackerPort}`;
document.getElementById("myUsername").innerText = "You: " + username;
document.getElementById("nodeInfo").innerText = `Local Node: ${nodeIp}:${port} | Tracker: ${trackerIp}:${trackerPort}`;

const targetSelect = document.getElementById("targetUser");
const chatTitle = document.getElementById("chatTitle");
const modeInputs = document.querySelectorAll('input[name="chatMode"]');

let knownPeers = {};
let peerOnlineMap = {};
let localNotices = [];
let lastHistory = [];

function selectedMode() {
    const checked = document.querySelector('input[name="chatMode"]:checked');
    return checked ? checked.value : "direct";
}

function updateChatTitle() {
    if (selectedMode() === "broadcast") {
        chatTitle.innerText = "Broadcast Chat";
        targetSelect.disabled = true;
        return;
    }

    targetSelect.disabled = false;
    const target = targetSelect.value;
    chatTitle.innerText = target ? `Direct Chat -> ${target}` : "Direct Chat";
}

function addLocalNotice(text) {
    localNotices.push({
        type: "system",
        message: text,
        ts: Date.now()
    });

    if (localNotices.length > 20) {
        localNotices = localNotices.slice(-20);
    }
    renderMessages(lastHistory);
}

// Fetch Peers List
async function fetchPeers() {
    try {
        const res = await fetch(`${trackerUrl}/get-list`, {
            headers: { 'Authorization': `Bearer ${trackerToken}` }
        });
        if (res.status === 200) {
            const data = await res.json();
            const peers = data.peers || {};
            
            const peerList = document.getElementById("peerList");
            const selectList = targetSelect;
            
            // Lấy old selected value để không bị mất khi render lại
            const selectedVal = selectList.value;
            
            peerList.innerHTML = "";
            let selectHtml = `<option value="">Select a peer...</option>`;
            const nextPeerOnlineMap = {};

            for (const [uname, info] of Object.entries(peers)) {
                if (uname === username) continue; // Skip self

                const isOnline = info.online !== false;
                nextPeerOnlineMap[uname] = isOnline;
                const statusClass = isOnline ? "online" : "offline";
                const statusText = isOnline ? "online" : "offline";
                
                // Add to Sidebar
                peerList.innerHTML += `
                    <li class="peer-item">
                        <span class="status-dot ${statusClass}"></span>
                        <strong>${uname}</strong> 
                        <span class="muted">(${info.ip || "-"}:${info.port || "-"}) - ${statusText}</span>
                    </li>
                `;

                // Direct list chỉ chứa peer online
                if (isOnline) {
                    selectHtml += `<option value="${uname}">👤 ${uname}</option>`;
                }
            }

            for (const uname of Object.keys(nextPeerOnlineMap)) {
                const oldOnline = peerOnlineMap[uname];
                const newOnline = nextPeerOnlineMap[uname];
                if (oldOnline === true && newOnline === false) {
                    addLocalNotice(`${uname} logged out/offline`);
                }
                if (oldOnline === false && newOnline === true) {
                    addLocalNotice(`${uname} is online`);
                }
            }

            peerOnlineMap = nextPeerOnlineMap;
            knownPeers = peers;
            
            selectList.innerHTML = selectHtml;
            // Khôi phục selected (nếu vẫn còn online)
            if ([...selectList.options].some(o => o.value === selectedVal)) {
                selectList.value = selectedVal;
            }
            updateChatTitle();
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
            lastHistory = history;
            
            // Chỉ render nếu có tin nhắn mới
            if (history.length > lastHistoryCount) {
                lastHistoryCount = history.length;
            }
            renderMessages(history);
        }
    } catch (e) {
        console.error("Messages fetch failed");
    }
}

function renderMessages(history) {
    const container = document.getElementById("messagesContainer");
    container.innerHTML = "";

    const mergedMessages = [...history, ...localNotices];
    mergedMessages.sort((a, b) => (a.ts || 0) - (b.ts || 0));
    
    mergedMessages.forEach(msg => {
        const div = document.createElement("div");
        div.className = "message-bubble";

        if (msg.type === "system") {
            div.classList.add("system");
            div.innerHTML = `<div class="msg-text">${msg.message}</div>`;
            container.appendChild(div);
            return;
        }
        
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
    
    const mode = selectedMode();
    const target = targetSelect.value;
    
    let apiUrl = `${nodeUrl}/send-peer`;
    let payload = { type: "outbound", target: target, message: text };

    if (mode === "broadcast") {
        apiUrl = `${nodeUrl}/broadcast-peer`;
        payload = { message: text, peers: knownPeers };
    } else if (!target) {
        alert("Please choose an online peer for direct message.");
        return;
    } else {
        if (knownPeers[target]) {
            payload.target_ip = knownPeers[target].ip;
            payload.target_port = knownPeers[target].port;
        }
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

async function heartbeat() {
    try {
        await fetch(`${trackerUrl}/heartbeat`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${trackerToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ ip: publicIp, port: parseInt(port) })
        });
    } catch (e) {
        // Presence ping best-effort
    }
}

async function logoutUser() {
    try {
        await fetch(`${trackerUrl}/logout`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${trackerToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ reason: "manual_logout" })
        });
    } catch (e) {
        // Even if request fails, clear local session on UI side.
    }

    try {
        if (trackerIp !== nodeIp || trackerPort !== port) {
            await fetch(`${nodeUrl}/logout`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ reason: "manual_logout" })
            });
        }
    } catch (e) {
        // Local node logout is best-effort if tracker is separate.
    }

    sessionStorage.removeItem("session_token");
    sessionStorage.removeItem("tracker_token");
    sessionStorage.removeItem("node_ip");
    sessionStorage.removeItem("node_port");
    sessionStorage.removeItem("tracker_ip");
    sessionStorage.removeItem("tracker_port");
    sessionStorage.removeItem("public_ip");
    sessionStorage.removeItem("username");
    window.location.href = "login.html";
}

// Bắt sự kiện Enter input
document.getElementById("msgInput").addEventListener("keypress", function(event) {
    if (event.key === "Enter") {
        sendMessage();
    }
});

targetSelect.addEventListener("change", updateChatTitle);
modeInputs.forEach((input) => input.addEventListener("change", updateChatTitle));

// Run Polling
setInterval(fetchPeers, 3000);
setInterval(fetchMessages, 2000);
setInterval(heartbeat, 4000);
fetchPeers();
fetchMessages();
heartbeat();
updateChatTitle();
