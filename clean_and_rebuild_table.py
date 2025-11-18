import pandas as pd
import json
import os
import logging
import asyncio
from typing import List, Dict, Any
from vector_service import VectorService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_disease_csv(csv_path: str) -> pd.DataFrame:
    """Load the disease CSV file."""
    try:
        df = pd.read_csv(csv_path, encoding='utf-8')
        logger.info(f"Loaded CSV with {len(df)} diseases")
        logger.info(f"Columns: {list(df.columns)}")
        return df
    except Exception as e:
        logger.error(f"Error loading CSV: {e}")
        return pd.DataFrame()

def get_disease_type(disease_name: str) -> str:
    """Determine disease type based on the disease name and characteristics."""
    disease_name_lower = disease_name.lower()
    
    # Viral diseases
    viral_keywords = ['viral', 'vírus', 'virus', 'bvd', 'ibr', 'aftosa', 'raiva', 'leucose']
    if any(keyword in disease_name_lower for keyword in viral_keywords):
        return "DoencasViricas"
    
    # Parasitic diseases  
    parasitic_keywords = ['parasitária', 'neosporose', 'protozoário', 'protozoarios']
    if any(keyword in disease_name_lower for keyword in parasitic_keywords):
        return "DoencasParasitarias"
    
    # Bacterial diseases (default for most)
    bacterial_keywords = ['bactéria', 'bacteria', 'brucelose', 'tuberculose', 'leptospirose', 'salmonelose', 'mastite']
    if any(keyword in disease_name_lower for keyword in bacterial_keywords):
        return "DoencaBacterianas"
    
    # Default to bacterial if unclear
    return "DoencaBacterianas"

def get_disease_id(disease_name: str) -> str:
    """Extract disease ID - use abbreviation if available, otherwise full name."""
    # Check for common abbreviations
    abbreviations = {
        'diarréia viral bovina (bvd)': 'BVD',
        'rinotraqueíte infecciosa bovina (ibr)': 'IBR',
        'febre aftosa': 'Febre Aftosa',
        'tristeza parasitária': 'TPB',
        'brucelose bovina': 'Brucelose',
        'tuberculose': 'Tuberculose',
        'leptospirose': 'Leptospirose',
        'neosporose': 'Neosporose',
        'raiva': 'RaivaDosHerbívoros',
        'leucose': 'Leucose',
        'salmonelose': 'Salmonelose',
        'mastite': 'Mastite'
    }
    
    disease_lower = disease_name.lower().strip()
    if disease_lower in abbreviations:
        return abbreviations[disease_lower]
    
    # Return first word if no abbreviation found
    return disease_name.split()[0] if disease_name.split() else disease_name

def format_disease_chunk(row: pd.Series, index: int) -> Dict[str, Any]:
    """Format a disease row as a structured text chunk with new format."""
    
    # Clean up disease name
    disease_name = str(row['Doença']).strip()
    if disease_name.endswith('.'):
        disease_name = disease_name[:-1]
    
    # Get disease type and ID
    disease_type = get_disease_type(disease_name)
    disease_id = get_disease_id(disease_name)
    
    # Format the structured text
    structured_text = f"""Doença: {disease_name}
- Microorganismo: {str(row['Microorganismos']).strip()}
- Transmissão: {str(row['Transmissão (via)']).strip()}
- Sinais clínicos: {str(row['Sinais clínicos']).strip()}
- Vacina: {str(row['Vacina']).strip()}
- Tratamento: {str(row['Tratamento']).strip()}
- Erradicável: {str(row['Erradicação']).strip()}"""
    
    # Create document structure with new format
    document = {
        "document_id": "PrincDoencas",
        "disease_type": disease_type,
        "disease_name": disease_name,
        "disease_id": disease_id,
        "chunk_id": f"table_disease_{index + 1}",
        "chunk_index": str(index + 1),
        "section_type": "table",
        "page_number": "25",  # All table entries on page 25
        "section_text": structured_text
    }
    
    return document

async def clean_old_table_embeddings():
    """Remove old table embeddings from Milvus."""
    logger.info("Cleaning old table embeddings...")
    
    async with VectorService() as vector_service:
        try:
            # Delete documents with document_id = "disease_table"
            result = await vector_service.delete_documents_by_filter({
                "document_id": "disease_table"
            })
            
            if result:
                logger.info("Successfully removed old table embeddings")
            else:
                logger.info("No old table embeddings found or already cleaned")
                
        except Exception as e:
            logger.error(f"Error cleaning old embeddings: {e}")

def process_disease_table(csv_path: str) -> List[Dict[str, Any]]:
    """Process the disease CSV and create document chunks with new format."""
    logger.info("Processing disease table with new format...")
    df = load_disease_csv(csv_path)
    
    if df.empty:
        logger.error("No data loaded from CSV")
        return []
    
    documents = []
    
    for index, row in df.iterrows():
        try:
            # Skip rows with missing disease names
            if pd.isna(row['Doença']) or str(row['Doença']).strip() == '':
                logger.warning(f"Skipping row {index + 1}: missing disease name")
                continue
            
            # Format the disease as a document chunk
            document = format_disease_chunk(row, index)
            documents.append(document)
            
            logger.info(f"Processed disease: {document['disease_name']} -> {document['disease_type']} -> {document['disease_id']}")
            
        except Exception as e:
            logger.error(f"Error processing row {index + 1}: {e}")
            continue
    
    logger.info(f"Successfully processed {len(documents)} diseases with new format")
    return documents

async def main():
    """Main function to clean old embeddings and create new structured ones."""
    # File path
    csv_path = "BD_doencas.csv"
    
    # Check if CSV exists
    if not os.path.exists(csv_path):
        logger.error(f"CSV file not found: {csv_path}")
        return
    
    # Step 1: Clean old table embeddings
    logger.info("Step 1: Cleaning old table embeddings...")
    await clean_old_table_embeddings()
    
    # Step 2: Process disease table with new format
    logger.info("Step 2: Processing disease table with new format...")
    documents = process_disease_table(csv_path)
    
    if not documents:
        logger.error("No documents processed")
        return
    
    # Log sample document for debugging
    if documents:
        sample_doc = documents[0]
        logger.info(f"Sample document structure:")
        logger.info(f"  - document_id: {sample_doc.get('document_id')}")
        logger.info(f"  - disease_type: {sample_doc.get('disease_type')}")
        logger.info(f"  - disease_id: {sample_doc.get('disease_id')}")
        logger.info(f"  - chunk_id: {sample_doc.get('chunk_id')}")
        logger.info(f"  - page_number: {sample_doc.get('page_number')}")
        logger.info(f"  - section_text preview: {sample_doc.get('section_text', '')[:200]}...")
    
    # Step 3: Insert new structured embeddings
    logger.info("Step 3: Inserting new structured disease chunks...")
    async with VectorService() as vector_service:
        success = await vector_service.insert_documents(documents)
        
        if success:
            logger.info(f"Successfully inserted {len(documents)} new structured disease chunks")
        else:
            logger.error("Failed to insert new disease chunks")
    
    logger.info("Table restructuring completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
