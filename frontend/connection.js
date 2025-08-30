// --- Elements for Single Review Analysis ---
const analyzeBtn = document.getElementById('analyze-btn');
const reviewText = document.getElementById('review-text');
const resultContainer = document.getElementById('result-container');

// --- Elements for Scraping ---
const scrapeBtn = document.getElementById('scrape-btn');
const urlInput = document.getElementById('url-input');
const scrapeResultsContainer = document.getElementById('scrape-results-container');
const downloadBtn = document.getElementById('download-btn');

// --- Global variable to store the latest results for download ---
let latestScrapeResults = [];

// --- API Endpoints (Update these with your live Render URL when deploying) ---
const PREDICT_API_URL = 'https://fake-review-detection-system-km43.onrender.com/predict';
const SCRAPE_API_URL = 'https://fake-review-detection-system-km43.onrender.com/scrape-and-predict';

// --- Event Listener for Single Review Analysis ---
analyzeBtn.addEventListener('click', () => {
    const review = reviewText.value;
    if (!review) {
        alert('Please enter a review to analyze.');
        return;
    }

    analyzeBtn.textContent = 'Analyzing...';
    analyzeBtn.disabled = true;
    resultContainer.classList.add('hidden');

    fetch(PREDICT_API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ review: review }),
    })
    .then(response => response.json())
    .then(data => {
        resultContainer.innerHTML = `
            <h2>Analysis Result</h2>
            <p>Prediction: ${data.prediction}</p>
            <p>Authenticity Score: ${data.authenticity_score}%</p>
        `;
        resultContainer.className = data.prediction === 'REAL' ? 'real' : 'fake';
        resultContainer.classList.remove('hidden');
    })
    .catch(error => {
        console.error('Error:', error);
        resultContainer.innerHTML = `<p class="error-message">Error: Could not connect to the backend.</p>`;
        resultContainer.className = 'fake';
        resultContainer.classList.remove('hidden');
    })
    .finally(() => {
        analyzeBtn.textContent = 'Analyze Single Review';
        analyzeBtn.disabled = false;
    });
});

// --- Event Listener for Scraping Button ---
scrapeBtn.addEventListener('click', () => {
    const url = urlInput.value;
    if (!url) {
        alert('Please enter a URL to scrape.');
        return;
    }

    scrapeBtn.textContent = 'Scraping... This may take a minute...';
    scrapeBtn.disabled = true;
    scrapeResultsContainer.innerHTML = '';
    downloadBtn.classList.add('hidden');

    fetch(SCRAPE_API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url }),
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw new Error(err.error || 'Scraping failed.') });
        }
        return response.json();
    })
    .then(results => {
        if (results.length === 0) {
            scrapeResultsContainer.innerHTML = `<p class="error-message">No reviews could be scraped from this URL.</p>`;
            return;
        }

        latestScrapeResults = results;

        const table = document.createElement('table');
        table.innerHTML = `
            <thead>
                <tr>
                    <th>Sr. No.</th>
                    <th>Review Snippet</th>
                    <th>Prediction</th>
                    <th>Authenticity Score</th>
                </tr>
            </thead>
        `; // <-- CHANGED: Added 'Sr. No.' header
        const tbody = document.createElement('tbody');
        results.forEach((result, index) => { // <-- CHANGED: Added 'index' to the loop
            const row = document.createElement('tr');
            row.className = result.prediction === 'REAL' ? 'real-row' : 'fake-row';
            // <-- CHANGED: Added table cell for the serial number (index + 1)
            row.innerHTML = `<td>${index + 1}</td><td>${result.review_text}</td><td>${result.prediction}</td><td>${result.authenticity_score}%</td>`;
            tbody.appendChild(row);
        });
        table.appendChild(tbody);
        scrapeResultsContainer.appendChild(table);

        downloadBtn.classList.remove('hidden');
    })
    .catch(error => {
        console.error('Error:', error);
        scrapeResultsContainer.innerHTML = `<p class="error-message">Error: ${error.message}</p>`;
    })
    .finally(() => {
        scrapeBtn.textContent = 'Scrape & Analyze';
        scrapeBtn.disabled = false;
    });
});

// --- Event Listener for Download Button ---
downloadBtn.addEventListener('click', () => {
    if (latestScrapeResults.length === 0) {
        alert('No results to download.');
        return;
    }

    function convertToCSV(data) {
        // <-- CHANGED: Added 'Sr. No.' to the CSV header
        const headers = 'Sr. No.,Reviews,Prediction,Authenticity Score\n';
        const rows = data.map((row, index) => { // <-- CHANGED: Added 'index' to the map function
            const review = `"${row.review_text.replace(/"/g, '""')}"`;
            // <-- CHANGED: Added the serial number (index + 1) to each row
            return [index + 1, review, row.prediction, row.authenticity_score].join(',');
        });
        return headers + rows.join('\n');
    }

    const csvData = convertToCSV(latestScrapeResults);
    const blob = new Blob([csvData], { type: 'text/csv;charset=utf-8;' });
    
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', 'review_analysis_report.csv');
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
});