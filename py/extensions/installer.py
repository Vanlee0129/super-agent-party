"""Extension installer for downloading and installing extensions."""
import asyncio
import hashlib
import json
import os
import shutil
import stat
import tempfile
import time
import httpx
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from urllib.parse import urlparse

from py.get_setting import EXT_DIR


class ExtensionInstaller:
    """Handles installation of extensions from various sources."""
    
    def __init__(self, extensions_dir: str = None):
        self.extensions_dir = Path(extensions_dir or EXT_DIR)
        self._install_tasks: Dict[str, Dict[str, Any]] = {}
    
    def get_install_status(self, ext_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of an install task."""
        return self._install_tasks.get(ext_id)
    
    def _update_status(self, ext_id: str, status: str, detail: str, progress: int = 0):
        """Update installation task status."""
        self._install_tasks[ext_id] = {
            "status": status,
            "detail": detail,
            "progress": progress,
            "timestamp": time.time()
        }
    
    @staticmethod
    def _remove_readonly(func, path, exc_info):
        """Windows readonly file handler."""
        os.chmod(path, stat.S_IWRITE)
        func(path)
    
    @staticmethod
    def robust_rmtree(target: Path):
        """Safely remove directory tree."""
        if not target.exists():
            return
        
        if os.name == 'nt':
            for root, dirs, files in os.walk(target):
                for name in files:
                    try:
                        os.chmod(Path(root) / name, stat.S_IWRITE)
                    except Exception:
                        pass
                for name in dirs:
                    try:
                        os.chmod(Path(root) / name, stat.S_IWRITE)
                    except Exception:
                        pass
        
        kwargs = {"onexc": ExtensionInstaller._remove_readonly} if hasattr(shutil, "rmtree") else {}
        shutil.rmtree(target, **kwargs)
    
    @staticmethod
    def github_url_to_zip(url: str) -> str:
        """Convert GitHub/Gitee URL to ZIP download URL."""
        url = url.strip().rstrip('/').removesuffix('.git')
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        
        if len(path_parts) < 2:
            raise ValueError(f"Invalid repository URL: {url}")
        
        owner, repo = path_parts[0], path_parts[1]
        host = parsed.netloc.lower()
        
        if 'github.com' in host:
            return f"https://github.com/{owner}/{repo}/archive/refs/heads/main.zip"
        elif 'gitee.com' in host:
            return f"https://gitee.com/{owner}/{repo}/repository/archive/main.zip"
        else:
            return f"{url}/archive/refs/heads/main.zip"
    
    @staticmethod
    def get_ext_id_from_url(url: str) -> str:
        """Extract extension ID from repository URL."""
        parsed = urlparse(url.strip().rstrip('/'))
        path_parts = parsed.path.strip('/').split('/')
        if len(path_parts) < 2:
            raise ValueError("Invalid repository URL")
        return f"{path_parts[0]}_{path_parts[1]}"
    
    @staticmethod
    def find_root_dir(temp_path: Path) -> Path:
        """Find root directory if zip extracts to single subdirectory."""
        entries = [p for p in temp_path.iterdir() if p.is_dir()]
        entry_files = ['index.html', 'index.js', 'package.json', 'manifest.json']
        
        if len(entries) == 1:
            subdir = entries[0]
            if any((subdir / f).exists() for f in entry_files):
                return subdir
        
        return temp_path
    
    async def install_from_github(
        self,
        ext_id: str,
        repo_url: str,
        backup_url: str = None,
        progress_callback: Callable[[str, str, int], None] = None
    ) -> tuple[bool, str]:
        """
        Install extension from GitHub/Gitee repository.
        Returns (success, message).
        """
        target = self.extensions_dir / ext_id
        target.parent.mkdir(parents=True, exist_ok=True)
        
        if target.exists():
            return False, "Extension already exists"
        
        temp_dir = Path(tempfile.mkdtemp())
        urls = []
        
        try:
            main_url = repo_url.strip().rstrip('/') if repo_url else ""
            backup = backup_url.strip().rstrip('/') if backup_url else ""
            
            # Test connectivity and build URL list
            try:
                with httpx.Client(timeout=3) as c:
                    c.head("https://github.com")
                if main_url:
                    urls.append(self.github_url_to_zip(main_url))
                if backup:
                    urls.append(self.github_url_to_zip(backup))
            except Exception:
                if backup:
                    urls.append(self.github_url_to_zip(backup))
                if main_url:
                    urls.append(self.github_url_to_zip(main_url))
            
            if not urls:
                return False, "No valid repository URLs"
            
            last_error = None
            for i, zip_url in enumerate(urls):
                try:
                    await self._download_and_install(zip_url, temp_dir, target, ext_id)
                    return True, "Installation complete"
                except Exception as e:
                    last_error = e
                    continue
            
            return False, f"All sources failed: {last_error}"
        
        except Exception as e:
            self.robust_rmtree(target)
            return False, str(e)
        finally:
            self.robust_rmtree(temp_dir)
    
    async def _download_and_install(
        self,
        zip_url: str,
        temp_dir: Path,
        target: Path,
        ext_id: str
    ):
        """Download ZIP and install to target directory."""
        # Check if we can reuse node_modules
        old_pkg = target / "package.json"
        old_node_modules = target / "node_modules"
        can_reuse = False
        
        zip_path = temp_dir / "repo.zip"
        
        if old_pkg.exists() and old_node_modules.exists():
            try:
                async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
                    async with client.get(zip_url) as resp:
                        resp.raise_for_status()
                        with open(zip_path, "wb") as f:
                            async for chunk in resp.aiter_bytes():
                                f.write(chunk)
                
                temp_unpack = temp_dir / "preview"
                shutil.unpack_archive(zip_path, temp_unpack)
                new_root = self.find_root_dir(temp_unpack)
                new_pkg = new_root / "package.json"
                
                if new_pkg.exists():
                    can_reuse = self._should_reuse_node_modules(old_pkg, new_pkg)
                    self.robust_rmtree(temp_unpack)
            except Exception as e:
                can_reuse = False
        
        if not can_reuse:
            self.robust_rmtree(target)
        else:
            self.robust_rmtree(target, preserve={'node_modules'})
        
        # Download fresh if needed
        if not zip_path.exists():
            async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
                async with client.get(zip_url) as resp:
                    resp.raise_for_status()
                    with open(zip_path, "wb") as f:
                        async for chunk in resp.aiter_bytes():
                            f.write(chunk)
        
        # Extract
        unpack_dir = temp_dir / "unpacked"
        shutil.unpack_archive(zip_path, unpack_dir)
        new_root = self.find_root_dir(unpack_dir)
        
        if can_reuse:
            preserved_modules = target / "node_modules"
            temp_modules = temp_dir / "preserved_modules"
            if preserved_modules.exists():
                shutil.move(str(preserved_modules), str(temp_modules))
                self.robust_rmtree(target)
                shutil.move(str(new_root), str(target))
                target.mkdir(parents=True, exist_ok=True)
                shutil.move(str(temp_modules), str(preserved_modules))
            else:
                shutil.move(str(new_root), str(target))
        else:
            shutil.move(str(new_root), str(target))
    
    @staticmethod
    def _should_reuse_node_modules(old_pkg: Path, new_pkg: Path) -> bool:
        """Check if node_modules can be reused based on dependency changes."""
        try:
            with open(old_pkg, 'r', encoding='utf-8') as f:
                old_deps = json.load(f).get('dependencies', {})
            with open(new_pkg, 'r', encoding='utf-8') as f:
                new_deps = json.load(f).get('dependencies', {})
            return old_deps == new_deps
        except Exception:
            return False
    
    async def install_from_zip(
        self,
        ext_id: str,
        zip_content: bytes,
        filename: str = "extension.zip"
    ) -> tuple[bool, str]:
        """
        Install extension from uploaded ZIP content.
        Returns (success, message).
        """
        target = self.extensions_dir / ext_id
        
        if target.exists():
            return False, "Extension already exists"
        
        temp_dir = Path(tempfile.mkdtemp())
        
        try:
            # Save ZIP
            zip_path = temp_dir / filename
            with open(zip_path, "wb") as f:
                f.write(zip_content)
            
            # Extract
            unpack_dir = temp_dir / "unpacked"
            shutil.unpack_archive(zip_path, unpack_dir)
            real_root = self.find_root_dir(unpack_dir)
            
            # Validate structure
            if not any((real_root / f).exists() for f in ['index.html', 'index.js', 'package.json']):
                return False, "ZIP content is not a valid extension"
            
            # Install
            target.mkdir(parents=True, exist_ok=True)
            for item in real_root.iterdir():
                shutil.move(str(item), str(target))
            
            return True, "Installation complete"
        
        except Exception as e:
            self.robust_rmtree(target)
            return False, str(e)
        finally:
            self.robust_rmtree(temp_dir)
