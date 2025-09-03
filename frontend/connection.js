// --- API Endpoints ---
const PREDICT_API_URL = 'https://fake-review-detection-system-km43.onrender.com/predict';
const SCRAPE_API_URL = 'https://fake-review-detection-system-km43.onrender.com/scrape-and-predict';
const FILE_ANALYSIS_URL = 'https://fake-review-detection-system-km43.onrender.com/analyze-file';

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing handlers...');

    // File Analysis Elements
    const fileAnalysis = {
        form: document.getElementById('file-upload-form'),
        input: document.getElementById('file-input'),
        button: document.getElementById('analyze-file-btn'),
        results: document.getElementById('file-result'),
        uploadUI: {
            fileInfo: document.querySelector('.file-info'),
            fileName: document.getElementById('file-name'),
            removeBtn: document.getElementById('remove-file'),
            uploadProgress: document.querySelector('.upload-progress'),
            progressFill: document.querySelector('.progress-fill'),
            uploadPercentage: document.getElementById('upload-percentage')
        },
        progress: {
            container: document.querySelector('.progress-container'),
            bar: document.querySelector('.progress'),
            percentage: document.getElementById('progress-percentage')
        },
        stats: {
            container: document.querySelector('.stats-container'),
            total: document.getElementById('total-reviews'),
            real: document.getElementById('real-reviews'),
            fake: document.getElementById('fake-reviews')
        },
        downloadBtn: document.getElementById('download-results-btn')
    };

    // Set up File Analysis if we're on that page
    if (fileAnalysis.form) {
        console.log('Setting up file analysis handler');

        // File selection handler: Toggles the "Analyze" button and file info display
        fileAnalysis.input.addEventListener('change', (event) => {
            const file = event.target.files[0];
            
            if (file && file.name.toLowerCase().endsWith('.csv')) {
                fileAnalysis.button.disabled = false;
                fileAnalysis.uploadUI.fileInfo.style.display = 'flex';
                fileAnalysis.uploadUI.fileName.textContent = file.name;
                fileAnalysis.uploadUI.fileName.title = file.name;
                console.log('File selected:', file.name);
            } else {
                fileAnalysis.button.disabled = true;
                fileAnalysis.uploadUI.fileInfo.style.display = 'none';
                fileAnalysis.uploadUI.fileName.textContent = 'No file selected';
                fileAnalysis.uploadUI.fileName.title = '';
                if (file) {
                    alert('Please select a CSV file.');
                }
            }
        });

        // Remove file handler: Clears the selected file
        if (fileAnalysis.uploadUI.removeBtn) {
            fileAnalysis.uploadUI.removeBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                fileAnalysis.input.value = '';
                fileAnalysis.uploadUI.fileInfo.style.display = 'none';
                fileAnalysis.button.disabled = true;
                console.log('File removed');
            });
        }
        
        // Form submission handler: Manages the entire file analysis process
        fileAnalysis.form.addEventListener('submit', async (e) => {
            e.preventDefault();
            console.log('File analysis form submitted');

            const file = fileAnalysis.input.files[0];
            if (!file) {
                alert('Please select a CSV file first.');
                return;
            }
            
            let progressInterval;
            try {
                // Update UI to loading state
                fileAnalysis.button.disabled = true;
                fileAnalysis.results.style.display = 'block';
                fileAnalysis.progress.container.style.display = 'block';
                fileAnalysis.stats.container.style.display = 'none';
                fileAnalysis.downloadBtn.classList.add('hidden');
                fileAnalysis.uploadUI.uploadProgress.style.display = 'block';
                fileAnalysis.uploadUI.progressFill.style.width = '0%';
                fileAnalysis.uploadUI.uploadPercentage.textContent = '0%';

                // Start a fake progress animation
                let progress = 0;
                progressInterval = setInterval(() => {
                    if (progress < 90) {
                        progress += 5;
                        fileAnalysis.uploadUI.progressFill.style.width = `${progress}%`;
                        fileAnalysis.uploadUI.uploadPercentage.textContent = `${progress}%`;
                    }
                }, 200);

                // Create FormData and send the file to the backend
                const formData = new FormData();
                formData.append('file', file);
                
                const response = await fetch(FILE_ANALYSIS_URL, {
                    method: 'POST',
                    body: formData,
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || 'Server error occurred.');
                }

                const results = await response.json();
                
                // End progress animation
                clearInterval(progressInterval);
                fileAnalysis.uploadUI.progressFill.style.width = '100%';
                fileAnalysis.uploadUI.uploadPercentage.textContent = '100%';
                
                // Update stats and show results
                fileAnalysis.stats.total.textContent = results.length;
                fileAnalysis.stats.real.textContent = results.filter(r => r.prediction === 'REAL').length;
                fileAnalysis.stats.fake.textContent = results.filter(r => r.prediction === 'FAKE').length;
                
                window.fileResults = results;

                setTimeout(() => {
                    fileAnalysis.uploadUI.uploadProgress.style.display = 'none';
                    fileAnalysis.progress.container.style.display = 'none';
                    fileAnalysis.stats.container.style.display = 'block';
                    fileAnalysis.downloadBtn.classList.remove('hidden');
                }, 500);

            } catch (error) {
                console.error('Analysis failed:', error);
                if (progressInterval) {
                    clearInterval(progressInterval);
                }
                fileAnalysis.uploadUI.uploadProgress.style.display = 'none';
                fileAnalysis.results.innerHTML = `<p class="error-message">Failed to analyze file: ${error.message}</p>`;
            } finally {
                fileAnalysis.button.disabled = false;
                console.log('File analysis completed');
            }
        });

        // Set up download handler for file analysis
        if (fileAnalysis.downloadBtn) {
            fileAnalysis.downloadBtn.addEventListener('click', () => {
                if (!window.fileResults || !window.fileResults.length) {
                    alert('No results to download');
                    return;
                }

                const csvContent = [
                    ['Review', 'Prediction', 'Confidence Score'],
                    ...window.fileResults.map(result => [
                        `"${result.review.replace(/"/g, '""')}"`,
                        result.prediction,
                        `${result.authenticity_score}%`
                    ])
                ].map(row => row.join(',')).join('\n');

                const blob = new Blob([csvContent], { type: 'text/csv' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'review-analysis-results.csv';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            });
        }
    }

    // Text Analysis Elements
    const textAnalysis = {
        button: document.getElementById('analyze-text-btn'),
        input: document.getElementById('text-input'),
        results: document.getElementById('text-result'),
        confidenceScore: document.getElementById('confidence-score'),
        analysisTime: document.getElementById('analysis-time')
    };

    // Set up Text Analysis if we're on that page
    if (textAnalysis.button && textAnalysis.input && textAnalysis.results) {
        console.log('Setting up text analysis handler');
        
        textAnalysis.button.addEventListener('click', async () => {
            const text = textAnalysis.input.value;
            if (!text) {
                alert('Please enter text to analyze.');
                return;
            }

            const startTime = Date.now();

            // Update UI to loading state
            textAnalysis.button.textContent = 'Analyzing...';
            textAnalysis.button.disabled = true;
            textAnalysis.results.style.display = 'none';

            try {
                const response = await fetch(PREDICT_API_URL, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ review: text })
                });

                if (!response.ok) {
                    throw new Error('Failed to analyze text');
                }

                const data = await response.json();

                // Update result icon and text
                const resultIcon = textAnalysis.results.querySelector('.result-icon');
                const resultText = textAnalysis.results.querySelector('.result-text');
                
                resultIcon.innerHTML = data.prediction === 'REAL' 
                    ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M9 12l2 2 4-4"></path><circle cx="12" cy="12" r="10"></circle></svg>'
                    : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>';
                
                resultText.textContent = data.prediction === 'REAL' 
                    ? 'This text appears to be real.'
                    : 'This text appears to be fake.';

                // Update analysis details
                textAnalysis.confidenceScore.textContent = `${data.authenticity_score}%`;
                textAnalysis.analysisTime.textContent = `${((Date.now() - startTime) / 1000).toFixed(2)}s`;

                // Show results
                textAnalysis.results.style.display = 'block';
                textAnalysis.results.className = `result-section ${data.prediction.toLowerCase()}`;

            } catch (error) {
                console.error('Analysis failed:', error);
                textAnalysis.results.style.display = 'block';
                textAnalysis.results.innerHTML = `
                    <p class="error-message">
                        Failed to analyze text: ${error.message}
                    </p>
                `;
            } finally {
                textAnalysis.button.textContent = 'Analyze Text';
                textAnalysis.button.disabled = false;
            }
        });
    }

    // URL Analysis Elements
    const urlAnalysis = {
        button: document.getElementById('analyze-url-btn'),
        input: document.getElementById('url-input'),
        results: document.getElementById('result-box'),
        content: document.querySelector('#result-box .result-content'),
        downloadBtn: document.getElementById('download-btn')
    };

    // Set up URL Analysis if we're on that page
    if (urlAnalysis.button && urlAnalysis.input && urlAnalysis.results) {
        console.log('Setting up URL analysis handler');
        
        urlAnalysis.button.addEventListener('click', async () => {
            const url = urlAnalysis.input.value;
            if (!url) {
                alert('Please enter a URL to analyze.');
                return;
            }

            // Update UI to loading state
            urlAnalysis.button.textContent = 'Analyzing...';
            urlAnalysis.button.disabled = true;
            urlAnalysis.results.style.display = 'block';
            urlAnalysis.content.innerHTML = '<p>Analyzing reviews... Please wait...</p>';

            try {
                const response = await fetch(SCRAPE_API_URL, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url })
                });

                if (!response.ok) {
                    throw new Error('Failed to fetch results');
                }

                const results = await response.json();
                
                if (results.length === 0) {
                    urlAnalysis.content.innerHTML = '<p class="error-message">No reviews found at this URL.</p>';
                    return;
                }

                // Create results table
                const table = document.createElement('table');
                table.innerHTML = `
                    <thead>
                        <tr>
                            <th>Count</th>
                            <th>Review</th>
                            <th>Prediction</th>
                            <th>Authenticity</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${results.map((result, index) => `
                            <tr class="${result.prediction.toLowerCase()}-row">
                                <td>${index + 1}</td>
                                <td>${result.review_text}</td>
                                <td>${result.prediction}</td>
                                <td>${result.authenticity_score}%</td>
                            </tr>
                        `).join('')}
                    </tbody>
                `;

                // Update UI with results
                urlAnalysis.content.innerHTML = '';
                urlAnalysis.content.appendChild(table);
                urlAnalysis.downloadBtn.classList.remove('hidden');

                // Store results for download
                window.latestResults = results;

            } catch (error) {
                console.error('Analysis failed:', error);
                urlAnalysis.content.innerHTML = `
                    <p class="error-message">
                        Failed to analyze reviews: ${error.message}
                    </p>
                `;
            } finally {
                urlAnalysis.button.textContent = 'Analyze URL';
                urlAnalysis.button.disabled = false;
            }
        });

        // Set up download handler
        if (urlAnalysis.downloadBtn) {
            urlAnalysis.downloadBtn.addEventListener('click', () => {
                if (!window.latestResults || !window.latestResults.length) {
                    alert('No results to download');
                    return;
                }

                const csv = [
                    ['Count', 'Review', 'Prediction', 'Authenticity Score'],
                    ...window.latestResults.map((result, index) => [
                        index + 1,
                        `"${result.review_text.replace(/"/g, '""')}"`,
                        result.prediction,
                        `${result.authenticity_score}%`
                    ])
                ].map(row => row.join(',')).join('\n');

                const blob = new Blob([csv], { type: 'text/csv' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'review-analysis.csv';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            });
        }
    }
});