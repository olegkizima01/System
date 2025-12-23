#!/usr/bin/env python3
"""
MCP Data Ingestion Script
Downloads and ingests prompts and schemas into ChromaDB.
Optimized for Apple Silicon (MPS).
"""

import os
import json
import logging
import argparse
import requests
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mcp_integration.chroma_utils import create_persistent_client, get_default_chroma_persist_dir
from typing import List, Dict, Any

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
CHROMA_PERSIST_DIR = os.path.expanduser("~/.system_cli/chroma/mcp_integration")
PROMPTS_COLLECTION = "mcp_prompts"
SCHEMAS_COLLECTION = "mcp_tool_schemas"

# Github Sources for Prompts
PROMPT_SOURCES = [
    {
        "name": "fabric_patterns",
        "url": "https://api.github.com/repos/danielmiessler/fabric/contents/patterns",
        "type": "github_dir"
    },
    {
        "name": "awesome_mcp_prompts",
        "url": "https://raw.githubusercontent.com/f/awesome-chatgpt-prompts/main/prompts.csv", # Placeholder for actual valid CSV/JSON
        "type": "csv"
    }
]

def get_device():
    """Check for MPS (Apple Silicon) or CUDA, else CPU."""
    try:
        import torch
        if torch.backends.mps.is_available():
            return "mps"
        elif torch.cuda.is_available():
            return "cuda"
    except ImportError:
        pass
    return "cpu"

def setup_chroma():
    """Setup ChromaDB client with sentence-transformers embedding function."""
    try:
        import chromadb
        from chromadb.utils import embedding_functions
        
        device = get_device()
        logger.info(f"🚀 Using device: {device} for embeddings")
        
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2",
            device=device
        )
        
        persist_dir = get_default_chroma_persist_dir() / "mcp_integration"
        init_res = create_persistent_client(persist_dir=persist_dir, logger=logger)
        
        if not init_res:
            logger.error("❌ Failed to initialize ChromaDB client")
            return None, None
            
        client = init_res.client
        
        prompts_col = client.get_or_create_collection(
            name=PROMPTS_COLLECTION,
            embedding_function=ef,
            metadata={"description": "MCP System Prompts"}
        )
        
        schemas_col = client.get_or_create_collection(
            name=SCHEMAS_COLLECTION,
            embedding_function=ef,
            metadata={"description": "MCP Tool Schemas"}
        )
        
        return prompts_col, schemas_col
    
    except Exception as e:
        logger.error(f"❌ Chroma Setup Failed: {e}")
        return None, None

def ingest_github_dir_prompts(source: Dict, collection):
    """Ingest prompts from a GitHub directory (like Fabric)."""
    logger.info(f"📥 Ingesting from {source['name']}...")
    try:
        # 1. List directory files
        resp = requests.get(source['url'])
        if resp.status_code != 200:
            logger.error(f"Failed to fetch {source['url']}")
            return
            
        items = resp.json()
        documents = []
        metadatas = []
        ids = []
        
        for item in items:
            if item['type'] == 'dir':
                # Deep dive for system.md
                pattern_name = item['name']
                sys_url = f"{item['url']}/system.md".replace("api.github.com/repos", "raw.githubusercontent.com").replace("/contents/", "/")
                # Fix raw url construction for reliability (basic attempt)
                # Fabric specific: patterns/PATTERN_NAME/system.md
                raw_url = f"https://raw.githubusercontent.com/danielmiessler/fabric/main/patterns/{pattern_name}/system.md"
                
                try:
                    p_resp = requests.get(raw_url)
                    if p_resp.status_code == 200:
                        content = p_resp.text
                        documents.append(content)
                        metadatas.append({"source": source['name'], "pattern": pattern_name, "type": "system_prompt"})
                        ids.append(f"fabric_{pattern_name}")
                        logger.info(f"   - Loaded {pattern_name}")
                except Exception as ex:
                    logger.warning(f"   Skipped {pattern_name}: {ex}")

        if documents:
            collection.upsert(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"✅ Upserted {len(documents)} prompts from {source['name']}")
            
    except Exception as e:
        logger.error(f"Error ingesting {source['name']}: {e}")

def ingest_samples(collection):
    """Ingest sample prompts for verification."""
    logger.info("🧪 Ingesting sample prompts...")
    documents = [
        "You are an expert at extracting patterns from text. Analyze the input and output a structured pattern description.",
        "You are a coding assistant optimized for Python. Always use type hints and docstrings.",
        "You are a database administrator. Analyze the logs for slow queries and suggest indexes."
    ]
    metadatas = [
        {"source": "sample", "pattern": "extract_pattern", "type": "system_prompt"},
        {"source": "sample", "pattern": "python_coder", "type": "system_prompt"},
        {"source": "sample", "pattern": "dba_expert", "type": "system_prompt"},
    ]
    ids = ["sample_1", "sample_2", "sample_3"]
    
    collection.upsert(documents=documents, metadatas=metadatas, ids=ids)
    logger.info(f"✅ Upserted {len(documents)} sample prompts")

def main():
    parser = argparse.ArgumentParser(description="Ingest MCP Data")
    parser.add_argument("--prompts", action="store_true", help="Ingest prompts")
    parser.add_argument("--schemas", action="store_true", help="Ingest schemas (placeholder)")
    args = parser.parse_args()
    
    prompts_col, schemas_col = setup_chroma()
    if not prompts_col:
        return

    if args.prompts:
        # Try samples first to guarantee data
        ingest_samples(prompts_col)
        
        for source in PROMPT_SOURCES:
            if source['type'] == 'github_dir':
                ingest_github_dir_prompts(source, prompts_col)
                
    if args.schemas:
        logger.info("Schema ingestion logic to be implemented based on specific registry format.")

if __name__ == "__main__":
    main()
