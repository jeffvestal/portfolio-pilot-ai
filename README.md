# Portfolio-Pilot-AI

## Project Overview

Portfolio-Pilot-AI is an AI-powered insights dashboard for financial analysts. It allows analysts to proactively monitor client portfolios, explore data conversationally, and streamline communication. The application is built with a React frontend and a Python FastAPI backend, using Elasticsearch as the primary data source and for powering AI search and generation features.

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js and npm
- An Elasticsearch instance with the required indices and an Inference API endpoint configured.

### Backend Setup

1.  **Navigate to the backend directory:**
    ```bash
    cd backend
    ```

2.  **Create a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install the required packages:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up your environment variables:**
    Create a `.env` file in the `backend` directory and add the following:
    ```
    ES_ENDPOINT_URL="<your_elasticsearch_endpoint>"
    ES_API_KEY="<your_elasticsearch_api_key>"
    INFERENCE_ID="<your_inference_id>" # Optional, defaults to .rainbow-sprinkles-elastic
    ```

5.  **Run the backend server:**
    ```bash
    uvicorn main:app --reload
    ```
    The backend will be available at `http://localhost:8000`.

### Frontend Setup

1.  **Navigate to the frontend directory:**
    ```bash
    cd frontend
    ```

2.  **Install the required packages:**
    ```bash
    npm install
    ```

3.  **Run the frontend development server:**
    ```bash
    npm start
    ```
    The frontend will be available at `http://localhost:3000`.
