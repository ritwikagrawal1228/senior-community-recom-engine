// Senior Living Recommendation System - Frontend JavaScript

// Global error handler to catch any JavaScript errors
window.onerror = function(message, source, lineno, colno, error) {
    console.error('JavaScript Error:', message, 'at', source, 'line', lineno);
    return false;
};

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
    console.log('DOM loaded, initializing app...');
    initializeThemeSystem();
    initializeNavigation();
    initializeTabs();
    initializeAudioUpload();
    initializeConsultationForms();
    initializeDatabaseSearch();
    initializeFilters();
    initializeFloatingLabels();
    initializeViewToggle();
    initializeVoiceAgent();
    checkSystemHealth();
    console.log('App initialization complete');
});

// ========================================
// Theme System
// ========================================

function initializeThemeSystem() {
    // Detect system preference
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const savedTheme = localStorage.getItem('theme');
    const theme = savedTheme || (prefersDark ? 'dark' : 'light');
    
    document.documentElement.setAttribute('data-theme', theme);
    
    // Create toggle button
    const toggle = document.createElement('button');
    toggle.className = 'theme-toggle';
    toggle.setAttribute('aria-label', 'Toggle theme');
    toggle.innerHTML = theme === 'dark' ? '☀️' : '🌙';
    
    toggle.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        toggle.innerHTML = newTheme === 'dark' ? '☀️' : '🌙';
    });
    
    // Watch system preference changes
    window.matchMedia('(prefers-color-scheme: dark)')
        .addEventListener('change', (e) => {
            if (!localStorage.getItem('theme')) {
                document.documentElement.setAttribute('data-theme', e.matches ? 'dark' : 'light');
                toggle.innerHTML = e.matches ? '☀️' : '🌙';
            }
        });
    
    // Add to navbar
    const navLinks = document.querySelector('.nav-links');
    if (navLinks) {
        navLinks.insertBefore(toggle, navLinks.firstChild);
    }
}

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

    // Update views with animation
    document.querySelectorAll('.view').forEach(viewEl => {
        const isActive = viewEl.id === `${view}-view`;
        if (isActive) {
            viewEl.classList.add('active');
            // Trigger animation
            viewEl.style.animation = 'none';
            setTimeout(() => {
                viewEl.style.animation = '';
            }, 10);
        } else {
            viewEl.classList.remove('active');
        }
    });

    // Load data for specific views
    if (view === 'database') {
        loadCommunities();
        loadDatabaseStats();
    } else if (view === 'history') {
        loadHistory();
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
    const selectBtn = uploadArea?.querySelector('.select-file-btn');
    
    if (!uploadArea || !audioFile) {
        console.warn('Upload area or audio file input not found');
        return;
    }
    
    // Remove any existing event listeners by cloning
    const newAudioFile = audioFile.cloneNode(true);
    audioFile.parentNode.replaceChild(newAudioFile, audioFile);
    
    // Get reference to the new element
    const audioInput = document.getElementById('audio-file');
    
    // Single file change handler
    audioInput.addEventListener('change', function(e) {
        e.stopPropagation();
        if (this.files && this.files.length > 0) {
            console.log('File selected:', this.files[0].name);
            handleFileSelect(this.files[0]);
        }
    });

    // Use a label-based approach for the button to avoid double-click issues
    if (selectBtn) {
        // Convert button to trigger input directly
        selectBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            audioInput.value = ''; // Clear previous selection
            audioInput.click();
        });
    }

    // Click on upload area (excluding button and input)
    uploadArea.addEventListener('click', function(e) {
        // Only trigger if clicking on the area itself, not children that handle their own clicks
        if (e.target === uploadArea || 
            e.target.closest('.upload-icon') || 
            e.target.tagName === 'H3' || 
            e.target.tagName === 'P') {
            e.preventDefault();
            audioInput.value = ''; // Clear previous selection
            audioInput.click();
        }
    });

    // Drag and drop
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        e.stopPropagation();
        this.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        e.stopPropagation();
        this.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        e.stopPropagation();
        this.classList.remove('dragover');
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            handleFileSelect(e.dataTransfer.files[0]);
        }
    });
    
    console.log('Audio upload initialized');
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
    console.log('processAudioConsultation started');
    if (!selectedFile) {
        console.log('No file selected');
        return;
    }

    const pushToCRM = document.getElementById('push-to-crm-audio').checked;
    const language = document.getElementById('language-select-consultation').value;
    console.log('Processing with language:', language, 'pushToCRM:', pushToCRM);

    const formData = new FormData();
    formData.append('audio', selectedFile);
    formData.append('push_to_crm', pushToCRM);
    formData.append('language', language);

    showLoading('Processing audio consultation...');
    console.log('Loading overlay shown');

    try {
        console.log('Sending API request...');
        const response = await fetch('/api/process-audio', {
            method: 'POST',
            body: formData
        });
        console.log('API response received, status:', response.status);

        const result = await response.json();
        console.log('API result parsed:', result);

        if (!response.ok) {
            // Show logs even on error
            if (result.logs) {
                updateProgressLogs(result.logs);
            }
            throw new Error(result.error || 'Processing failed');
        }

        // Display logs before showing results
        if (result.logs) {
            console.log('Updating progress logs');
            updateProgressLogs(result.logs);
        }

        // Brief delay to let user see the final logs
        console.log('Waiting 1s before displaying results...');
        await new Promise(resolve => setTimeout(resolve, 1000));

        console.log('Calling displayResults...');
        displayResults(result);
        console.log('displayResults completed');
    } catch (error) {
        console.error('Error in processAudioConsultation:', error);
        showError(`Error: ${error.message}`);
    } finally {
        console.log('Hiding loading overlay');
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
    console.log('displayResults called with:', result);
    
    try {
        const resultsSection = document.getElementById('results-section');
        const analysisContent = document.getElementById('analysis-content');
        const clientInfo = document.getElementById('client-info');
        const recommendations = document.getElementById('recommendations');
        const metricsInfo = document.getElementById('metrics-info');
        
        console.log('DOM elements found:', {
            resultsSection: !!resultsSection,
            analysisContent: !!analysisContent,
            clientInfo: !!clientInfo,
            recommendations: !!recommendations,
            metricsInfo: !!metricsInfo
        });

        if (!resultsSection) {
            console.error('results-section element not found!');
            return;
        }

        // Show results section with animation
        resultsSection.style.display = 'block';
    resultsSection.style.opacity = '0';
    resultsSection.style.transform = 'translateY(20px)';
    
    // Animate in
    requestAnimationFrame(() => {
        resultsSection.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        resultsSection.style.opacity = '1';
        resultsSection.style.transform = 'translateY(0)';
        
        // Scroll into view after animation starts
        setTimeout(() => {
            resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);
    });

    // Store run_id for fetching transcription later
    if (result.run_id) {
        resultsSection.dataset.runId = result.run_id;
    }
    
    // Display Analysis Details - Transcription & Extracted Info (Collapsible)
    const client = result.client_info || {};
    const specialNeeds = client.special_needs || {};
    
    // Build extracted info items
    const extractedItems = [
        { label: 'Care Level', value: client.care_level },
        { label: 'Budget', value: client.budget ? `$${Number(client.budget).toLocaleString()}` : null },
        { label: 'Timeline', value: client.timeline },
        { label: 'Location/ZIP', value: client.location_preference },
        { label: 'Client Name', value: client.client_name },
        { label: 'Enhanced Services', value: client.enhanced ? 'Yes' : 'No' },
        { label: 'Enriched Housing', value: client.enriched ? 'Yes' : 'No' },
        { label: 'Pets', value: specialNeeds.pets },
        { label: 'Couples', value: specialNeeds.couples },
        { label: 'Apartment Preference', value: specialNeeds.apartment_type_preference },
    ].filter(item => item.value && item.value !== 'N/A' && item.value !== 'Unknown');
    
    // Get transcription if available (for text input, it's the input itself)
    const transcription = result.transcription || result.logs?.find(l => l.includes('Transcription:'))?.split('Transcription:')[1]?.trim() || null;
    
    if (analysisContent) {
        analysisContent.innerHTML = `
            ${transcription ? `
                <div class="analysis-section">
                    <div class="analysis-section-title">🎙️ Transcription / Input</div>
                    <div class="transcription-box">${escapeHtml(transcription)}</div>
                </div>
            ` : ''}
            
            <div class="analysis-section">
                <div class="analysis-section-title">🔍 AI-Extracted Information</div>
                <div class="extracted-info-grid">
                    ${extractedItems.map(item => `
                        <div class="extracted-item">
                            <span class="extracted-label">${item.label}</span>
                            <span class="extracted-value">${item.value}</span>
                        </div>
                    `).join('')}
                </div>
                ${client.notes ? `
                    <div style="margin-top: var(--spacing-md);">
                        <div class="analysis-section-title">📝 Additional Notes</div>
                        <div class="transcription-box">${escapeHtml(client.notes)}</div>
                    </div>
                ` : ''}
            </div>
            
            ${result.run_id ? `
                <div style="margin-top: var(--spacing-md); text-align: center;">
                    <button class="btn btn-outline btn-sm" onclick="viewTranscription('${result.run_id}')">
                        📋 View Full Run Details
                    </button>
                </div>
            ` : ''}
        `;
    }
    
    // Display client info - Compact summary card
    clientInfo.innerHTML = `
        <div class="client-info-header">
            <h3>Client Requirements</h3>
        </div>
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
            <div class="crm-pushed-badge">
                <span>✓</span> Pushed to CRM (Consultation #${result.consultation_id})
            </div>
        ` : ''}
    `;

    // Display recommendations - Vertical hierarchy with full community data
    const recs = result.recommendations || [];
    recommendations.innerHTML = recs.map((rec, index) => {
        const rankClass = index === 0 ? 'gold' : index === 1 ? 'silver' : index === 2 ? 'bronze' : '';
        const km = rec.key_metrics || {};
        const cd = rec.community_data || {}; // Full community data from database
        
        // Format currency helper
        const fmt = (val) => val != null && !isNaN(val) ? `$${Number(val).toLocaleString()}` : 'N/A';
        const fmtNum = (val, suffix = '') => val != null && !isNaN(val) ? `${Number(val).toLocaleString()}${suffix}` : 'N/A';

        return `
            <div class="recommendation-card expanded" role="article" aria-label="Recommendation ${rec.final_rank}: Community ${rec.community_id}">
                <div class="rec-header-row">
                    <div class="rank-badge ${rankClass}">${rec.final_rank}</div>
                    <div class="rec-title">
                        <h3>Community ${rec.community_id}</h3>
                        <span class="recommendation-score">Score: ${rec.combined_rank_score.toFixed(0)}</span>
                    </div>
                    <button class="btn btn-sm btn-outline" onclick="toggleCommunityDetails(this)">
                        📋 Details
                    </button>
                </div>
                
                <div class="rec-reasoning">
                    ${(rec.explanations && rec.explanations.holistic_reason) || 'No reasoning available'}
                </div>
                
                <div class="community-data-grid">
                    <div class="data-section">
                        <h4>💰 Pricing</h4>
                        <div class="data-row"><span>Monthly Fee</span><strong>${fmt(cd['Monthly Fee'])}</strong></div>
                        <div class="data-row"><span>Deposit</span><strong>${fmt(cd['Deposit'])}</strong></div>
                        <div class="data-row"><span>Move-In Fee</span><strong>${fmt(cd['Move-In Fee'])}</strong></div>
                        <div class="data-row"><span>Community Fee</span><strong>${fmt(cd['Community Fee - One Time'])}</strong></div>
                        <div class="data-row"><span>2nd Person Fee</span><strong>${fmt(cd['2nd Person Fee'])}</strong></div>
                        <div class="data-row"><span>Pet Fee</span><strong>${fmt(cd['Pet Fee'])}</strong></div>
                    </div>
                    
                    <div class="data-section">
                        <h4>🏠 Details</h4>
                        <div class="data-row"><span>Care Type</span><strong>${cd['Type of Service'] || 'N/A'}</strong></div>
                        <div class="data-row"><span>Apartment</span><strong>${cd['Apartment Type'] || 'N/A'}</strong></div>
                        <div class="data-row"><span>ZIP Code</span><strong>${cd['ZIP'] || 'N/A'}</strong></div>
                        <div class="data-row"><span>Distance</span><strong>${fmtNum(km.distance_miles, ' mi')}</strong></div>
                        <div class="data-row"><span>Enhanced</span><strong>${cd['Enhanced'] || 'N/A'}</strong></div>
                        <div class="data-row"><span>Enriched</span><strong>${cd['Enriched'] || 'N/A'}</strong></div>
                    </div>
                    
                    <div class="data-section">
                        <h4>📅 Availability</h4>
                        <div class="data-row"><span>Waitlist</span><strong>${cd['Est. Waitlist Length'] || km.est_waitlist || 'N/A'}</strong></div>
                        <div class="data-row"><span>Contract Rate</span><strong>${cd['Contract (w rate)?'] || 'N/A'}</strong></div>
                        <div class="data-row"><span>Works w/ Placement</span><strong>${cd['Work with Placement?'] || 'N/A'}</strong></div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    // Add entrance animation to recommendation cards
    setTimeout(() => {
        const cards = recommendations.querySelectorAll('.recommendation-card');
        cards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            setTimeout(() => {
                card.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 50);
        });
    }, 50);

    // Display performance metrics with real historical charts
    const perfMetrics = result.performance_metrics || {};
    const timings = perfMetrics.timings || {};
    const tokenCounts = perfMetrics.token_counts || {};
    const costs = perfMetrics.costs || {};
    
    metricsInfo.innerHTML = `
        <h3>Performance Stats</h3>
        <div class="metrics-grid">
            <div class="metric-item">
                <span class="metric-item-label">⏱️ Processing Time</span>
                <span class="metric-item-value">${(timings.e2e_total || 0).toFixed(1)}s</span>
                <div class="mini-chart" id="chart-processing-time"></div>
            </div>
            <div class="metric-item">
                <span class="metric-item-label">🔤 Tokens Used</span>
                <span class="metric-item-value">${(tokenCounts.total_tokens || 0).toLocaleString()}</span>
                <div class="mini-chart" id="chart-tokens"></div>
            </div>
            <div class="metric-item">
                <span class="metric-item-label">💵 API Cost</span>
                <span class="metric-item-value">$${(costs.total_cost || 0).toFixed(4)}</span>
                <div class="mini-chart" id="chart-cost"></div>
            </div>
        </div>
    `;
    
    // Fetch and render real historical charts
    loadHistoricalCharts();
    
    console.log('displayResults completed successfully');
    } catch (err) {
        console.error('Error in displayResults:', err);
        throw err;
    }
}

function clearResults() {
    document.getElementById('results-section').style.display = 'none';
    document.getElementById('text-input').value = '';
    clearAudioFile();
}

// ========================================
// History View
// ========================================

async function loadHistory() {
    try {
        const typeFilter = document.getElementById('history-type-filter')?.value || 'all';
        const statusFilter = document.getElementById('history-status-filter')?.value || 'all';
        
        const params = new URLSearchParams();
        if (typeFilter !== 'all') params.append('type', typeFilter);
        if (statusFilter !== 'all') params.append('status', statusFilter);
        
        const response = await fetch(`/api/run-logs?${params.toString()}`);
        if (!response.ok) throw new Error('Failed to load history');
        
        const data = await response.json();
        const historyList = document.getElementById('history-list');
        
        if (!data.runs || data.runs.length === 0) {
            historyList.innerHTML = `
                <div class="empty-state">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <circle cx="12" cy="12" r="10"></circle>
                        <polyline points="12 6 12 12 16 14"></polyline>
                    </svg>
                    <h3>No Consultation History</h3>
                    <p>Your consultation history will appear here</p>
                </div>
            `;
            return;
        }
        
        historyList.innerHTML = data.runs.map(run => {
            const date = new Date(run.created_at);
            const typeIcon = run.input_type === 'voice_agent' ? '🎤' : run.input_type === 'audio' ? '🎵' : '📝';
            const statusBadge = run.status === 'completed' ? 
                '<span class="badge badge-success">Completed</span>' : 
                '<span class="badge badge-error">Failed</span>';
            
            return `
                <div class="history-item" onclick="viewHistoryDetail('${run.run_id}')">
                    <div class="history-item-header">
                        <div class="history-item-icon">${typeIcon}</div>
                        <div class="history-item-info">
                            <h4>${run.input_type === 'voice_agent' ? 'Voice Consultation' : run.input_type === 'audio' ? 'Audio Consultation' : 'Text Consultation'}</h4>
                            <p class="history-meta">${date.toLocaleString()} • ${run.username || 'Unknown'}</p>
                        </div>
                        ${statusBadge}
                    </div>
                    <div class="history-item-details">
                        <div class="detail-item">
                            <span class="detail-label">Processing Time:</span>
                            <span class="detail-value">${run.processing_time_seconds ? run.processing_time_seconds.toFixed(2) + 's' : 'N/A'}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Recommendations:</span>
                            <span class="detail-value">${run.recommendations ? JSON.parse(run.recommendations).length : 0}</span>
                        </div>
                        ${run.crm_pushed ? '<div class="detail-item"><span class="badge badge-info">CRM Pushed</span></div>' : ''}
                    </div>
                </div>
            `;
        }).join('');
        
    } catch (error) {
        console.error('Error loading history:', error);
        document.getElementById('history-list').innerHTML = `
            <div class="error-state">
                <p>Failed to load history. Please try again.</p>
                <button class="btn btn-primary" onclick="loadHistory()">Retry</button>
            </div>
        `;
    }
}

function viewHistoryDetail(runId) {
    viewTranscription(runId);
}

// ========================================
// Transcription Viewer
// ========================================

async function viewTranscription(runId) {
    try {
        showLoading('Loading transcription...');
        
        const response = await fetch(`/api/run-logs/${runId}`);
        if (!response.ok) {
            throw new Error('Failed to fetch transcription');
        }
        
        const data = await response.json();
        
        // Create modal content
        const modalContent = `
            <div class="transcription-modal">
                <div class="transcription-header">
                    <h3>📝 Transcription & Extracted Info</h3>
                    <span class="transcription-meta">Run ID: ${runId}</span>
                </div>
                
                <div class="transcription-section">
                    <h4>🎤 Full Transcription</h4>
                    <div class="transcription-text">
                        ${data.transcription || 'No transcription available'}
                    </div>
                </div>
                
                <div class="transcription-section">
                    <h4>📋 Extracted Client Information</h4>
                    <div class="extracted-info">
                        ${data.client_info ? `
                            <div class="info-row"><strong>Care Level:</strong> ${data.client_info.care_level || 'N/A'}</div>
                            <div class="info-row"><strong>Budget:</strong> $${(data.client_info.budget || 0).toLocaleString()}</div>
                            <div class="info-row"><strong>Timeline:</strong> ${data.client_info.timeline || 'N/A'}</div>
                            <div class="info-row"><strong>Location:</strong> ${data.client_info.location_preference || 'N/A'}</div>
                            ${data.client_info.special_requirements ? `
                                <div class="info-row"><strong>Special Requirements:</strong> ${data.client_info.special_requirements}</div>
                            ` : ''}
                        ` : 'No client info extracted'}
                    </div>
                </div>
                
                <div class="transcription-section">
                    <h4>📊 Run Metadata</h4>
                    <div class="metadata-grid">
                        <div><strong>Input Type:</strong> ${data.input_type}</div>
                        <div><strong>Language:</strong> ${data.language}</div>
                        <div><strong>Processing Time:</strong> ${data.processing_time_seconds?.toFixed(1) || 'N/A'}s</div>
                        <div><strong>Tokens Used:</strong> ${data.tokens_used?.toLocaleString() || 'N/A'}</div>
                        <div><strong>API Cost:</strong> $${data.api_cost?.toFixed(4) || 'N/A'}</div>
                        <div><strong>Created:</strong> ${new Date(data.created_at).toLocaleString()}</div>
                    </div>
                </div>
            </div>
        `;
        
        // Show in a modal
        showTranscriptionModal(modalContent);
        
    } catch (error) {
        showError(`Error loading transcription: ${error.message}`);
    } finally {
        hideLoading();
    }
}

function showTranscriptionModal(content) {
    // Remove existing modal if any
    const existingModal = document.getElementById('transcription-modal');
    if (existingModal) existingModal.remove();
    
    // Create modal
    const modal = document.createElement('div');
    modal.id = 'transcription-modal';
    modal.className = 'modal active';
    modal.innerHTML = `
        <div class="modal-overlay" onclick="closeTranscriptionModal()"></div>
        <div class="modal-content transcription-modal-content">
            <button class="modal-close" onclick="closeTranscriptionModal()">×</button>
            ${content}
        </div>
    `;
    
    document.body.appendChild(modal);
    document.body.style.overflow = 'hidden';
}

function closeTranscriptionModal() {
    const modal = document.getElementById('transcription-modal');
    if (modal) {
        modal.remove();
        document.body.style.overflow = '';
    }
}

// Expose globally
window.viewTranscription = viewTranscription;
window.closeTranscriptionModal = closeTranscriptionModal;

// Escape HTML to prevent XSS
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Toggle analysis details section
function toggleAnalysisDetails() {
    const analysisCard = document.getElementById('analysis-details');
    if (analysisCard) {
        analysisCard.classList.toggle('collapsed');
    }
}
window.toggleAnalysisDetails = toggleAnalysisDetails;

// Toggle community details visibility
function toggleCommunityDetails(btn) {
    const card = btn.closest('.recommendation-card');
    const grid = card.querySelector('.community-data-grid');
    
    if (grid.style.display === 'none') {
        grid.style.display = 'grid';
        btn.textContent = '📋 Hide';
    } else {
        grid.style.display = 'none';
        btn.textContent = '📋 Details';
    }
}

window.toggleCommunityDetails = toggleCommunityDetails;

// ========================================
// Historical Charts
// ========================================

async function loadHistoricalCharts() {
    try {
        // Fetch all three histories in parallel
        const [timeRes, tokenRes, costRes] = await Promise.all([
            fetch('/api/run-logs/history/processing-time?limit=15'),
            fetch('/api/run-logs/history/tokens?limit=15'),
            fetch('/api/run-logs/history/cost?limit=15')
        ]);
        
        const [timeData, tokenData, costData] = await Promise.all([
            timeRes.json(),
            tokenRes.json(),
            costRes.json()
        ]);
        
        // Render charts with real data (or fallback to empty)
        const timeChart = document.getElementById('chart-processing-time');
        const tokenChart = document.getElementById('chart-tokens');
        const costChart = document.getElementById('chart-cost');
        
        if (timeChart && timeData.data?.length > 0) {
            timeChart.appendChild(MiniChart.create(timeData.data, { color: 'var(--primary)', showFill: true }));
        }
        
        if (tokenChart && tokenData.data?.length > 0) {
            tokenChart.appendChild(MiniChart.create(tokenData.data, { color: 'var(--info)', showFill: true }));
        }
        
        if (costChart && costData.data?.length > 0) {
            // Scale cost data for visibility (multiply by 1000 for cents display)
            const scaledCosts = costData.data.map(c => c * 1000);
            costChart.appendChild(MiniChart.create(scaledCosts, { color: 'var(--warning)', showFill: true }));
        }
        
    } catch (error) {
        console.warn('Failed to load historical charts:', error);
    }
}

// ========================================
// Floating Labels
// ========================================

function initializeFloatingLabels() {
    // Add floating label support to modal form inputs
    const modalForm = document.getElementById('community-form');
    if (modalForm) {
        const formGroups = modalForm.querySelectorAll('.form-group.floating-label');
        formGroups.forEach(group => {
            const input = group.querySelector('input, select');
            const label = group.querySelector('label');
            
            if (input && label) {
                // Ensure label is after input for CSS sibling selector
                if (input.nextElementSibling !== label) {
                    input.parentNode.insertBefore(label, input.nextSibling);
                }
                
                // Check initial state
                const hasValue = input.value && input.value !== '' && 
                               (input.tagName !== 'SELECT' || input.value !== '');
                
                if (hasValue) {
                    label.style.transform = 'translateY(-28px) scale(0.85)';
                    label.style.color = 'var(--primary)';
                }
                
                // Handle input changes
                const updateLabel = () => {
                    const hasValue = input.value && input.value !== '' && 
                                   (input.tagName !== 'SELECT' || input.value !== '');
                    
                    if (hasValue || document.activeElement === input) {
                        label.style.transform = 'translateY(-28px) scale(0.85)';
                        label.style.color = 'var(--primary)';
                    } else {
                        label.style.transform = '';
                        label.style.color = '';
                    }
                };
                
                input.addEventListener('input', updateLabel);
                input.addEventListener('change', updateLabel);
                input.addEventListener('focus', updateLabel);
                input.addEventListener('blur', updateLabel);
            }
        });
    }
}

// ========================================
// Database Management
// ========================================

function initializeDatabaseSearch() {
    // Search functionality is now handled by the filters panel
    // This function is kept for backwards compatibility
}

async function loadCommunities() {
    // Show skeleton loading
    showSkeletonLoading('communities-tbody');

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
        document.getElementById('communities-tbody').innerHTML = 
            '<tr><td colspan="7" class="loading">Error loading communities</td></tr>';
    }
}

function showSkeletonLoading(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    container.innerHTML = '';
    for (let i = 0; i < 5; i++) {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><div class="skeleton" style="width: 60px; height: 20px;"></div></td>
            <td><div class="skeleton" style="width: 100px; height: 20px;"></div></td>
            <td><div class="skeleton" style="width: 80px; height: 20px;"></div></td>
            <td><div class="skeleton" style="width: 70px; height: 20px;"></div></td>
            <td><div class="skeleton" style="width: 50px; height: 20px;"></div></td>
            <td><div class="skeleton" style="width: 90px; height: 20px;"></div></td>
            <td><div class="skeleton" style="width: 80px; height: 20px;"></div></td>
        `;
        container.appendChild(row);
    }
}

function displayCommunities(communitiesToDisplay) {
    const tbody = document.getElementById('communities-tbody');

    if (communitiesToDisplay.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="loading">No communities found</td></tr>';
        return;
    }

    // Animate rows appearing
    tbody.innerHTML = communitiesToDisplay.map((comm, index) => `
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
                    <button class="btn-icon" onclick="editCommunity(${comm.CommunityID})" title="Edit" aria-label="Edit community ${comm.CommunityID}">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                        </svg>
                    </button>
                    <button class="btn-icon" onclick="deleteCommunity(${comm.CommunityID})" title="Delete" aria-label="Delete community ${comm.CommunityID}">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        </svg>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
    
    // Add staggered animation to rows
    const rows = tbody.querySelectorAll('tr');
    rows.forEach((row, index) => {
        row.style.opacity = '0';
        row.style.transform = 'translateY(10px)';
        setTimeout(() => {
            row.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            row.style.opacity = '1';
            row.style.transform = 'translateY(0)';
        }, index * 50);
    });
}

function filterCommunities() {
    // Get all filter values
    const filters = {
        id: document.getElementById('filter-id')?.value?.trim() || '',
        careLevel: document.getElementById('filter-care-level')?.value || '',
        feeMin: parseFloat(document.getElementById('filter-fee-min')?.value) || 0,
        feeMax: parseFloat(document.getElementById('filter-fee-max')?.value) || Infinity,
        zip: document.getElementById('filter-zip')?.value?.trim() || '',
        enhanced: document.getElementById('filter-enhanced')?.value || '',
        waitlist: document.getElementById('filter-waitlist')?.value || ''
    };
    
    const filtered = communities.filter(comm => {
        // ID filter
        if (filters.id && !String(comm.CommunityID).includes(filters.id)) {
            return false;
        }
        
        // Care level filter
        if (filters.careLevel && (comm['Care Level'] || '') !== filters.careLevel) {
            return false;
        }
        
        // Fee range filter
        const fee = comm['Monthly Fee'] || 0;
        if (fee < filters.feeMin || fee > filters.feeMax) {
            return false;
        }
        
        // ZIP filter
        if (filters.zip && !(comm.ZIP || '').includes(filters.zip)) {
            return false;
        }
        
        // Enhanced filter
        if (filters.enhanced) {
            const isEnhanced = comm.Enhanced;
            if (filters.enhanced === 'true' && !isEnhanced) return false;
            if (filters.enhanced === 'false' && isEnhanced) return false;
        }
        
        // Waitlist filter
        if (filters.waitlist && (comm['Est. Waitlist Length'] || '') !== filters.waitlist) {
            return false;
        }
        
        return true;
    });
    
    // Update results count
    updateResultsCount(filtered.length, communities.length);
    
    // Update active filter count
    updateActiveFilterCount(filters);
    
    displayCommunities(filtered);
}

function updateResultsCount(shown, total) {
    const countEl = document.getElementById('results-count');
    if (countEl) {
        countEl.innerHTML = `Showing <strong>${shown}</strong> of <strong>${total}</strong> communities`;
    }
}

function updateActiveFilterCount(filters) {
    let count = 0;
    if (filters.id) count++;
    if (filters.careLevel) count++;
    if (filters.feeMin > 0 || filters.feeMax < Infinity) count++;
    if (filters.zip) count++;
    if (filters.enhanced) count++;
    if (filters.waitlist) count++;
    
    const countEl = document.getElementById('active-filter-count');
    if (countEl) {
        countEl.textContent = `${count} active`;
        countEl.style.display = count > 0 ? 'inline-block' : 'none';
    }
}

function initializeFilters() {
    // All filter inputs
    const filterInputs = [
        'filter-id',
        'filter-care-level',
        'filter-fee-min',
        'filter-fee-max',
        'filter-zip',
        'filter-enhanced',
        'filter-waitlist'
    ];
    
    // Add event listeners to all filters
    filterInputs.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener('input', debounce(filterCommunities, 300));
            el.addEventListener('change', filterCommunities);
        }
    });
    
    // Clear all filters button
    const clearBtn = document.getElementById('clear-all-filters');
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            filterInputs.forEach(id => {
                const el = document.getElementById(id);
                if (el) {
                    if (el.tagName === 'SELECT') {
                        el.value = '';
                    } else {
                        el.value = '';
                    }
                }
            });
            filterCommunities();
        });
    }
}

// Debounce utility
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

let previousStats = null;

async function loadDatabaseStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();

        if (!response.ok) {
            throw new Error(stats.error || 'Failed to load stats');
        }

        const totalEl = document.getElementById('stat-total');
        const feeEl = document.getElementById('stat-fee');
        const enhancedEl = document.getElementById('stat-enhanced');
        
        // Animate number changes
        if (previousStats) {
            animateNumber(totalEl, stats.total_communities);
            animateNumber(feeEl, Math.round(stats.avg_monthly_fee), '$');
            animateNumber(enhancedEl, stats.enhanced_available);
        } else {
            totalEl.textContent = stats.total_communities;
            feeEl.textContent = `$${Math.round(stats.avg_monthly_fee).toLocaleString()}`;
            enhancedEl.textContent = stats.enhanced_available;
        }
        
        // Add trend indicators if we have previous data
        if (previousStats) {
            addTrendIndicators(stats, previousStats);
        }
        
        previousStats = stats;
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

function animateNumber(element, target, prefix = '') {
    const start = parseInt(element.textContent.replace(/[^0-9]/g, '')) || 0;
    const range = target - start;
    const startTime = performance.now();
    const duration = 1000;
    
    const update = (currentTime) => {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3); // Ease out cubic
        
        const current = Math.round(start + range * eased);
        element.textContent = prefix + current.toLocaleString();
        
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    };
    
    requestAnimationFrame(update);
}

function addTrendIndicators(currentStats, previousStats) {
    // Add trend indicators to stat cards (optional enhancement)
    // This would require modifying the HTML structure
}

// ========================================
// Community CRUD Operations
// ========================================

function showAddCommunityModal() {
    editingCommunityId = null;
    const modal = document.getElementById('community-modal');
    document.getElementById('modal-title').textContent = 'Add Community';
    document.getElementById('save-btn-text').textContent = 'Save Community';
    document.getElementById('community-form').reset();
    modal.classList.add('active');
    modal.setAttribute('aria-hidden', 'false');
    
    // Reset floating labels
    modal.querySelectorAll('.form-group.floating-label label').forEach(label => {
        label.style.transform = '';
        label.style.color = '';
    });
    
    // Focus first input
    setTimeout(() => {
        const firstInput = modal.querySelector('input, select');
        if (firstInput) firstInput.focus();
    }, 100);
}

async function editCommunity(communityId) {
    editingCommunityId = communityId;
    const modal = document.getElementById('community-modal');
    document.getElementById('modal-title').textContent = 'Edit Community';
    document.getElementById('save-btn-text').textContent = 'Update Community';
    modal.setAttribute('aria-hidden', 'false');
    
    // Update floating labels after form is populated
    setTimeout(() => {
        modal.querySelectorAll('.form-group.floating-label input, .form-group.floating-label select').forEach(input => {
            const label = input.nextElementSibling;
            if (label && label.tagName === 'LABEL' && input.value) {
                label.style.transform = 'translateY(-28px) scale(0.85)';
                label.style.color = 'var(--primary)';
            }
        });
    }, 50);

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
    const modal = document.getElementById('community-modal');
    modal.classList.remove('active');
    modal.setAttribute('aria-hidden', 'true');
    document.getElementById('community-form').reset();
    editingCommunityId = null;
    
    // Reset floating labels
    modal.querySelectorAll('.form-group.floating-label label').forEach(label => {
        label.style.transform = '';
        label.style.color = '';
    });
    
    // Return focus to trigger element if available
    const trigger = document.activeElement;
    if (trigger && (trigger.classList.contains('btn-primary') || trigger.classList.contains('btn-icon'))) {
        setTimeout(() => trigger.focus(), 100);
    }
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
// Mini Chart Component
// ========================================

const MiniChart = {
    create(data, options = {}) {
        const {
            width = 100,
            height = 30,
            color = 'var(--primary)',
            fillColor = 'rgba(8, 145, 178, 0.1)',
            lineWidth = 2,
            showFill = true,
            showDots = false
        } = options;
        
        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;
        canvas.style.display = 'block';
        canvas.setAttribute('aria-hidden', 'true');
        
        const ctx = canvas.getContext('2d');
        if (data.length === 0) return canvas;
        
        const max = Math.max(...data);
        const min = Math.min(...data);
        const range = max - min || 1;
        
        const points = data.map((value, index) => ({
            x: (index / (data.length - 1)) * width,
            y: height - ((value - min) / range) * (height - 4) - 2
        }));
        
        // Draw fill
        if (showFill && points.length > 0) {
            ctx.beginPath();
            ctx.moveTo(points[0].x, height);
            points.forEach(p => ctx.lineTo(p.x, p.y));
            ctx.lineTo(points[points.length - 1].x, height);
            ctx.closePath();
            ctx.fillStyle = fillColor;
            ctx.fill();
        }
        
        // Draw line
        if (points.length > 1) {
            ctx.beginPath();
            ctx.moveTo(points[0].x, points[0].y);
            points.slice(1).forEach(p => ctx.lineTo(p.x, p.y));
            ctx.strokeStyle = color;
            ctx.lineWidth = lineWidth;
            ctx.lineCap = 'round';
            ctx.lineJoin = 'round';
            ctx.stroke();
        }
        
        // Draw dots
        if (showDots) {
            points.forEach(p => {
                ctx.beginPath();
                ctx.arc(p.x, p.y, 3, 0, Math.PI * 2);
                ctx.fillStyle = color;
                ctx.fill();
            });
        }
        
        return canvas;
    },
    
    // Generate sample trend data
    generateTrendData(length = 10, trend = 'up') {
        const data = [];
        const base = 50;
        for (let i = 0; i < length; i++) {
            let value = base;
            if (trend === 'up') {
                value += Math.random() * 30 + (i * 5);
            } else if (trend === 'down') {
                value += Math.random() * 30 - (i * 5);
            } else {
                value += Math.random() * 40 - 20;
            }
            data.push(Math.max(10, Math.min(100, value)));
        }
        return data;
    }
};

// ========================================
// Trend Indicator Component
// ========================================

const TrendIndicator = {
    create(value, previousValue, options = {}) {
        const {
            showPercent = true,
            showArrow = true,
            formatValue = (v) => v.toLocaleString()
        } = options;
        
        const change = value - previousValue;
        const percent = previousValue ? ((change / previousValue) * 100).toFixed(1) : 0;
        const isPositive = change > 0;
        const isNeutral = change === 0;
        
        const span = document.createElement('span');
        span.className = `trend-indicator ${isPositive ? 'positive' : isNeutral ? 'neutral' : 'negative'}`;
        span.setAttribute('aria-label', `${isPositive ? 'Increased' : isNeutral ? 'No change' : 'Decreased'} by ${Math.abs(percent)}%`);
        
        let html = '';
        if (showArrow && !isNeutral) {
            html += `
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                    <path d="${isPositive ? 'M18 15l-6-6-6 6' : 'M6 9l6 6 6-6'}"/>
                </svg>
            `;
        }
        if (showPercent) {
            html += `<span>${isPositive ? '+' : ''}${percent}%</span>`;
        }
        
        span.innerHTML = html;
        return span;
    }
};

// ========================================
// UI Utilities
// ========================================

function showLoading(message = 'Loading...') {
    const overlay = document.getElementById('loading-overlay');
    const text = document.getElementById('loading-text');
    const log = document.getElementById('progress-log');
    
    if (text) text.textContent = message;
    if (log) log.innerHTML = ''; // Clear previous logs
    
    // Use requestAnimationFrame for smooth display
    requestAnimationFrame(() => {
        if (overlay) overlay.classList.add('active');
    });
}

function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        // Smooth fade out
        overlay.style.opacity = '0';
        setTimeout(() => {
            overlay.classList.remove('active');
            overlay.style.opacity = '';
        }, 200);
    }
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
// View Toggle (Table/Cards)
// ========================================

function initializeViewToggle() {
    const viewBtns = document.querySelectorAll('.view-btn');
    
    viewBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const view = btn.dataset.view;
            
            // Update active state
            viewBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Toggle view
            const tableContainer = document.querySelector('.table-container');
            const cardsContainer = document.querySelector('.cards-container');
            
            if (view === 'table') {
                if (tableContainer) tableContainer.style.display = 'block';
                if (cardsContainer) cardsContainer.style.display = 'none';
            } else if (view === 'cards') {
                if (tableContainer) tableContainer.style.display = 'none';
                if (cardsContainer) {
                    cardsContainer.style.display = 'grid';
                } else {
                    // Create cards view if it doesn't exist
                    createCardsView();
                }
            }
        });
    });
}

function createCardsView() {
    const tableCard = document.querySelector('.table-card');
    if (!tableCard || !communities.length) return;
    
    // Check if cards container already exists
    let cardsContainer = document.querySelector('.cards-container');
    if (!cardsContainer) {
        cardsContainer = document.createElement('div');
        cardsContainer.className = 'cards-container';
        tableCard.appendChild(cardsContainer);
    }
    
    cardsContainer.innerHTML = communities.map(comm => `
        <div class="community-card">
            <div class="community-card-header">
                <span class="community-id">#${comm.CommunityID}</span>
                <span class="community-badge ${comm.Enhanced ? 'enhanced' : ''}">${comm.Enhanced ? 'Enhanced' : 'Standard'}</span>
            </div>
            <div class="community-card-body">
                <div class="community-info">
                    <span class="label">Care Level</span>
                    <span class="value">${comm['Care Level'] || 'N/A'}</span>
                </div>
                <div class="community-info">
                    <span class="label">Monthly Fee</span>
                    <span class="value">$${(comm['Monthly Fee'] || 0).toLocaleString()}</span>
                </div>
                <div class="community-info">
                    <span class="label">ZIP Code</span>
                    <span class="value">${comm.ZIP || 'N/A'}</span>
                </div>
                <div class="community-info">
                    <span class="label">Waitlist</span>
                    <span class="value">${comm['Est. Waitlist Length'] || 'N/A'}</span>
                </div>
            </div>
            <div class="community-card-actions">
                <button class="btn btn-ghost" onclick="editCommunity(${comm.CommunityID})">Edit</button>
                <button class="btn btn-ghost" onclick="deleteCommunity(${comm.CommunityID})">Delete</button>
            </div>
        </div>
    `).join('');
    
    // Hide table, show cards
    const tableContainer = document.querySelector('.table-container');
    if (tableContainer) tableContainer.style.display = 'none';
    cardsContainer.style.display = 'grid';
}

// ========================================
// Gemini Voice Agent
// ========================================

let voiceAgentState = {
    isActive: false,
    sessionId: null,
    qrCode: null,
    socket: null,
    audioContext: null,
    mediaRecorder: null,
    conversationPhase: 'collecting', // 'collecting', 'processing', 'results'
    clientInfo: {},
    recommendations: null,
    expiresIn: null,
    countdownInterval: null
};

function startSessionCountdown(seconds) {
    // Clear any existing countdown
    if (voiceAgentState.countdownInterval) {
        clearInterval(voiceAgentState.countdownInterval);
    }
    
    let remaining = seconds;
    
    const updateDisplay = () => {
        const countdown = document.getElementById('session-countdown');
        if (!countdown) return;
        
        if (remaining <= 0) {
            countdown.textContent = 'Expired';
            countdown.style.color = 'var(--error)';
            clearInterval(voiceAgentState.countdownInterval);
            
            // Auto-cleanup expired session
            showError('Session expired. Please generate a new QR code.');
            endVoiceSession();
            return;
        }
        
        const mins = Math.floor(remaining / 60);
        const secs = remaining % 60;
        
        if (remaining < 300) { // Less than 5 minutes
            countdown.style.color = 'var(--warning)';
        }
        if (remaining < 60) { // Less than 1 minute
            countdown.style.color = 'var(--error)';
            countdown.textContent = `${secs}s`;
        } else {
            countdown.textContent = `${mins}m ${secs}s`;
        }
        
        remaining--;
    };
    
    updateDisplay();
    voiceAgentState.countdownInterval = setInterval(updateDisplay, 1000);
}

function initializeVoiceAgent() {
    // Initialize Socket.IO connection if not already done
    if (typeof io !== 'undefined' && !voiceAgentState.socket) {
        voiceAgentState.socket = io();
        setupVoiceSocketListeners();
    }
}

function setupVoiceSocketListeners() {
    const socket = voiceAgentState.socket;
    if (!socket) return;
    
    socket.on('connect', () => {
        console.log('Socket.IO connected for voice agent');
    });
    
    socket.on('client_connected', (data) => {
        updateVoiceStatus('active', 'Client connected! Conversation starting...');
        addVoiceMessage('system', '✅ Client has joined the session');
    });
    
    socket.on('voice_message', (data) => {
        addVoiceMessage(data.role, data.text);
        if (data.role === 'agent') {
            updateVoiceStatus('active', 'AI is speaking...');
        }
    });
    
    socket.on('voice_status', (data) => {
        updateVoiceStatus(data.status, data.message);
        voiceAgentState.conversationPhase = data.status;
    });
    
    socket.on('voice_stopped', (data) => {
        updateVoiceStatus('', 'Session ended');
        voiceAgentState.isActive = false;
    });
    
    socket.on('error', (data) => {
        console.error('Voice agent error:', data.message);
        showError(data.message);
    });
}

async function generateVoiceSession() {
    try {
        updateVoiceStatus('connecting', 'Creating session...');
        
        // First try to load existing session
        let response = await fetch('/api/voice/create-session', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                language: 'english',
                load_existing: true
            })
        });
        
        // If no existing session, create new one
        if (!response.ok || !(await response.json()).loaded_existing) {
            response = await fetch('/api/voice/create-session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    language: 'english',
                    load_existing: false
                })
            });
        }
        
        const data = await response.json();
        
        if (!response.ok) {
            if (response.status === 429) {
                // Too many sessions
                showError(`${data.error} (${data.active_sessions}/${data.max_sessions} active)`);
                updateVoiceStatus('', 'Session limit reached');
                return;
            }
            throw new Error(data.error || 'Failed to create session');
        }
        
        voiceAgentState.sessionId = data.session_id;
        voiceAgentState.isActive = true;
        voiceAgentState.expiresIn = data.expires_in_seconds;
        
        // Update QR code display
        const qrContainer = document.getElementById('voice-qr-code');
        if (qrContainer) {
            qrContainer.innerHTML = `
                <img src="${data.qr_url}" 
                     alt="Scan to start voice consultation" 
                     class="qr-image"
                     style="border-radius: 12px;">
            `;
            qrContainer.style.cursor = 'default';
            qrContainer.onclick = null;
        }
        
        // Update session info with expiration timer
        const sessionInfo = document.getElementById('voice-session-info');
        if (sessionInfo) {
            const expiresInMins = Math.floor(data.expires_in_seconds / 60);
            sessionInfo.innerHTML = `
                <p class="session-id">Session: <code>${data.session_id.slice(-8)}</code></p>
                <p class="session-status">Share QR code with client to start</p>
                <p class="session-timer" style="font-size: 0.85rem; margin-top: 8px; color: var(--fg-secondary);">
                    ⏱️ Expires in: <span id="session-countdown">${expiresInMins} min</span>
                </p>
                <p class="session-capacity" style="font-size: 0.75rem; margin-top: 4px; color: var(--fg-muted);">
                    Active sessions: ${data.active_sessions}/${data.max_sessions}
                </p>
                <p class="session-url" style="font-size: 0.75rem; margin-top: 8px; word-break: break-all;">
                    <a href="${data.session_url}" target="_blank" style="color: var(--primary);">${data.session_url}</a>
                </p>
            `;
            
            // Start countdown timer
            startSessionCountdown(data.expires_in_seconds);
        }
        
        // Join the session room as consultant
        if (voiceAgentState.socket) {
            voiceAgentState.socket.emit('join_session', {
                session_id: data.session_id,
                client_type: 'consultant'
            });
        }
        
        updateVoiceStatus('ready', 'Waiting for client to scan QR code...');
        
        // Clear conversation
        const conversation = document.getElementById('voice-conversation');
        if (conversation) {
            conversation.innerHTML = `
                <div class="conversation-empty">
                    <div class="empty-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                            <rect x="7" y="7" width="3" height="3"></rect>
                            <rect x="14" y="7" width="3" height="3"></rect>
                            <rect x="7" y="14" width="3" height="3"></rect>
                            <rect x="14" y="14" width="3" height="3"></rect>
                        </svg>
                    </div>
                    <h3>QR Code Generated</h3>
                    <p>Have the client scan the QR code to start the voice consultation</p>
                </div>
            `;
        }
        
    } catch (error) {
        console.error('Error generating voice session:', error);
        showError('Failed to generate voice session: ' + error.message);
        updateVoiceStatus('', 'Error creating session');
    }
}

function updateVoiceStatus(status, message) {
    const statusEl = document.getElementById('voice-agent-status');
    const statusText = document.getElementById('voice-status-text');
    
    if (statusEl) {
        statusEl.className = `voice-status ${status}`;
    }
    if (statusText) {
        statusText.textContent = message;
    }
}

function startVoiceConversation() {
    voiceAgentState.isActive = true;
    voiceAgentState.conversationPhase = 'collecting';
    
    updateVoiceStatus('active', 'Client connected! Collecting information...');
    
    // Update conversation display
    addVoiceMessage('agent', "Hello! I'm your senior living placement assistant. I'm here to help find the perfect community for you or your loved one. Let's start with a few questions. What type of care are you looking for? Independent living, assisted living, or memory care?");
}

function addVoiceMessage(role, text) {
    const conversation = document.getElementById('voice-conversation');
    if (!conversation) return;
    
    const messageEl = document.createElement('div');
    messageEl.className = `voice-message ${role}`;
    messageEl.innerHTML = `
        <div class="message-avatar">${role === 'agent' ? '🤖' : '👤'}</div>
        <div class="message-content">
            <p>${text}</p>
            <span class="message-time">${new Date().toLocaleTimeString()}</span>
        </div>
    `;
    
    conversation.appendChild(messageEl);
    conversation.scrollTop = conversation.scrollHeight;
}

function simulateVoiceProcessing() {
    voiceAgentState.conversationPhase = 'processing';
    
    updateVoiceStatus('processing', 'Processing your information...');
    
    addVoiceMessage('agent', "Thank you for sharing all that information! I'm now searching our database of over 500 communities to find the best matches for you. This usually takes about 2-3 minutes. While we wait, would you like to hear about some of the amenities that are typically available at senior living communities?");
    
    // Simulate small talk during processing
    setTimeout(() => {
        addVoiceMessage('agent', "Many communities offer wonderful dining options with restaurant-style meals, fitness centers, and organized social activities. Some even have on-site salons and movie theaters!");
    }, 30000);
    
    setTimeout(() => {
        addVoiceMessage('agent', "I'm still working on finding the best matches. Did you know that most communities also offer transportation services for medical appointments and shopping trips?");
    }, 60000);
}

function showVoiceResults(recommendations) {
    voiceAgentState.conversationPhase = 'results';
    voiceAgentState.recommendations = recommendations;
    
    updateVoiceStatus('complete', 'Recommendations ready!');
    
    addVoiceMessage('agent', `Great news! I've found ${recommendations.length} excellent communities that match your needs! Let me tell you about the top recommendations...`);
    
    // Announce each recommendation
    recommendations.slice(0, 3).forEach((rec, index) => {
        setTimeout(() => {
            addVoiceMessage('agent', `Number ${index + 1}: Community ${rec.community_id}. This is a ${rec.care_level} community with a monthly fee of $${rec.monthly_fee.toLocaleString()}. It has a match score of ${rec.match_score}%. ${rec.explanation}`);
        }, (index + 1) * 5000);
    });
}

async function endVoiceSession() {
    // Clear countdown timer
    if (voiceAgentState.countdownInterval) {
        clearInterval(voiceAgentState.countdownInterval);
        voiceAgentState.countdownInterval = null;
    }
    
    if (voiceAgentState.sessionId) {
        try {
            // Call backend to end session
            await fetch(`/api/voice/session/${voiceAgentState.sessionId}/end`, {
                method: 'POST'
            });
            
            // Leave socket room
            if (voiceAgentState.socket) {
                voiceAgentState.socket.emit('leave_session', {
                    session_id: voiceAgentState.sessionId
                });
            }
        } catch (error) {
            console.error('Error ending session:', error);
        }
    }
    
    voiceAgentState.isActive = false;
    voiceAgentState.sessionId = null;
    voiceAgentState.expiresIn = null;
    
    if (voiceAgentState.audioContext) {
        voiceAgentState.audioContext.close();
        voiceAgentState.audioContext = null;
    }
    
    // Reset QR code display
    const qrContainer = document.getElementById('voice-qr-code');
    if (qrContainer) {
        qrContainer.innerHTML = `
            <div class="qr-placeholder">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                    <rect x="7" y="7" width="3" height="3"></rect>
                    <rect x="14" y="7" width="3" height="3"></rect>
                    <rect x="7" y="14" width="3" height="3"></rect>
                    <rect x="14" y="14" width="3" height="3"></rect>
                </svg>
                <p>Click to generate QR code</p>
            </div>
        `;
    }
    
    // Reset session info
    const sessionInfo = document.getElementById('voice-session-info');
    if (sessionInfo) {
        sessionInfo.innerHTML = `<p class="session-status">No active session</p>`;
    }
    
    // Reset conversation display
    const conversation = document.getElementById('voice-conversation');
    if (conversation) {
        conversation.innerHTML = `
            <div class="conversation-empty">
                <div class="empty-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path>
                        <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                        <line x1="12" y1="19" x2="12" y2="22"></line>
                    </svg>
                </div>
                <h3>No Active Conversation</h3>
                <p>Generate a QR code and have a client scan it to start a voice consultation</p>
            </div>
        `;
    }
    
    updateVoiceStatus('', 'Waiting to start...');
}

// Demo function to simulate voice conversation
async function simulateVoiceDemo() {
    // Clear any existing conversation
    const conversation = document.getElementById('voice-conversation');
    if (conversation) {
        conversation.innerHTML = '';
    }
    
    voiceAgentState.isActive = true;
    
    // Simulate the conversation flow
    const demoConversation = [
        { role: 'agent', text: "Hello! I'm your senior living placement assistant powered by AI. I'm here to help find the perfect community for you or your loved one. Let's start - what type of care are you looking for? Independent living, assisted living, or memory care?", delay: 0 },
        { role: 'user', text: "We're looking for assisted living for my mother. She needs some help with daily activities.", delay: 3000 },
        { role: 'agent', text: "I understand. Assisted living is a great choice for those who need support with daily activities while maintaining independence. What's your budget range for monthly fees?", delay: 6000 },
        { role: 'user', text: "We're hoping to stay around $4,000 to $5,500 per month.", delay: 9000 },
        { role: 'agent', text: "That's a reasonable range with many good options available. What area or ZIP code are you looking in?", delay: 12000 },
        { role: 'user', text: "We're in the 90210 area, Beverly Hills.", delay: 15000 },
        { role: 'agent', text: "Beverly Hills has some wonderful communities! Are there any special requirements? For example, does she have any pets, or would she need couples accommodation?", delay: 18000 },
        { role: 'user', text: "Yes, she has a small dog, a Pomeranian. That's very important to her.", delay: 21000 },
        { role: 'agent', text: "Absolutely, pets are family! I'll make sure to find pet-friendly communities. How soon are you looking to make this transition?", delay: 24000 },
        { role: 'user', text: "Within the next month or two ideally.", delay: 27000 },
        { role: 'agent', text: "Perfect! I have all the information I need. Let me search our database of over 500 communities to find the best matches for your mother. This usually takes about 2-3 minutes. While we wait, I can tell you that many of our assisted living communities offer wonderful amenities like chef-prepared meals, fitness programs, and social activities!", delay: 30000 },
    ];
    
    // Start conversation
    updateVoiceStatus('active', 'Client connected - Conversation active');
    
    for (const msg of demoConversation) {
        await new Promise(resolve => setTimeout(resolve, msg.delay === 0 ? 500 : msg.delay - (demoConversation[demoConversation.indexOf(msg) - 1]?.delay || 0)));
        addVoiceMessage(msg.role, msg.text);
    }
    
    // Simulate processing
    updateVoiceStatus('processing', 'Processing recommendations...');
    
    await new Promise(resolve => setTimeout(resolve, 5000));
    
    addVoiceMessage('agent', "I'm still searching for the perfect matches. Did you know that most pet-friendly communities have designated walking areas and even pet grooming services?");
    
    await new Promise(resolve => setTimeout(resolve, 5000));
    
    // Show results
    updateVoiceStatus('complete', 'Recommendations ready!');
    
    addVoiceMessage('agent', "Great news! I've found 5 excellent assisted living communities that match your requirements! Here are the top 3:");
    
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    addVoiceMessage('agent', "🏆 Number 1: Sunrise Senior Living Beverly Hills - This is a premium assisted living community with a 95% match score! Monthly fee is $5,200. They're pet-friendly and have immediate availability. They offer 24-hour care, gourmet dining, and a beautiful garden for pet walks.");
    
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    addVoiceMessage('agent', "🥈 Number 2: The Watermark at Beverly Hills - 92% match score with a monthly fee of $4,800. Also pet-friendly with a 1-2 month waitlist. They have an award-winning memory care program and excellent therapy services.");
    
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    addVoiceMessage('agent', "🥉 Number 3: Belmont Village Senior Living - 89% match score at $4,500 per month. Pet-friendly with immediate availability. They're known for their exceptional dining program and active social calendar.");
    
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    addVoiceMessage('agent', "I've sent these recommendations to your placement agent who will follow up with more details. Is there anything else you'd like to know about these communities?");
}

// ========================================
// Admin Panel Functions
// ========================================

function initializeAdminPanel() {
    // Initialize admin tabs
    const adminTabs = document.querySelectorAll('.admin-tab');
    adminTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabId = tab.dataset.adminTab;
            switchAdminTab(tabId);
        });
    });
    
    // Initialize weight sliders
    const weightSliders = document.querySelectorAll('.weight-slider');
    weightSliders.forEach(slider => {
        slider.addEventListener('input', (e) => {
            const valueDisplay = document.getElementById(`${e.target.id}-value`);
            if (valueDisplay) {
                valueDisplay.textContent = parseFloat(e.target.value).toFixed(1);
            }
        });
    });
    
    // Load initial data
    loadAdminConfig();
}

function switchAdminTab(tabId) {
    // Update tab buttons
    document.querySelectorAll('.admin-tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.adminTab === tabId);
    });
    
    // Update content panels
    document.querySelectorAll('.admin-panel-content').forEach(panel => {
        panel.classList.toggle('active', panel.id === `admin-${tabId}`);
    });
    
    // Load data for the tab
    switch (tabId) {
        case 'voice-settings':
            loadVoiceSettings();
            refreshActiveSessions();
            break;
        case 'ranking-weights':
            loadRankingWeights();
            break;
        case 'events':
            loadEvents();
            break;
        case 'system':
            loadSystemSettings();
            break;
        case 'audit-log':
            refreshAuditLog();
            break;
    }
}

async function loadAdminConfig() {
    try {
        const response = await fetch('/api/admin/config');
        if (response.ok) {
            const config = await response.json();
            console.log('Admin config loaded:', config);
            
            // Load voice settings
            if (config.voice_agent) {
                document.getElementById('max-sessions').value = config.voice_agent.max_concurrent_sessions || 10;
                document.getElementById('session-timeout').value = config.voice_agent.session_timeout_minutes || 30;
                document.getElementById('default-language').value = config.voice_agent.default_language || 'english';
                document.getElementById('enable-voice-agent').checked = config.voice_agent.enable_voice_agent !== false;
                document.getElementById('voice-push-to-crm').checked = config.voice_agent.push_to_crm !== false;
            }
            
            // Load ranking weights
            if (config.ranking_weights) {
                Object.entries(config.ranking_weights).forEach(([key, value]) => {
                    const slider = document.getElementById(`weight-${key}`);
                    const valueDisplay = document.getElementById(`weight-${key}-value`);
                    if (slider) {
                        slider.value = value;
                        if (valueDisplay) valueDisplay.textContent = parseFloat(value).toFixed(1);
                    }
                });
            }
            
            // Load system settings
            if (config.system) {
                document.getElementById('maintenance-mode').checked = config.system.maintenance_mode || false;
                document.getElementById('enable-crm').checked = config.system.enable_crm_integration !== false;
                document.getElementById('enable-email').checked = config.system.enable_email_notifications !== false;
                document.getElementById('max-recommendations').value = config.system.max_recommendations || 10;
                document.getElementById('log-level').value = config.system.log_level || 'INFO';
            }
        }
    } catch (error) {
        console.error('Error loading admin config:', error);
    }
}

async function loadVoiceSettings() {
    try {
        const response = await fetch('/api/admin/voice-settings');
        if (response.ok) {
            const settings = await response.json();
            document.getElementById('max-sessions').value = settings.max_concurrent_sessions || 10;
            document.getElementById('session-timeout').value = settings.session_timeout_minutes || 30;
            document.getElementById('default-language').value = settings.default_language || 'english';
            document.getElementById('enable-voice-agent').checked = settings.enable_voice_agent !== false;
        }
    } catch (error) {
        console.error('Error loading voice settings:', error);
    }
}

async function saveVoiceSettings() {
    try {
        const settings = {
            max_concurrent_sessions: parseInt(document.getElementById('max-sessions').value),
            session_timeout_minutes: parseInt(document.getElementById('session-timeout').value),
            default_language: document.getElementById('default-language').value,
            enable_voice_agent: document.getElementById('enable-voice-agent').checked,
            push_to_crm: document.getElementById('voice-push-to-crm').checked
        };
        
        const response = await fetch('/api/admin/voice-settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        });
        
        if (response.ok) {
            showSuccess('Voice settings saved successfully!');
        } else {
            const error = await response.json();
            showError(error.error || 'Failed to save settings');
        }
    } catch (error) {
        showError('Error saving voice settings: ' + error.message);
    }
}

async function refreshActiveSessions() {
    const container = document.getElementById('active-sessions-list');
    if (!container) return;
    
    try {
        const response = await fetch('/api/voice/sessions');
        if (response.ok) {
            const data = await response.json();
            
            if (data.sessions.length === 0) {
                container.innerHTML = '<p class="loading-text">No active sessions</p>';
                return;
            }
            
            container.innerHTML = data.sessions.map(session => `
                <div class="session-item">
                    <div class="session-info">
                        <span class="session-id-display">${session.session_id.slice(-12)}</span>
                        <span class="session-meta">Created by: ${session.created_by} • ${Math.floor(session.time_remaining / 60)}m remaining</span>
                    </div>
                    <span class="session-status ${session.status}">${session.status}</span>
                </div>
            `).join('');
        }
    } catch (error) {
        container.innerHTML = '<p class="loading-text">Error loading sessions</p>';
    }
}

async function loadRankingWeights() {
    try {
        const response = await fetch('/api/admin/ranking-weights');
        if (response.ok) {
            const data = await response.json();
            Object.entries(data.weights).forEach(([key, value]) => {
                const slider = document.getElementById(`weight-${key}`);
                const valueDisplay = document.getElementById(`weight-${key}-value`);
                if (slider) {
                    slider.value = value;
                    if (valueDisplay) valueDisplay.textContent = parseFloat(value).toFixed(1);
                }
            });
        }
    } catch (error) {
        console.error('Error loading ranking weights:', error);
    }
}

async function saveRankingWeights() {
    try {
        const weights = {};
        const weightKeys = ['business', 'cost', 'distance', 'availability', 'budget_efficiency', 'couple', 'amenity', 'holistic'];
        
        weightKeys.forEach(key => {
            const slider = document.getElementById(`weight-${key}`);
            if (slider) {
                weights[key] = parseFloat(slider.value);
            }
        });
        
        const response = await fetch('/api/admin/ranking-weights', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ weights })
        });
        
        if (response.ok) {
            showSuccess('Ranking weights saved successfully!');
        } else {
            const error = await response.json();
            showError(error.error || 'Failed to save weights');
        }
    } catch (error) {
        showError('Error saving ranking weights: ' + error.message);
    }
}

async function resetRankingWeights() {
    if (!confirm('Reset all ranking weights to default values?')) return;
    
    try {
        const response = await fetch('/api/admin/ranking-weights', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reset: true })
        });
        
        if (response.ok) {
            await loadRankingWeights();
            showSuccess('Ranking weights reset to defaults!');
        }
    } catch (error) {
        showError('Error resetting weights: ' + error.message);
    }
}

async function applyWeightPreset(presetName) {
    try {
        const response = await fetch('/api/admin/ranking-weights', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ preset: presetName })
        });
        
        if (response.ok) {
            await loadRankingWeights();
            showSuccess(`Applied "${presetName}" preset!`);
        } else {
            const error = await response.json();
            showError(error.error || 'Failed to apply preset');
        }
    } catch (error) {
        showError('Error applying preset: ' + error.message);
    }
}

async function loadEvents() {
    const container = document.getElementById('events-list');
    if (!container) return;
    
    try {
        const response = await fetch('/api/admin/events');
        if (response.ok) {
            const data = await response.json();
            
            if (data.events.length === 0) {
                container.innerHTML = '<p class="loading-text">No events created yet</p>';
                return;
            }
            
            container.innerHTML = data.events.map(event => {
                const isExpired = event.is_expired;
                const statusClass = !event.is_active ? 'inactive' : (isExpired ? 'expired' : 'active');
                const statusText = !event.is_active ? 'Inactive' : (isExpired ? 'Expired' : 'Active');
                const timeRemaining = formatTimeRemaining(event.time_remaining);
                
                return `
                <div class="event-item">
                    <div class="event-info">
                        <span class="event-name-display">${event.name}</span>
                        <span class="event-meta">
                            ${event.current_sessions}/${event.max_concurrent_sessions} active now • 
                            ${event.total_sessions_served} total served
                        </span>
                        <span class="event-meta">
                            ${isExpired ? 'Expired' : `⏱️ ${timeRemaining} remaining`}
                        </span>
                    </div>
                    <div class="event-actions">
                        <button class="btn btn-ghost" onclick="viewEventQR('${event.event_id}')" title="View QR Code">
                            📱
                        </button>
                        <button class="btn btn-ghost" onclick="editEvent('${event.event_id}')" title="Edit">
                            ✏️
                        </button>
                        <button class="btn btn-ghost" onclick="deleteEvent('${event.event_id}')" title="Delete">
                            🗑️
                        </button>
                        <span class="event-status ${statusClass}">
                            ${statusText}
                        </span>
                    </div>
                </div>
            `}).join('');
        }
    } catch (error) {
        container.innerHTML = '<p class="loading-text">Error loading events</p>';
    }
}

function formatTimeRemaining(seconds) {
    if (seconds <= 0) return 'Expired';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (hours > 24) {
        const days = Math.floor(hours / 24);
        return `${days}d ${hours % 24}h`;
    } else if (hours > 0) {
        return `${hours}h ${minutes}m`;
    } else {
        return `${minutes}m`;
    }
}

async function handleCreateEvent() {
    console.log('handleCreateEvent called');
    
    const nameEl = document.getElementById('event-name');
    const concurrentEl = document.getElementById('event-concurrent');
    const descriptionEl = document.getElementById('event-description');
    const hoursEl = document.getElementById('event-hours');
    const minutesEl = document.getElementById('event-minutes');
    
    console.log('Elements found:', { nameEl, concurrentEl, descriptionEl, hoursEl, minutesEl });
    
    if (!nameEl || !concurrentEl || !hoursEl || !minutesEl) {
        showError('Form elements not found. Please refresh the page.');
        return;
    }
    
    const name = nameEl.value.trim();
    const concurrent = parseInt(concurrentEl.value) || 50;
    const description = descriptionEl ? descriptionEl.value.trim() : '';
    const hours = parseInt(hoursEl.value) || 0;
    const minutes = parseInt(minutesEl.value) || 0;
    
    console.log('Form values:', { name, concurrent, description, hours, minutes });
    
    if (!name) {
        showError('Please enter an event name');
        return;
    }
    
    if (hours === 0 && minutes === 0) {
        showError('Please set a duration (hours or minutes)');
        return;
    }
    
    try {
        console.log('Sending request to /api/admin/events');
        const response = await fetch('/api/admin/events', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name,
                description,
                max_concurrent_sessions: concurrent,
                duration_hours: hours,
                duration_minutes: minutes
            })
        });
        
        console.log('Response status:', response.status);
        
        if (response.ok) {
            const data = await response.json();
            console.log('Event created:', data);
            showSuccess(`Event created! QR code ready for up to ${concurrent} concurrent users.`);
            
            // Clear form
            nameEl.value = '';
            if (descriptionEl) descriptionEl.value = '';
            
            // Reload events list
            loadEvents();
            
            // Show QR code
            if (data.event && data.event.event_id) {
                viewEventQR(data.event.event_id);
            }
        } else {
            const errorText = await response.text();
            console.error('Error response:', errorText);
            try {
                const error = JSON.parse(errorText);
                showError(error.error || 'Failed to create event');
            } catch (e) {
                showError('Failed to create event: ' + response.status + ' - ' + errorText);
            }
        }
    } catch (error) {
        console.error('Fetch error:', error);
        showError('Error creating event: ' + error.message);
    }
}

async function viewEventQR(eventId) {
    try {
        const response = await fetch(`/api/admin/events/${eventId}`);
        if (response.ok) {
            const data = await response.json();
            const event = data.event;
            const timeRemaining = formatTimeRemaining(event.time_remaining);
            
            // Create modal to show single QR code
            const modal = document.createElement('div');
            modal.className = 'modal active';
            modal.id = 'event-qr-modal';
            modal.innerHTML = `
                <div class="modal-content" style="max-width: 500px;">
                    <div class="modal-header">
                        <h2>${event.name}</h2>
                        <button class="btn-icon" onclick="this.closest('.modal').remove()">✕</button>
                    </div>
                    <div class="modal-body" style="text-align: center;">
                        <div style="background: white; padding: 20px; border-radius: 16px; display: inline-block; margin-bottom: 20px;">
                            <img src="${data.qr_url}" alt="Event QR Code" style="width: 200px; height: 200px;">
                        </div>
                        
                        <div class="event-stats" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 20px;">
                            <div class="stat-box" style="background: var(--glass-bg); padding: 12px; border-radius: 12px;">
                                <div style="font-size: 1.5rem; font-weight: 700; color: var(--primary);">${event.current_sessions}</div>
                                <div style="font-size: 0.8rem; color: var(--fg-muted);">Active Now</div>
                            </div>
                            <div class="stat-box" style="background: var(--glass-bg); padding: 12px; border-radius: 12px;">
                                <div style="font-size: 1.5rem; font-weight: 700; color: var(--primary);">${event.max_concurrent_sessions}</div>
                                <div style="font-size: 0.8rem; color: var(--fg-muted);">Max Concurrent</div>
                            </div>
                            <div class="stat-box" style="background: var(--glass-bg); padding: 12px; border-radius: 12px;">
                                <div style="font-size: 1.5rem; font-weight: 700; color: var(--primary);">${event.total_sessions_served}</div>
                                <div style="font-size: 0.8rem; color: var(--fg-muted);">Total Served</div>
                            </div>
                        </div>
                        
                        <p style="margin-bottom: 8px; color: var(--fg-secondary);">
                            ⏱️ <strong>${event.is_expired ? 'Expired' : timeRemaining + ' remaining'}</strong>
                        </p>
                        <p style="font-size: 0.85rem; color: var(--fg-muted); word-break: break-all;">
                            ${data.session_url}
                        </p>
                        
                        <div style="margin-top: 20px; display: flex; gap: 12px; justify-content: center;">
                            <button class="btn btn-outline" onclick="copyEventUrl('${data.session_url}')">
                                📋 Copy URL
                            </button>
                            <button class="btn btn-outline" onclick="printEventQR('${eventId}')">
                                🖨️ Print
                            </button>
                        </div>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
        }
    } catch (error) {
        showError('Error loading QR code: ' + error.message);
    }
}

function copyEventUrl(url) {
    navigator.clipboard.writeText(url).then(() => {
        showSuccess('URL copied to clipboard!');
    }).catch(() => {
        showError('Failed to copy URL');
    });
}

function printEventQR(eventId) {
    const modal = document.getElementById('event-qr-modal');
    if (modal) {
        const content = modal.querySelector('.modal-body').innerHTML;
        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <html>
            <head><title>Event QR Code</title></head>
            <body style="display: flex; justify-content: center; align-items: center; min-height: 100vh; font-family: sans-serif;">
                ${content}
            </body>
            </html>
        `);
        printWindow.document.close();
        printWindow.print();
    }
}

async function editEvent(eventId) {
    try {
        const response = await fetch(`/api/admin/events/${eventId}`);
        if (response.ok) {
            const data = await response.json();
            const event = data.event;
            
            // Populate edit form
            document.getElementById('edit-event-id').value = eventId;
            document.getElementById('edit-event-name').value = event.name;
            document.getElementById('edit-event-description').value = event.description || '';
            document.getElementById('edit-event-concurrent').value = event.max_concurrent_sessions;
            document.getElementById('edit-event-hours').value = 0;
            document.getElementById('edit-event-minutes').value = 0;
            document.getElementById('edit-event-active').checked = event.is_active;
            
            // Show modal
            document.getElementById('event-edit-modal').classList.add('active');
        }
    } catch (error) {
        showError('Error loading event: ' + error.message);
    }
}

function closeEventEditModal() {
    document.getElementById('event-edit-modal').classList.remove('active');
}

async function saveEventEdit() {
    const eventId = document.getElementById('edit-event-id').value;
    const updates = {
        name: document.getElementById('edit-event-name').value.trim(),
        description: document.getElementById('edit-event-description').value.trim(),
        max_concurrent_sessions: parseInt(document.getElementById('edit-event-concurrent').value),
        duration_hours: parseInt(document.getElementById('edit-event-hours').value) || 0,
        duration_minutes: parseInt(document.getElementById('edit-event-minutes').value) || 0,
        is_active: document.getElementById('edit-event-active').checked
    };
    
    try {
        const response = await fetch(`/api/admin/events/${eventId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updates)
        });
        
        if (response.ok) {
            showSuccess('Event updated successfully!');
            closeEventEditModal();
            loadEvents();
        } else {
            const error = await response.json();
            showError(error.error || 'Failed to update event');
        }
    } catch (error) {
        showError('Error updating event: ' + error.message);
    }
}

async function deleteEvent(eventId) {
    if (!confirm('Delete this event? This cannot be undone.')) return;
    
    try {
        const response = await fetch(`/api/admin/events/${eventId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showSuccess('Event deleted');
            loadEvents();
        } else {
            const error = await response.json();
            showError(error.error || 'Failed to delete event');
        }
    } catch (error) {
        showError('Error deleting event: ' + error.message);
    }
}

async function deactivateEvent(eventId) {
    if (!confirm('Deactivate this event? No new sessions can be started.')) return;
    
    try {
        const response = await fetch(`/api/admin/events/${eventId}/deactivate`, {
            method: 'POST'
        });
        
        if (response.ok) {
            showSuccess('Event deactivated');
            loadEvents();
        }
    } catch (error) {
        showError('Error deactivating event: ' + error.message);
    }
}

async function loadSystemSettings() {
    try {
        const response = await fetch('/api/admin/system-settings');
        if (response.ok) {
            const settings = await response.json();
            document.getElementById('maintenance-mode').checked = settings.maintenance_mode || false;
            document.getElementById('enable-crm').checked = settings.enable_crm_integration !== false;
            document.getElementById('enable-email').checked = settings.enable_email_notifications !== false;
            document.getElementById('max-recommendations').value = settings.max_recommendations || 10;
            document.getElementById('log-level').value = settings.log_level || 'INFO';
        }
    } catch (error) {
        console.error('Error loading system settings:', error);
    }
}

async function saveSystemSettings() {
    try {
        const settings = {
            maintenance_mode: document.getElementById('maintenance-mode').checked,
            enable_crm_integration: document.getElementById('enable-crm').checked,
            enable_email_notifications: document.getElementById('enable-email').checked,
            max_recommendations: parseInt(document.getElementById('max-recommendations').value),
            log_level: document.getElementById('log-level').value
        };
        
        const response = await fetch('/api/admin/system-settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        });
        
        if (response.ok) {
            showSuccess('System settings saved successfully!');
        } else {
            const error = await response.json();
            showError(error.error || 'Failed to save settings');
        }
    } catch (error) {
        showError('Error saving system settings: ' + error.message);
    }
}

async function refreshAuditLog() {
    const container = document.getElementById('audit-log-list');
    if (!container) return;
    
    try {
        const response = await fetch('/api/admin/audit-log?limit=50');
        if (response.ok) {
            const data = await response.json();
            
            if (data.log.length === 0) {
                container.innerHTML = '<p class="loading-text">No audit log entries</p>';
                return;
            }
            
            container.innerHTML = data.log.map(entry => `
                <div class="audit-item">
                    <div class="audit-header">
                        <span class="audit-action">${formatAuditAction(entry.action)}</span>
                        <span class="audit-time">${new Date(entry.timestamp).toLocaleString()}</span>
                    </div>
                    <span class="audit-user">by ${entry.user}</span>
                    ${entry.details ? `<pre class="audit-details">${JSON.stringify(entry.details, null, 2)}</pre>` : ''}
                </div>
            `).join('');
        }
    } catch (error) {
        container.innerHTML = '<p class="loading-text">Error loading audit log</p>';
    }
}

function formatAuditAction(action) {
    const actions = {
        'update_voice_settings': '🎤 Voice Settings Updated',
        'update_ranking_weights': '⚖️ Ranking Weights Updated',
        'reset_ranking_weights': '🔄 Ranking Weights Reset',
        'update_system_settings': '🖥️ System Settings Updated',
        'create_event': '🎉 Event Created',
        'deactivate_event': '🚫 Event Deactivated',
        'delete_event': '🗑️ Event Deleted',
        'import_config': '📤 Config Imported'
    };
    return actions[action] || action;
}

async function exportConfig() {
    try {
        const response = await fetch('/api/admin/export-config');
        if (response.ok) {
            const config = await response.json();
            const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `admin-config-${new Date().toISOString().split('T')[0]}.json`;
            a.click();
            URL.revokeObjectURL(url);
            showSuccess('Configuration exported!');
        }
    } catch (error) {
        showError('Error exporting config: ' + error.message);
    }
}

async function importConfig(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    try {
        const text = await file.text();
        const config = JSON.parse(text);
        
        if (!confirm('Import this configuration? This will overwrite current settings.')) return;
        
        const response = await fetch('/api/admin/import-config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        
        if (response.ok) {
            showSuccess('Configuration imported successfully!');
            loadAdminConfig();
        } else {
            const error = await response.json();
            showError(error.error || 'Failed to import config');
        }
    } catch (error) {
        showError('Error importing config: ' + error.message);
    }
    
    // Reset file input
    event.target.value = '';
}

// Initialize admin panel when view is switched to admin
document.addEventListener('DOMContentLoaded', () => {
    // Check if admin panel exists and initialize
    if (document.getElementById('admin-view')) {
        initializeAdminPanel();
    }
});

// Expose functions globally for onclick handlers
// Note: Using handleCreateEvent to avoid conflict with native document.createEvent()
window.handleCreateEvent = handleCreateEvent;
window.viewEventQR = viewEventQR;
window.editEvent = editEvent;
window.deleteEvent = deleteEvent;
window.deactivateEvent = deactivateEvent;
window.saveEventEdit = saveEventEdit;
window.closeEventEditModal = closeEventEditModal;
window.applyWeightPreset = applyWeightPreset;
window.saveRankingWeights = saveRankingWeights;
window.resetRankingWeights = resetRankingWeights;
window.saveVoiceSettings = saveVoiceSettings;
window.saveSystemSettings = saveSystemSettings;
window.exportConfig = exportConfig;
window.importConfig = importConfig;
window.refreshAuditLog = refreshAuditLog;
window.generateVoiceSession = generateVoiceSession;

console.log('All admin functions exposed globally');

