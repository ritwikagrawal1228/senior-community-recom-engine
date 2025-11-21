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

