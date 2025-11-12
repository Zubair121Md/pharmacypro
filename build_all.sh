#!/bin/bash
# Build script for cross-platform distribution

echo "🏥 Building Pharmacy Revenue Management for all platforms..."

# Create dist directory
mkdir -p dist

# Build for macOS (current platform)
echo "📱 Building for macOS..."
npm run tauri:build

# Copy macOS app
cp -r "src-tauri/target/release/bundle/macos/Pharmacy Revenue Management.app" dist/
cp "src-tauri/target/release/bundle/dmg/Pharmacy Revenue Management_1.0.0_aarch64.dmg" dist/

# Build for Windows (if possible)
echo "🪟 Attempting Windows build..."
if command -v x86_64-pc-windows-msvc-gcc &> /dev/null; then
    npm run tauri:build -- --target x86_64-pc-windows-msvc
    if [ -d "src-tauri/target/release/bundle/msi" ]; then
        cp "src-tauri/target/release/bundle/msi/Pharmacy Revenue Management_1.0.0_x64_en-US.msi" dist/
    fi
else
    echo "⚠️  Windows build tools not available. Skipping Windows build."
fi

# Build for Linux (if possible)
echo "🐧 Attempting Linux build..."
if command -v x86_64-unknown-linux-gnu-gcc &> /dev/null; then
    npm run tauri:build -- --target x86_64-unknown-linux-gnu
    if [ -d "src-tauri/target/release/bundle/appimage" ]; then
        cp "src-tauri/target/release/bundle/appimage/Pharmacy Revenue Management_1.0.0_amd64.AppImage" dist/
    fi
else
    echo "⚠️  Linux build tools not available. Skipping Linux build."
fi

# Create README
cat > dist/README.txt << 'EOF'
Pharmacy Revenue Management System v1.0.0
=========================================

INSTALLATION INSTRUCTIONS:

macOS:
1. Double-click "Pharmacy Revenue Management.app"
2. If you see a security warning, right-click → Open
3. Click "Open" in the security dialog

Windows:
1. Double-click "Pharmacy Revenue Management_1.0.0_x64_en-US.msi"
2. Follow the installation wizard
3. Launch from Start Menu or Desktop

Linux:
1. Make the AppImage executable: chmod +x "Pharmacy Revenue Management_1.0.0_amd64.AppImage"
2. Double-click to run

SYSTEM REQUIREMENTS:
- macOS: 10.15+ (Catalina or later)
- Windows: 10 or later
- Linux: Ubuntu 18.04+ or equivalent
- RAM: 4GB minimum, 8GB recommended

TROUBLESHOOTING:
- If the app crashes, make sure Python 3.8+ is installed
- For Windows: Install Visual C++ Redistributable
- For Linux: Install libgtk-3-dev and libwebkit2gtk-4.0-dev

SUPPORT:
Contact [your-email] for technical support
EOF

echo "✅ Distribution package created in 'dist' folder"
echo "📁 Contents:"
ls -la dist/
