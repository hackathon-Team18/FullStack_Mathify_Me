import os
import json
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProblemRewriter:
    def __init__(self):
        """Initialize the ProblemRewriter with necessary components."""
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            logger.warning("MISTRAL_API_KEY not found in environment variables")
        
        # Initialize sentence transformer for embeddings
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.embedding_dim = 384  # Dimension of the embeddings
        
        # Initialize FAISS index for RAG
        self.faiss_index = faiss.IndexFlatL2(self.embedding_dim)
        self.examples = []
        
        # Load example problems for RAG
        self._load_examples()
    
    def _load_examples(self):
        """Load example problems for RAG."""
        self.examples = [
            {
                "original": "A bakery sold 24 muffins in the morning and 18 muffins in the afternoon. How many muffins did they sell in total?",
                "theme": "Minecraft",
                "rewritten": "In Minecraft, a baker crafted 24 cookies in the morning and another 18 in the afternoon. How many cookies did they make in total?"
            },
            {
                "original": "James has 45 marbles. He gave 12 to his friend. How many does he have left?",
                "theme": "Football",
                "rewritten": "James had 45 football trading cards. He gave 12 to his teammate. How many cards does he have left?"
            },
            # Add more examples as needed
        ]
        
        # Create embeddings for examples
        if self.examples:
            texts = [f"{ex['original']} {ex['theme']}" for ex in self.examples]
            embeddings = self.embedding_model.encode(texts, show_progress_bar=False)
            self.faiss_index.add(np.array(embeddings).astype('float32'))
    
    def _get_similar_examples(self, problem: str, theme: str, k: int = 2) -> List[Dict[str, Any]]:
        """Find similar examples using semantic search."""
        if not self.examples:
            return []
            
        # Get embedding for the query
        query_embedding = self.embedding_model.encode(
            f"{problem} {theme}", 
            show_progress_bar=False
        ).reshape(1, -1)
        
        # Search for similar examples
        distances, indices = self.faiss_index.search(
            np.array(query_embedding).astype('float32'), 
            k=min(k, len(self.examples))
        )
        
        return [self.examples[i] for i in indices[0] if i < len(self.examples)]
    
    async def rewrite(self, problem: str, theme: str, prompt_override: str = None, **kwargs) -> str:
        """
        Rewrite a math problem according to the specified theme.
        
        Args:
            problem: The original math problem
            theme: The theme to rewrite the problem with
            prompt_override: Optional pre-built prompt to use instead of generating one
            **kwargs: Additional keyword arguments for backward compatibility
            
        Returns:
            The rewritten problem
        """
        try:
            # If no API is available, return a helpful message
            if not self.api_key:
                return ("Mistral API is not available. "
                       "Please set the MISTRAL_API_KEY environment variable and restart the server.")
                
            # If prompt_override is provided, use it directly
            if prompt_override:
                return await self._call_mistral_api(prompt_override)
                
            # Otherwise, generate a prompt using RAG
            examples = self._get_similar_examples(problem, theme, k=2)
            prompt = self._create_prompt(problem, theme, examples)
            
            return await self._call_mistral_api(prompt)
            
        except Exception as e:
            error_msg = f"Error in rewrite: {str(e)}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
    
    def _create_prompt(self, problem: str, theme: str, examples: List[Dict[str, Any]]) -> str:
        """Create a prompt for the Mistral model."""
        system_prompt = """You are an AI assistant that rewrites math word problems to match a specific student interest or theme, while keeping the original math logic and structure exactly the same. Only respond with the rewritten problem, no additional text or explanation."""
        
        examples_text = "\n\n".join(
            f"Original: {ex['original']}\nTheme: {ex['theme']}\nRewritten: {ex['rewritten']}"
            for ex in examples
        )
        
        prompt = f"""{system_prompt}

Examples:
{examples_text}

Now rewrite this problem with the given theme:
Original: {problem}
Theme: {theme}
Rewritten: """
        
        return prompt
    
    async def _call_mistral_api(self, prompt: str) -> str:
        """Call the OpenRouter API to generate the rewritten problem."""
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY is not set")

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        data = {
            "model": "mistralai/mistral-7b-instruct",  # You can also use mixtral-8x7b-instruct
            "messages": [
                {"role": "system", "content": "You are an AI assistant that rewrites math word problems to match a specific student interest or theme, while keeping the original math logic and structure exactly the same. Only respond with the rewritten problem, no additional text or explanation."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 200
        }

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
        except Exception as e:
            logger.error(f"Error calling OpenRouter API: {str(e)}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                logger.error(f"Response: {e.response.text}")
            raise
