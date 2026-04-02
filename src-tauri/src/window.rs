//! Window management for Tauri windows

use tauri::{AppHandle, Manager, WebviewWindowBuilder, WebviewUrl};

#[tauri::command]
pub async fn create_vrm_window(app: AppHandle) -> Result<(), String> {
    let _vrm_window = WebviewWindowBuilder::new(
        &app,
        "vrm",
        WebviewUrl::App("vrm".into()),
    )
    .title("VRM Avatar")
    .inner_size(800.0, 600.0)
    .min_inner_size(400.0, 300.0)
    .resizable(true)
    .build()
    .map_err(|e| format!("Failed to create VRM window: {}", e))?;

    Ok(())
}

#[tauri::command]
pub async fn create_screenshot_overlay(app: AppHandle) -> Result<(), String> {
    let _overlay = WebviewWindowBuilder::new(
        &app,
        "screenshot-overlay",
        WebviewUrl::App("screenshot".into()),
    )
    .title("Screenshot Overlay")
    .inner_size(400.0, 300.0)
    .resizable(false)
    .always_on_top(true)
    .decorations(false)
    .skip_taskbar(true)
    .build()
    .map_err(|e| format!("Failed to create screenshot overlay: {}", e))?;

    Ok(())
}

#[tauri::command]
pub async fn close_window(app: AppHandle, label: String) -> Result<(), String> {
    if let Some(window) = app.get_webview_window(&label) {
        window.close().map_err(|e| format!("Failed to close window: {}", e))?;
    }
    Ok(())
}

#[tauri::command]
pub async fn toggle_fullscreen(app: AppHandle, label: String) -> Result<bool, String> {
    if let Some(window) = app.get_webview_window(&label) {
        let is_fullscreen = window.is_fullscreen().map_err(|e| e.to_string())?;
        window.set_fullscreen(!is_fullscreen).map_err(|e| e.to_string())?;
        Ok(!is_fullscreen)
    } else {
        Err("Window not found".to_string())
    }
}
