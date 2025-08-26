// Get the HTML elements
const analyzeBtn = document.getElementById('analyze-btn');
const reviewText = document.getElementById('review-text');
const resultContainer = document.getElementById('result-container');
const predictionText = document.getElementById('prediction-text');
const scoreText = document.getElementById('score-text');

const API_URL = 'http://127.0.0.1:5000/predict';

// Add an event listener to the button
analyzeBtn.addEventListener('click', () => {
    const review = reviewText.value;
    if (!review) {
        alert('Please enter a review to analyze.');
        return;
    }

    // Show a simple loading state
    resultContainer.classList.add('hidden');
    analyzeBtn.textContent = 'Analyzing...';
    analyzeBtn.disabled = true;

    // Send the data to the Flask API
    fetch(API_URL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ review: review }),
    })
    .then(response => response.json())
    .then(data => {
        // Display the results
        predictionText.textContent = `This review is likely ${data.prediction}`;
        scoreText.textContent = `Authenticity Score: ${data.authenticity_score}%`;
        
        // Style the result container based on the prediction
        if (data.prediction === 'REAL') {
            resultContainer.className = 'real';
        } else {
            resultContainer.className = 'fake';
        }

        resultContainer.classList.remove('hidden');
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error connecting to the analysis server. Please ensure the backend is running.');
    })
    .finally(() => {
        // Reset the button
        analyzeBtn.textContent = 'Analyze Review';
        analyzeBtn.disabled = false;
    });
});