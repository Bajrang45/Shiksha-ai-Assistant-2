const user = JSON.parse(localStorage.getItem('shiksha_user') || 'null');
if (!user || !localStorage.getItem('shiksha_token')) window.location.replace('index.html');
else { document.querySelector('#student-name').textContent = user.name.split(' ')[0]; document.querySelector('#avatar').textContent = user.name.charAt(0).toUpperCase(); }

const workspace = document.querySelector('#ai-workspace');
const fileInput = document.querySelector('#file-input');
const token = () => localStorage.getItem('shiksha_token');
function apiUrl() {
  const saved = localStorage.getItem('shiksha_api_url');
  const base = saved?.trim() || 'https://shiksha-ai-assistant.onrender.com';
  return base.replace(/\/+$|\/api$/g, '') + '/api';
}
const localHistoryKey = 'shiksha_chat_history';
function logout() { localStorage.removeItem('shiksha_token'); localStorage.removeItem('shiksha_user'); window.location.replace('index.html'); }
document.querySelector('#logout').onclick = logout;
document.querySelector('#logout-top').onclick = logout;

// ── Toast Notifications ──
const toastContainer = (() => { const el = document.createElement('div'); el.id = 'toast-container'; document.body.appendChild(el); return el; })();
function showToast(msg, type = 'info', duration = 3500) { const t = document.createElement('div'); t.className = `toast ${type}`; t.textContent = msg; toastContainer.appendChild(t); setTimeout(() => { t.classList.add('removing'); t.addEventListener('animationend', () => t.remove()); }, duration); }

// ── Typing Indicator ──
function showTypingIndicator() { const md = workspace.querySelector('#chat-messages'); if (!md) return null; const el = document.createElement('div'); el.className = 'typing-indicator'; el.id = 'typing-ind'; el.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>'; md.appendChild(el); md.scrollTop = md.scrollHeight; return el; }
function removeTypingIndicator() { const el = workspace.querySelector('#typing-ind'); if (el) el.remove(); }

function messageFromDetail(detail, fallback) {
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) return detail.map((item) => item.msg || fallback).join(' ');
  return fallback;
}

async function apiError(response, fallback) {
  let detail = fallback;
  try { const data = await response.json(); detail = messageFromDetail(data.detail, fallback); } catch (_) { /* use readable fallback for non-JSON failures */ }
  if (response.status === 401) {
    localStorage.removeItem('shiksha_token'); localStorage.removeItem('shiksha_user');
    detail = 'Your session expired because the local API restarted. Please log in again.';
  }
  return new Error(detail);
}

function setActive(view) { document.querySelectorAll('[data-view]').forEach((item) => item.classList.toggle('active', item.dataset.view === view)); }
function showWorkspace(view) {
  workspace.hidden = false; setActive(view);
  if (view === 'flashcards') {
    workspace.innerHTML = `<div class="view-content"><p class="card-kicker">ACTIVE RECALL</p><h2>Generate flashcards</h2><p>Turn your uploaded notes into short cards for quick, focused revision.</p><form id="flashcards-form" class="inline-form"><input id="flashcards-topic" required placeholder="For example: Newton's laws" /><button class="btn btn-coral">Generate cards</button></form><button class="text-button" data-action="upload">Need notes? Upload a file first</button><p class="workspace-message"></p><section id="flashcards-result" class="flashcards-result" hidden></section></div>`;
    workspace.scrollIntoView({ behavior: 'smooth', block: 'start' });
    return;
  }
  if (view === 'chat') {
    workspace.innerHTML = `<div class="chat-layout"><section><div class="chat-header"><p class="card-kicker">RAG-POWERED AI ASSISTANT</p><h2>🤖 Ask Shiksha about your notes</h2></div><div id="chat-messages" class="chat-messages"></div><form id="chat-form" class="chat-box"><textarea id="chat-question" required placeholder="Type your question about your uploaded notes..."></textarea><div class="chat-tools"><button class="tool-button" type="button" data-action="voice" aria-label="Voice assistant">🎤</button><button class="tool-button" id="tts-button" type="button" aria-label="Read out loud">🔊</button><button class="tool-button" type="button" data-action="upload" aria-label="Attach a file">📎</button><button class="btn btn-coral" type="submit">Send <span>→</span></button></div></form><div class="example-questions"><button type="button">Explain Ohm's Law</button><button type="button">Summarize this chapter</button><button type="button">Create MCQs</button><button type="button">Explain in Marathi</button></div><p class="workspace-message" aria-live="polite"></p></section><aside class="chat-side"><h3>💡 Learn with your notes</h3><p>Shiksha searches your uploaded material first, then creates a clear explanation grounded in those sources.</p><h3>Recent questions</h3><div id="history-list"></div></aside></div>`;
    loadHistory();
  } else if (view === 'quizzes') {
    workspace.innerHTML = `<div class="view-content"><p class="card-kicker">AI PRACTICE MODE</p><h2>◉ Generate a quiz from your notes</h2><p>Choose a topic and Shiksha will create questions to test your understanding.</p><form id="quiz-form" class="inline-form"><input id="quiz-topic" required placeholder="For example: Ohm's Law" /><button class="btn btn-coral">Create quiz</button></form><p class="workspace-message"></p><section id="quiz-result" class="quiz-result" hidden></section></div>`;
  } else if (view === 'flashcards') {
    workspace.innerHTML = `<div class="view-content"><p class="card-kicker">ACTIVE RECALL</p><h2>▣ Generate flashcards</h2><p>Upload a document, then turn its most important concepts into quick revision cards.</p><button class="btn btn-coral" data-action="upload">Upload notes <span>→</span></button></div>`;
  }
  workspace.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function showProcessing(file) {
  const status = document.querySelector('#upload-status'); status.hidden = false;
  status.innerHTML = `<div class="processing-title"><span id="process-label">Uploading ${file.name}...</span><span id="process-percent">10%</span></div><div class="processing-bar"><i id="process-bar" style="width:10%"></i></div><div class="process-list"><span>○ Uploading file</span><span>○ Reading PDF</span><span>○ Creating embeddings</span><span>○ Understanding notes</span><span>○ Generating flashcards</span><span>○ Generating quiz</span></div>`;
  return status;
}
function updateProcessing(status, index, label, percent) {
  const tasks = status.querySelectorAll('.process-list span'); tasks.forEach((task, i) => task.className = i < index ? 'done' : i === index ? 'active' : '');
  status.querySelector('#process-label').textContent = label; status.querySelector('#process-percent').textContent = `${percent}%`; status.querySelector('#process-bar').style.width = `${percent}%`;
}
async function uploadFile(file) {
  const status = showProcessing(file); const phases = [['Uploading file...', 18], ['Reading PDF...', 38], ['Creating embeddings...', 59], ['Understanding notes...', 76], ['Generating flashcards...', 88], ['Generating quiz...', 100]];
  let phase = 0; updateProcessing(status, phase, phases[phase][0], phases[phase][1]);
  const timer = setInterval(() => { phase = Math.min(phase + 1, phases.length - 2); updateProcessing(status, phase, phases[phase][0], phases[phase][1]); }, 650);
  try {
    const body = new FormData(); body.append('file', file);
    const response = await fetch(`${apiUrl()}/materials/upload`, { method: 'POST', headers: { Authorization: `Bearer ${token()}` }, body });
    if (!response.ok) throw await apiError(response, 'Unable to process this file.');
    const data = await response.json();
    clearInterval(timer); updateProcessing(status, 5, 'Done ✓ Your notes are ready for AI chat.', 100);
    status.insertAdjacentHTML('beforeend', `<p class="upload-ready"><b>${data.filename}</b> is ready. ${data.characters_extracted.toLocaleString()} characters understood. <button data-action="chat">Ask Shiksha →</button></p>`);
    showToast(`✅ ${data.filename} uploaded successfully!`, 'success');
  } catch (error) { clearInterval(timer); status.innerHTML = `<p class="workspace-message">${error.message || 'Upload failed. Please try again.'}</p>`; showToast(error.message || 'Upload failed.', 'error'); }
  finally { fileInput.value = ''; }
}

function saveHistory(question, answer, source) { const history = JSON.parse(localStorage.getItem(localHistoryKey) || '[]'); history.unshift({ question, answer, source, created_at: new Date().toISOString() }); localStorage.setItem(localHistoryKey, JSON.stringify(history.slice(0, 20))); }
function renderHistory(items) { const list = document.querySelector('#history-list'); if (!list) return; list.replaceChildren(); if (!items.length) { list.textContent = 'No questions yet.'; return; } items.slice(0, 5).forEach((item) => { const button = document.createElement('button'); button.className = 'history-item'; button.type = 'button'; button.textContent = item.question; button.onclick = () => displayAnswer(item.answer, item.source); list.append(button); }); }
async function loadHistory() { const local = JSON.parse(localStorage.getItem(localHistoryKey) || '[]'); renderHistory(local); try { const response = await fetch(`${apiUrl()}/chat/history`, { headers: { Authorization: `Bearer ${token()}` } }); if (response.ok) { const remote = await response.json(); if (remote.length) renderHistory(remote); } } catch (_) { /* local history remains available */ } }
function displayAnswer(answerText, source = {}, questionText = '') { const messagesDiv = workspace.querySelector('#chat-messages'); if (!messagesDiv) return; if (questionText) messagesDiv.insertAdjacentHTML('beforeend', `<div class="chat-bubble user-bubble">${questionText}</div>`); messagesDiv.insertAdjacentHTML('beforeend', `<div class="chat-bubble ai-bubble"><div class="bubble-content"><p>${answerText}</p></div>${source && source.filename ? `<div class="source-card"><span>📄</span><div><small>SOURCE</small><b class="source-name">${source.filename}</b><small class="source-page">${source.page ? `Page ${source.page}` : 'Relevant passage'}</small></div><strong class="confidence">${source.confidence || 97}%</strong></div>` : ''}</div>`); messagesDiv.scrollTop = messagesDiv.scrollHeight; window.lastAiAnswer = answerText; }

document.addEventListener('click', (event) => {
  const action = event.target.closest('[data-action]')?.dataset.action; const view = event.target.closest('[data-view]')?.dataset.view;
  if (view) showWorkspace(view); if (action === 'upload') fileInput.click(); if (action === 'chat') showWorkspace('chat');
  if (action === 'summary') { showWorkspace('chat'); document.querySelector('#chat-question').value = 'Summarize this chapter into the key ideas.'; }
  if (action === 'voice') { showWorkspace('chat'); const message = workspace.querySelector('.workspace-message'); message.textContent = 'Voice assistant is ready — speak your study question.'; }
  if (event.target.matches('.example-questions button')) document.querySelector('#chat-question').value = event.target.textContent;
});
fileInput.onchange = () => { if (fileInput.files[0]) uploadFile(fileInput.files[0]); };

function startVoiceInput() {
  showWorkspace('chat');
  const message = workspace.querySelector('.workspace-message');
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Recognition) { showToast('Voice input not supported. Try Chrome.', 'error'); return; }
  const recognition = new Recognition();
  const langSel = document.querySelector('#language-selector')?.value || 'English';
  recognition.lang = langSel === 'Hindi' ? 'hi-IN' : langSel === 'Marathi' ? 'mr-IN' : 'en-IN';
  recognition.interimResults = false; recognition.maxAlternatives = 1;
  const micBtn = workspace.querySelector('[data-action="voice"]');
  if (micBtn) micBtn.classList.add('listening');
  showToast('🎤 Listening… speak your question.', 'info', 2500);
  recognition.onresult = (event) => { document.querySelector('#chat-question').value = event.results[0][0].transcript; if (micBtn) micBtn.classList.remove('listening'); showToast('✅ Voice captured! Press Send.', 'success'); };
  recognition.onerror = () => { if (micBtn) micBtn.classList.remove('listening'); showToast('Could not hear audio. Allow microphone access.', 'error'); };
  recognition.onend = () => { if (micBtn) micBtn.classList.remove('listening'); };
  recognition.start();
}

document.addEventListener('click', (event) => {
  if (event.target.closest('[data-action="voice"]')) startVoiceInput();
  if (event.target.closest('#tts-button')) {
    if (!window.lastAiAnswer) return;
    const utterance = new SpeechSynthesisUtterance(window.lastAiAnswer);
    const lang = document.querySelector('#language-selector').value;
    if (lang === 'Hindi') utterance.lang = 'hi-IN';
    else if (lang === 'Marathi') utterance.lang = 'mr-IN';
    else utterance.lang = 'en-US';
    window.speechSynthesis.speak(utterance);
  }
});

const dropZone = document.querySelector('#drop-zone');['dragenter', 'dragover'].forEach((name) => dropZone.addEventListener(name, (event) => { event.preventDefault(); dropZone.classList.add('dragging'); }));['dragleave', 'drop'].forEach((name) => dropZone.addEventListener(name, (event) => { event.preventDefault(); dropZone.classList.remove('dragging'); })); dropZone.addEventListener('drop', (event) => { const file = event.dataTransfer.files[0]; if (file) uploadFile(file); });

document.addEventListener('submit', async (event) => {
  if (event.target.id === 'flashcards-form') {
    event.preventDefault();
    const topic = document.querySelector('#flashcards-topic').value.trim();
    const button = event.target.querySelector('button');
    const result = document.querySelector('#flashcards-result');
    const message = workspace.querySelector('.workspace-message');
    button.disabled = true; button.textContent = 'Creating...'; message.textContent = '';
    try {
      const response = await fetch(`${apiUrl()}/flashcards`, { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token()}` }, body: JSON.stringify({ topic }) });
      if (!response.ok) throw await apiError(response, 'Unable to create flashcards.');
      const data = await response.json(); result.replaceChildren();
      data.cards.forEach((card, index) => {
        const element = document.createElement('div'); element.className = 'flashcard-container';
        element.innerHTML = `<div class="flashcard-inner"><div class="flashcard-front"><small>CARD ${index + 1}</small><h3></h3><p class="click-hint">Click to flip ↩</p></div><div class="flashcard-back"><p></p></div></div>`;
        element.querySelector('h3').textContent = card.front; element.querySelector('.flashcard-back p').textContent = card.back;
        element.onclick = () => element.querySelector('.flashcard-inner').classList.toggle('flipped');
        result.append(element);
      });
      result.hidden = false;
      showToast(`🃏 ${data.cards.length} flashcards created!`, 'success');
    } catch (error) { message.textContent = error.message || 'Unable to create flashcards.'; showToast(error.message || 'Flashcard error.', 'error'); }
    finally { button.disabled = false; button.textContent = 'Generate cards'; }
  }
  if (event.target.id === 'chat-form') {
    event.preventDefault(); const question = document.querySelector('#chat-question').value.trim(); const button = event.target.querySelector('[type="submit"]'); const message = workspace.querySelector('.workspace-message'); if (!question) return; button.disabled = true; button.innerHTML = '<span class="btn-spinner">⏳</span> Thinking...'; message.textContent = ''; document.querySelector('#chat-question').value = '';
    const typingEl = showTypingIndicator();
    try { const lang = document.querySelector('#language-selector')?.value || 'English'; const response = await fetch(`${apiUrl()}/chat`, { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token()}` }, body: JSON.stringify({ question: `${question} (Answer in ${lang})` }) }); removeTypingIndicator(); if (!response.ok) throw await apiError(response, 'Unable to get an answer.'); const data = await response.json(); displayAnswer(data.answer, data.source, question); saveHistory(question, data.answer, data.source); loadHistory(); } catch (error) { removeTypingIndicator(); showToast(error.message || 'AI chat error.', 'error'); message.textContent = error.message || 'Unable to connect to AI chat.'; } finally { button.disabled = false; button.innerHTML = 'Send <span>→</span>'; }
  }
  if (event.target.id === 'quiz-form') { event.preventDefault(); const topic = document.querySelector('#quiz-topic').value.trim(); const button = event.target.querySelector('button'); const result = document.querySelector('#quiz-result'); const message = workspace.querySelector('.workspace-message'); button.disabled = true; button.textContent = 'Creating...'; try { const response = await fetch(`${apiUrl()}/quizzes`, { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token()}` }, body: JSON.stringify({ topic }) }); const data = await response.json(); if (!response.ok) throw new Error(data.detail || 'Unable to create a quiz.'); result.replaceChildren(); data.questions.forEach((item, index) => { const question = document.createElement('details'); question.className = 'quiz-question'; question.innerHTML = `<summary>${index + 1}. ${item.question}</summary><p>Answer: ${item.answer}</p>`; result.append(question); }); result.hidden = false; } catch (error) { message.textContent = error.message; } finally { button.disabled = false; button.textContent = 'Create quiz'; } }
});
