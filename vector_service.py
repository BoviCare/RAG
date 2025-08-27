import os
import logging
import asyncio
from typing import List, Dict, Any, Optional
from pymilvus import MilvusClient, DataType, AnnSearchRequest, WeightedRanker, Function, FunctionType
from openai import AsyncOpenAI
from dotenv import load_dotenv
import mmh3

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DOCUMENT_MULTIPLIER = 3

class VectorService:
    """
    Async service class for interacting with Milvus vector database, using BM25 for sparse search.
    """
    
    def __init__(
        self, 
        collection_name: str = "BoviCareDocuments"
    ):
        """
        Initialize the VectorService for Milvus.
        """
        self.milvus_uri = os.getenv("MILVUS_URI")
        self.api_token = os.getenv("MILVUS_API_TOKEN")
        self.collection_name = collection_name
        self.openai_client = None
        
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            logger.warning("OpenAI API key not provided. Set OPENAI_API_KEY environment variable.")
        else:
            self.openai_client = AsyncOpenAI(api_key=self.openai_api_key)

        if self.milvus_uri:
            logger.info(f"Connecting to Milvus server at URI: {self.milvus_uri}")
            self.client = MilvusClient(uri=self.milvus_uri, token=self.api_token)
        else:
            logger.info("Using Milvus Lite with local database file")
            self.local_db_file = f"./milvus_data_{collection_name}.db"
            self.client = MilvusClient(self.local_db_file)

    async def initialize(self):
        """Async initialization method to set up the collection."""
        await self._setup_collection()

    async def _setup_collection(self):
        """Create the Milvus collection with a hybrid search schema using BM25."""
        try:
            # Run blocking Milvus operations in a thread
            has_collection = await asyncio.to_thread(self.client.has_collection, self.collection_name)
            
            if has_collection:
                logger.info(f"Collection '{self.collection_name}' already exists")
                # Check if we need to recreate due to schema changes
                try:
                    # Try to get collection info to check schema
                    collection_info = await asyncio.to_thread(
                        self.client.describe_collection, 
                        collection_name=self.collection_name
                    )
                    logger.info(f"Collection schema: {collection_info}")
                except Exception as e:
                    logger.warning(f"Could not describe collection, may need recreation: {e}")
                    # Drop and recreate if there are issues
                    logger.info("Dropping existing collection to recreate with new schema...")
                    await asyncio.to_thread(
                        self.client.drop_collection, 
                        collection_name=self.collection_name
                    )
                    has_collection = False
            
            if not has_collection:
                logger.info(f"Creating collection '{self.collection_name}' with new schema...")
                
                schema = MilvusClient.create_schema(
                    auto_id=False,
                    enable_dynamic_field=True
                )
                
                schema.add_field(field_name="id", datatype=DataType.VARCHAR, max_length=256, is_primary=True)
                schema.add_field(field_name="document_id", datatype=DataType.VARCHAR, max_length=256)
                schema.add_field(field_name="disease_type", datatype=DataType.VARCHAR, max_length=256)
                schema.add_field(field_name="disease_name", datatype=DataType.VARCHAR, max_length=512)
                schema.add_field(field_name="disease_id", datatype=DataType.VARCHAR, max_length=256)
                schema.add_field(field_name="chunk_id", datatype=DataType.VARCHAR, max_length=256)
                schema.add_field(field_name="chunk_index", datatype=DataType.VARCHAR, max_length=256)
                schema.add_field(field_name="section_type", datatype=DataType.VARCHAR, max_length=256)
                schema.add_field(field_name="page_number", datatype=DataType.VARCHAR, max_length=256)
                schema.add_field(field_name="section_text", datatype=DataType.VARCHAR, max_length=65535, enable_analyzer=True)
                schema.add_field(field_name="dense_vector", datatype=DataType.FLOAT_VECTOR, dim=3072)
                schema.add_field(field_name="sparse_vector", datatype=DataType.SPARSE_FLOAT_VECTOR)

                # Define a function to automatically create BM25 sparse embeddings from "section_text"
                bm25_function = Function(
                    name="bm25_embedding_fn",
                    input_field_names=["section_text"],
                    output_field_names=["sparse_vector"],
                    function_type=FunctionType.BM25
                )
                schema.add_function(bm25_function)

                # Prepare index parameters for both dense and sparse vectors
                index_params = self.client.prepare_index_params()
                index_params.add_index(
                    field_name="dense_vector",
                    index_type="IVF_FLAT",
                    metric_type="IP",
                    params={"nlist": 128}
                )
                index_params.add_index(
                    field_name="sparse_vector",
                    index_type="SPARSE_INVERTED_INDEX",
                    metric_type="BM25"
                )

                # Create collection with the schema and dense index.
                # The sparse index is managed by the BM25 function.
                await asyncio.to_thread(
                    self.client.create_collection,
                    collection_name=self.collection_name,
                    schema=schema,
                    index_params=index_params
                )
                
                logger.info(f"Collection '{self.collection_name}' created successfully")
            else:
                logger.info(f"Collection '{self.collection_name}' already exists")
                
        except Exception as e:
            logger.error(f"Error setting up collection: {e}")
            raise

    async def insert_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Insert documents into the collection."""
        try:
            if not documents:
                logger.warning("No documents to insert")
                return False

            # Prepare data for insertion
            data = []
            for i, doc in enumerate(documents):
                try:
                    # Generate dense embeddings using OpenAI
                    dense_vector = await self._get_dense_embedding(doc.get('section_text', ''))
                    
                    # Ensure all required fields are present and properly formatted
                    chunk_id = str(doc.get('chunk_id', '')).strip()
                    if not chunk_id:
                        chunk_id = f"chunk_{i + 1}"
                    
                    document_data = {
                        "id": chunk_id,
                        "document_id": str(doc.get('document_id', '')),
                        "disease_type": str(doc.get('disease_type', '')),
                        "disease_name": str(doc.get('disease_name', '')),
                        "disease_id": str(doc.get('disease_id', '')),
                        "chunk_id": chunk_id,
                        "chunk_index": str(doc.get('chunk_index', '')),
                        "section_type": str(doc.get('section_type', '')),
                        "page_number": str(doc.get('page_number', '')),
                        "section_text": str(doc.get('section_text', '')),
                        "dense_vector": dense_vector
                    }
                    
                    data.append(document_data)
                    
                except Exception as doc_error:
                    logger.error(f"Error processing document {i}: {doc_error}")
                    logger.error(f"Document data: {doc}")
                    continue

            if not data:
                logger.error("No valid documents to insert after processing")
                return False

            # Log sample data for debugging
            logger.info(f"Sample document data for insertion:")
            logger.info(f"  - ID: {data[0].get('id')} (type: {type(data[0].get('id'))})")
            logger.info(f"  - chunk_id: {data[0].get('chunk_id')} (type: {type(data[0].get('chunk_id'))})")

            # Insert data
            await asyncio.to_thread(
                self.client.insert,
                collection_name=self.collection_name,
                data=data
            )
            
            logger.info(f"Successfully inserted {len(data)} documents")
            return True
            
        except Exception as e:
            logger.error(f"Error inserting documents: {e}")
            logger.error(f"Error type: {type(e)}")
            return False

    async def _get_dense_embedding(self, text: str) -> List[float]:
        """Get dense embedding for text using OpenAI."""
        if not self.openai_client or not text.strip():
            # Return a default vector if no OpenAI client or empty text
            return [0.0] * 3072
        
        try:
            response = await self.openai_client.embeddings.create(
                model="text-embedding-3-large",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            return [0.0] * 3072

    async def hybrid_search(
        self, 
        query: str, 
        top_k: int = 10,
        dense_weight: float = 0.3,
        sparse_weight: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search using both dense and sparse vectors.
        """
        try:
            # Get query embedding
            query_embedding = await self._get_dense_embedding(query)
            
            # Define search requests for hybrid search
            dense_request = AnnSearchRequest(
                data=[query_embedding],
                anns_field="dense_vector",
                param={"metric_type": "IP"},
                limit=top_k * DOCUMENT_MULTIPLIER
            )
            
            # For Full Text Search, the search data is the raw query string and it targets the sparse vector field
            sparse_request = AnnSearchRequest(
                data=[query], 
                anns_field="sparse_vector", # Target the sparse vector field
                param={"metric_type": "BM25"},
                limit=top_k * DOCUMENT_MULTIPLIER
            )
            
            # Perform hybrid search
            results = await asyncio.to_thread(
                self.client.hybrid_search,
                collection_name=self.collection_name,
                reqs=[dense_request, sparse_request],
                ranker=WeightedRanker(sparse_weight, dense_weight),
                limit=top_k,
                output_fields=["document_id", "disease_type", "disease_name", "disease_id", "chunk_id", "chunk_index", "section_type", "page_number", "section_text"]
            )
            
            # Process results
            documents = []
            if results and results[0]:
                for hit in results[0]:
                    entity = hit.get('entity', {})
                    doc = {
                        "document_id": entity.get("document_id", ""),
                        "disease_type": entity.get("disease_type", ""),
                        "disease_name": entity.get("disease_name", ""),
                        "disease_id": entity.get("disease_id", ""),
                        "chunk_id": entity.get("chunk_id", ""),
                        "chunk_index": entity.get("chunk_index", ""),
                        "section_type": entity.get("section_type", ""),
                        "page_number": entity.get("page_number", ""),
                        "section_text": entity.get("section_text", ""),
                        "score": hit.get("distance", 0.0)
                    }
                    documents.append(doc)
            
            logger.info(f"Found {len(documents)} documents from hybrid search.")
            return documents
            
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            return []

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        try:
            await asyncio.to_thread(self.client.close)
        except Exception as e:
            logger.error(f"Error closing Milvus client: {e}")
