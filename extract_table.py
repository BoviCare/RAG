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

def format_disease_chunk(row: pd.Series, index: int) -> Dict[str, Any]:
    """Format a disease row as a structured text chunk."""
    
    # Clean up disease name
    disease_name = str(row['Doença']).strip()
    if disease_name.endswith('.'):
        disease_name = disease_name[:-1]
    
    # Format the structured text
    structured_text = f"""TABELA: Principais doenças de bovinos leiteiros

Doença: {disease_name}
- Microorganismo: {str(row['Microorganismos']).strip()}
- Transmissão: {str(row['Transmissão (via)']).strip()}
- Sinais clínicos: {str(row['Sinais clínicos']).strip()}
- Vacina: {str(row['Vacina']).strip()}
- Tratamento: {str(row['Tratamento']).strip()}
- Erradicável: {str(row['Erradicação']).strip()}"""
    
    # Create document structure matching existing schema
    document = {
        "document_id": "disease_table",
        "disease_type": "table",
        "disease_name": disease_name,
        "disease_id": f"disease_{index + 1}",
        "chunk_id": f"table_disease_{index + 1}",
        "chunk_index": str(index + 1),
        "section_type": "table",
        "page_number": "1",
        "section_text": structured_text
    }
    
    return document

def process_disease_table(csv_path: str) -> List[Dict[str, Any]]:
    """Process the disease CSV and create document chunks."""
    logger.info("Loading disease CSV...")
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
            
            logger.info(f"Processed disease: {document['disease_name']}")
            
        except Exception as e:
            logger.error(f"Error processing row {index + 1}: {e}")
            continue
    
    logger.info(f"Successfully processed {len(documents)} diseases")
    return documents

async def main():
    """Main function to extract and embed disease table data."""
    # File path
    csv_path = "BD_doencas.csv"
    
    # Check if CSV exists
    if not os.path.exists(csv_path):
        logger.error(f"CSV file not found: {csv_path}")
        return
    
    # Process disease table
    logger.info("Processing disease table...")
    documents = process_disease_table(csv_path)
    
    if not documents:
        logger.error("No documents processed")
        return
    
    # Log sample document for debugging
    if documents:
        sample_doc = documents[0]
        logger.info(f"Sample document structure:")
        logger.info(f"  - disease_name: {sample_doc.get('disease_name')}")
        logger.info(f"  - chunk_id: {sample_doc.get('chunk_id')}")
        logger.info(f"  - section_text length: {len(sample_doc.get('section_text', ''))}")
        logger.info(f"  - section_text preview: {sample_doc.get('section_text', '')[:200]}...")
    
    # Insert into vector database
    logger.info("Inserting disease chunks into vector database...")
    async with VectorService() as vector_service:
        success = await vector_service.insert_documents(documents)
        
        if success:
            logger.info(f"Successfully inserted {len(documents)} disease chunks")
        else:
            logger.error("Failed to insert disease chunks")
    
    logger.info("Disease table extraction completed")

if __name__ == "__main__":
    asyncio.run(main())

