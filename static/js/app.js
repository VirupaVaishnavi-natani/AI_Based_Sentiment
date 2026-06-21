/* ==========================================================================
   SentiMind AI - JavaScript Frontend Logic (API, UI & Chart.js)
   ========================================================================== */

// Global App State
const state = {
    activeTab: 'single',
    dbStatus: { type: 'SQLite', status: 'Active' },
    modelStatus: { loaded: false, model_name: '', active_method: 'Rule-based' },
    history: {
        limit: 10,
        offset: 0,
        sentiment: 'all',
        query: '',
        total: 0
    },
    charts: {
        ratio: null,
        trend: null,
        confidence: null
    },
    selectedFile: null
};

// DOM Elements
const elements = {
    // Status Badges
    dbValue: document.getElementById('db-value'),
    dbIndicator: document.getElementById('db-indicator'),
    modelValue: document.getElementById('model-value'),
    modelIndicator: document.getElementById('model-indicator'),
    
    // Inputs & Tabs
    tabSingle: document.getElementById('tab-single'),
    tabBatch: document.getElementById('tab-batch'),
    contentSingle: document.getElementById('content-single'),
    contentBatch: document.getElementById('content-batch'),
    reviewInput: document.getElementById('review-input'),
    charCount: document.getElementById('char-count'),
    clearBtn: document.getElementById('clear-btn'),
    analyzeBtn: document.getElementById('analyze-btn'),
    singleSpinner: document.getElementById('single-spinner'),
    
    // Batch Upload
    dropZone: document.getElementById('drop-zone'),
    fileInput: document.getElementById('file-input'),
    fileDetails: document.getElementById('file-details'),
    selectedFileName: document.getElementById('selected-file-name'),
    selectedFileSize: document.getElementById('selected-file-size'),
    removeFileBtn: document.getElementById('remove-file-btn'),
    batchAnalyzeBtn: document.getElementById('batch-analyze-btn'),
    batchSpinner: document.getElementById('batch-spinner'),
    batchProgressUi: document.getElementById('batch-progress-ui'),
    batchProgressPercent: document.getElementById('batch-progress-percent'),
    batchProgressFill: document.getElementById('batch-progress-fill'),
    batchProgressStats: document.getElementById('batch-progress-stats'),
    
    // Results display
    resultsPanel: document.getElementById('results-panel'),
    resultPlaceholder: document.getElementById('result-placeholder'),
    resultDisplay: document.getElementById('result-display'),
    resultMethod: document.getElementById('result-method'),
    sentimentValue: document.getElementById('sentiment-value'),
    confidencePercent: document.getElementById('confidence-percent'),
    gaugeFill: document.getElementById('gauge-fill'),
    barPos: document.getElementById('bar-pos'),
    barNeu: document.getElementById('bar-neu'),
    barNeg: document.getElementById('bar-neg'),
    valPos: document.getElementById('val-pos'),
    valNeu: document.getElementById('val-neu'),
    valNeg: document.getElementById('val-neg'),
    analyzedTextContent: document.getElementById('analyzed-text-content'),
    
    // KPIs
    kpiTotal: document.getElementById('kpi-total'),
    kpiPositive: document.getElementById('kpi-positive'),
    kpiNeutral: document.getElementById('kpi-neutral'),
    kpiNegative: document.getElementById('kpi-negative'),
    refreshStatsBtn: document.getElementById('refresh-stats-btn'),
    
    // History
    historySearch: document.getElementById('history-search'),
    sentimentFilter: document.getElementById('sentiment-filter'),
    historyTable: document.getElementById('history-table'),
    historyTbody: document.getElementById('history-tbody'),
    paginationInfo: document.getElementById('pagination-info'),
    prevPageBtn: document.getElementById('prev-page-btn'),
    nextPageBtn: document.getElementById('next-page-btn'),
    exportBtn: document.getElementById('export-btn'),
    exportMenu: document.getElementById('export-menu')
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    checkSystemStatus();
    refreshData();
    
    // Check status periodically (every 5 seconds)
    setInterval(checkSystemStatus, 5000);
});

// Setup Event Listeners
function setupEventListeners() {
    // Character Counter
    elements.reviewInput.addEventListener('input', () => {
        const length = elements.reviewInput.value.length;
        elements.charCount.textContent = length;
    });

    // Clear Text Button
    elements.clearBtn.addEventListener('click', () => {
        elements.reviewInput.value = '';
        elements.charCount.textContent = '0';
        elements.reviewInput.focus();
    });

    // Single Analysis Run
    elements.analyzeBtn.addEventListener('click', runSingleAnalysis);

    // Drag and Drop listeners
    const dropZone = elements.dropZone;
    
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
        }, false);
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            handleSelectedFile(files[0]);
        }
    });

    elements.fileInput.addEventListener('change', (e) => {
        if (elements.fileInput.files.length > 0) {
            handleSelectedFile(elements.fileInput.files[0]);
        }
    });

    elements.removeFileBtn.addEventListener('click', resetFileSelector);
    
    // Batch Analyze Run
    elements.batchAnalyzeBtn.addEventListener('click', runBatchAnalysis);

    // KPIs & Stats refresh
    elements.refreshStatsBtn.addEventListener('click', refreshStatsAndCharts);

    // History controls
    elements.historySearch.addEventListener('input', debounce(() => {
        state.history.offset = 0;
        state.history.query = elements.historySearch.value;
        fetchHistory();
    }, 400));

    elements.sentimentFilter.addEventListener('change', () => {
        state.history.offset = 0;
        state.history.sentiment = elements.sentimentFilter.value;
        fetchHistory();
    });

    elements.prevPageBtn.addEventListener('click', () => {
        if (state.history.offset > 0) {
            state.history.offset -= state.history.limit;
            fetchHistory();
        }
    });

    elements.nextPageBtn.addEventListener('click', () => {
        if (state.history.offset + state.history.limit < state.history.total) {
            state.history.offset += state.history.limit;
            fetchHistory();
        }
    });

    // Export Dropdown
    elements.exportBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        elements.exportMenu.classList.toggle('show');
    });

    document.addEventListener('click', () => {
        elements.exportMenu.classList.remove('show');
    });
}

// Debounce helper
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

// Switch Tabs (Single Text vs Batch)
window.switchTab = function(tabName) {
    state.activeTab = tabName;
    if (tabName === 'single') {
        elements.tabSingle.classList.add('active');
        elements.tabBatch.classList.remove('active');
        elements.contentSingle.classList.add('active');
        elements.contentBatch.classList.remove('active');
    } else {
        elements.tabSingle.classList.remove('active');
        elements.tabBatch.classList.add('active');
        elements.contentSingle.classList.remove('active');
        elements.contentBatch.classList.add('active');
    }
};

// Check DB and Model Status
async function checkSystemStatus() {
    try {
        // Fetch DB Status
        const dbRes = await fetch('/api/db-status');
        const dbData = await dbRes.json();
        state.dbStatus = dbData;
        updateDbStatusUI();

        // Fetch Model Status
        const modelRes = await fetch('/api/model-status');
        const modelData = await modelRes.json();
        state.modelStatus = modelData;
        updateModelStatusUI();
    } catch (err) {
        console.error("Error updating system status badges:", err);
    }
}

function updateDbStatusUI() {
    const val = state.dbStatus.type;
    elements.dbValue.textContent = val;
    elements.dbIndicator.className = 'status-indicator';
    
    if (val === 'MongoDB') {
        elements.dbIndicator.classList.add('green');
        elements.dbValue.title = `URI: ${state.dbStatus.host}`;
    } else {
        elements.dbIndicator.classList.add('yellow');
        elements.dbValue.title = `Using fallback database: ${state.dbStatus.host}`;
    }
}

function updateModelStatusUI() {
    const val = state.modelStatus.loaded;
    elements.modelIndicator.className = 'status-indicator';
    
    if (val) {
        elements.modelIndicator.classList.add('green');
        elements.modelValue.textContent = state.modelStatus.model_name.split('/').pop() + ' (Ready)';
        elements.modelValue.title = `Hugging Face model loaded locally on CPU.`;
    } else {
        elements.modelIndicator.classList.add('yellow');
        elements.modelValue.textContent = 'Fallback Mode (Loading HF...)';
        elements.modelValue.title = `Hugging Face model downloading/loading in background. Using rule-based lexicon for now.`;
    }
}

// Format file size
function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = 2;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

// Handle Drag & Dropped or Selected File
function handleSelectedFile(file) {
    const ext = file.name.split('.').pop().toLowerCase();
    const allowed = ['csv', 'json', 'xlsx', 'xls'];
    
    if (!allowed.includes(ext)) {
        alert("Unsupported file format! Please select a CSV, JSON, or Excel file.");
        return;
    }
    
    state.selectedFile = file;
    elements.selectedFileName.textContent = file.name;
    elements.selectedFileSize.textContent = formatBytes(file.size);
    
    elements.dropZone.classList.add('hidden');
    elements.fileDetails.classList.remove('hidden');
    elements.batchProgressUi.classList.add('hidden');
}

// Reset File Selection UI
function resetFileSelector() {
    state.selectedFile = null;
    elements.fileInput.value = '';
    elements.dropZone.classList.remove('hidden');
    elements.fileDetails.classList.add('hidden');
    elements.batchProgressUi.classList.add('hidden');
}

// Run Single Sentiment Analysis
async function runSingleAnalysis() {
    const text = elements.reviewInput.value.trim();
    if (!text) {
        alert("Please enter some review text to analyze!");
        return;
    }

    // Show loading
    elements.analyzeBtn.disabled = true;
    elements.singleSpinner.classList.remove('hidden');

    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            displaySingleResult(data);
            refreshData(); // Refresh history and charts
        } else {
            alert(data.error || "Analysis failed.");
        }
    } catch (err) {
        console.error("API error:", err);
        alert("An error occurred connecting to the backend server.");
    } finally {
        elements.analyzeBtn.disabled = false;
        elements.singleSpinner.classList.add('hidden');
    }
}

// Display Single Result Card
function displaySingleResult(data) {
    elements.resultPlaceholder.classList.add('hidden');
    elements.resultDisplay.classList.remove('hidden');
    
    // Text preview
    elements.analyzedTextContent.textContent = `"${data.text}"`;
    
    // Method used
    elements.resultMethod.textContent = data.method || 'AI Model';
    
    // Score Gauge & Color logic
    const sentiment = data.sentiment.toLowerCase();
    elements.sentimentValue.textContent = data.sentiment;
    elements.confidencePercent.textContent = (data.confidence * 100).toFixed(1);
    
    // Reset colors
    elements.sentimentValue.className = 'sentiment-value';
    const fill = elements.gaugeFill;
    fill.style.stroke = '';
    
    // Gauge representation (125.6 is empty, 0 is full)
    const confidence = data.confidence;
    const dashoffset = 125.6 * (1 - confidence);
    fill.style.strokeDashoffset = dashoffset;
    
    if (sentiment === 'positive') {
        elements.sentimentValue.classList.add('positive-text');
        fill.style.stroke = 'var(--positive)';
        
        updateBarFills(confidence, 0.1 * (1 - confidence), 0.1 * (1 - confidence));
    } else if (sentiment === 'negative') {
        elements.sentimentValue.classList.add('negative-text');
        fill.style.stroke = 'var(--negative)';
        
        updateBarFills(0.1 * (1 - confidence), 0.1 * (1 - confidence), confidence);
    } else {
        elements.sentimentValue.classList.add('neutral-text');
        fill.style.stroke = 'var(--neutral)';
        
        updateBarFills(0.15 * (1 - confidence), confidence, 0.15 * (1 - confidence));
    }
}

function updateBarFills(posVal, neuVal, negVal) {
    elements.barPos.style.width = `${posVal * 100}%`;
    elements.barNeu.style.width = `${neuVal * 100}%`;
    elements.barNeg.style.width = `${negVal * 100}%`;
    
    elements.valPos.textContent = `${(posVal * 100).toFixed(0)}%`;
    elements.valNeu.textContent = `${(neuVal * 100).toFixed(0)}%`;
    elements.valNeg.textContent = `${(negVal * 100).toFixed(0)}%`;
}

// Run Batch Reviews Analysis
async function runBatchAnalysis() {
    if (!state.selectedFile) {
        alert("Please select a file first!");
        return;
    }

    elements.batchAnalyzeBtn.disabled = true;
    elements.batchSpinner.classList.remove('hidden');
    elements.batchProgressUi.classList.remove('hidden');
    
    // Simulate UI progress while fetching
    let progress = 0;
    elements.batchProgressPercent.textContent = '0%';
    elements.batchProgressFill.style.width = '0%';
    elements.batchProgressStats.textContent = 'Preparing file...';

    const progressInterval = setInterval(() => {
        if (progress < 85) {
            progress += 5;
            elements.batchProgressPercent.textContent = `${progress}%`;
            elements.batchProgressFill.style.width = `${progress}%`;
            elements.batchProgressStats.textContent = 'Uploading and processing reviews on AI engine...';
        }
    }, 300);

    const formData = new FormData();
    formData.append('file', state.selectedFile);

    try {
        const response = await fetch('/api/analyze-batch', {
            method: 'POST',
            body: formData
        });
        
        clearInterval(progressInterval);
        
        const data = await response.json();
        
        if (response.ok) {
            elements.batchProgressPercent.textContent = '100%';
            elements.batchProgressFill.style.width = '100%';
            elements.batchProgressStats.textContent = `Completed! Analyzed ${data.analyzed_count} reviews using column '${data.column_used}'.`;
            
            // Show preview results if available
            if (data.preview_results && data.preview_results.length > 0) {
                // Display first preview row in results panel
                const firstRow = data.preview_results[0];
                displaySingleResult({
                    text: firstRow.text,
                    sentiment: firstRow.sentiment,
                    confidence: firstRow.confidence,
                    method: firstRow.method
                });
            }
            
            refreshData(); // Refresh history and statistics charts
            setTimeout(() => {
                resetFileSelector();
            }, 3000);
        } else {
            alert(data.error || "Batch analysis failed.");
            resetFileSelector();
        }
    } catch (err) {
        clearInterval(progressInterval);
        console.error("Batch API error:", err);
        alert("An error occurred during batch file transmission.");
        resetFileSelector();
    } finally {
        elements.batchAnalyzeBtn.disabled = false;
        elements.batchSpinner.classList.add('hidden');
    }
}

// Refresh stats, charts, and history table
function refreshData() {
    refreshStatsAndCharts();
    fetchHistory();
}

async function refreshStatsAndCharts() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        if (response.ok) {
            updateKPIs(data.stats);
            renderCharts(data.stats);
        }
    } catch (err) {
        console.error("Error fetching stats:", err);
    }
}

// Update KPI Metrics Cards
function updateKPIs(stats) {
    elements.kpiTotal.textContent = stats.total.toLocaleString();
    
    if (stats.total === 0) {
        elements.kpiPositive.textContent = '0%';
        elements.kpiNeutral.textContent = '0%';
        elements.kpiNegative.textContent = '0%';
        return;
    }

    const posPercent = (stats.counts.positive / stats.total) * 100;
    const neuPercent = (stats.counts.neutral / stats.total) * 100;
    const negPercent = (stats.counts.negative / stats.total) * 100;
    
    elements.kpiPositive.textContent = `${posPercent.toFixed(1)}%`;
    elements.kpiNeutral.textContent = `${neuPercent.toFixed(1)}%`;
    elements.kpiNegative.textContent = `${negPercent.toFixed(1)}%`;
}

// Render dynamic charts using Chart.js
function renderCharts(stats) {
    const isDark = true; // default dark mode themes
    const gridColor = 'rgba(255, 255, 255, 0.05)';
    const textColor = '#9ca3af';

    // 1. Ratio Chart (Doughnut)
    if (state.charts.ratio) state.charts.ratio.destroy();
    
    const ratioCtx = document.getElementById('ratioChart').getContext('2d');
    state.charts.ratio = new Chart(ratioCtx, {
        type: 'doughnut',
        data: {
            labels: ['Positive', 'Neutral', 'Negative'],
            datasets: [{
                data: [stats.counts.positive, stats.counts.neutral, stats.counts.negative],
                backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
                borderWidth: 1,
                borderColor: '#111322'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: textColor, font: { family: 'Plus Jakarta Sans', size: 10 } }
                }
            },
            cutout: '65%'
        }
    });

    // 2. Trend Chart (Line chart representing last 30 reviews)
    if (state.charts.trend) state.charts.trend.destroy();
    
    const trendCtx = document.getElementById('trendChart').getContext('2d');
    const trendPoints = stats.trend || [];
    
    // Create label list and datasets
    const labels = trendPoints.map((_, i) => `#${i + 1}`);
    const confValues = trendPoints.map(p => p.confidence * 100);
    const pointColors = trendPoints.map(p => {
        if (p.sentiment === 'positive') return '#10b981';
        if (p.sentiment === 'negative') return '#ef4444';
        return '#f59e0b';
    });

    state.charts.trend = new Chart(trendCtx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Confidence Score',
                data: confValues,
                borderColor: 'rgba(99, 102, 241, 0.6)',
                backgroundColor: 'rgba(99, 102, 241, 0.1)',
                borderWidth: 2,
                pointBackgroundColor: pointColors,
                pointBorderColor: '#111322',
                pointRadius: 4,
                fill: true,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { color: gridColor },
                    ticks: { color: textColor, font: { size: 9 } }
                },
                y: {
                    grid: { color: gridColor },
                    ticks: { color: textColor, font: { size: 9 } },
                    min: 0,
                    max: 100
                }
            }
        }
    });

    // 3. Average Confidence Bar Chart
    if (state.charts.confidence) state.charts.confidence.destroy();
    
    const confidenceCtx = document.getElementById('confidenceChart').getContext('2d');
    state.charts.confidence = new Chart(confidenceCtx, {
        type: 'bar',
        data: {
            labels: ['Positive', 'Neutral', 'Negative'],
            datasets: [{
                data: [stats.averages.positive * 100, stats.averages.neutral * 100, stats.averages.negative * 100],
                backgroundColor: ['rgba(16, 185, 129, 0.7)', 'rgba(245, 158, 11, 0.7)', 'rgba(239, 68, 68, 0.7)'],
                borderColor: ['#10b981', '#f59e0b', '#ef4444'],
                borderWidth: 1,
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: textColor, font: { size: 10 } }
                },
                y: {
                    grid: { color: gridColor },
                    ticks: { color: textColor, font: { size: 10 } },
                    min: 0,
                    max: 100
                }
            }
        }
    });
}

// Fetch Paginated & Filtered History
async function fetchHistory() {
    try {
        const queryParams = new URLSearchParams({
            limit: state.history.limit,
            offset: state.history.offset,
            sentiment: state.history.sentiment,
            q: state.history.query
        });
        
        const response = await fetch(`/api/history?${queryParams.toString()}`);
        const data = await response.json();
        
        if (response.ok) {
            renderHistoryTable(data.reviews);
            
            // Note: Since SQLite counts can be dynamic, let's fetch statistics to update the totals
            const statsRes = await fetch('/api/stats');
            const statsData = await statsRes.json();
            
            let filteredTotal = 0;
            if (state.history.sentiment === 'all' && !state.history.query) {
                filteredTotal = statsData.stats.total;
            } else {
                // If filtered, approximate total to length + offset or simple fetch count
                // For simplicity, make active total match overall stats, but pagination handles limits
                filteredTotal = data.reviews.length < state.history.limit && state.history.offset === 0 
                    ? data.reviews.length 
                    : statsData.stats.total; // fallback
            }
            
            state.history.total = filteredTotal;
            updatePaginationUI(filteredTotal);
        }
    } catch (err) {
        console.error("Error fetching history:", err);
    }
}

// Render History Table
function renderHistoryTable(reviews) {
    const tbody = elements.historyTbody;
    tbody.innerHTML = '';
    
    if (reviews.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="empty-state">
                    <p>No historical records found.</p>
                </td>
            </tr>
        `;
        return;
    }
    
    reviews.forEach(review => {
        const tr = document.createElement('tr');
        tr.id = `row-${review.id}`;
        
        // Format timestamp
        const dateStr = formatDate(review.timestamp);
        
        // Sentiment badge
        const sentiment = review.sentiment.toLowerCase();
        
        tr.innerHTML = `
            <td title="${review.text}">${review.text}</td>
            <td><span class="sentiment-badge ${sentiment}">${review.sentiment}</span></td>
            <td>${(review.confidence * 100).toFixed(1)}%</td>
            <td>${dateStr}</td>
            <td>
                <button class="icon-btn-danger" onclick="deleteRecord('${review.id}')" title="Delete record">
                    <i data-lucide="trash-2" style="width: 14px; height: 14px;"></i>
                </button>
            </td>
        `;
        
        tbody.appendChild(tr);
    });
    
    // Re-create icons for table items
    lucide.createIcons();
}

function formatDate(isoString) {
    if (!isoString) return '';
    try {
        const date = new Date(isoString);
        return date.toLocaleDateString(undefined, { 
            month: 'short', 
            day: 'numeric', 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    } catch (e) {
        return isoString;
    }
}

// Delete Record
window.deleteRecord = async function(id) {
    if (!confirm("Are you sure you want to delete this record? This will alter stats.")) return;

    try {
        const response = await fetch(`/api/reviews/${id}`, {
            method: 'DELETE'
        });
        const data = await response.json();
        
        if (data.success) {
            // Remove row from UI with animation
            const row = document.getElementById(`row-${id}`);
            if (row) {
                row.style.opacity = '0';
                row.style.transform = 'scale(0.9)';
                setTimeout(() => {
                    refreshData();
                }, 300);
            }
        } else {
            alert("Delete failed.");
        }
    } catch (err) {
        console.error("Delete error:", err);
    }
};

// Update Pagination controls
function updatePaginationUI(filteredTotal) {
    const start = state.history.total === 0 ? 0 : state.history.offset + 1;
    const end = Math.min(state.history.offset + state.history.limit, state.history.total);
    
    elements.paginationInfo.textContent = `Showing ${start}-${end} of ${state.history.total} records`;
    
    elements.prevPageBtn.disabled = state.history.offset === 0;
    // Disable next if we have less rows than limit or reached total
    elements.nextPageBtn.disabled = (state.history.offset + state.history.limit >= state.history.total) || (end - start + 1 < state.history.limit);
}

// Client-side Data Export
window.exportData = async function(format) {
    // Fetch all reviews matching current filter (up to 1000 items)
    const queryParams = new URLSearchParams({
        limit: 1000,
        offset: 0,
        sentiment: state.history.sentiment,
        q: state.history.query
    });
    
    try {
        const response = await fetch(`/api/history?${queryParams.toString()}`);
        const data = await response.json();
        
        if (!response.ok || !data.reviews || data.reviews.length === 0) {
            alert("No data available to export.");
            return;
        }

        const items = data.reviews.map(r => ({
            text: r.text,
            sentiment: r.sentiment,
            confidence: r.confidence,
            timestamp: r.timestamp
        }));

        let content = '';
        let filename = `sentimind_export_${new Date().toISOString().split('T')[0]}`;
        let mimeType = 'text/plain';

        if (format === 'json') {
            content = JSON.stringify(items, null, 2);
            filename += '.json';
            mimeType = 'application/json';
        } else if (format === 'csv') {
            // Build CSV rows
            const headers = ['Text', 'Sentiment', 'Confidence', 'Timestamp'];
            const rows = items.map(item => [
                `"${item.text.replace(/"/g, '""')}"`,
                item.sentiment,
                item.confidence,
                item.timestamp
            ]);
            content = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
            filename += '.csv';
            mimeType = 'text/csv';
        }

        // Trigger file download
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    } catch (e) {
        console.error("Export failed:", e);
        alert("Failed to compile export data.");
    }
};
