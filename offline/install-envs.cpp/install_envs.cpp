#include <windows.h>
#include <commctrl.h>
#include <shellapi.h>
#include <iostream>
#include <string>
#include <vector>
#include <filesystem>
#include <fstream>

#pragma comment(lib, "comctl32.lib")
#pragma comment(lib, "shell32.lib")

// Window and control IDs
#define IDC_CHECKBOX_AI_BACKEND 1001
#define IDC_CHECKBOX_COMFYUI 1002
#define IDC_CHECKBOX_OPENVINO 1003
#define IDC_CHECKBOX_LLAMACPP 1004
#define IDC_BUTTON_OK 1005
#define IDC_LABEL_MAIN 1006
#define IDC_LABEL_NOTE 1007
#define IDC_PROGRESSBAR 1008

// Custom Windows message for progress updates
#define WM_INSTALL_PROGRESS (WM_USER + 100)

// Global variables
HWND g_hWnd;
HWND g_hCheckboxAI, g_hCheckboxComfy, g_hCheckboxOpenVINO, g_hCheckboxLlama;
HWND g_hButtonOK, g_hLabelMain, g_hLabelNote, g_hProgressBar;
std::string g_installDir;
std::string g_scriptDir;
HFONT g_hFont = NULL;

// Progress tracking variables
volatile int g_currentProgress = 0;
volatile int g_realBProgress = 0;
volatile int g_realEProgress = 0;
volatile bool g_installationActive = false;
HANDLE g_progressThread = NULL;

// Function declarations
LRESULT CALLBACK WindowProc(HWND hwnd, UINT uMsg, WPARAM wParam, LPARAM lParam);
void CreateControls(HWND hwnd);
void CreateModernFont();
void OnOKButtonClick();
void ShowInstallProgress();
void ExecuteInstallation(const std::string& envs);
std::string GetExecutableDirectory();
std::string GetParentDirectory(const std::string& path);
DWORD WINAPI ProgressThread(LPVOID lpParam);
void StopProgressThread();

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow)
{    // Initialize common controls
    INITCOMMONCONTROLSEX icex;
    icex.dwSize = sizeof(INITCOMMONCONTROLSEX);
    icex.dwICC = ICC_WIN95_CLASSES | ICC_PROGRESS_CLASS;
    InitCommonControlsEx(&icex);

    // Get script directory and install directory
    g_scriptDir = GetExecutableDirectory();
    g_installDir = GetParentDirectory(g_scriptDir);
    
    // Parse command line arguments if provided
    if (strlen(lpCmdLine) > 0) {
        g_installDir = std::string(lpCmdLine);
    }
    
    std::cout << "Script Directory: " << g_scriptDir << std::endl;
    std::cout << "Install Directory: " << g_installDir << std::endl;    // Window class
    const char* CLASS_NAME = "InstallEnvsWindow";
    
    WNDCLASSA wc = {};
    wc.lpfnWndProc = WindowProc;
    wc.hInstance = hInstance;
    wc.lpszClassName = CLASS_NAME;
    wc.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);
    wc.hCursor = LoadCursor(NULL, IDC_ARROW);
    wc.hIcon = LoadIcon(NULL, IDI_APPLICATION);

    RegisterClassA(&wc);

    // Create modern font for better appearance
    CreateModernFont();

    // Create window
    g_hWnd = CreateWindowExA(
        0,
        CLASS_NAME,
        "Install Backends for AI Playground",
        WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU,
        CW_USEDEFAULT, CW_USEDEFAULT, 500, 260,
        NULL,
        NULL,
        hInstance,
        NULL
    );

    if (g_hWnd == NULL) {
        return 0;
    }

    // Center the window
    RECT rect;
    GetWindowRect(g_hWnd, &rect);
    int screenWidth = GetSystemMetrics(SM_CXSCREEN);
    int screenHeight = GetSystemMetrics(SM_CYSCREEN);
    int windowWidth = rect.right - rect.left;
    int windowHeight = rect.bottom - rect.top;
    SetWindowPos(g_hWnd, NULL, 
        (screenWidth - windowWidth) / 2, 
        (screenHeight - windowHeight) / 2, 
        0, 0, SWP_NOSIZE);    
    ShowWindow(g_hWnd, nCmdShow);
    UpdateWindow(g_hWnd);
    
    // Message loop
    MSG msg = {};
    while (GetMessage(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }

    return 0;
}

LRESULT CALLBACK WindowProc(HWND hwnd, UINT uMsg, WPARAM wParam, LPARAM lParam)
{
    switch (uMsg) {
    case WM_CREATE:
        CreateControls(hwnd);
        break;

    case WM_COMMAND:
        if (LOWORD(wParam) == IDC_BUTTON_OK && HIWORD(wParam) == BN_CLICKED) {
            OnOKButtonClick();
        }
        break;    
    case WM_INSTALL_PROGRESS:
        // Update progress bar with the value from wParam (0-100)
        if (g_hProgressBar) {
            int beginValue = (int)wParam;
            int endValue = (int)lParam;

            if(endValue == 2000) 
            {
                // Installation complete - stop progress thread and close window
                g_installationActive = false;
                StopProgressThread();
                DestroyWindow(hwnd);
            }
            else 
            {
                // Update real progress from PowerShell script
                g_realBProgress = beginValue;
                g_realEProgress = endValue;
                g_currentProgress = beginValue;

                // char progressText[256];
                // sprintf(progressText, "Installing backends...: %d%%", progressValue);
                // PostMessage(g_hProgressBar, PBM_SETPOS, (WPARAM)progressValue, 0);
                // SetWindowTextA(g_hLabelMain, (LPCSTR)progressText);
            }
        }
        
        break;    
    case WM_CLOSE:
        g_installationActive = false;
        StopProgressThread();
        DestroyWindow(hwnd);
        break;    case WM_DESTROY:
        g_installationActive = false;
        StopProgressThread();
        
        // Clean up font resource
        if (g_hFont && g_hFont != (HFONT)GetStockObject(DEFAULT_GUI_FONT)) {
            DeleteObject(g_hFont);
            g_hFont = NULL;
        }
        
        PostQuitMessage(0);
        break;

    default:
        return DefWindowProc(hwnd, uMsg, wParam, lParam);
    }
    return 0;
}

void CreateControls(HWND hwnd)
{
    // Main label
    g_hLabelMain = CreateWindowA(
        "STATIC",
        "Please select backends to install:",
        WS_VISIBLE | WS_CHILD,
        20, 20, 460, 30,
        hwnd,
        (HMENU)IDC_LABEL_MAIN,
        GetModuleHandle(NULL),
        NULL
    );
    if (g_hFont) SendMessage(g_hLabelMain, WM_SETFONT, (WPARAM)g_hFont, TRUE);

    // AI-Playground Backend checkbox
    g_hCheckboxAI = CreateWindowA(
        "BUTTON",
        "AI-Playground Backend (Required, or will install online later)",
        WS_VISIBLE | WS_CHILD | BS_AUTOCHECKBOX,
        20, 60, 460, 30,
        hwnd,
        (HMENU)IDC_CHECKBOX_AI_BACKEND,
        GetModuleHandle(NULL),
        NULL
    );
    SendMessage(g_hCheckboxAI, BM_SETCHECK, BST_CHECKED, 0);
    if (g_hFont) SendMessage(g_hCheckboxAI, WM_SETFONT, (WPARAM)g_hFont, TRUE);

    // OpenVINO checkbox
    g_hCheckboxOpenVINO = CreateWindowA(
        "BUTTON",
        "OpenVINO (Optional, LLM Answer requires OpenVINO)",
        WS_VISIBLE | WS_CHILD | BS_AUTOCHECKBOX,
        20, 90, 460, 30,
        hwnd,
        (HMENU)IDC_CHECKBOX_OPENVINO,
        GetModuleHandle(NULL),
        NULL
    );
    SendMessage(g_hCheckboxOpenVINO, BM_SETCHECK, BST_CHECKED, 0);
    if (g_hFont) SendMessage(g_hCheckboxOpenVINO, WM_SETFONT, (WPARAM)g_hFont, TRUE);

    // ComfyUI checkbox
    g_hCheckboxComfy = CreateWindowA(
        "BUTTON",
        "ComfyUI",
        WS_CHILD | BS_AUTOCHECKBOX,
        20, 120, 460, 30,
        hwnd,
        (HMENU)IDC_CHECKBOX_COMFYUI,
        GetModuleHandle(NULL),
        NULL
    );
    SendMessage(g_hCheckboxComfy, BM_SETCHECK, BST_UNCHECKED, 0);
    if (g_hFont) SendMessage(g_hCheckboxComfy, WM_SETFONT, (WPARAM)g_hFont, TRUE);


    // LlamaCPP checkbox (hidden for now, like in the original)
    g_hCheckboxLlama = CreateWindowA(
        "BUTTON",
        "LlamaCPP",
        WS_CHILD | BS_AUTOCHECKBOX, // Not visible
        20, 150, 460, 30,
        hwnd,
        (HMENU)IDC_CHECKBOX_LLAMACPP,
        GetModuleHandle(NULL),
        NULL
    );
    if (g_hFont) SendMessage(g_hCheckboxLlama, WM_SETFONT, (WPARAM)g_hFont, TRUE);

    g_hLabelNote = CreateWindowA(
        "STATIC",
        "NOTES: Backends can be installed online later.",
        WS_VISIBLE | WS_CHILD,
        20, 140, 460, 30,
        hwnd,
        (HMENU)IDC_LABEL_NOTE,
        GetModuleHandle(NULL),
        NULL
    );
    if (g_hFont) SendMessage(g_hLabelNote, WM_SETFONT, (WPARAM)g_hFont, TRUE);

    // OK button
    g_hButtonOK = CreateWindowA(
        "BUTTON",
        "OK",
        WS_VISIBLE | WS_CHILD | BS_PUSHBUTTON,
        400, 180, 75, 28,
        hwnd,
        (HMENU)IDC_BUTTON_OK,
        GetModuleHandle(NULL),
        NULL
    );
    if (g_hFont) {
        SendMessage(g_hButtonOK, WM_SETFONT, (WPARAM)g_hFont, TRUE);
    }
}

void OnOKButtonClick()
{
    std::string envs = "";
    std::string names = "";

    // Check which checkboxes are selected
    if (SendMessage(g_hCheckboxAI, BM_GETCHECK, 0, 0) == BST_CHECKED) {
        std::cout << "AI-Playground Backend is checked" << std::endl;
        envs += "ai-backend ";
        names += "AI-Playground Backend ";
    }

    if (SendMessage(g_hCheckboxComfy, BM_GETCHECK, 0, 0) == BST_CHECKED) {
        std::cout << "ComfyUI is checked" << std::endl;
        envs += "comfyui ";
        names += "ComfyUI ";
    }

    if (SendMessage(g_hCheckboxOpenVINO, BM_GETCHECK, 0, 0) == BST_CHECKED) {
        std::cout << "OpenVINO is checked" << std::endl;
        envs += "ov ";
        names += "OpenVINO ";
    }

    if (SendMessage(g_hCheckboxLlama, BM_GETCHECK, 0, 0) == BST_CHECKED) {
        std::cout << "LlamaCPP is checked" << std::endl;
        envs += "llamacpp ";
        names += "LlamaCPP ";
    }

    std::cout << "Selected environments: " << envs << std::endl;
    
    if (envs.empty()) {
        std::cout << "No environments selected. Exiting..." << std::endl;
        DestroyWindow(g_hWnd);
        return;
    }    std::cout << "Installing Backends: " << envs << std::endl;
    
    ShowInstallProgress();
    
    // Start the progress thread before executing installation
    g_installationActive = true;
    g_currentProgress = 0;
    g_realBProgress = 0;
    g_realEProgress = 0;
    g_progressThread = CreateThread(NULL, 0, ProgressThread, NULL, 0, NULL);

    ExecuteInstallation(envs);
}

void ShowInstallProgress()
{
    // Clear all controls and show progress message
    DestroyWindow(g_hCheckboxAI);
    DestroyWindow(g_hCheckboxComfy);
    DestroyWindow(g_hCheckboxOpenVINO);
    DestroyWindow(g_hCheckboxLlama);
    DestroyWindow(g_hButtonOK);
    DestroyWindow(g_hLabelMain);
    
    // Create new progress label
    g_hLabelMain = CreateWindowA(
        "STATIC",
        "Installing Backends: (please be patient)...",
        WS_VISIBLE | WS_CHILD,
        20, 20, 440, 30,
        g_hWnd,
        (HMENU)IDC_LABEL_MAIN,
        GetModuleHandle(NULL),
        NULL
    );
    if (g_hFont) SendMessage(g_hLabelMain, WM_SETFONT, (WPARAM)g_hFont, TRUE);// Create progress bar
    g_hProgressBar = CreateWindowA(
        "msctls_progress32",
        "",
        WS_VISIBLE | WS_CHILD | PBS_SMOOTH,
        20, 60, 460, 20,
        g_hWnd,
        (HMENU)IDC_PROGRESSBAR,
        GetModuleHandle(NULL),
        NULL
    );

    // Set progress bar range (0-100)
    SendMessage(g_hProgressBar, PBM_SETRANGE, 0, MAKELPARAM(0, 500));
    SendMessage(g_hProgressBar, PBM_SETPOS, 0, 0);

    // Refresh the window
    InvalidateRect(g_hWnd, NULL, TRUE);
    UpdateWindow(g_hWnd);
}

void ExecuteInstallation(const std::string& envs)
{
    // Get the window handle as a string
    std::string windowHandle = std::to_string((uintptr_t)g_hWnd);
    
    // Construct the PowerShell command to execute setup_all.ps1
    std::string scriptPath = g_scriptDir + "\\setup_all.ps1";
    std::string command = "powershell.exe -ExecutionPolicy Bypass -File \"" + scriptPath + "\" -installdir \"" + g_installDir + "\" -envs \"" + envs + "\" -windowhandle \"" + windowHandle + "\"";
    
    // Execute the command
    STARTUPINFOA si;
    PROCESS_INFORMATION pi;
    ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);
    ZeroMemory(&pi, sizeof(pi));

    if (CreateProcessA(NULL, const_cast<char*>(command.c_str()), NULL, NULL, FALSE, 0, NULL, NULL, &si, &pi)) {
        // Wait for the process to complete
        //WaitForSingleObject(pi.hProcess, INFINITE);
        
        // Close process and thread handles
        //CloseHandle(pi.hProcess);
        //CloseHandle(pi.hThread);
        
        std::cout << "Environments installed successfully." << std::endl;
    } else {
        std::cout << "Failed to execute installation script." << std::endl;
    }

    // Close the window
    //DestroyWindow(g_hWnd);
}

std::string GetExecutableDirectory()
{
    char buffer[MAX_PATH];
    GetModuleFileNameA(NULL, buffer, MAX_PATH);
    std::string path(buffer);
    size_t pos = path.find_last_of("\\/");
    return (pos != std::string::npos) ? path.substr(0, pos) : "";
}

std::string GetParentDirectory(const std::string& path)
{
    std::filesystem::path p(path);
    return p.parent_path().string();
}

void CreateModernFont()
{
    // Create a modern font - Segoe UI is the standard Windows modern font
    g_hFont = CreateFontA(
        -16,                        // Height (negative for character height)
        0,                          // Width (0 = default)
        0,                          // Escapement
        0,                          // Orientation
        FW_NORMAL,                  // Weight
        FALSE,                      // Italic
        FALSE,                      // Underline
        FALSE,                      // StrikeOut
        DEFAULT_CHARSET,            // CharSet
        OUT_DEFAULT_PRECIS,         // OutPrecision
        CLIP_DEFAULT_PRECIS,        // ClipPrecision
        CLEARTYPE_QUALITY,          // Quality (ClearType for smooth rendering)
        DEFAULT_PITCH | FF_DONTCARE, // PitchAndFamily
        "Segoe UI"                  // Font name
    );
    
    // If Segoe UI is not available, try Tahoma as fallback
    if (!g_hFont) {
        g_hFont = CreateFontA(
            -16, 0, 0, 0, FW_NORMAL, FALSE, FALSE, FALSE,
            DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS,
            CLEARTYPE_QUALITY, DEFAULT_PITCH | FF_DONTCARE,
            "Tahoma"
        );
    }
    // Final fallback to system default font
    if (!g_hFont) {
        g_hFont = (HFONT)GetStockObject(DEFAULT_GUI_FONT);
    }
}

DWORD WINAPI ProgressThread(LPVOID lpParam)
{
    const int UPDATE_INTERVAL_MS = 500; // Update every 100ms
    const double FAKE_PROGRESS_RATE = 0.05; // Slow fake progress rate
    
    while (g_installationActive) {
        Sleep(UPDATE_INTERVAL_MS);
        
        if (!g_installationActive) break;

        char progressText[256];
        sprintf(progressText, "Installing backends...: %d%%", g_currentProgress/5);

        PostMessage(g_hProgressBar, PBM_SETPOS, (WPARAM)g_currentProgress, 0);
        SetWindowTextA(g_hLabelMain, (LPCSTR)progressText);
        
        if (g_currentProgress<g_realEProgress)
            g_currentProgress++;
    }
    
    return 0;
}

void StopProgressThread()
{
    if (g_progressThread != NULL) {
        // Signal thread to stop
        g_installationActive = false;
        
        // Wait for thread to finish (with timeout)
        if (WaitForSingleObject(g_progressThread, 1000) == WAIT_TIMEOUT) {
            // Force terminate if it doesn't stop gracefully
            TerminateThread(g_progressThread, 0);
        }
        
        CloseHandle(g_progressThread);
        g_progressThread = NULL;
    }
}
