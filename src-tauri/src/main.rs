// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::{Child, Command, Stdio};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::Duration;
use tauri::{Manager, WebviewWindow};

// Check if the backend is ready
async fn is_backend_ready() -> bool {
    match reqwest::get("http://127.0.0.1:8000/docs").await {
        Ok(response) => response.status().is_success(),
        Err(_) => false,
    }
}

// Check if the frontend is ready
async fn is_frontend_ready() -> bool {
    match reqwest::get("http://127.0.0.1:3000").await {
        Ok(response) => response.status().is_success(),
        Err(_) => false,
    }
}

// Start the Python backend server
fn start_backend() -> std::io::Result<Child> {
    println!("Starting Python backend...");
    
    // Prefer project venv if present
    let venv_python = "../backend/venv/bin/python";
    if std::path::Path::new(venv_python).exists() {
        match Command::new(venv_python)
            .arg("-m")
            .arg("uvicorn")
            .arg("app.main_complete:app")
            .arg("--host")
            .arg("127.0.0.1")
            .arg("--port")
            .arg("8000")
            .current_dir("../backend")
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
        {
            Ok(child) => {
                println!("Backend started with project venv python");
                return Ok(child);
            }
            Err(e) => {
                println!("Failed to start backend with venv python: {}", e);
            }
        }
    }

    // Try different Python commands
    let python_commands = ["python3", "python", "py"];
    
    for &python_cmd in &python_commands {
        match Command::new(python_cmd)
            .arg("-m")
            .arg("uvicorn")
            .arg("app.main_complete:app")
            .arg("--host")
            .arg("127.0.0.1")
            .arg("--port")
            .arg("8000")
            .current_dir("../backend")
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
        {
            Ok(child) => {
                println!("Backend started with {}", python_cmd);
                return Ok(child);
            }
            Err(e) => {
                println!("Failed to start backend with {}: {}", python_cmd, e);
                continue;
            }
        }
    }
    
    Err(std::io::Error::new(
        std::io::ErrorKind::NotFound,
        "Could not start Python backend - Python not found"
    ))
}

// Start the React frontend dev server
fn start_frontend() -> std::io::Result<Child> {
    println!("Starting React frontend dev server...");

    // Try npm, yarn, pnpm, bun
    let commands: Vec<(&str, Vec<&str>)> = vec![
        ("npm", vec!["run", "start"]),
        ("yarn", vec!["start"]),
        ("pnpm", vec!["start"]),
        ("bun", vec!["run", "start"]),
    ];

    for (cmd, args) in commands {
        let mut command = Command::new(cmd);
        for a in &args { command.arg(a); }
        let spawned = command
            .current_dir("../frontend")
            .env("BROWSER", "none") // prevent CRA from opening external browser
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn();
        match spawned {
            Ok(child) => {
                println!("Frontend started with {} {}", cmd, args.join(" "));
                return Ok(child);
            }
            Err(e) => {
                println!("Failed to start frontend with {}: {}", cmd, e);
                continue;
            }
        }
    }

    Err(std::io::Error::new(
        std::io::ErrorKind::NotFound,
        "Could not start React frontend - node package manager not found",
    ))
}

struct AppState {
    backend: Option<Child>,
    frontend: Option<Child>,
}

// Wait for both services to be ready
async fn wait_for_services(window: WebviewWindow) {
    let mut attempts = 0;
    let max_attempts = 60; // 60 seconds max
    
    while attempts < max_attempts {
        let backend_ready = is_backend_ready().await;
        let frontend_ready = is_frontend_ready().await;
        
        if backend_ready && frontend_ready {
            println!("Both backend and frontend are ready!");
            
            // Load the frontend
            let _ = window.navigate("http://127.0.0.1:3000".parse().unwrap());
            return;
        }
        
        // Update loading message
        let status = if backend_ready && !frontend_ready {
            "Waiting for frontend..."
        } else if !backend_ready && frontend_ready {
            "Waiting for backend..."
        } else {
            "Starting services..."
        };
        
        let _ = window.eval(&format!(r#"
            document.querySelector('p').textContent = '{}';
        "#, status));
        
        tokio::time::sleep(Duration::from_secs(1)).await;
        attempts += 1;
        println!("Waiting for services... ({}/{}) - Backend: {}, Frontend: {}", 
                 attempts, max_attempts, backend_ready, frontend_ready);
    }
    
    println!("Services failed to start within 60 seconds");
    // Show error message in the window
    let _ = window.eval(r#"
        document.body.innerHTML = `
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; font-family: Arial, sans-serif;">
                <h1 style="color: #f44336;">⚠️ Services Not Available</h1>
                <p>Please make sure both backend and frontend are running:</p>
                <p>Backend: <code>cd backend && python -m uvicorn app.main_complete:app --host 127.0.0.1 --port 8000</code></p>
                <p>Frontend: <code>cd frontend && npm start</code></p>
                <button onclick="location.reload()" style="margin-top: 20px; padding: 10px 20px; font-size: 16px; cursor: pointer;">
                    Try Again
                </button>
            </div>
        `;
    "#);
}

#[tauri::command]
async fn check_backend_status() -> Result<bool, String> {
    Ok(is_backend_ready().await)
}

#[tauri::command]
async fn check_frontend_status() -> Result<bool, String> {
    Ok(is_frontend_ready().await)
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![check_backend_status, check_frontend_status])
        .setup(|app| {
            let window = app.get_webview_window("main").unwrap();
            
            // Show loading screen initially
            let _ = window.eval(r#"
                document.body.innerHTML = `
                    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; font-family: Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                        <div style="text-align: center; color: white;">
                            <h1 style="margin-bottom: 20px;">🏥 Pharmacy Revenue Management</h1>
                            <div style="margin: 20px 0;">
                                <div style="border: 4px solid #f3f3f3; border-top: 4px solid #3498db; border-radius: 50%; width: 50px; height: 50px; animation: spin 1s linear infinite; margin: 0 auto;"></div>
                            </div>
                            <p>Starting application...</p>
                            <p style="font-size: 14px; opacity: 0.8;">Please wait while we initialize the system</p>
                        </div>
                        <style>
                            @keyframes spin {
                                0% { transform: rotate(0deg); }
                                100% { transform: rotate(360deg); }
                            }
                        </style>
                    </div>
                `;
            "#);
            
            // Prepare shared state for child process handles
            let state = Arc::new(Mutex::new(AppState { backend: None, frontend: None }));

            // Start backend
            {
                let state_clone = Arc::clone(&state);
                thread::spawn(move || {
                    match start_backend() {
                        Ok(child) => {
                            let mut s = state_clone.lock().unwrap();
                            s.backend = Some(child);
                        }
                        Err(e) => eprintln!("Failed to start backend: {}", e),
                    }
                });
            }

            // Start frontend
            {
                let state_clone = Arc::clone(&state);
                thread::spawn(move || {
                    match start_frontend() {
                        Ok(child) => {
                            let mut s = state_clone.lock().unwrap();
                            s.frontend = Some(child);
                        }
                        Err(e) => eprintln!("Failed to start frontend: {}", e),
                    }
                });
            }
            
            // Wait for both services to be ready
            let window_clone = window.clone();
            tauri::async_runtime::spawn(async move {
                wait_for_services(window_clone).await;
            });
            
            // Ensure child processes are terminated when app exits
            let app_handle = app.handle();
            let state_for_cleanup = Arc::clone(&state);
            app_handle.once_global("tauri://close-requested", move |_| {
                let mut s = state_for_cleanup.lock().unwrap();
                if let Some(child) = s.backend.as_mut() {
                    let _ = child.kill();
                }
                if let Some(child) = s.frontend.as_mut() {
                    let _ = child.kill();
                }
            });
            
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}