from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Load environment variables
load_dotenv()

# Models
class ProblemRequest(BaseModel):
    original_problem: str
    theme: str
    num_examples: int = 3  # Number of examples to use in the prompt

class RewrittenProblem(BaseModel):
    rewritten_problem: str
    examples_used: List[Dict[str, str]]

class RAGStatus(BaseModel):
    dataset_loaded: bool
    num_examples: int
    index_built: bool
    excel_path: str

# Initialize FastAPI
app = FastAPI(
    title="Math Problem Rewriter API",
    description="""
    API for rewriting math problems with different themes using RAG and Mistral AI.
    
    Features:
    - Rewrite math problems using a RAG system
    - Uses FAISS for efficient similarity search
    - Supports custom datasets via Excel
    """,
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the Excel file path from environment or use default
EXAMPLES_FILE = os.getenv("EXAMPLES_FILE", "math_problems_dataset1.xlsx")

# Convert to absolute path if not already
if not os.path.isabs(EXAMPLES_FILE):
    # First try in the current working directory
    if os.path.exists(EXAMPLES_FILE):
        EXAMPLES_FILE = os.path.abspath(EXAMPLES_FILE)
    else:
        # If not found, try in the project root
        project_root = Path(__file__).parent.parent
        possible_path = project_root / EXAMPLES_FILE
        if possible_path.exists():
            EXAMPLES_FILE = str(possible_path.absolute())
        else:
            logger.warning(f"Excel file not found at: {os.path.abspath(EXAMPLES_FILE)} or {possible_path}")

logger.info(f"Using Excel file at: {EXAMPLES_FILE}")

# Initialize services
from app.services.rag_service import RAGService
from app.services.rewriter import ProblemRewriter

# Initialize the legacy rewriter (fallback)
rewriter = ProblemRewriter()

# Initialize RAG service
rag_service = None
if os.path.exists(EXAMPLES_FILE):
    try:
        rag_service = RAGService(EXAMPLES_FILE)
        logger.info("RAG service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize RAG service: {str(e)}")
        rag_service = None
else:
    logger.warning(f"Excel file not found at {EXAMPLES_FILE}, RAG service will not be available")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/rag/status", response_model=RAGStatus)
async def get_rag_status():
    """
    Get the status of the RAG service.
    
    Returns:
        RAGStatus: Status information about the RAG service
    """
    if not rag_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG service is not available"
        )
    return rag_service.get_status()

@app.post("/rewrite", response_model=RewrittenProblem)
async def rewrite_problem(request: ProblemRequest):
    """
    Rewrite a math problem with the specified theme.
    
    Args:
        original_problem: The original math problem
        theme: The theme to rewrite the problem with (e.g., 'Space', 'Minecraft')
        num_examples: Number of similar examples to use (default: 3)
    """
    try:
        result = {}
        
        # If RAG service is available, use it to get similar examples
        if rag_service and rag_service.is_ready():
            try:
                similar_examples = rag_service.get_similar_examples(
                    request.original_problem, 
                    request.theme, 
                    k=min(request.num_examples, 5) if request.num_examples else 3
                )
                
                # Build the prompt with RAG examples
                prompt = rag_service.build_prompt(
                    request.original_problem,
                    request.theme,
                    similar_examples
                )
                
                # Call the rewriter with the RAG-enhanced prompt
                rewritten = await rewriter.rewrite(
                    problem=request.original_problem,
                    theme=request.theme,
                    prompt_override=prompt
                )
                
                result.update({
                    "rewritten_problem": rewritten,
                    "examples_used": similar_examples,
                    "rag_used": True
                })
                
            except Exception as rag_error:
                logger.warning(f"RAG service error, falling back to basic rewriting: {str(rag_error)}")
                # Fall through to basic rewriting
        
        # If we don't have a result yet, use basic rewriting
        if not result:
            rewritten = await rewriter.rewrite(
                problem=request.original_problem,
                theme=request.theme
            )
            result = {
                "rewritten_problem": rewritten,
                "examples_used": [],
                "rag_used": False
            }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error in rewrite endpoint: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
