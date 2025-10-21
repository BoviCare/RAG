import asyncio
import logging
from vector_service import VectorService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_table_integration():
    """Test if disease table chunks are properly integrated."""
    
    # Test queries that should retrieve table information
    test_queries = [
        "Quais doenças têm vacina disponível?",
        "Mostre doenças bacterianas",
        "Quais doenças são erradicáveis?",
        "Doenças que causam aborto",
        "Brucelose bovina"
    ]
    
    async with VectorService() as vector_service:
        logger.info("Testing disease table integration...")
        
        for query in test_queries:
            logger.info(f"\n🔍 Testing query: '{query}'")
            
            try:
                # Perform hybrid search
                results = await vector_service.hybrid_search(
                    query=query,
                    top_k=5
                )
                
                if results and len(results) > 0:
                    logger.info(f"✅ Found {len(results)} results")
                    
                    # Show first result details
                    first_result = results[0]
                    logger.info(f"📄 First result:")
                    logger.info(f"  - Disease: {first_result.get('disease_name', 'N/A')}")
                    logger.info(f"  - Chunk ID: {first_result.get('chunk_id', 'N/A')}")
                    logger.info(f"  - Section Type: {first_result.get('section_type', 'N/A')}")
                    logger.info(f"  - Text preview: {first_result.get('section_text', '')[:200]}...")
                    logger.info(f"  - Score: {first_result.get('score', 'N/A')}")
                else:
                    logger.warning(f"❌ No results found for query: '{query}'")
                    
            except Exception as e:
                logger.error(f"❌ Error testing query '{query}': {e}")
        
        # Test specific table queries
        logger.info(f"\n🧪 Testing specific table queries...")
        
        # Query for diseases with vaccine
        vaccine_query = "doenças com vacina"
        results = await vector_service.hybrid_search(query=vaccine_query, top_k=10)
        
        if results:
            logger.info(f"📊 Found {len(results)} diseases with vaccine information:")
            for i, result in enumerate(results[:5]):  # Show first 5
                disease_name = result.get('disease_name', 'Unknown')
                section_type = result.get('section_type', 'Unknown')
                logger.info(f"  {i+1}. {disease_name} (type: {section_type})")
        
        # Check if we have table chunks
        table_results = await vector_service.hybrid_search(query="TABELA", top_k=10)
        logger.info(f"\n📋 Found {len(table_results)} table chunks in database")
        
        for i, result in enumerate(table_results[:3]):  # Show first 3
            logger.info(f"  {i+1}. {result.get('disease_name', 'Unknown')} - {result.get('chunk_id', 'Unknown')}")

if __name__ == "__main__":
    asyncio.run(test_table_integration())
