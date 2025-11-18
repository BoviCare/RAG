import os
import logging
import asyncio
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from openai import OpenAI

# Configure logging
logger = logging.getLogger(__name__)

# --- Pydantic Models for RAG Operations ---

class DocumentScore(BaseModel):
    relevance_score: float = Field(description="Relevance score between 0.0 and 1.0, where 1.0 is most relevant")
    reasoning: str = Field(description="Brief explanation of why this document is relevant to the query")

class RerankingResponse(BaseModel):
    scores: List[DocumentScore] = Field(description="List of document scores sorted by relevance")

class SingleDocumentResponse(BaseModel):
    """The structured response for a single document's relevance score."""
    score: DocumentScore = Field(description="The relevance score and reasoning for this document")

# --- RAG Functions ---

async def rerank_documents_with_openai(
    query: str, 
    documents: List[Dict[str, Any]], 
    openai_client: Optional[OpenAI] = None
) -> List[Dict[str, Any]]:
    """Reranks documents using an LLM for semantic relevance with structured outputs."""
    if not openai_client or not documents:
        return documents

    async def score_document(doc: Dict[str, Any]) -> tuple[float, Dict[str, Any]]:
        prompt = f"""
        Given the user query about bovine diseases, evaluate the following document's relevance. 
        Provide a score from 0.0 (not relevant) to 1.0 (highly relevant) and a brief reasoning.

        Query: "{query}"

        Document: "{doc.get('section_text', '')}"
        """
        try:
            response = await asyncio.to_thread(
                openai_client.beta.chat.completions.parse,
                model="gpt-5-nano",
                messages=[
                    {"role": "system", "content": "You are a relevance scoring expert for veterinary medicine documents that provides structured JSON output."},
                    {"role": "user", "content": prompt}
                ],
                response_format=SingleDocumentResponse,
                # temperature=0.0,
                # max_completion_tokens=1000
            )
            
            parsed_response = response.choices[0].message.parsed
            logger.info(f"Parsed response: {parsed_response}")
            
            if parsed_response and parsed_response.score:
                score = parsed_response.score.relevance_score
                logger.info(f"Document relevance score: {score}")
                return (score, doc)
            else:
                logger.warning(f"No valid score in parsed response: {parsed_response}")
                return (0.0, doc)
        except Exception as e:
            logger.error(f"Error reranking document with structured output: {e}")
            logger.error(f"Error type: {type(e)}")
            
            # Fallback: try without structured output
            try:
                logger.info("Trying fallback reranking without structured output...")
                fallback_response = await asyncio.to_thread(
                    openai_client.chat.completions.create,
                    model="gpt-5-nano",
                    messages=[
                        {"role": "system", "content": "You are a relevance scoring expert. Return only a number between 0.0 and 1.0 representing relevance."},
                        {"role": "user", "content": f"Query: '{query}'\nDocument: '{doc.get('section_text', '')}'\nRelevance score (0.0-1.0):"}
                    ],
                    # temperature=0.0,
                    # max_completion_tokens=100
                )
                
                fallback_score = fallback_response.choices[0].message.content.strip()
                try:
                    score = float(fallback_score)
                    logger.info(f"Fallback score: {score}")
                    return (score, doc)
                except ValueError:
                    logger.warning(f"Could not parse fallback score: {fallback_score}")
                    return (0.0, doc)
                    
            except Exception as fallback_error:
                logger.error(f"Fallback reranking also failed: {fallback_error}")
                return (0.0, doc)

    scoring_tasks = [score_document(doc) for doc in documents]
    scored_docs = await asyncio.gather(*scoring_tasks)
    
    reranked_docs = sorted(scored_docs, key=lambda x: x[0], reverse=True)
    
    return [doc for score, doc in reranked_docs]


async def generate_rag_response(
    query: str, 
    context_docs: List[Dict[str, Any]], 
    openai_client: Optional[OpenAI] = None
) -> str:
    """Generates a final response using the retrieved and reranked context."""
    if not openai_client:
        return "Error: OpenAI client not configured."

    context = ""
    for doc in context_docs:
        context += f"Source: {doc.get('disease_name', 'N/A')} - {doc.get('section_type', 'N/A')}\n"
        context += f"Content: {doc.get('section_text', '')}\n\n"

    prompt = f"""
    You are an expert veterinary medicine Q&A assistant specializing in bovine diseases. 
    Use the following context to answer the user's question about bovine diseases.
    If the context does not contain the answer, state that you could not find the information.
    Provide accurate, helpful information based on the veterinary literature provided.
    Make the response in the following format:
    <Summary of the answer>
    <Detailed answer in markdown format>

    Context:
    ---
    {context}
    ---

    Question: "{query}"
    """
    try:
        response = await asyncio.to_thread(
            openai_client.chat.completions.create,
            model="gpt-5-nano",
            messages=[
                {"role": "system", "content": "You are an expert veterinary medicine assistant specializing in bovine diseases. Provide accurate, helpful information based on the veterinary literature provided."},
                {"role": "user", "content": prompt}
            ],
            # temperature=0.0,
            # max_completion_tokens=1000
        )
        
        response_content = response.choices[0].message.content
        logger.info(f"Generated response length: {len(response_content) if response_content else 0}")
        logger.info(f"Response preview: {response_content[:200] if response_content else 'None'}")
        
        if not response_content or response_content.strip() == "":
            logger.warning("Empty response from GPT-5, returning fallback message")
            return "I apologize, but I couldn't generate a proper response. Please try rephrasing your question."
        
        return response_content
        
    except Exception as e:
        logger.error(f"Error generating RAG response: {e}")
        logger.error(f"Error type: {type(e)}")
        return f"Error generating response: {str(e)}"
