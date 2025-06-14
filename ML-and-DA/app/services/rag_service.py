import os
import pandas as pd
import numpy as np
import faiss
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import logging
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self, excel_path: str, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the RAG service with an Excel dataset.
        
        Args:
            excel_path: Path to the Excel file containing the dataset
            model_name: Name of the sentence transformer model to use
        """
        self.excel_path = excel_path
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        self.index = None
        self.df = None
        self.initialized = False
        try:
            self._load_dataset()
            self.initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize RAGService: {str(e)}")
            self.initialized = False
    
    def is_ready(self) -> bool:
        """Check if the RAG service is properly initialized and ready to use."""
        return self.initialized and self.index is not None and not self.df.empty
    
    def _load_dataset(self):
        """Load the dataset from Excel and build the FAISS index."""
        try:
            # Convert to Path object and handle relative/absolute paths
            excel_path = Path(self.excel_path)
            if not excel_path.is_absolute():
                # If path is relative, try to find it relative to project root
                project_root = Path(__file__).parent.parent.parent  # Go up to project root
                excel_path = project_root / excel_path
                
            logger.info(f"Looking for Excel file at: {excel_path.absolute()}")
            
            if not excel_path.exists():
                raise FileNotFoundError(f"Excel file not found at: {excel_path.absolute()}")
                
            # Read the Excel file
            self.df = pd.read_excel(excel_path)
            
            # Clean and validate the data
            required_columns = ['Original Problem', 'Theme', 'Rewritten Problem']
            missing_columns = [col for col in required_columns if col not in self.df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns in Excel file: {missing_columns}")
                
            self.df = self.df.dropna(subset=required_columns)
            
            # Create search text by combining theme and original problem
            self.df['search_text'] = self.df['Theme'] + " - " + self.df['Original Problem']
            
            logger.info(f"Successfully loaded {len(self.df)} examples from {excel_path.name}")
            
            # Generate embeddings
            logger.info("Generating embeddings for the dataset...")
            texts = self.df['search_text'].tolist()
            embeddings = self.model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
            
            # Build FAISS index
            self.index = faiss.IndexFlatL2(embeddings.shape[1])
            self.index.add(np.array(embeddings).astype('float32'))
            
            logger.info(f"Loaded {len(self.df)} examples and built FAISS index")
            
        except Exception as e:
            logger.error(f"Error loading dataset: {str(e)}")
            raise
    
    def search_similar(self, query: str, theme: str, k: int = 3) -> List[Dict[str, Any]]:
        """
        Search for similar problems in the dataset.
        
        Args:
            query: The original problem text
            theme: The theme to search for
            k: Number of similar examples to retrieve
            
        Returns:
            List of similar examples with their metadata
        """
        if self.index is None or self.df is None:
            raise ValueError("Dataset not loaded. Call _load_dataset() first.")
        
        # Create search query
        search_query = f"{theme} - {query}"
        
        # Encode the query
        query_embedding = self.model.encode([search_query], show_progress_bar=False, convert_to_numpy=True)
        
        # Search in FAISS index
        distances, indices = self.index.search(np.array(query_embedding).astype('float32'), k=k)
        
        # Get the most similar examples
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.df):  # Make sure the index is valid
                example = self.df.iloc[idx].to_dict()
                example['distance'] = float(distance)
                results.append(example)
        
        return results
    
    def build_prompt(self, original_problem: str, theme: str, num_examples: int = 3) -> str:
        """
        Build a prompt with few-shot examples.
        
        Args:
            original_problem: The problem to rewrite
            theme: The target theme
            num_examples: Number of examples to include in the prompt
            
        Returns:
            Formatted prompt string
        """
        # Retrieve similar examples
        examples = self.search_similar(original_problem, theme, k=num_examples)
        
        # Build the prompt
        prompt_parts = [
            "You are an AI assistant that rewrites math word problems to match a specific theme, "
            "while keeping the original math logic and structure exactly the same. "
            "Only respond with the rewritten problem, no additional text or explanation.\n\n"
            "Here are some examples of how to rewrite problems:\n"
        ]
        
        # Add examples
        for ex in examples:
            prompt_parts.append(
                f"Original: {ex['Original Problem']}\n"
                f"Theme: {ex['Theme']}\n"
                f"Rewritten: {ex['Rewritten Problem']}\n"
            )
        
        # Add the current problem to be rewritten
        prompt_parts.append(
            f"\nNow rewrite this problem with the given theme:\n"
            f"Original: {original_problem}\n"
            f"Theme: {theme}\n"
            "Rewritten:"
        )
        
        return "\n".join(prompt_parts)
    
    def get_status(self) -> Dict[str, Any]:
        """Get the status of the RAG service."""
        return {
            "dataset_loaded": self.df is not None,
            "num_examples": len(self.df) if self.df is not None else 0,
            "index_built": self.index is not None,
            "excel_path": str(self.excel_path)
        }
