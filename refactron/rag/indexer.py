"""Vector index management using ChromaDB."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

try:
    import chromadb
    from chromadb.config import Settings
    from sentence_transformers import SentenceTransformer

    CHROMA_AVAILABLE = True
except ImportError:
    chromadb = None
    Settings = None
    SentenceTransformer = None
    CHROMA_AVAILABLE = False

from refactron.rag.chunker import CodeChunk
from refactron.rag.parser import CodeParser

# Import for type hints
try:
    from refactron.llm.client import GroqClient
except ImportError:
    GroqClient = None  # type: ignore


@dataclass
class IndexStats:
    """Statistics about the RAG index."""

    total_chunks: int
    total_files: int
    chunk_types: dict
    embedding_model: str
    index_path: str


class RAGIndexer:
    """Manages code indexing for RAG retrieval."""

    def __init__(
        self,
        workspace_path: Path,
        embedding_model: str = "all-MiniLM-L6-v2",
        collection_name: str = "code_chunks",
        llm_client: Optional[GroqClient] = None,
    ):
        """Initialize the RAG indexer.

        Args:
            workspace_path: Path to the workspace directory
            embedding_model: Name of the sentence-transformers model
            collection_name: Name of the ChromaDB collection
            llm_client: Optional LLM client for code summarization
        """
        if not CHROMA_AVAILABLE:
            raise RuntimeError(
                "ChromaDB is not available. "
                "Install with: pip install chromadb sentence-transformers"
            )

        self.workspace_path = Path(workspace_path)
        self.index_path = self.workspace_path / ".rag"
        self.index_path.mkdir(exist_ok=True)

        # Initialize LLM client for summarization
        # GroqClient is used for type hints and potential init below

        self.llm_client = llm_client

        # Initialize embedding model
        self.embedding_model_name = embedding_model
        self.embedding_model = SentenceTransformer(embedding_model)

        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=str(self.index_path / "chroma"), settings=Settings(anonymized_telemetry=False)
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"embedding_model": embedding_model, "hnsw:space": "cosine"},
        )

        self.parser = CodeParser()
        from refactron.rag.chunker import CodeChunker
        self.chunker = CodeChunker(self.parser)

    def index_repository(
        self, repo_path: Optional[Path] = None, summarize: bool = False
    ) -> IndexStats:
        """Index an entire repository.

        Args:
            repo_path: Path to repository (defaults to workspace_path)
            summarize: Whether to use AI to summarize code for better retrieval

        Returns:
            Statistics about the indexed content
        """
        if summarize and not self.llm_client:
            from refactron.llm.client import GroqClient

            try:
                self.llm_client = GroqClient()
            except Exception as e:
                print(f"Warning: Could not initialize AI for summarization: {e}")
                summarize = False

        if repo_path is None:
            repo_path = self.workspace_path

        repo_path = Path(repo_path)

        # Find all Python files
        python_files = list(repo_path.rglob("*.py"))

        # Filter out common excluded directories
        excluded_dirs = {".git", ".rag", "__pycache__", "venv", ".venv", "env", "node_modules"}
        python_files = [
            f for f in python_files if not any(excluded in f.parts for excluded in excluded_dirs)
        ]

        total_chunks = 0
        chunk_type_counts: Dict[str, int] = {}

        # Index each file
        for py_file in python_files:
            try:
                chunks = self._index_file(py_file, summarize=summarize)
                total_chunks += len(chunks)

                # Count chunk types
                for chunk in chunks:
                    chunk_type_counts[chunk.chunk_type] = (
                        chunk_type_counts.get(chunk.chunk_type, 0) + 1
                    )
            except Exception as e:
                # Skip files that can't be parsed
                print(f"Warning: Could not index {py_file}: {e}")
                continue

        # Save index metadata
        self._save_metadata(
            {
                "total_chunks": total_chunks,
                "total_files": len(python_files),
                "chunk_types": chunk_type_counts,
            }
        )

        return IndexStats(
            total_chunks=total_chunks,
            total_files=len(python_files),
            chunk_types=chunk_type_counts,
            embedding_model=self.embedding_model_name,
            index_path=str(self.index_path),
        )

    def _index_file(self, file_path: Path, summarize: bool = False) -> List[CodeChunk]:
        """Index a single Python file.

        Args:
            file_path: Path to the Python file
            summarize: Whether to use AI to summarize chunks

        Returns:
            List of code chunks that were indexed
        """
        # Chunk the file (parser is called inside chunker)
        chunks = self.chunker.chunk_file(file_path)

        if summarize and self.llm_client:
            for chunk in chunks:
                try:
                    summary = self._summarize_chunk(chunk)
                    if summary:
                        # Prepend summary for semantic searchability
                        chunk.content = f"Summary: {summary}\n\n{chunk.content}"
                        chunk.metadata["ai_summary"] = summary
                except Exception as e:
                    print(f"Warning: AI summarization failed for chunk in {file_path}: {e}")

        # Add chunks to the index
        self.add_chunks(chunks)

        return chunks

    def _summarize_chunk(self, chunk: CodeChunk) -> Optional[str]:
        """Use AI to generate a brief semantic summary of a code chunk."""
        if not self.llm_client:
            return None

        prompt = (
            "Analyze the following Python code snippet and provide a one-sentence "
            "summary of its purpose, focusing on what it DOES (e.g. 'Calculates user permissions' "
            "or 'Handles secure database connections').\n\n"
            f"Code:\n{chunk.content}"
        )

        try:
            summary = self.llm_client.generate(
                prompt=prompt,
                system=(
                    "You are a senior software architect. "
                    "Provide a concise, semantic summary of code purpose."
                ),
                max_tokens=100,
            )
            return summary.strip()
        except Exception:
            return None

    def add_chunks(self, chunks: List[CodeChunk]) -> None:
        """Add code chunks to the vector index.

        Args:
            chunks: List of code chunks to add
        """
        if not chunks:
            return

        # Prepare data for ChromaDB
        documents = [chunk.content for chunk in chunks]
        metadatas = []
        for chunk in chunks:
            metadata = {
                "chunk_type": chunk.chunk_type,
                "file_path": chunk.file_path,
                "name": chunk.name,
                "line_start": chunk.line_range[0],
                "line_end": chunk.line_range[1],
            }
            # Add chunk metadata, converting lists/dicts to JSON strings
            for key, value in chunk.metadata.items():
                if isinstance(value, (list, dict)):
                    metadata[key] = json.dumps(value)
                elif value is not None:  # Skip None values
                    metadata[key] = value
            metadatas.append(metadata)

        ids = [f"{chunk.file_path}:{chunk.line_range[0]}-{chunk.line_range[1]}" for chunk in chunks]

        # Generate embeddings
        embeddings = self.embedding_model.encode(documents, show_progress_bar=False).tolist()

        # Add to collection
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
            embeddings=embeddings,
        )

    def get_stats(self) -> IndexStats:
        """Get statistics about the current index.

        Returns:
            Index statistics
        """
        metadata = self._load_metadata()

        return IndexStats(
            total_chunks=metadata.get("total_chunks", 0),
            total_files=metadata.get("total_files", 0),
            chunk_types=metadata.get("chunk_types", {}),
            embedding_model=self.embedding_model_name,
            index_path=str(self.index_path),
        )

    def _save_metadata(self, metadata: Dict[str, Any]) -> None:
        """Save index metadata."""
        metadata_file = self.index_path / "metadata.json"
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

    def _load_metadata(self) -> Dict[str, Any]:
        """Load index metadata."""
        metadata_file = self.index_path / "metadata.json"
        if not metadata_file.exists():
            return {}

        with open(metadata_file, "r") as f:
            return cast(Dict[str, Any], json.load(f))
