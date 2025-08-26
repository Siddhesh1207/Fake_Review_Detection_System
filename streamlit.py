import streamlit as st
import requests

# --- Page Configuration ---
st.set_page_config(
    page_title="Fake Review Detection System",
    page_icon="🔎",
    layout="wide"
)

# --- App Title ---
st.title("🔎 Fake Review Detection System")
st.write("Enter a product review below to check its authenticity.")

# --- The Flask API Endpoint ---
# This is the URL where your Flask backend is running
API_URL = "http://127.0.0.1:5000/predict"

# --- User Input Section ---
with st.form("review_form"):
    review_text = st.text_area("Enter the review text:", height=150)
    submitted = st.form_submit_button("Analyze Review")

# --- Logic to handle form submission ---
if submitted and review_text:
    # Prepare the data to send to the Flask API
    payload = {"review": review_text}

    try:
        # Display a spinner while waiting for the API response
        with st.spinner('Analyzing...'):
            response = requests.post(API_URL, json=payload)
            response.raise_for_status() # Raise an exception for bad status codes

            # Get the result from the API
            result = response.json()
            prediction = result.get('prediction')
            score = float(result.get('authenticity_score'))

        # --- Display Results ---
        st.subheader("Analysis Result")

        if prediction == 'REAL':
            st.success(f"**This review is likely REAL**")
        else:
            st.error(f"**This review is likely FAKE**")

        st.metric(label="Authenticity Score (Chance of being Real)", value=f"{score:.2f}%")
        
        # Display a progress bar for visual effect
        st.progress(score / 100)

    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to the analysis server: {e}")
        st.warning("Please ensure the Flask backend (app.py) is running.")

elif submitted:
    st.warning("Please enter a review to analyze.")