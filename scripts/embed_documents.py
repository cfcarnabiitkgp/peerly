#!/usr/bin/env python3
"""
Script to embed documents and store them in Qdrant using LangChain.

This script processes PDFs from the rag_resources folder, chunks them,
generates embeddings (with automatic caching), and stores them in Qdrant.

Usage:
    python scripts/embed_documents.py --agent clarity
    python scripts/embed_documents.py --agent rigor
    python scripts/embed_documents.py --agent shared
    python scripts/embed_documents.py --all
"""

import argparse
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from qdrant_client import QdrantClient
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from langchain_qdrant import QdrantVectorStore
from langchain_core.documents import Document
from unstructured.partition.pdf import partition_pdf

from app.rag.config import clarity_rag_config, rigor_rag_config
from app.rag.caching import create_cached_embeddings


def embed_and_store(config, agent_type: str) -> None:
    """
    Embed documents and store them in Qdrant using LangChain.

    Args:
        config: RAG configuration
        agent_type: Type of agent (for metadata)
    """
    print(f"\n{'='*60}")
    print(f"Processing {agent_type.upper()} documents")
    print(f"{'='*60}")

    # 1. Load documents using Unstructured PDF parser
    print(f"\n1. Loading and parsing documents from {config.documents_path}...")
    docs_path = Path(config.documents_path)

    if not docs_path.exists():
        print(f"   Warning: Directory {config.documents_path} does not exist")
        return

    # Check if there are any PDFs
    pdf_files = list(docs_path.glob("*.pdf"))
    if not pdf_files:
        print(f"   No PDF files found in {config.documents_path}")
        return

    # Process all PDFs with Unstructured
    documents = []
    for pdf_file in pdf_files:
        print(f"   Processing {pdf_file.name}...")
        # Partition PDF with Unstructured - extracts elements with types
        elements = partition_pdf(
            filename=str(pdf_file),
            strategy="fast",  # Uses pypdfium2 (faster, no poppler required)
            infer_table_structure=False,  # Disable for faster processing
        )

        # Filter out headers, footers, and page numbers (often noise)
        filtered_elements = [
            el for el in elements
            if el.category not in ["Header", "Footer", "PageNumber"]
        ]

        # Convert to LangChain Documents (one doc per element initially)
        for element in filtered_elements:
            if element.text.strip():  # Skip empty elements
                doc = Document(
                    page_content=element.text,
                    metadata={
                        "source": str(pdf_file),
                        "element_type": element.category,
                    }
                )
                documents.append(doc)

    print(f"   Extracted {len(documents)} elements from {len(pdf_files)} PDFs")

    if not documents:
        print(f"   No content extracted from PDFs")
        return

    # 2. Create cached embeddings (used for both chunking and storage)
    print(f"\n2. Creating cached embeddings (namespace: {agent_type})...")
    embeddings = create_cached_embeddings(
        model=config.embedding_config.embedding_model,
        namespace=agent_type,  # Separate cache per agent
    )
    print(f"   Using model: {config.embedding_config.embedding_model}")
    print(f"   Cache enabled: {config.embedding_config.use_cache}")

    # 3. Split documents using configured chunking strategy
    print(f"\n3. Chunking documents...")
    print(f"   Strategy: {config.embedding_config.chunking_strategy}")

    if config.embedding_config.chunking_strategy == "semantic":
        # Semantic chunker using the embeddings we just created
        text_splitter = SemanticChunker(
            embeddings=embeddings,
            breakpoint_threshold_type=config.embedding_config.breakpoint_threshold_type,
            breakpoint_threshold_amount=config.embedding_config.breakpoint_threshold_amount,
        )
        print(f"   Breakpoint: {config.embedding_config.breakpoint_threshold_type} @ {config.embedding_config.breakpoint_threshold_amount}")
    else:
        # Recursive character text splitter with custom separators for list-based docs
        # Numbers, bullets, and structure-aware separators
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.embedding_config.chunk_size,
            chunk_overlap=config.embedding_config.chunk_overlap,
            length_function=len,
            separators=[
                "\n\n",  # Double newlines (paragraphs)
                "\n",    # Single newlines
                ". ",    # Sentence boundaries
                " ",     # Word boundaries
                "",      # Character-level fallback
            ],
        )
        print(f"   Chunk size: {config.embedding_config.chunk_size}, Overlap: {config.embedding_config.chunk_overlap}")

    chunks = text_splitter.split_documents(documents)
    print(f"   Created {len(chunks)} chunks")

    # 4. Post-processing: Smart filtering for quality chunks
    print(f"\n4. Filtering low-quality chunks...")
    min_chunk_length = 200  # Default minimum for regular text

    # Mathematical symbols that indicate valuable content
    math_symbols = ['=', '∫', '∑', '∂', '∆', 'lim', 'sup', 'inf', '±', '≤', '≥',
                    '∀', '∃', '⊥', '∧', '∨', '→', '¬', '∈', '⊂', '⊆', '∪', '∩']

    quality_chunks = []
    for chunk in chunks:
        content = chunk.page_content.strip()

        # Check if chunk contains mathematical content
        has_math = any(symbol in content for symbol in math_symbols)

        # Smart length filtering: lower threshold for mathematical content
        effective_min_length = 50 if has_math else min_chunk_length

        # Skip very short chunks (unless they have math and are at least 50 chars)
        if len(content) < effective_min_length:
            continue

        # Skip chunks that are just URLs or references
        if content.startswith("http://") or content.startswith("https://"):
            continue

        # Skip chunks that are just "See" or similar navigation text
        if content.lower().startswith("see ") and len(content) < 100:
            continue

        quality_chunks.append(chunk)

    print(f"   Kept {len(quality_chunks)} quality chunks (filtered {len(chunks) - len(quality_chunks)} low-quality)")
    chunks = quality_chunks

    # 5. Add agent_type metadata to all chunks
    print(f"\n5. Adding metadata...")
    for chunk in chunks:
        chunk.metadata["agent_type"] = agent_type

    # 6. Create Qdrant client
    print(f"\n6. Connecting to Qdrant...")
    qdrant_client = QdrantClient(url="http://localhost:6333")

    # Check if collection exists and delete it for clean re-indexing
    try:
        collections = qdrant_client.get_collections().collections
        if any(col.name == config.collection_name for col in collections):
            print(f"   Deleting existing collection '{config.collection_name}'...")
            qdrant_client.delete_collection(config.collection_name)
    except Exception as e:
        print(f"   Note: {e}")

    # 7. Create collection and embed documents
    print(f"\n7. Creating collection and embedding documents...")
    print(f"   Collection: '{config.collection_name}'")
    print(f"   (This may take a while on first run, subsequent runs use cache)")

    # from_documents creates the collection and adds all documents
    vector_store = QdrantVectorStore.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=config.collection_name,
        url="http://localhost:6333",
    )

    print(f"   ✓ Successfully created collection and stored {len(chunks)} chunks")

    # 8. Verify storage
    print(f"\n8. Verifying storage...")
    collection_info = qdrant_client.get_collection(config.collection_name)
    print(f"   Collection: {collection_info.config.params.vectors}")
    print(f"   Points count: {collection_info.points_count}")


def main():
    """Main function to run the embedding script."""
    parser = argparse.ArgumentParser(
        description="Embed documents and store in Qdrant using LangChain"
    )
    parser.add_argument(
        "--agent",
        choices=["clarity", "rigor"],
        help="Agent type to embed documents for",
    )
    parser.add_argument(
        "--all", action="store_true", help="Embed documents for all agents"
    )

    args = parser.parse_args()

    if not args.agent and not args.all:
        parser.error("Either --agent or --all must be specified")

    # Process based on arguments
    if args.all:
        embed_and_store(clarity_rag_config, "clarity")
        embed_and_store(rigor_rag_config, "rigor")
    else:
        if args.agent == "clarity":
            embed_and_store(clarity_rag_config, "clarity")
        elif args.agent == "rigor":
            embed_and_store(rigor_rag_config, "rigor")
        else:
            parser.error(f"Invalid agent: {args.agent}")
            
    print(f"\n{'='*60}")
    print("All done! ✓")
    print(f"{'='*60}\n")
    print("Next steps:")
    print("1. Verify Qdrant collections: curl http://localhost:6333/collections")
    print("2. Check cache directory: ls -la app/embedding_cache/")
    print("3. Run your review workflow - RAG is now active!")


if __name__ == "__main__":
    main()
