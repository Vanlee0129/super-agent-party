//! Tauri commands - IPC bridge between frontend and backend

use crate::backend::{BackendManager, BackendStatus, StartBackendResult};
use std::sync::Arc;
use tauri::State;

pub type BackendState = Arc<BackendManager>;

#[tauri::command]
pub async fn start_backend(
    app: tauri::AppHandle,
    backend: State<'_, BackendState>,
) -> Result<StartBackendResult, String> {
    backend.start(app).await
}

#[tauri::command]
pub async fn stop_backend(backend: State<'_, BackendState>) -> Result<(), String> {
    backend.stop().await
}

#[tauri::command]
pub async fn get_backend_status(
    backend: State<'_, BackendState>,
) -> Result<BackendStatus, String> {
    Ok(backend.get_status().await)
}
