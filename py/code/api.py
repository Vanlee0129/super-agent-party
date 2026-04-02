"""Code execution API - FastAPI routes for code execution."""
from typing import List, Dict, Any, Optional
from enum import Enum

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from py.code.executor import CodeExecutor, ExecutionResult
from py.code.sandbox import SandboxManager, SandboxConfig, SandboxType
from py.code.languages import Languages


router = APIRouter(prefix="/api/v1/code", tags=["code"])


# ==================== Request/Response Models ====================

class SandboxTypeModel(str, Enum):
    """Sandbox type enumeration."""
    E2B = "e2b"
    LOCAL = "local"


class ExecutionRequest(BaseModel):
    """Code execution request."""
    code: str
    language: str
    sandbox: SandboxTypeModel = SandboxTypeModel.LOCAL
    timeout: int = 30000  # milliseconds


class ExecutionResponse(BaseModel):
    """Code execution response."""
    stdout: str
    stderr: str
    exit_code: int
    execution_time: float
    error: Optional[str] = None


class SandboxConfigRequest(BaseModel):
    """Sandbox configuration request."""
    type: SandboxTypeModel
    api_key: Optional[str] = None
    local_endpoint: str = "http://localhost:3001"


class SandboxStatusResponse(BaseModel):
    """Sandbox status response."""
    e2b: Dict[str, Any]
    local: Dict[str, Any]
    current_type: str
    configured: Dict[str, bool]


# ==================== Module-level Instances ====================

_executor: Optional[CodeExecutor] = None


def get_executor() -> CodeExecutor:
    """Get or create code executor instance."""
    global _executor
    if _executor is None:
        _executor = CodeExecutor.get_instance()
    return _executor


def get_sandbox_manager() -> SandboxManager:
    """Get sandbox manager instance."""
    return SandboxManager.get_instance()


# ==================== API Routes ====================

@router.post("/execute", response_model=ExecutionResponse)
async def execute_code(request: ExecutionRequest) -> ExecutionResponse:
    """
    Execute code in the specified sandbox.
    
    Supports:
    - E2B cloud sandbox (requires API key configuration)
    - Local node_runner sandbox (default, localhost:3001)
    """
    executor = get_executor()
    
    result = await executor.execute(
        code=request.code,
        language=request.language,
        sandbox=SandboxType(request.sandbox.value),
        timeout=request.timeout
    )
    
    return ExecutionResponse(
        stdout=result.stdout,
        stderr=result.stderr,
        exit_code=result.exit_code,
        execution_time=result.execution_time,
        error=result.error
    )


@router.get("/languages", response_model=List[str])
async def list_supported_languages() -> List[str]:
    """List all supported programming languages."""
    return Languages.list_all()


@router.get("/languages/local", response_model=List[str])
async def list_local_languages() -> List[str]:
    """List languages supported by local sandbox."""
    return Languages.list_local_supported()


@router.get("/languages/e2b", response_model=List[str])
async def list_e2b_languages() -> List[str]:
    """List languages supported by E2B sandbox."""
    return Languages.list_e2b_supported()


@router.get("/sandbox/status", response_model=SandboxStatusResponse)
async def sandbox_status() -> SandboxStatusResponse:
    """Check sandbox availability and status."""
    manager = get_sandbox_manager()
    status = await manager.get_status()
    
    return SandboxStatusResponse(
        e2b=status["e2b"],
        local=status["local"],
        current_type=status["current_type"],
        configured=status["configured"]
    )


@router.post("/sandbox/config")
async def configure_sandbox(config: SandboxConfigRequest) -> SandboxConfig:
    """Configure sandbox settings."""
    manager = get_sandbox_manager()
    
    sandbox_config = SandboxConfig(
        type=SandboxType(config.type.value),
        api_key=config.api_key,
        local_endpoint=config.local_endpoint
    )
    
    manager.update_config(sandbox_config)
    
    return sandbox_config


@router.get("/sandbox/config", response_model=SandboxConfigRequest)
async def get_sandbox_config() -> SandboxConfigRequest:
    """Get current sandbox configuration."""
    manager = get_sandbox_manager()
    config = manager.get_config()
    
    return SandboxConfigRequest(
        type=SandboxTypeModel(config.type.value),
        api_key=config.api_key,
        local_endpoint=config.local_endpoint
    )


@router.post("/sandbox/test")
async def test_sandbox_connection(sandbox_type: SandboxTypeModel = SandboxTypeModel.LOCAL) -> Dict[str, Any]:
    """Test connection to a specific sandbox."""
    manager = get_sandbox_manager()
    
    if sandbox_type == SandboxTypeModel.E2B:
        status = await manager.check_e2b_status()
    else:
        status = await manager.check_local_status()
    
    return {
        "sandbox": sandbox_type.value,
        "status": status
    }
