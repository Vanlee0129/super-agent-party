//! Super Agent Party - Tauri 2.x Desktop Application

mod backend;
mod commands;
mod window;

use backend::BackendManager;
use std::sync::Arc;
use tauri::Manager;

#[cfg(debug_assertions)]
fn setup_devtools(app: &tauri::App) {
    if let Some(window) = app.get_webview_window("main") {
        let _ = window.open_devtools();
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    // Create backend manager
    let backend_manager = Arc::new(BackendManager::new());

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_http::init())
        .plugin(tauri_plugin_process::init())
        .plugin(tauri_plugin_os::init())
        .plugin(
            tauri_plugin_log::Builder::new()
                .target(tauri_plugin_log::Target::new(
                    tauri_plugin_log::TargetKind::Stdout,
                ))
                .target(tauri_plugin_log::Target::new(
                    tauri_plugin_log::TargetKind::LogDir {
                        file_name: Some("super-agent-party".to_string()),
                    },
                ))
                .build(),
        )
        .manage(backend_manager)
        .setup(|app| {
            #[cfg(debug_assertions)]
            setup_devtools(app);

            log::info!("Super Agent Party starting...");

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            commands::start_backend,
            commands::stop_backend,
            commands::get_backend_status,
            window::create_vrm_window,
            window::create_screenshot_overlay,
            window::close_window,
            window::toggle_fullscreen,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
