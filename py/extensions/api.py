"""Extensions API - FastAPI routes for extension management."""
import asyncio
import time
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File
from pydantic import BaseModel
from enum import Enum

from py.get_setting import EXT_DIR
from py.extensions.manager import ExtensionManager, ExtensionStatus, Extension
from py.extensions.installer import ExtensionInstaller
from py.extensions.validator import ManifestValidator


router = APIRouter(prefix="/api/v1/extensions", tags=["extensions"])


# ==================== Request/Response Models ====================

class ExtensionStatusModel(str, Enum):
    INSTALLED = "installed"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


class ExtensionModel(BaseModel):
    """Extension response model."""
    id: str
    name: str
    description: str
    version: str
    author: str
    status: ExtensionStatusModel
    config: Dict[str, Any] = {}


class ExtensionManifestModel(BaseModel):
    """Extension manifest input model."""
    id: str
    name: str
    description: str
    version: str
    author: str
    systemPrompt: str = ""
    repository: Optional[str] = None
    category: str = ""
    transparent: bool = False
    width: int = 800
    height: int = 600
    enableVrmWindowSize: bool = False


class InstallRequest(BaseModel):
    """Install extension request."""
    repo_url: Optional[str] = None
    zip_file: Optional[str] = None


class InstallResponse(BaseModel):
    """Install operation response."""
    ext_id: str
    status: str
    message: Optional[str] = None


class TaskStatusResponse(BaseModel):
    """Installation task status response."""
    status: str
    detail: str
    progress: Optional[int] = None
    timestamp: Optional[float] = None


class RemotePluginItem(BaseModel):
    """Remote plugin list item."""
    id: str
    name: str
    description: str
    author: str
    version: str
    category: str = "Unknown"
    repository: str
    backupRepository: str = ""
    installed: bool = False


class RemotePluginList(BaseModel):
    """Remote plugin list response."""
    plugins: List[RemotePluginItem]


# ==================== Module-level Instances ====================

_manager: Optional[ExtensionManager] = None
_installer: Optional[ExtensionInstaller] = None


def get_manager() -> ExtensionManager:
    """Get or create extension manager instance."""
    global _manager
    if _manager is None:
        _manager = ExtensionManager(EXT_DIR)
    return _manager


def get_installer() -> ExtensionInstaller:
    """Get or create extension installer instance."""
    global _installer
    if _installer is None:
        _installer = ExtensionInstaller(EXT_DIR)
    return _installer


# ==================== Background Install Tasks ====================

install_tasks: Dict[str, Dict[str, Any]] = {}


def update_task_status(ext_id: str, status: str, detail: str, progress: Optional[int] = None):
    """Update background install task status."""
    install_tasks[ext_id] = {
        "status": status,
        "detail": detail,
        "progress": progress,
        "timestamp": time.time()
    }


async def _run_bg_install(ext_id: str, repo_url: str, backup_url: str = ""):
    """Background installation task."""
    import time
    installer = get_installer()
    
    update_task_status(ext_id, "installing", "Preparing installation...", 0)
    
    try:
        success, message = await installer.install_from_github(ext_id, repo_url, backup_url)
        
        if success:
            update_task_status(ext_id, "success", "Installation complete", 100)
        else:
            update_task_status(ext_id, "error", message)
    except Exception as e:
        update_task_status(ext_id, "error", str(e))


# ==================== API Routes ====================

@router.get("/", response_model=List[ExtensionModel])
async def list_extensions() -> List[ExtensionModel]:
    """List all installed extensions."""
    manager = get_manager()
    extensions = manager.list_all()
    
    return [
        ExtensionModel(
            id=ext.id,
            name=ext.name,
            description=ext.description,
            version=ext.version,
            author=ext.author,
            status=ExtensionStatusModel(ext.status.value if isinstance(ext.status, ExtensionStatus) else ext.status),
            config=ext.config
        )
        for ext in extensions
    ]


@router.get("/{ext_id}", response_model=ExtensionModel)
async def get_extension(ext_id: str) -> ExtensionModel:
    """Get extension details."""
    manager = get_manager()
    ext = manager.get(ext_id)
    
    if not ext:
        raise HTTPException(status_code=404, detail="Extension not found")
    
    return ExtensionModel(
        id=ext.id,
        name=ext.name,
        description=ext.description,
        version=ext.version,
        author=ext.author,
        status=ExtensionStatusModel(ext.status.value if isinstance(ext.status, ExtensionStatus) else ext.status),
        config=ext.config
    )


@router.post("/install", response_model=ExtensionModel)
async def install_extension(
    request: InstallRequest,
    background: BackgroundTasks
) -> ExtensionModel:
    """
    Install extension from repository or ZIP.
    
    Supports:
    - Git repository (GitHub/Gitee) via repo_url
    - ZIP file via zip_file (base64 encoded)
    """
    import time
    
    installer = get_installer()
    
    if request.repo_url:
        ext_id = installer.get_ext_id_from_url(request.repo_url)
        
        # Check if already installed
        manager = get_manager()
        if manager.exists(ext_id):
            raise HTTPException(status_code=409, detail="Extension already installed")
        
        # Check for existing task
        if ext_id in install_tasks and install_tasks[ext_id]["status"] == "installing":
            raise HTTPException(status_code=409, detail="Installation already in progress")
        
        background.add_task(_run_bg_install, ext_id, request.repo_url, "")
        
        return ExtensionModel(
            id=ext_id,
            name=ext_id,
            description="",
            version="",
            author="",
            status=ExtensionStatusModel.INSTALLED,
            config={}
        )
    
    elif request.zip_file:
        # ZIP installation would need file upload endpoint
        raise HTTPException(status_code=400, detail="ZIP installation requires /upload-zip endpoint")
    
    else:
        raise HTTPException(status_code=400, detail="Either repo_url or zip_file is required")


@router.post("/upload-zip", response_model=InstallResponse)
async def upload_zip(
    file: UploadFile = File(...),
    background: BackgroundTasks = None
) -> InstallResponse:
    """Upload and install extension from ZIP file."""
    import time
    
    if not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only ZIP files are supported")
    
    ext_id = Path(file.filename).stem
    manager = get_manager()
    
    if manager.exists(ext_id):
        raise HTTPException(status_code=409, detail="Extension already exists")
    
    if ext_id in install_tasks and install_tasks[ext_id]["status"] == "installing":
        return InstallResponse(ext_id=ext_id, status="installing", message="Installation already in progress")
    
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file")
    
    installer = get_installer()
    success, message = await installer.install_from_zip(ext_id, content, file.filename)
    
    if success:
        update_task_status(ext_id, "success", "Installation complete", 100)
        return InstallResponse(ext_id=ext_id, status="success", message=message)
    else:
        update_task_status(ext_id, "error", message)
        raise HTTPException(status_code=500, detail=message)


@router.delete("/{ext_id}")
async def uninstall_extension(ext_id: str):
    """Uninstall extension."""
    manager = get_manager()
    
    if not manager.exists(ext_id):
        raise HTTPException(status_code=404, detail="Extension not found")
    
    if not manager.delete(ext_id):
        raise HTTPException(status_code=500, detail="Failed to uninstall extension")
    
    return {"status": "deleted", "ext_id": ext_id}


@router.post("/{ext_id}/enable")
async def enable_extension(ext_id: str):
    """Enable extension."""
    manager = get_manager()
    
    if not manager.exists(ext_id):
        raise HTTPException(status_code=404, detail="Extension not found")
    
    if not manager.enable(ext_id):
        raise HTTPException(status_code=500, detail="Failed to enable extension")
    
    return {"status": "enabled", "ext_id": ext_id}


@router.post("/{ext_id}/disable")
async def disable_extension(ext_id: str):
    """Disable extension."""
    manager = get_manager()
    
    if not manager.exists(ext_id):
        raise HTTPException(status_code=404, detail="Extension not found")
    
    if not manager.disable(ext_id):
        raise HTTPException(status_code=500, detail="Failed to disable extension")
    
    return {"status": "disabled", "ext_id": ext_id}


@router.put("/{ext_id}/config")
async def update_config(ext_id: str, config: Dict[str, Any]):
    """Update extension configuration."""
    manager = get_manager()
    
    if not manager.exists(ext_id):
        raise HTTPException(status_code=404, detail="Extension not found")
    
    if not manager.update_config(ext_id, config):
        raise HTTPException(status_code=500, detail="Failed to update configuration")
    
    return {"status": "updated", "ext_id": ext_id, "config": config}


@router.get("/{ext_id}/config", response_model=Dict[str, Any])
async def get_config(ext_id: str) -> Dict[str, Any]:
    """Get extension configuration."""
    manager = get_manager()
    
    if not manager.exists(ext_id):
        raise HTTPException(status_code=404, detail="Extension not found")
    
    return manager.get_config(ext_id)


@router.get("/task-status/{ext_id}", response_model=TaskStatusResponse)
async def get_task_status(ext_id: str) -> TaskStatusResponse:
    """Get installation task status."""
    status = install_tasks.get(ext_id)
    
    if not status:
        # Check if extension exists (task completed and was cleaned)
        manager = get_manager()
        if manager.exists(ext_id):
            return TaskStatusResponse(
                status="success",
                detail="Extension installed",
                progress=100,
                timestamp=time.time()
            )
        return TaskStatusResponse(
            status="unknown",
            detail="No such task",
            timestamp=time.time()
        )
    
    return TaskStatusResponse(**status)


@router.get("/remote-list", response_model=RemotePluginList)
async def remote_plugin_list() -> RemotePluginList:
    """Get list of available remote plugins."""
    import httpx
    from urllib.parse import urlparse
    
    github_raw = "https://raw.githubusercontent.com/super-agent-party/super-agent-party.github.io/main/plugins.json"
    gitee_raw = "https://gitee.com/super-agent-party/super-agent-party.github.io/raw/main/plugins.json"
    
    remote = None
    for url in (github_raw, gitee_raw):
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(url)
                r.raise_for_status()
                remote = r.json()
                break
        except Exception:
            if url == gitee_raw:
                raise HTTPException(status_code=502, detail="Failed to fetch remote plugin list")
            continue
    
    # Get installed repos
    manager = get_manager()
    installed_extensions = manager.list_all()
    installed_repos = {
        ext.repository.strip().rstrip("/").lower()
        for ext in installed_extensions
        if ext.repository
    }
    
    def _with_status(p: dict) -> RemotePluginItem:
        repo = p.get("repository", "").strip().rstrip("/").lower()
        parse = urlparse(p.get("repository", ""))
        path_parts = parse.path.strip("/").split("/")
        ext_id = f"{path_parts[0]}_{path_parts[1]}" if len(path_parts) >= 2 else p.get("id", "")
        
        return RemotePluginItem(
            id=ext_id,
            name=p.get("name", "Unnamed"),
            description=p.get("description", ""),
            author=p.get("author", "Unknown"),
            version=p.get("version", "1.0.0"),
            category=p.get("category", "Unknown"),
            repository=p.get("repository", ""),
            backupRepository=p.get("backupRepository", ""),
            installed=repo in installed_repos,
        )
    
    return RemotePluginList(plugins=[_with_status(p) for p in remote])
