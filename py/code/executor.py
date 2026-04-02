"""Code execution engine."""
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Optional

import httpx

from py.code.sandbox import SandboxManager, SandboxType
from py.code.languages import Languages


@dataclass
class ExecutionResult:
    """Result of code execution."""
    stdout: str
    stderr: str
    exit_code: int
    execution_time: float
    error: Optional[str] = None


class CodeExecutor:
    """Executes code in configured sandbox."""
    
    _instance: Optional["CodeExecutor"] = None
    
    def __init__(self):
        self._sandbox_manager = SandboxManager.get_instance()
        self._executor = ThreadPoolExecutor(max_workers=4)
    
    @classmethod
    def get_instance(cls) -> "CodeExecutor":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = CodeExecutor()
        return cls._instance
    
    async def execute(
        self,
        code: str,
        language: str,
        sandbox: SandboxType = None,
        timeout: int = 30000
    ) -> ExecutionResult:
        """
        Execute code in the specified sandbox.
        
        Args:
            code: Source code to execute
            language: Programming language
            sandbox: Sandbox type (uses configured default if not specified)
            timeout: Timeout in milliseconds
        
        Returns:
            ExecutionResult with stdout, stderr, exit_code, execution_time
        """
        if sandbox is None:
            sandbox = self._sandbox_manager.current_type
        
        if sandbox == SandboxType.E2B:
            return await self._execute_e2b(code, language, timeout)
        else:
            return await self._execute_local(code, language, timeout)
    
    async def _execute_e2b(
        self,
        code: str,
        language: str,
        timeout: int
    ) -> ExecutionResult:
        """Execute code using E2B sandbox."""
        start_time = time.time()
        
        api_key = self._sandbox_manager.e2b_api_key
        if not api_key:
            return ExecutionResult(
                stdout="",
                stderr="",
                exit_code=1,
                execution_time=0,
                error="E2B API key not configured"
            )
        
        e2b_language = Languages.get_e2b_name(language)
        
        try:
            # Import here to avoid import errors if e2b not installed
            from e2b_code_interpreter import Sandbox
            
            loop = asyncio.get_event_loop()
            
            def run_in_sandbox():
                try:
                    with Sandbox(api_key=api_key, timeout_ms=timeout) as sandbox:
                        execution = sandbox.run_code(code, language=e2b_language)
                        logs = execution.logs
                        
                        stdout = ""
                        stderr = ""
                        
                        if logs:
                            for log in logs:
                                if hasattr(log, 'line'):
                                    if log.type == 'stdout':
                                        stdout += log.line + "\n"
                                    else:
                                        stderr += log.line + "\n"
                                elif isinstance(log, dict):
                                    stdout += log.get('line', '') + "\n"
                        
                        return ExecutionResult(
                            stdout=stdout.strip(),
                            stderr=stderr.strip(),
                            exit_code=0 if not execution.error else 1,
                            execution_time=time.time() - start_time,
                            error=str(execution.error) if execution.error else None
                        )
                except Exception as e:
                    return ExecutionResult(
                        stdout="",
                        stderr="",
                        exit_code=1,
                        execution_time=time.time() - start_time,
                        error=str(e)
                    )
            
            result = await loop.run_in_executor(self._executor, run_in_sandbox)
            result.execution_time = time.time() - start_time
            return result
            
        except ImportError:
            return ExecutionResult(
                stdout="",
                stderr="",
                exit_code=1,
                execution_time=time.time() - start_time,
                error="e2b-code-interpreter package not installed"
            )
        except Exception as e:
            return ExecutionResult(
                stdout="",
                stderr="",
                exit_code=1,
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    async def _execute_local(
        self,
        code: str,
        language: str,
        timeout: int
    ) -> ExecutionResult:
        """Execute code using local node_runner sandbox."""
        start_time = time.time()
        
        endpoint = self._sandbox_manager.local_endpoint
        url = f"{endpoint.strip('/')}/run_code"
        
        payload = {
            "code": code,
            "language": language,
            "timeout": timeout
        }
        
        try:
            async with httpx.AsyncClient(timeout=timeout / 1000.0) as client:
                response = await client.post(url, json=payload)
                
                if response.status_code == 200:
                    result = response.json()
                    return ExecutionResult(
                        stdout=result.get("stdout", ""),
                        stderr=result.get("stderr", ""),
                        exit_code=result.get("exit_code", 0),
                        execution_time=time.time() - start_time,
                        error=result.get("error")
                    )
                else:
                    return ExecutionResult(
                        stdout="",
                        stderr=f"HTTP {response.status_code}: {response.text}",
                        exit_code=1,
                        execution_time=time.time() - start_time,
                        error=f"Request failed with status {response.status_code}"
                    )
                    
        except httpx.ConnectError:
            return ExecutionResult(
                stdout="",
                stderr="",
                exit_code=1,
                execution_time=time.time() - start_time,
                error=f"Could not connect to local sandbox at {endpoint}. Is node_runner running?"
            )
        except Exception as e:
            return ExecutionResult(
                stdout="",
                stderr="",
                exit_code=1,
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    async def execute_with_fallback(
        self,
        code: str,
        language: str,
        timeout: int = 30000
    ) -> ExecutionResult:
        """
        Execute code with automatic fallback between sandboxes.
        Tries E2B first if configured, falls back to local.
        """
        result = await self.execute(
            code, language, 
            sandbox=SandboxType.E2B, 
            timeout=timeout
        )
        
        if "not configured" in (result.error or "").lower() or \
           "not installed" in (result.error or "").lower():
            # Try local sandbox
            result = await self.execute(
                code, language,
                sandbox=SandboxType.LOCAL,
                timeout=timeout
            )
        
        return result
