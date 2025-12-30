"""
Data loader for OmniAgent.

Handles the complete flow of:
1. Receiving uploaded files
2. Storing them safely
3. Loading into DuckDB
4. Inferring schema
5. Creating dataset profile
"""

import hashlib
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import BinaryIO

from omniagent.config.logging import get_logger
from omniagent.config.settings import get_settings
from omniagent.data.duckdb_engine import DuckDBEngine
from omniagent.data.schema_inference import SchemaInferrer
from omniagent.models.dataset import DatasetMetadata, DatasetProfile

logger = get_logger(__name__)


class DataLoader:
    """
    Handles dataset loading and management.
    
    This is the main entry point for getting data into OmniAgent.
    """
    
    def __init__(self, db_engine: DuckDBEngine | None = None):
        """
        Initialize data loader.
        
        Args:
            db_engine: DuckDB engine to use. Creates new one if not provided.
        """
        self.settings = get_settings()
        self.db_engine = db_engine or DuckDBEngine()
        
        # Ensure upload directory exists
        self.uploads_dir = Path(self.settings.uploads_dir)
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        
        # Track loaded datasets
        self._datasets: dict[str, DatasetMetadata] = {}
    
    def _generate_dataset_id(self, filename: str) -> str:
        """Generate a unique dataset ID."""
        timestamp = datetime.now().isoformat()
        content = f"{filename}-{timestamp}"
        return hashlib.sha256(content.encode()).hexdigest()[:12]
    
    def _sanitize_table_name(self, filename: str) -> str:
        """Create a valid table name from filename."""
        # Remove extension and invalid characters
        name = Path(filename).stem
        # Replace non-alphanumeric with underscore
        name = "".join(c if c.isalnum() else "_" for c in name)
        # Ensure doesn't start with number
        if name[0].isdigit():
            name = f"t_{name}"
        return name.lower()
    
    def load_file(
        self,
        file: BinaryIO,
        filename: str,
    ) -> DatasetProfile:
        """
        Load a file into the system.
        
        Args:
            file: File-like object with the data
            filename: Original filename
            
        Returns:
            DatasetProfile with all metadata
        """
        logger.info("Loading file", filename=filename)
        
        # Generate IDs
        dataset_id = self._generate_dataset_id(filename)
        table_name = self._sanitize_table_name(filename)
        
        # Save file to disk
        file_path = self.uploads_dir / f"{dataset_id}_{filename}"
        
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file, f)
        
        file_size = file_path.stat().st_size
        logger.info("File saved", path=str(file_path), size=file_size)
        
        # Load into DuckDB
        row_count = self.db_engine.load_csv(file_path, table_name)
        
        # Infer schema
        inferrer = SchemaInferrer(self.db_engine.connection)
        columns = inferrer.infer_all_columns(table_name)
        
        # Create metadata
        metadata = DatasetMetadata(
            dataset_id=dataset_id,
            filename=filename,
            file_size_bytes=file_size,
            row_count=row_count,
            column_count=len(columns),
            columns=columns,
            storage_path=str(file_path),
            table_name=table_name,
        )
        
        # Get sample rows
        sample_rows = self.db_engine.get_sample_rows(table_name, n=5)
        
        # Calculate quality metrics
        total_cells = row_count * len(columns)
        total_nulls = sum(col.null_count for col in columns)
        null_percentage = (total_nulls / total_cells * 100) if total_cells > 0 else 0
        
        # Create profile
        profile = DatasetProfile(
            metadata=metadata,
            total_null_cells=total_nulls,
            null_percentage=round(null_percentage, 2),
            memory_usage_mb=file_size / (1024 * 1024),
            sample_rows=sample_rows,
        )
        
        # Store in registry
        self._datasets[dataset_id] = metadata
        
        logger.info(
            "Dataset loaded successfully",
            dataset_id=dataset_id,
            table=table_name,
            rows=row_count,
            columns=len(columns),
        )
        
        return profile
    
    def load_csv_path(self, csv_path: str | Path) -> DatasetProfile:
        """
        Load a CSV file from a path.
        
        Convenience method for loading existing files.
        """
        path = Path(csv_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        with open(path, "rb") as f:
            return self.load_file(f, path.name)
    
    def get_dataset(self, dataset_id: str) -> DatasetMetadata | None:
        """Get metadata for a dataset."""
        return self._datasets.get(dataset_id)
    
    def get_table_name(self, dataset_id: str) -> str | None:
        """Get the DuckDB table name for a dataset."""
        metadata = self.get_dataset(dataset_id)
        return metadata.table_name if metadata else None
    
    def list_datasets(self) -> list[DatasetMetadata]:
        """List all loaded datasets."""
        return list(self._datasets.values())
    
    def delete_dataset(self, dataset_id: str) -> bool:
        """
        Delete a dataset and its files.
        
        Returns True if deleted, False if not found.
        """
        metadata = self._datasets.get(dataset_id)
        if not metadata:
            return False
        
        # Delete file
        try:
            Path(metadata.storage_path).unlink(missing_ok=True)
        except Exception as e:
            logger.warning(f"Could not delete file: {e}")
        
        # Drop table (if not read-only)
        try:
            self.db_engine.connection.execute(
                f"DROP TABLE IF EXISTS {metadata.table_name}"
            )
        except Exception as e:
            logger.warning(f"Could not drop table: {e}")
        
        # Remove from registry
        del self._datasets[dataset_id]
        
        logger.info("Dataset deleted", dataset_id=dataset_id)
        return True
