# Research_Assistant

## Prerequisites
* **Node.js**
* **Python**
* **MongoDB Atlas URI** (for chat and state management)
* **Pinecone API Key** (for vector embeddings)
* **Google Gemini API Key** (from Google AI Studio)

## Backend Setup (FastAPI)

1. Open a terminal and navigate to the backend directory:
    ```bash
    cd backend
    ```

2. Create and activate a Python virtual environment:
    ``` bash
    # Windows
    python -m venv venv
    venv\Scripts\activate

    # macOS/Linux
    python -m venv venv
    source venv/bin/activate
    ```

3. Install required dependencies
    ``` bash
    pip install -r requirements.txt
    ```

4. Create a `.env` file in the `backend` folder and add your credentials:
    ```
    PORT="port"
    MONGO_URI="your_mongodb_connection_string"
    PINECONE_API_KEY="your_pinecone_api_key"
    PINECONE_INDEX_NAME="research-papers"
    GEMINI_API_KEY="your_google_ai_studio_key"
    ```

5. Start the FastAPI development server:
    ``` bash
    uvicorn app.main:app --reload
    ```

## Frontend Setup (React + Vite)

1. Open a new terminal window and navigate to the frontend directory:
    ``` bash
    cd frontend
    ```

2. Install the necessary packages:
    ``` bash
    npm install
    ```

3. Start the Vite development server:
    ``` bash
    npm run dev
    ```