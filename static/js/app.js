// Senior Living Recommendation System - Frontend JavaScript

// ========================================
// Global State
// ========================================

let currentView = 'consultation';
let currentTab = 'audio';
let selectedFile = null;
let communities = [];
let editingCommunityId = null;

// ========================================
// Initialization
// ========================================

document.addEventListener('DOMContentLoaded', () => {
    initializeNavigation();
    initializeTabs();
    initializeAudioUpload();
    initializeConsultationForms();
    initializeDatabaseSearch();
    initializeLiveSession();
    checkSystemHealth();
});

// ========================================
// Navigation
// ========================================

function initializeNavigation() {
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const view = link.dataset.view;
            switchView(view);
        });
    });
}

function switchView(view) {
    currentView = view;

    // Update nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.toggle('active', link.dataset.view === view);
    });

    // Update views
    document.querySelectorAll('.view').forEach(viewEl => {
        viewEl.classList.toggle('active', viewEl.id === `${view}-view`);
    });

    // Load data for specific views
    if (view === 'database') {
        loadCommunities();
        loadDatabaseStats();
    }
}

// ========================================
// Tabs (Audio/Text)
// ========================================

function initializeTabs() {
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const tabName = tab.dataset.tab;
            switchTab(tabName);
        });
    });
}

function switchTab(tabName) {
    currentTab = tabName;

    // Update tab buttons
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.tab === tabName);
    });

    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === `${tabName}-tab`);
    });
}

// ========================================
// Audio Upload
// ========================================

function initializeAudioUpload() {
    const uploadArea = document.getElementById('upload-area');
    const audioFile = document.getElementById('audio-file');
    const processBtn = document.getElementById('process-audio-btn');

    // Click to upload
    uploadArea.addEventListener('click', () => {
        audioFile.click();
    });

    // File selection
    audioFile.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });

    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            handleFileSelect(e.dataTransfer.files[0]);
        }
    });
}

function handleFileSelect(file) {
    // Validate file type
    const validTypes = ['audio/m4a', 'audio/mp3', 'audio/mpeg', 'audio/wav', 'audio/ogg'];
    const validExtensions = ['.m4a', '.mp3', '.wav', '.ogg'];
    const isValid = validTypes.includes(file.type) ||
                   validExtensions.some(ext => file.name.toLowerCase().endsWith(ext));

    if (!isValid) {
        showError('Invalid file type. Please upload M4A, MP3, WAV, or OGG files.');
        return;
    }

    // Validate file size (50MB)
    if (file.size > 50 * 1024 * 1024) {
        showError('File too large. Maximum file size is 50MB.');
        return;
    }

    selectedFile = file;

    // Update UI
    document.getElementById('file-name').textContent = file.name;
    document.getElementById('file-size').textContent = formatFileSize(file.size);
    document.getElementById('upload-area').style.display = 'none';
    document.getElementById('file-preview').style.display = 'block';
    document.getElementById('process-audio-btn').disabled = false;
}

function clearAudioFile() {
    selectedFile = null;
    document.getElementById('audio-file').value = '';
    document.getElementById('upload-area').style.display = 'block';
    document.getElementById('file-preview').style.display = 'none';
    document.getElementById('process-audio-btn').disabled = true;
}

// ========================================
// Consultation Processing
// ========================================

function initializeConsultationForms() {
    document.getElementById('process-audio-btn').addEventListener('click', processAudioConsultation);
    document.getElementById('process-text-btn').addEventListener('click', processTextConsultation);
}

async function processAudioConsultation() {
    if (!selectedFile) return;

    const pushToCRM = document.getElementById('push-to-crm-audio').checked;
    const language = document.getElementById('language-select-consultation').value;

    const formData = new FormData();
    formData.append('audio', selectedFile);
    formData.append('push_to_crm', pushToCRM);
    formData.append('language', language);

    showLoading('Processing audio consultation...');

    try {
        const response = await fetch('/api/process-audio', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (!response.ok) {
            // Show logs even on error
            if (result.logs) {
                updateProgressLogs(result.logs);
            }
            throw new Error(result.error || 'Processing failed');
        }

        // Display logs before showing results
        if (result.logs) {
            updateProgressLogs(result.logs);
        }

        // Brief delay to let user see the final logs
        await new Promise(resolve => setTimeout(resolve, 1000));

        displayResults(result);
    } catch (error) {
        showError(`Error: ${error.message}`);
    } finally {
        hideLoading();
    }
}

async function processTextConsultation() {
    const text = document.getElementById('text-input').value.trim();

    if (!text) {
        showError('Please enter consultation text');
        return;
    }

    const pushToCRM = document.getElementById('push-to-crm-text').checked;
    const language = document.getElementById('language-select-consultation').value;

    showLoading('Processing text consultation...');

    try {
        const response = await fetch('/api/process-text', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: text,
                push_to_crm: pushToCRM,
                language: language
            })
        });

        const result = await response.json();

        if (!response.ok) {
            // Show logs even on error
            if (result.logs) {
                updateProgressLogs(result.logs);
            }
            throw new Error(result.error || 'Processing failed');
        }

        // Display logs before showing results
        if (result.logs) {
            updateProgressLogs(result.logs);
        }

        // Brief delay to let user see the final logs
        await new Promise(resolve => setTimeout(resolve, 1000));

        displayResults(result);
    } catch (error) {
        showError(`Error: ${error.message}`);
    } finally {
        hideLoading();
    }
}

// ========================================
// Results Display
// ========================================

function displayResults(result) {
    const resultsSection = document.getElementById('results-section');
    const clientInfo = document.getElementById('client-info');
    const recommendations = document.getElementById('recommendations');
    const metricsInfo = document.getElementById('metrics-info');

    // Show results section
    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ behavior: 'smooth' });

    // Display client info
    const client = result.client_info || {};
    clientInfo.innerHTML = `
        <h3>Client Information</h3>
        <div class="info-grid">
            <div class="info-item">
                <span class="info-label">Care Level</span>
                <span class="info-value">${client.care_level || 'N/A'}</span>
            </div>
            <div class="info-item">
                <span class="info-label">Budget</span>
                <span class="info-value">$${(client.budget || 0).toLocaleString()}</span>
            </div>
            <div class="info-item">
                <span class="info-label">Timeline</span>
                <span class="info-value">${client.timeline || 'N/A'}</span>
            </div>
            <div class="info-item">
                <span class="info-label">Location</span>
                <span class="info-value">${client.location_preference || 'N/A'}</span>
            </div>
        </div>
        ${result.crm_pushed ? `
            <div style="margin-top: 1rem; padding: 1rem; background: #D1FAE5; border-radius: 0.5rem; color: #065F46;">
                ✓ Results pushed to Google Sheets CRM (Consultation #${result.consultation_id})
            </div>
        ` : ''}
    `;

    // Display recommendations
    const recs = result.recommendations || [];
    recommendations.innerHTML = recs.map((rec, index) => {
        const rankClass = index === 0 ? 'gold' : index === 1 ? 'silver' : index === 2 ? 'bronze' : '';

        return `
            <div class="recommendation-card">
                <div class="rank-badge ${rankClass}">${rec.final_rank}</div>
                <div class="recommendation-header">
                    <h3>Community ${rec.community_id}</h3>
                    <div class="recommendation-score">
                        Combined Score: ${rec.combined_rank_score.toFixed(2)} (lower is better)
                    </div>
                </div>
                <div class="metrics-row">
                    <div class="metric">
                        <span class="metric-label">Monthly Fee</span>
                        <span class="metric-value">$${((rec.key_metrics && rec.key_metrics.monthly_fee) || 0).toLocaleString()}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Distance</span>
                        <span class="metric-value">${((rec.key_metrics && rec.key_metrics.distance_miles) || 0).toFixed(2)} mi</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Availability</span>
                        <span class="metric-value">${(rec.key_metrics && rec.key_metrics.est_waitlist) || 'Unknown'}</span>
                    </div>
                </div>
                <div class="reasoning">
                    <div class="reasoning-label">AI Reasoning</div>
                    <div class="reasoning-text">${(rec.explanations && rec.explanations.holistic_reason) || 'No reasoning available'}</div>
                </div>
            </div>
        `;
    }).join('');

    // Display metrics - FIX: Use performance_metrics not metrics
    const perfMetrics = result.performance_metrics || {};
    const timings = perfMetrics.timings || {};
    const tokenCounts = perfMetrics.token_counts || {};
    const costs = perfMetrics.costs || {};

    metricsInfo.innerHTML = `
        <h3>Performance Metrics</h3>
        <div class="metrics-grid">
            <div class="metric-item">
                <span class="metric-item-label">Processing Time</span>
                <span class="metric-item-value">${(timings.e2e_total || 0).toFixed(1)}s</span>
            </div>
            <div class="metric-item">
                <span class="metric-item-label">Total Tokens</span>
                <span class="metric-item-value">${(tokenCounts.total_tokens || 0).toLocaleString()}</span>
            </div>
            <div class="metric-item">
                <span class="metric-item-label">Total Cost</span>
                <span class="metric-item-value">$${(costs.total_cost || 0).toFixed(6)}</span>
            </div>
            <div class="metric-item">
                <span class="metric-item-label">Recommendations</span>
                <span class="metric-item-value">${recs.length}</span>
            </div>
        </div>
    `;
}

function clearResults() {
    document.getElementById('results-section').style.display = 'none';
    document.getElementById('text-input').value = '';
    clearAudioFile();
}

// ========================================
// Database Management
// ========================================

function initializeDatabaseSearch() {
    const searchInput = document.getElementById('search-communities');
    searchInput.addEventListener('input', (e) => {
        filterCommunities(e.target.value);
    });
}

async function loadCommunities() {
    showLoading('Loading communities...');

    try {
        const response = await fetch('/api/communities');
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to load communities');
        }

        communities = data.communities;
        displayCommunities(communities);
    } catch (error) {
        showError(`Error loading communities: ${error.message}`);
    } finally {
        hideLoading();
    }
}

function displayCommunities(communitiesToDisplay) {
    const tbody = document.getElementById('communities-tbody');

    if (communitiesToDisplay.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="loading">No communities found</td></tr>';
        return;
    }

    tbody.innerHTML = communitiesToDisplay.map(comm => `
        <tr>
            <td><strong>${comm.CommunityID}</strong></td>
            <td>${comm['Care Level'] || 'N/A'}</td>
            <td>$${(comm['Monthly Fee'] || 0).toLocaleString()}</td>
            <td>${comm.ZIP || 'N/A'}</td>
            <td>
                <span class="badge ${comm.Enhanced ? 'success' : 'error'}">
                    ${comm.Enhanced ? 'Yes' : 'No'}
                </span>
            </td>
            <td>${comm['Est. Waitlist Length'] || 'Unconfirmed'}</td>
            <td>
                <div class="actions-group">
                    <button class="btn-icon" onclick="editCommunity(${comm.CommunityID})" title="Edit">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                        </svg>
                    </button>
                    <button class="btn-icon" onclick="deleteCommunity(${comm.CommunityID})" title="Delete">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        </svg>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

function filterCommunities(searchTerm) {
    const filtered = communities.filter(comm => {
        const term = searchTerm.toLowerCase();
        return (
            String(comm.CommunityID).includes(term) ||
            (comm['Care Level'] || '').toLowerCase().includes(term) ||
            (comm.ZIP || '').toLowerCase().includes(term) ||
            (comm['Est. Waitlist Length'] || '').toLowerCase().includes(term)
        );
    });
    displayCommunities(filtered);
}

async function loadDatabaseStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();

        if (!response.ok) {
            throw new Error(stats.error || 'Failed to load stats');
        }

        document.getElementById('stat-total').textContent = stats.total_communities;
        document.getElementById('stat-fee').textContent = `$${Math.round(stats.avg_monthly_fee).toLocaleString()}`;
        document.getElementById('stat-enhanced').textContent = stats.enhanced_available;
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// ========================================
// Community CRUD Operations
// ========================================

function showAddCommunityModal() {
    editingCommunityId = null;
    document.getElementById('modal-title').textContent = 'Add Community';
    document.getElementById('save-btn-text').textContent = 'Save Community';
    document.getElementById('community-form').reset();
    document.getElementById('community-modal').classList.add('active');
}

async function editCommunity(communityId) {
    editingCommunityId = communityId;
    document.getElementById('modal-title').textContent = 'Edit Community';
    document.getElementById('save-btn-text').textContent = 'Update Community';

    showLoading('Loading community...');

    try {
        const response = await fetch(`/api/communities/${communityId}`);
        const community = await response.json();

        if (!response.ok) {
            throw new Error(community.error || 'Failed to load community');
        }

        // Populate form
        document.getElementById('community-id').value = community.CommunityID;
        document.getElementById('care-level').value = community['Type of Service'] || '';
        document.getElementById('monthly-fee').value = community['Monthly Fee'] || '';
        document.getElementById('zip-code').value = community.ZIP || '';
        document.getElementById('apartment-type').value = community['Apartment Type'] || '';
        document.getElementById('deposit').value = community.Deposit || '';
        document.getElementById('move-in-fee').value = community['Move-In Fee'] || '';
        document.getElementById('second-person-fee').value = community['2nd Person Fee'] || '';
        document.getElementById('pet-fee').value = community['Pet Fee'] || '';
        document.getElementById('community-fee').value = community['Community Fee - One Time'] || '';
        document.getElementById('contract-rate').value = community['Contract (w rate)?'] || '';
        document.getElementById('waitlist').value = community['Est. Waitlist Length'] || 'Unconfirmed';
        document.getElementById('work-placement').value = community['Work with Placement?'] ? 'TRUE' : 'FALSE';
        document.getElementById('enhanced').checked = community.Enhanced || false;
        document.getElementById('enriched').checked = community.Enriched || false;

        document.getElementById('community-modal').classList.add('active');
    } catch (error) {
        showError(`Error: ${error.message}`);
    } finally {
        hideLoading();
    }
}

async function saveCommunity() {
    const data = {
        'Type of Service': document.getElementById('care-level').value,
        'Monthly Fee': parseFloat(document.getElementById('monthly-fee').value),
        'ZIP': document.getElementById('zip-code').value,
        'Apartment Type': document.getElementById('apartment-type').value || '',
        'Deposit': parseFloat(document.getElementById('deposit').value) || 0,
        'Move-In Fee': parseFloat(document.getElementById('move-in-fee').value) || 0,
        '2nd Person Fee': parseFloat(document.getElementById('second-person-fee').value) || 0,
        'Pet Fee': parseFloat(document.getElementById('pet-fee').value) || 0,
        'Community Fee - One Time': parseFloat(document.getElementById('community-fee').value) || 0,
        'Contract (w rate)?': parseFloat(document.getElementById('contract-rate').value) || 0,
        'Est. Waitlist Length': document.getElementById('waitlist').value,
        'Work with Placement?': document.getElementById('work-placement').value === 'TRUE',
        'Enhanced': document.getElementById('enhanced').checked,
        'Enriched': document.getElementById('enriched').checked
    };

    showLoading(editingCommunityId ? 'Updating community...' : 'Adding community...');

    try {
        const url = editingCommunityId
            ? `/api/communities/${editingCommunityId}`
            : '/api/communities';

        const method = editingCommunityId ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || 'Failed to save community');
        }

        closeCommunityModal();
        await loadCommunities();
        await loadDatabaseStats();

        showSuccess(result.message);
    } catch (error) {
        showError(`Error: ${error.message}`);
    } finally {
        hideLoading();
    }
}

async function deleteCommunity(communityId) {
    if (!confirm(`Are you sure you want to delete Community ${communityId}? This cannot be undone.`)) {
        return;
    }

    showLoading('Deleting community...');

    try {
        const response = await fetch(`/api/communities/${communityId}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || 'Failed to delete community');
        }

        await loadCommunities();
        await loadDatabaseStats();

        showSuccess(result.message);
    } catch (error) {
        showError(`Error: ${error.message}`);
    } finally {
        hideLoading();
    }
}

function closeCommunityModal() {
    document.getElementById('community-modal').classList.remove('active');
    document.getElementById('community-form').reset();
    editingCommunityId = null;
}

// ========================================
// System Health Check
// ========================================

async function checkSystemHealth() {
    try {
        const response = await fetch('/api/health');
        const health = await response.json();

        if (!health.gemini_configured) {
            showError('Warning: Gemini API key not configured. Please add GEMINI_API_KEY to .env file.');
        }
    } catch (error) {
        console.error('Health check failed:', error);
    }
}

// ========================================
// UI Utilities
// ========================================

function showLoading(message = 'Loading...') {
    document.getElementById('loading-text').textContent = message;
    document.getElementById('progress-log').innerHTML = ''; // Clear previous logs
    document.getElementById('loading-overlay').classList.add('active');
}

function hideLoading() {
    document.getElementById('loading-overlay').classList.remove('active');
}

function updateProgressLogs(logs) {
    if (!logs || logs.length === 0) return;

    const logContainer = document.getElementById('progress-log');

    logs.forEach(log => {
        const entry = document.createElement('div');
        entry.className = 'log-entry';

        // Classify log type
        if (log.includes('PHASE') || log.includes('PROCESSING') || log.includes('INITIALIZING')) {
            entry.classList.add('phase');
        } else if (log.includes('[SUCCESS]') || log.includes('[OK]') || log.includes('[COMPLETE]')) {
            entry.classList.add('success');
        } else if (log.includes('[WARNING]') || log.includes('[RETRY]')) {
            entry.classList.add('warning');
        } else if (log.includes('[ERROR]') || log.includes('Error') || log.includes('failed')) {
            entry.classList.add('error');
        }

        entry.textContent = log;
        logContainer.appendChild(entry);
    });

    // Auto-scroll to bottom
    logContainer.scrollTop = logContainer.scrollHeight;
}

function showError(message) {
    alert('❌ ' + message);
}

function showSuccess(message) {
    alert('✓ ' + message);
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}

// ========================================
// Live Session
// ========================================

let socket = null;
let liveSessionActive = false;
let mediaRecorder = null;
let audioContext = null;
let audioStream = null;
let sessionId = null;
let audioBuffer = [];
let silenceStartTime = null;
let isUserSpeaking = false;
let silenceThreshold = 0.01; // Minimum audio level to consider as speech
let silenceDuration = 500; // ms of silence before considering turn ended
let audioBufferTimeout = null;

function initializeLiveSession() {
    // Initialize Socket.IO connection
    socket = io();

    // Socket event handlers
    socket.on('connect', () => {
        console.log('Connected to server');
    });

    socket.on('session_started', (data) => {
        console.log('Session started:', data);
        sessionId = data.session_id;
        updateSessionStatus('active', 'Session active');
        document.getElementById('start-session-btn').style.display = 'none';
        document.getElementById('stop-session-btn').style.display = 'inline-flex';
        document.getElementById('audio-visualization').style.display = 'block';
        startAudioCapture();
    });

    socket.on('session_stopped', (data) => {
        console.log('Session stopped:', data);
        stopLiveSession();
    });

    socket.on('live_message', (data) => {
        handleLiveMessage(data);
    });

    socket.on('error', (data) => {
        showError(data.message || 'An error occurred');
        stopLiveSession();
    });

    // Button handlers
    document.getElementById('start-session-btn').addEventListener('click', startLiveSession);
    document.getElementById('stop-session-btn').addEventListener('click', stopLiveSession);
}

function startLiveSession() {
    if (liveSessionActive) return;

    const language = document.getElementById('language-select-live').value;
    sessionId = 'session_' + Date.now();

    // Request microphone permission and start session
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then((stream) => {
            audioStream = stream;
            socket.emit('start_live_session', {
                session_id: sessionId,
                language: language
            });
        })
        .catch((error) => {
            showError('Microphone access denied. Please allow microphone access to use live sessions.');
            console.error('Microphone error:', error);
        });
}

function stopLiveSession() {
    if (!liveSessionActive && !sessionId) return;

    // Clear any pending timeouts
    if (audioBufferTimeout) {
        clearTimeout(audioBufferTimeout);
        audioBufferTimeout = null;
    }

    if (sessionId) {
        socket.emit('stop_live_session', { session_id: sessionId });
    }

    // Stop audio capture
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
    }
    if (audioStream) {
        audioStream.getTracks().forEach(track => track.stop());
        audioStream = null;
    }
    if (audioContext) {
        audioContext.close();
        audioContext = null;
    }

    // Reset state
    liveSessionActive = false;
    sessionId = null;
    audioBuffer = [];
    silenceStartTime = null;
    isUserSpeaking = false;
    
    updateSessionStatus('inactive', 'Ready to start');
    document.getElementById('start-session-btn').style.display = 'inline-flex';
    document.getElementById('stop-session-btn').style.display = 'none';
    document.getElementById('audio-visualization').style.display = 'none';
}

function startAudioCapture() {
    if (!audioStream) return;

    try {
        // Reset state
        audioBuffer = [];
        silenceStartTime = null;
        isUserSpeaking = false;
        
        // Create audio context - note: sampleRate option may not be supported in all browsers
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const source = audioContext.createMediaStreamSource(audioStream);
        
        // Use ScriptProcessorNode for audio processing
        // Buffer size: 4096 samples, 1 input channel, 1 output channel
        const processor = audioContext.createScriptProcessor(4096, 1, 1);
        
        // Track if we need to resample
        const targetSampleRate = 16000;
        const sourceSampleRate = audioContext.sampleRate;
        const needsResampling = sourceSampleRate !== targetSampleRate;
        
        // Helper function to convert array buffer to base64
        function arrayBufferToBase64(buffer) {
            const bytes = new Uint8Array(buffer);
            let binary = '';
            const chunkSize = 8192; // Process in chunks to avoid stack overflow
            for (let i = 0; i < bytes.length; i += chunkSize) {
                const chunk = bytes.subarray(i, i + chunkSize);
                binary += String.fromCharCode.apply(null, chunk);
            }
            return btoa(binary);
        }
        
        // Simple resampling function (linear interpolation)
        function resampleAudio(inputData, fromRate, toRate) {
            if (fromRate === toRate) return inputData;
            
            const ratio = fromRate / toRate;
            const outputLength = Math.round(inputData.length / ratio);
            const output = new Float32Array(outputLength);
            
            for (let i = 0; i < outputLength; i++) {
                const index = i * ratio;
                const indexFloor = Math.floor(index);
                const indexCeil = Math.min(indexFloor + 1, inputData.length - 1);
                const fraction = index - indexFloor;
                
                output[i] = inputData[indexFloor] * (1 - fraction) + inputData[indexCeil] * fraction;
            }
            
            return output;
        }
        
        // Calculate RMS (Root Mean Square) for voice activity detection
        function calculateRMS(data) {
            let sum = 0;
            for (let i = 0; i < data.length; i++) {
                sum += data[i] * data[i];
            }
            return Math.sqrt(sum / data.length);
        }
        
        // Normalize audio to improve transcription quality
        function normalizeAudio(data) {
            // Find peak amplitude
            let maxAmplitude = 0;
            for (let i = 0; i < data.length; i++) {
                const abs = Math.abs(data[i]);
                if (abs > maxAmplitude) {
                    maxAmplitude = abs;
                }
            }
            
            // Normalize if peak is too low (amplify) or too high (reduce)
            if (maxAmplitude > 0 && maxAmplitude < 0.5) {
                // Amplify quiet audio
                const gain = 0.7 / maxAmplitude; // Target 70% of max
                for (let i = 0; i < data.length; i++) {
                    data[i] = Math.max(-1, Math.min(1, data[i] * gain));
                }
            } else if (maxAmplitude > 0.95) {
                // Reduce clipping
                const gain = 0.9 / maxAmplitude;
                for (let i = 0; i < data.length; i++) {
                    data[i] = data[i] * gain;
                }
            }
            
            return data;
        }
        
        // Send buffered audio
        function sendBufferedAudio(endOfTurn = false) {
            if (audioBuffer.length === 0) return;
            
            // Combine all buffered chunks
            const totalLength = audioBuffer.reduce((sum, chunk) => sum + chunk.length, 0);
            const combined = new Int16Array(totalLength);
            let offset = 0;
            for (const chunk of audioBuffer) {
                combined.set(chunk, offset);
                offset += chunk.length;
            }
            
            // Convert to base64
            const base64 = arrayBufferToBase64(combined.buffer);
            
            // Send to server
            socket.emit('send_audio', {
                session_id: sessionId,
                audio: base64,
                end_of_turn: endOfTurn
            });
            
            // Clear buffer
            audioBuffer = [];
        }

        processor.onaudioprocess = (e) => {
            if (!liveSessionActive || !sessionId) return;

            try {
                let inputData = e.inputBuffer.getChannelData(0);
                
                // Calculate RMS to detect voice activity
                const rms = calculateRMS(inputData);
                const hasVoice = rms > silenceThreshold;
                
                const now = Date.now();
                
                if (hasVoice) {
                    // User is speaking
                    if (!isUserSpeaking) {
                        isUserSpeaking = true;
                        silenceStartTime = null;
                        // Clear any pending silence timeout
                        if (audioBufferTimeout) {
                            clearTimeout(audioBufferTimeout);
                            audioBufferTimeout = null;
                        }
                    }
                    
                    // Normalize audio to improve quality
                    inputData = normalizeAudio(inputData);
                    
                    // Resample if needed
                    if (needsResampling) {
                        inputData = resampleAudio(inputData, sourceSampleRate, targetSampleRate);
                    }
                    
                    // Convert float32 (-1 to 1) to int16 (-32768 to 32767)
                    const pcmData = new Int16Array(inputData.length);
                    for (let i = 0; i < inputData.length; i++) {
                        const sample = Math.max(-1, Math.min(1, inputData[i]));
                        // Convert to 16-bit PCM (little-endian)
                        pcmData[i] = sample < 0 ? sample * 0x8000 : sample * 0x7FFF;
                    }
                    
                    // Add to buffer
                    audioBuffer.push(pcmData);
                    
                    // Send buffered audio periodically while speaking (every ~200ms)
                    if (audioBuffer.length >= 5) { // ~200ms of audio at 16kHz
                        sendBufferedAudio(false);
                    }
                } else {
                    // Silence detected
                    if (isUserSpeaking) {
                        // User just stopped speaking
                        if (silenceStartTime === null) {
                            silenceStartTime = now;
                        }
                        
                        // If silence continues for threshold duration, end turn
                        if (now - silenceStartTime >= silenceDuration) {
                            isUserSpeaking = false;
                            
                            // Send any remaining buffered audio with end_of_turn
                            if (audioBuffer.length > 0) {
                                sendBufferedAudio(true);
                            }
                            
                            silenceStartTime = null;
                        } else {
                            // Still in silence period, buffer small amount of silence
                            if (needsResampling) {
                                inputData = resampleAudio(inputData, sourceSampleRate, targetSampleRate);
                            }
                            
                            const pcmData = new Int16Array(inputData.length);
                            for (let i = 0; i < inputData.length; i++) {
                                const sample = Math.max(-1, Math.min(1, inputData[i]));
                                pcmData[i] = sample < 0 ? sample * 0x8000 : sample * 0x7FFF;
                            }
                            
                            // Only buffer a small amount of silence
                            if (audioBuffer.length < 2) {
                                audioBuffer.push(pcmData);
                            }
                        }
                    }
                    // If not speaking, ignore silence completely
                }
            } catch (error) {
                console.error('Error processing audio chunk:', error);
            }
        };

        source.connect(processor);
        processor.connect(audioContext.destination);
        liveSessionActive = true;
        
        console.log(`Audio capture started. Source sample rate: ${sourceSampleRate}Hz, Target: ${targetSampleRate}Hz, Resampling: ${needsResampling}`);
        console.log(`Voice Activity Detection: Threshold=${silenceThreshold}, Silence duration=${silenceDuration}ms`);
    } catch (error) {
        console.error('Audio capture error:', error);
        showError('Failed to start audio capture: ' + error.message);
    }
}

function handleLiveMessage(data) {
    if (data.session_id !== sessionId) return;

    const transcriptionBox = document.getElementById('transcription-box');
    const placeholder = transcriptionBox.querySelector('.transcription-placeholder');
    
    if (placeholder) {
        placeholder.remove();
    }

    let messageDiv = document.createElement('div');
    messageDiv.className = 'transcription-message';

    const msg = data.message || data;
    if (msg.type === 'user_transcript') {
        // STRICT FILTER: Block any non-English characters client-side as well
        const transcriptText = msg.text || '';
        
        // Check for non-ASCII characters (Hindi, Spanish accents, etc.)
        if (/[^\x00-\x7F]/.test(transcriptText)) {
            console.warn('[LANGUAGE FILTER] Blocked non-English transcription:', transcriptText.substring(0, 50));
            // Don't display non-English transcriptions
            return;
        }
        
        messageDiv.classList.add('user-message');
        messageDiv.innerHTML = `
            <div class="message-label">You:</div>
            <div class="message-text">${escapeHtml(transcriptText)}</div>
        `;
    } else if (msg.type === 'model_transcript') {
        messageDiv.classList.add('ai-message');
        messageDiv.innerHTML = `
            <div class="message-label">AI:</div>
            <div class="message-text">${escapeHtml(msg.text || '')}</div>
        `;
    } else if (msg.type === 'error') {
        messageDiv.classList.add('error-message');
        messageDiv.innerHTML = `
            <div class="message-label">Error:</div>
            <div class="message-text">${escapeHtml(msg.message || '')}</div>
        `;
    } else if (msg.type === 'function_call') {
        // Handle function calls silently for now
        return;
    } else {
        // Fallback for any other message format
        messageDiv.classList.add('info-message');
        messageDiv.innerHTML = `
            <div class="message-text">${escapeHtml(JSON.stringify(msg))}</div>
        `;
    }

    transcriptionBox.appendChild(messageDiv);
    transcriptionBox.scrollTop = transcriptionBox.scrollHeight;
}

function updateSessionStatus(status, text) {
    const indicator = document.getElementById('status-indicator');
    const statusText = document.getElementById('status-text');
    
    indicator.className = 'status-indicator ' + status;
    statusText.textContent = text;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
