# Math Problem Rewriter API

A FastAPI backend service that rewrites math word problems to match specific themes using Mistral-7B-Instruct-v0.1 and RAG (Retrieval-Augmented Generation).

## Features

- Rewrite math problems based on student interests/themes
- Preserves mathematical structure and logic
- Uses RAG for better context-aware rewriting
- FastAPI-based RESTful API
- CORS enabled for frontend integration

## Prerequisites

- Python 3.8+
- pip
- Mistral AI API key

## Setup

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd math_rewriter_backend
   ```

2. Create a virtual environment and activate it:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root and add your Mistral AI API key:
   ```
   MISTRAL_API_KEY=your_api_key_here
   ```

## Running the Application

1. Start the FastAPI server:

   ```bash
   uvicorn app.main:app --reload
   ```

2. The API will be available at `http://127.0.0.1:8000`

## API Documentation

Once the server is running, you can access:

- Interactive API docs: `http://127.0.0.1:8000/docs`
- Alternative API docs: `http://127.0.0.1:8000/redoc`

### Endpoints

#### POST /rewrite

Rewrites a math problem according to the specified theme.

**Request Body:**

```json
{
  "original_problem": "A bakery sold 24 muffins in the morning and 18 muffins in the afternoon. How many muffins did they sell in total?",
  "theme": "Minecraft"
}
```

**Response:**

```json
{
  "rewritten_problem": "In Minecraft, a baker crafted 24 cookies in the morning and another 18 in the afternoon. How many cookies did they make in total?"
}
```

#### GET /health

Health check endpoint.

**Response:**

```json
{
  "status": "healthy"
}
```

## Adding More Examples

To improve the RAG system, add more examples to the `_load_examples` method in `app/services/rewriter.py`. Each example should include:

- `original`: The original math problem
- `theme`: The theme for rewriting
- `rewritten`: The rewritten version of the problem

## License

MIT

## to run

conda create -n mathenv python=3.11
conda activate mathenv
pip install -r requirements.txt
uvicorn app.main:app --reload
