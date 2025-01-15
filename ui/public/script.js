let messages = [];
let isMotionEnabled = false;
let currentResponse = '';
let isGenerating = false;

const chatContainer = document.getElementById('chatContainer');
const userInput = document.getElementById('userInput');
const sendButton = document.getElementById('sendButton');
const modelSelect = document.getElementById('modelSelect');
const temperature = document.getElementById('temperature');
const motionToggle = document.getElementById('motionToggle');

// メッセージ追加関数
function addMessage(content, isUser) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
    messageDiv.textContent = content;
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// モーションボタンのトグル
motionToggle.addEventListener('click', () => {
    isMotionEnabled = !isMotionEnabled;
    motionToggle.textContent = `モーション: ${isMotionEnabled ? 'オン' : 'オフ'}`;
    motionToggle.classList.toggle('active', isMotionEnabled);
});

// チャット送信処理
async function sendChat() {
    if (isGenerating || !userInput.value.trim()) return;

    const message = userInput.value.trim();
    addMessage(message, true);
    messages.push({ role: "user", content: message });
    userInput.value = '';
    sendButton.disabled = true;
    isGenerating = true;

    try {
        const endpoint = isMotionEnabled ? 'chat_and_motion' : 'chat';
        const eventSource = new EventSource(`http://localhost:8000/${endpoint}?${new URLSearchParams({
            messages: JSON.stringify(messages),
            model: modelSelect.value,
            temperature: temperature.value
        })}`);

        let botMessageDiv = null;
        currentResponse = '';

        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (!botMessageDiv) {
                botMessageDiv = document.createElement('div');
                botMessageDiv.className = 'message bot-message';
                chatContainer.appendChild(botMessageDiv);
            }
            botMessageDiv.textContent += data.content;
            currentResponse += data.content;
            chatContainer.scrollTop = chatContainer.scrollHeight;
        };

        eventSource.onerror = (error) => {
            console.error('EventSource error:', error);
            eventSource.close();
            messages.push({ role: "assistant", content: currentResponse });
            currentResponse = '';
            sendButton.disabled = false;
            isGenerating = false;
        };

    } catch (error) {
        console.error('Error:', error);
        addMessage('エラーが発生しました。もう一度お試しください。', false);
        sendButton.disabled = false;
        isGenerating = false;
    }
}

// 送信ボタンのイベントリスナー
sendButton.addEventListener('click', sendChat);

// エンターキーでの送信（Shift + Enterで改行）
userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendChat();
    }
});
