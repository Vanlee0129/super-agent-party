//! Backend process management - starts and manages the Python FastAPI backend

use serde::{Deserialize, Serialize};
use std::process::Stdio;
use std::sync::Arc;
use tauri::{Emitter, Manager};
use tokio::io::{AsyncBufReadExt, BufReader};
use tokio::process::Command;
use tokio::sync::Mutex;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BackendStatus {
    pub running: bool,
    pub port: Option<u16>,
    pub pid: Option<u32>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StartBackendResult {
    pub success: bool,
    pub port: u16,
    pub pid: u32,
    pub message: String,
}

pub struct BackendManager {
    process: Arc<Mutex<Option<tokio::process::Child>>>,
    port: Arc<Mutex<Option<u16>>>,
}

impl BackendManager {
    pub fn new() -> Self {
        Self {
            process: Arc::new(Mutex::new(None)),
            port: Arc::new(Mutex::new(None)),
        }
    }

    pub async fn start(&self, app_handle: tauri::AppHandle) -> Result<StartBackendResult, String> {
        // Check if already running
        {
            let process_guard = self.process.lock().await;
            if process_guard.is_some() {
                let port_guard = self.port.lock().await;
                let port = port_guard.unwrap_or(3456);
                return Ok(StartBackendResult {
                    success: true,
                    port,
                    pid: 0,
                    message: "Backend already running".to_string(),
                });
            }
        }

        // Find Python executable
        let python_cmd = if cfg!(target_os = "windows") {
            "python"
        } else {
            "python3"
        };

        // Get the app root directory
        let app_root = app_handle
            .path()
            .app_data_dir()
            .map_err(|e| format!("Failed to get app data dir: {}", e))?;

        // Start the backend server
        let mut child = Command::new(python_cmd)
            .args(["-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "3456"])
            .current_dir(&app_root)
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .map_err(|e| format!("Failed to start backend: {}", e))?;

        let stdout = child.stdout.take().expect("Failed to capture stdout");
        let stderr = child.stderr.take().expect("Failed to capture stderr");

        // Store the process
        {
            let mut process_guard = self.process.lock().await;
            *process_guard = Some(child);
        }
        {
            let mut port_guard = self.port.lock().await;
            *port_guard = Some(3456);
        }

        // Log output in background
        let log_handle = app_handle.clone();
        tokio::spawn(async move {
            let mut stdout_reader = BufReader::new(stdout).lines();
            let mut stderr_reader = BufReader::new(stderr).lines();

            loop {
                tokio::select! {
                    line = stdout_reader.next_line() => {
                        match line {
                            Ok(Some(l)) => {
                                let _ = log_handle.emit("backend-log", format!("[server] {}", l));
                            }
                            Ok(None) => break,
                            Err(e) => {
                                let _ = log_handle.emit("backend-log", format!("[error] stdout: {}", e));
                                break;
                            }
                        }
                    }
                    line = stderr_reader.next_line() => {
                        match line {
                            Ok(Some(l)) => {
                                let _ = log_handle.emit("backend-log", format!("[server:err] {}", l));
                            }
                            Ok(None) => break,
                            Err(e) => {
                                let _ = log_handle.emit("backend-log", format!("[error] stderr: {}", e));
                                break;
                            }
                        }
                    }
                }
            }
        });

        Ok(StartBackendResult {
            success: true,
            port: 3456,
            pid: 0,
            message: "Backend started successfully".to_string(),
        })
    }

    pub async fn stop(&self) -> Result<(), String> {
        let mut process_guard = self.process.lock().await;
        if let Some(mut child) = process_guard.take() {
            child.kill().await.map_err(|e| format!("Failed to stop backend: {}", e))?;
        }
        let mut port_guard = self.port.lock().await;
        *port_guard = None;
        Ok(())
    }

    pub async fn get_status(&self) -> BackendStatus {
        let process_guard = self.process.lock().await;
        let port_guard = self.port.lock().await;

        BackendStatus {
            running: process_guard.is_some(),
            port: *port_guard,
            pid: None,
        }
    }
}

impl Default for BackendManager {
    fn default() -> Self {
        Self::new()
    }
}
