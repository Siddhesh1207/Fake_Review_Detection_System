// --- API Endpoints ---
const PREDICT_API_URL = 'https://fake-review-detection-system-km43.onrender.com/predict';
const SCRAPE_API_URL = 'https://fake-review-detection-system-km43.onrender.com/scrape-and-predict';

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing handlers...');

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