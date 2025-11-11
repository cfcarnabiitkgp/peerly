#!/sr/bin/env python3
"""
Simplified script to populate Railway Qdrant using direct REST API calls.
This bypasses the Qdrant client library timeout issues.
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

import requests
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from langchain_core.documents import Document
from unstructured.partition.pdf import partition_pdf
from langchain_openai import OpenAIEmbeddings

from app.rag.config import clarity_rag_config, rigor_rag_config


def process_pdfs(docs_path: Path):
    """Process PDFs and return documents."""
    if not docs_path.exists():
        print(f"   Warning: Directory {docs_path} does not exist")
        return []

    pdf_files = list(docs_path.glob("*.pdf"))
    if not pdf_files:
        print(f"   No PDF files found in {docs_path}")
        return []

    documents = []
    for pdf_file in pdf_files:
        print(f"   Processing {pdf_file.name}...")
        elements = partition_pdf(
            filename=str(pdf_file),
            strategy="fast",
            infer_table_structure=False,
        )

        filtered_elements = [
            el for el in elements
            if el.category not in ["Header", "Footer", "PageNumber"]
        ]

        for element in filtered_elements:
            if element.text.strip():
                doc = Document(
                    page_content=element.text,
                    metadata={
                        "source": str(pdf_file),
                        "element_type": element.category,
                    }
                )
                documents.append(doc)

    return documents


def chunk_documents(documents, config, embeddings_model):
    """Chunk documents using config settings."""
    if config.embedding_config.chunking_strategy == "semantic":
        # Semantic chunking using embeddings
        text_splitter = SemanticChunker(
            embeddings=embeddings_model,
            breakpoint_threshold_type=config.embedding_config.breakpoint_threshold_type,
            breakpoint_threshold_amount=config.embedding_config.breakpoint_threshold_amount,
        )
        print(f"   Using semantic chunking: {config.embedding_config.breakpoint_threshold_type} @ {config.embedding_config.breakpoint_threshold_amount}")
    else:
        # Recursive character-based chunking
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.embedding_config.chunk_size,
            chunk_overlap=config.embedding_config.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        print(f"   Using recursive chunking: size={config.embedding_config.chunk_size}, overlap={config.embedding_config.chunk_overlap}")

    return text_splitter.split_documents(documents)


def filter_chunks(chunks):
    """Filter out low-quality chunks."""
    math_symbols = ['=', '∫', '∑', '∂', '∆', 'lim', 'sup', 'inf', '±', '≤', '≥',
                    '∀', '∃', '⊥', '∧', '∨', '→', '¬', '∈', '⊂', '⊆', '∪', '∩']

    quality_chunks = []
    for chunk in chunks:
        content = chunk.page_content.strip()
        has_math = any(symbol in content for symbol in math_symbols)
        min_length = 50 if has_math else 200

        if len(content) < min_length:
            continue
        if content.startswith(("http://", "https://")):
            continue
        if content.lower().startswith("see ") and len(content) < 100:
            continue

        quality_chunks.append(chunk)

    return quality_chunks


def create_collection_via_api(qdrant_url, collection_name, vector_size=1536):
    """Create a collection using REST API."""
    url = f"{qdrant_url}/collections/{collection_name}"

    # Delete if exists
    try:
        response = requests.delete(url, timeout=30)
        if response.status_code == 200:
            print(f"   Deleted existing collection '{collection_name}'")
    except Exception as e:
        print(f"   Collection doesn't exist yet (expected): {e}")

    # Create new collection
    payload = {
        "vectors": {
            "size": vector_size,
            "distance": "Cosine"
        }
    }

    response = requests.put(url, json=payload, timeout=30)
    if response.status_code == 200:
        print(f"   ✓ Created collection '{collection_name}'")
        return True
    else:
        print(f"   ❌ Failed to create collection: {response.status_code} - {response.text}")
        return False


def upload_points_via_api(qdrant_url, collection_name, points):
    """Upload points to collection using REST API."""
    url = f"{qdrant_url}/collections/{collection_name}/points"

    # Upload in batches of 100
    batch_size = 100
    total_uploaded = 0

    for i in range(0, len(points), batch_size):
        batch = points[i:i+batch_size]
        payload = {"points": batch}

        response = requests.put(url, json=payload, timeout=120)
        if response.status_code == 200:
            total_uploaded += len(batch)
            print(f"   Uploaded batch {i//batch_size + 1} ({total_uploaded}/{len(points)} points)")
        else:
            print(f"   ❌ Failed batch {i//batch_size + 1}: {response.status_code}")
            return False

    return True


def embed_and_store(config, agent_type, qdrant_url):
    """Process documents and upload to Railway Qdrant."""
    print(f"\n{'='*60}")
    print(f"Processing {agent_type.upper()} documents")
    print(f"{'='*60}")

    # 1. Load documents
    print(f"\n1. Loading documents from {config.documents_path}...")
    docs_path = Path(config.documents_path)
    documents = process_pdfs(docs_path)
    print(f"   Extracted {len(documents)} elements")

    if not documents:
        return

    # 2. Create embeddings model (needed for semantic chunking)
    print(f"\n2. Creating embeddings model...")
    embeddings_model = OpenAIEmbeddings(model=config.embedding_config.embedding_model)
    print(f"   Using model: {config.embedding_config.embedding_model}")

    # 3. Chunk documents (may use embeddings for semantic chunking)
    print(f"\n3. Chunking documents...")
    chunks = chunk_documents(documents, config, embeddings_model)
    print(f"   Created {len(chunks)} chunks")

    # 4. Filter chunks
    print(f"\n4. Filtering low-quality chunks...")
    chunks = filter_chunks(chunks)
    print(f"   Kept {len(chunks)} quality chunks")

    # 5. Add metadata
    print(f"\n5. Adding metadata...")
    for chunk in chunks:
        chunk.metadata["agent_type"] = agent_type

    # 6. Create embeddings for filtered chunks
    print(f"\n6. Creating embeddings for chunks...")
    texts = [chunk.page_content for chunk in chunks]
    vectors = embeddings_model.embed_documents(texts)
    print(f"   Generated {len(vectors)} embeddings")

    # 7. Create collection via REST API
    print(f"\n7. Creating collection via REST API...")
    if not create_collection_via_api(qdrant_url, config.collection_name, vector_size=len(vectors[0])):
        return

    # 8. Prepare points
    print(f"\n8. Preparing points...")
    points = []
    for idx, (chunk, vector) in enumerate(zip(chunks, vectors)):
        point = {
            "id": idx,
            "vector": vector,
            "payload": {
                "page_content": chunk.page_content,
                "metadata": chunk.metadata
            }
        }
        points.append(point)

    # 9. Upload via REST API
    print(f"\n9. Uploading to Railway Qdrant...")
    if upload_points_via_api(qdrant_url, config.collection_name, points):
        print(f"   ✓ Successfully uploaded {len(points)} points")
    else:
        print(f"   ❌ Upload failed")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--qdrant-url", required=True)
    parser.add_argument("--agent", choices=["clarity", "rigor"])
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    if not args.agent and not args.all:
        parser.error("Either --agent or --all required")

    qdrant_url = args.qdrant_url.rstrip('/')

    if args.all:
        embed_and_store(clarity_rag_config, "clarity", qdrant_url)
        embed_and_store(rigor_rag_config, "rigor", qdrant_url)
    elif args.agent == "clarity":
        embed_and_store(clarity_rag_config, "clarity", qdrant_url)
    elif args.agent == "rigor":
        embed_and_store(rigor_rag_config, "rigor", qdrant_url)

    print(f"\n{'='*60}")
    print("✓ Railway Qdrant populated successfully!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
