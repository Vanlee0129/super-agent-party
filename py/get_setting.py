"""
Backward-compatibility shim: re-export everything from py.core.config,
plus preserve legacy utility functions that haven't been migrated yet.

All new code should import from py.core.config directly.
"""
import io
import json
import logging
import os
import sys
import time
import asyncio
from pathlib import Path
from typing import Any, Dict, Optional

import aiosqlite
from appdirs import user_data_dir

# ---- Import everything from py.core.config for re-export ----
from py.core.config import (
    APP_NAME,
    IS_DOCKER,
    HOST,
    PORT,
    get_base_path,
    base_path,
    USER_DATA_DIR,
    DATABASE_PATH,
    COVS_PATH,
    MEMORY_CACHE_DIR,
    UPLOAD_FILES_DIR,
    AGENT_DIR,
    KB_DIR,
    DEFAULT_VRM_DIR,
    SKILLS_DIR,
    get_global_skills_dir,
    Config,
    config,
    EXTENSIONS_DIR as _EXT_DIR,
)

# Alias for backward compat (some code used EXTENSIONS_DIR)
EXTENSIONS_DIR = _EXT_DIR
# Alias so code importing EXT_DIR still works
EXT_DIR = _EXT_DIR

# Legacy path definitions not in config.py
LOG_DIR = os.path.join(USER_DATA_DIR, 'logs')
TOOL_TEMP_DIR = os.path.join(USER_DATA_DIR, 'tool_temp')
DEFAULT_ASR_DIR = os.path.join(USER_DATA_DIR, 'asr')
DEFAULT_EBD_DIR = os.path.join(USER_DATA_DIR, 'ebd')

# Blocklist for URL/IP blocking (loaded at startup in server.py)
BLOCKLIST = set()

# ---- Additional utilities from the legacy get_setting.py ----

def in_docker():
    return IS_DOCKER

def configure_host_port(host, port):
    global HOST, PORT
    HOST = host
    PORT = port

def get_host():
    return HOST or "127.0.0.1"

def get_port():
    return PORT or 3456

# Legacy settings template path (used by settings/manager.py)
SETTINGS_TEMPLATE_FILE = os.path.join(get_base_path(), 'config', 'settings_template.json')

def get_default_settings_sync():
    """Load default settings from the settings template file."""
    if os.path.exists(SETTINGS_TEMPLATE_FILE):
        try:
            with open(SETTINGS_TEMPLATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}

# ---- Skills initialization ----

async def _copy_default_skills():
    """
    Copy default skills from project root to SKILLS_DIR.
    Skips skills that already exist in the destination.
    """
    src_skills_root = os.path.join(base_path, 'skills')
    dst_skills_root = SKILLS_DIR

    if not os.path.isdir(src_skills_root):
        logging.info("[Skills] No skills/ folder in project root, skipping init copy.")
        return

    os.makedirs(dst_skills_root, exist_ok=True)

    try:
        for item_name in os.listdir(src_skills_root):
            src_path = os.path.join(src_skills_root, item_name)
            dst_path = os.path.join(dst_skills_root, item_name)
            if os.path.isdir(src_path):
                if os.path.exists(dst_path):
                    logging.debug(f"[Skills] Skill already exists, skipping: {item_name}")
                    continue
                import shutil
                shutil.copytree(src_path, dst_path)
                logging.info(f"[Skills] Installed default skill: {item_name}")
    except Exception as e:
        logging.error(f"[Skills] Error copying default skills: {e}", exc_info=True)

# ---- Database init ----

_db_init_done = False
_covs_db_init_done = False

async def init_db():
    global _db_init_done
    if _db_init_done:
        return
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY,
                data TEXT NOT NULL
            )
        ''')
        await db.commit()
    _db_init_done = True

async def init_covs_db():
    global _covs_db_init_done
    if _covs_db_init_done:
        return
    Path(USER_DATA_DIR).mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(COVS_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY,
                data TEXT NOT NULL
            )
        ''')
        await db.commit()
    _covs_db_init_done = True

# ---- Utility functions ----

async def clean_temp_files_task():
    try:
        await asyncio.to_thread(_clean_temp_files_sync)
    except Exception:
        pass

def _clean_temp_files_sync():
    if not os.path.exists(TOOL_TEMP_DIR):
        return
    threshold = time.time() - 7 * 24 * 60 * 60
    for filename in os.listdir(TOOL_TEMP_DIR):
        file_path = os.path.join(TOOL_TEMP_DIR, filename)
        try:
            if os.path.isfile(file_path) and os.path.getmtime(file_path) < threshold:
                os.remove(file_path)
        except Exception:
            pass

def convert_to_opus_simple(audio_data):
    try:
        from pydub import AudioSegment
        import imageio_ffmpeg

        if not getattr(AudioSegment, 'converter_configured', False):
            try:
                ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
                AudioSegment.converter = ffmpeg_path
                AudioSegment.converter_configured = True
            except Exception:
                logging.warning("imageio-ffmpeg execution failed")

        audio = None
        try:
            audio_io = io.BytesIO(audio_data)
            audio = AudioSegment.from_file(audio_io)
        except Exception:
            pass

        if audio is None:
            try:
                audio = AudioSegment(
                    data=audio_data,
                    sample_width=2,
                    frame_rate=24000,
                    channels=1
                )
            except Exception as e:
                logging.error(f"Raw PCM read failed: {e}")
                return audio_data, False

        audio = audio.set_frame_rate(16000).set_channels(1)
        out_io = io.BytesIO()
        audio.export(
            out_io,
            format="opus",
            codec="libopus",
            parameters=["-b:a", "16k", "-application", "voip"]
        )
        return out_io.getvalue(), True
    except ImportError:
        logging.error("pydub/ffmpeg not installed")
        return _wrap_pcm_to_wav(audio_data), False
    except Exception as e:
        logging.error(f"Opus conversion failed: {e}")
        return _wrap_pcm_to_wav(audio_data), False

def _wrap_pcm_to_wav(pcm_data):
    try:
        import wave
        wav_io = io.BytesIO()
        with wave.open(wav_io, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(24000)
            wav_file.writeframes(pcm_data)
        return wav_io.getvalue()
    except Exception:
        return pcm_data

# ---- Settings load/save ----

async def load_settings():
    await init_db()
    defaults = get_default_settings_sync().copy()

    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('SELECT data FROM settings WHERE id = 1') as cursor:
            row = await cursor.fetchone()
            if row:
                try:
                    user_settings = json.loads(row[0])
                except Exception:
                    user_settings = {}

                def merge_defaults(default_dict, target_dict):
                    for key, value in default_dict.items():
                        if key not in target_dict:
                            target_dict[key] = value
                        elif isinstance(value, dict) and isinstance(target_dict.get(key), dict):
                            merge_defaults(value, target_dict[key])

                merge_defaults(defaults, user_settings)
                return user_settings
            else:
                if IS_DOCKER:
                    defaults["isdocker"] = True
                await save_settings(defaults)
                return defaults

async def save_settings(settings):
    data = json.dumps(settings, ensure_ascii=False, indent=2)
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('INSERT OR REPLACE INTO settings (id, data) VALUES (1, ?)', (data,))
        await db.commit()

async def load_covs():
    try:
        await init_covs_db()
        async with aiosqlite.connect(COVS_PATH) as db:
            async with db.execute('SELECT data FROM settings WHERE id = 1') as cursor:
                row = await cursor.fetchone()
                return json.loads(row[0]) if row else {"conversations": []}
    except Exception:
        return {"conversations": []}

async def save_covs(settings):
    data = json.dumps(settings, ensure_ascii=False, indent=2)
    async with aiosqlite.connect(COVS_PATH) as db:
        await db.execute('INSERT OR REPLACE INTO settings (id, data) VALUES (1, ?)', (data,))
        await db.commit()
