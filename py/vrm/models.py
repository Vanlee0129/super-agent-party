"""VRM model management for storing and loading avatar models."""

import asyncio
import logging
import os
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, BinaryIO
from enum import Enum

from py.core.config import config, DEFAULT_VRM_DIR

logger = logging.getLogger(__name__)


class ModelFormat(Enum):
    """VRM model format versions."""
    VRM0 = "vrm0"
    VRM1 = "vrm1"


@dataclass
class VRMModel:
    """VRM model metadata."""
    id: str
    name: str
    file_path: str
    format: ModelFormat = ModelFormat.VRM1
    thumbnail_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=0)
    file_size: int = 0

    @property
    def url(self) -> str:
        """Get the URL/path for this model."""
        return self.file_path

    @property
    def exists(self) -> bool:
        """Check if model file exists."""
        return os.path.exists(self.file_path)


@dataclass
class ModelUploadResult:
    """Result of a model upload operation."""
    success: bool
    model_id: Optional[str] = None
    error: Optional[str] = None
    file_path: Optional[str] = None


class VRMModelManager:
    """Manages VRM model storage and retrieval."""

    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize VRM model manager.

        Args:
            storage_dir: Directory to store VRM models. Defaults to configured path.
        """
        self.storage_dir = storage_dir or DEFAULT_VRM_DIR
        self._models: Dict[str, VRMModel] = {}
        self._lock = asyncio.Lock()

        # Ensure storage directory exists
        os.makedirs(self.storage_dir, exist_ok=True)

        # Load existing models
        asyncio.create_task(self._scan_existing_models())

    async def _scan_existing_models(self) -> None:
        """Scan storage directory for existing VRM models."""
        try:
            if not os.path.exists(self.storage_dir):
                return

            for filename in os.listdir(self.storage_dir):
                if filename.lower().endswith(('.vrm', '.glb', '.gltf')):
                    file_path = os.path.join(self.storage_dir, filename)

                    # Create model entry
                    model = VRMModel(
                        id=str(uuid.uuid4()),
                        name=Path(filename).stem,
                        file_path=file_path,
                        file_size=os.path.getsize(file_path),
                        created_at=os.path.getmtime(file_path),
                    )

                    self._models[model.id] = model

            logger.info(f"Loaded {len(self._models)} existing VRM models")

        except Exception as e:
            logger.error(f"Error scanning existing models: {e}")

    async def upload_model(
        self,
        file_data: BinaryIO,
        filename: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ModelUploadResult:
        """
        Upload and store a new VRM model.

        Args:
            file_data: File-like object containing model data
            filename: Original filename
            metadata: Optional metadata dictionary

        Returns:
            ModelUploadResult with success status and model ID
        """
        async with self._lock:
            try:
                # Generate unique ID and file path
                model_id = str(uuid.uuid4())
                safe_filename = f"{model_id}_{filename}"
                file_path = os.path.join(self.storage_dir, safe_filename)

                # Determine format
                format = ModelFormat.VRM1 if filename.lower().endswith('.vrm') else ModelFormat.VRM0

                # Write file
                with open(file_path, 'wb') as f:
                    content = file_data.read()
                    f.write(content)

                file_size = len(content)

                # Create model entry
                model = VRMModel(
                    id=model_id,
                    name=Path(filename).stem,
                    file_path=file_path,
                    format=format,
                    metadata=metadata or {},
                    created_at=asyncio.get_event_loop().time(),
                    file_size=file_size,
                )

                self._models[model_id] = model

                logger.info(f"Uploaded VRM model: {filename} (ID: {model_id})")

                return ModelUploadResult(
                    success=True,
                    model_id=model_id,
                    file_path=file_path,
                )

            except Exception as e:
                logger.error(f"Error uploading VRM model: {e}")
                return ModelUploadResult(success=False, error=str(e))

    async def get_model(self, model_id: str) -> Optional[VRMModel]:
        """Get model by ID."""
        return self._models.get(model_id)

    async def list_models(self) -> List[VRMModel]:
        """List all available models."""
        return list(self._models.values())

    async def delete_model(self, model_id: str) -> bool:
        """
        Delete a VRM model.

        Args:
            model_id: ID of model to delete

        Returns:
            True if deleted, False if not found
        """
        async with self._lock:
            model = self._models.get(model_id)
            if not model:
                return False

            # Delete file
            try:
                if os.path.exists(model.file_path):
                    os.remove(model.file_path)
            except Exception as e:
                logger.error(f"Error deleting model file: {e}")

            # Remove from registry
            del self._models[model_id]

            logger.info(f"Deleted VRM model: {model_id}")
            return True

    async def update_metadata(
        self,
        model_id: str,
        metadata: Dict[str, Any]
    ) -> Optional[VRMModel]:
        """Update model metadata."""
        model = self._models.get(model_id)
        if model:
            model.metadata.update(metadata)
            return model
        return None

    async def get_model_file(self, model_id: str) -> Optional[bytes]:
        """Get raw model file data."""
        model = self._models.get(model_id)
        if not model or not model.exists:
            return None

        try:
            with open(model.file_path, 'rb') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading model file: {e}")
            return None

    @property
    def model_count(self) -> int:
        """Get total number of models."""
        return len(self._models)


# Global model manager instance
_vrm_model_manager: Optional[VRMModelManager] = None


def get_vrm_model_manager() -> VRMModelManager:
    """Get the global VRM model manager instance."""
    global _vrm_model_manager
    if _vrm_model_manager is None:
        _vrm_model_manager = VRMModelManager()
    return _vrm_model_manager
