# Manipulação de Processos e Memória em C#

## 1. Gerenciamento de Processos

### 1.1 Listar Processos

```csharp
using System;
using System.Diagnostics;
using System.Linq;

public class ProcessManager
{
    // Listar todos os processos
    public void ListarProcessos()
    {
        foreach (Process proc in Process.GetProcesses())
        {
            try
            {
                Console.WriteLine($"PID: {proc.Id}, Nome: {proc.ProcessName}");
                Console.WriteLine($"  Memória: {proc.WorkingSet64 / 1024 / 1024} MB");
                Console.WriteLine($"  Threads: {proc.Threads.Count}");
                Console.WriteLine($"  Início: {proc.StartTime}");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"  Erro ao acessar: {ex.Message}");
            }
        }
    }

    // Buscar processo por nome
    public Process[] BuscarPorNome(string nome)
    {
        return Process.GetProcessesByName(nome);
    }

    // Buscar processo por PID
    public Process BuscarPorId(int pid)
    {
        return Process.GetProcessById(pid);
    }

    // Obter processo atual
    public Process ProcessoAtual()
    {
        return Process.GetCurrentProcess();
    }

    // Informações detalhadas
    public void InfoDetalhada(int pid)
    {
        Process proc = Process.GetProcessById(pid);

        Console.WriteLine($"Nome: {proc.ProcessName}");
        Console.WriteLine($"PID: {proc.Id}");
        Console.WriteLine($"Handle: {proc.Handle}");
        Console.WriteLine($"MainWindowHandle: {proc.MainWindowHandle}");
        Console.WriteLine($"MainWindowTitle: {proc.MainWindowTitle}");

        try
        {
            Console.WriteLine($"Caminho: {proc.MainModule.FileName}");
            Console.WriteLine($"Versão: {proc.MainModule.FileVersionInfo.FileVersion}");
        }
        catch { }

        Console.WriteLine($"Memória física: {proc.WorkingSet64 / 1024 / 1024} MB");
        Console.WriteLine($"Memória virtual: {proc.VirtualMemorySize64 / 1024 / 1024} MB");
        Console.WriteLine($"Memória privada: {proc.PrivateMemorySize64 / 1024 / 1024} MB");

        Console.WriteLine($"CPU Total: {proc.TotalProcessorTime}");
        Console.WriteLine($"Threads: {proc.Threads.Count}");
        Console.WriteLine($"Handles: {proc.HandleCount}");
        Console.WriteLine($"Prioridade: {proc.PriorityClass}");
    }
}
```

### 1.2 Iniciar e Encerrar Processos

```csharp
public class ProcessControl
{
    // Iniciar processo simples
    public Process IniciarSimples(string path)
    {
        return Process.Start(path);
    }

    // Iniciar com argumentos
    public Process IniciarComArgs(string path, string args)
    {
        return Process.Start(path, args);
    }

    // Iniciar com configurações avançadas
    public Process IniciarAvancado(string path, string args)
    {
        ProcessStartInfo psi = new ProcessStartInfo
        {
            FileName = path,
            Arguments = args,
            WorkingDirectory = Path.GetDirectoryName(path),
            UseShellExecute = false,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            RedirectStandardInput = true,
            CreateNoWindow = true,
            WindowStyle = ProcessWindowStyle.Hidden
        };

        Process proc = new Process { StartInfo = psi };
        proc.Start();
        return proc;
    }

    // Iniciar como administrador
    public Process IniciarComoAdmin(string path)
    {
        ProcessStartInfo psi = new ProcessStartInfo
        {
            FileName = path,
            UseShellExecute = true,
            Verb = "runas" // Elevação UAC
        };

        return Process.Start(psi);
    }

    // Iniciar com credenciais
    public Process IniciarComCredenciais(string path, string usuario, string senha, string dominio)
    {
        ProcessStartInfo psi = new ProcessStartInfo
        {
            FileName = path,
            UserName = usuario,
            Domain = dominio,
            UseShellExecute = false
        };

        // Converter senha para SecureString
        var securePassword = new System.Security.SecureString();
        foreach (char c in senha)
            securePassword.AppendChar(c);
        psi.Password = securePassword;

        return Process.Start(psi);
    }

    // Executar e capturar output
    public async Task<(string output, string error, int exitCode)> ExecutarComOutput(string path, string args)
    {
        ProcessStartInfo psi = new ProcessStartInfo
        {
            FileName = path,
            Arguments = args,
            UseShellExecute = false,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            CreateNoWindow = true
        };

        using Process proc = new Process { StartInfo = psi };
        proc.Start();

        string output = await proc.StandardOutput.ReadToEndAsync();
        string error = await proc.StandardError.ReadToEndAsync();

        await proc.WaitForExitAsync();

        return (output, error, proc.ExitCode);
    }

    // Encerrar processo
    public void Encerrar(int pid)
    {
        Process proc = Process.GetProcessById(pid);
        proc.Kill();
    }

    // Encerrar com timeout
    public bool EncerrarComTimeout(int pid, int timeoutMs)
    {
        Process proc = Process.GetProcessById(pid);

        // Tenta fechar graciosamente primeiro
        proc.CloseMainWindow();

        if (proc.WaitForExit(timeoutMs))
            return true;

        // Força encerramento
        proc.Kill();
        return proc.WaitForExit(timeoutMs);
    }

    // Encerrar árvore de processos
    public void EncerrarArvore(int pid)
    {
        Process proc = Process.GetProcessById(pid);

        foreach (Process child in GetChildProcesses(pid))
        {
            try
            {
                child.Kill();
            }
            catch { }
        }

        proc.Kill();
    }

    private IEnumerable<Process> GetChildProcesses(int parentPid)
    {
        // Usa WMI ou ManagementObjectSearcher
        // Simplificado aqui
        return Process.GetProcesses()
            .Where(p => GetParentProcessId(p.Id) == parentPid);
    }

    [DllImport("ntdll.dll")]
    private static extern int NtQueryInformationProcess(
        IntPtr processHandle, int processInformationClass,
        ref PROCESS_BASIC_INFORMATION processInformation,
        int processInformationLength, out int returnLength);

    [StructLayout(LayoutKind.Sequential)]
    private struct PROCESS_BASIC_INFORMATION
    {
        public IntPtr Reserved1;
        public IntPtr PebBaseAddress;
        public IntPtr Reserved2_0;
        public IntPtr Reserved2_1;
        public IntPtr UniqueProcessId;
        public IntPtr InheritedFromUniqueProcessId;
    }

    private int GetParentProcessId(int pid)
    {
        try
        {
            Process proc = Process.GetProcessById(pid);
            PROCESS_BASIC_INFORMATION pbi = new PROCESS_BASIC_INFORMATION();
            int returnLength;
            NtQueryInformationProcess(proc.Handle, 0, ref pbi, Marshal.SizeOf(pbi), out returnLength);
            return pbi.InheritedFromUniqueProcessId.ToInt32();
        }
        catch
        {
            return -1;
        }
    }
}
```

### 1.3 Monitorar Processos

```csharp
public class ProcessMonitor
{
    public event EventHandler<Process> ProcessStarted;
    public event EventHandler<int> ProcessEnded;

    private HashSet<int> _knownProcesses = new HashSet<int>();
    private Timer _timer;

    public void StartMonitoring(int intervalMs = 1000)
    {
        // Inicializa com processos atuais
        foreach (var proc in Process.GetProcesses())
            _knownProcesses.Add(proc.Id);

        _timer = new Timer(CheckProcesses, null, intervalMs, intervalMs);
    }

    public void StopMonitoring()
    {
        _timer?.Dispose();
    }

    private void CheckProcesses(object state)
    {
        var currentProcesses = new HashSet<int>(
            Process.GetProcesses().Select(p => p.Id));

        // Novos processos
        foreach (int pid in currentProcesses.Except(_knownProcesses))
        {
            try
            {
                ProcessStarted?.Invoke(this, Process.GetProcessById(pid));
            }
            catch { }
        }

        // Processos encerrados
        foreach (int pid in _knownProcesses.Except(currentProcesses))
        {
            ProcessEnded?.Invoke(this, pid);
        }

        _knownProcesses = currentProcesses;
    }
}

// Monitorar com WMI (mais eficiente)
public class WmiProcessMonitor : IDisposable
{
    private ManagementEventWatcher _startWatcher;
    private ManagementEventWatcher _stopWatcher;

    public event EventHandler<ProcessEventArgs> ProcessStarted;
    public event EventHandler<ProcessEventArgs> ProcessStopped;

    public void Start()
    {
        // Monitora criação de processos
        _startWatcher = new ManagementEventWatcher(
            new WqlEventQuery("SELECT * FROM Win32_ProcessStartTrace"));
        _startWatcher.EventArrived += (s, e) =>
        {
            ProcessStarted?.Invoke(this, new ProcessEventArgs
            {
                ProcessId = Convert.ToInt32(e.NewEvent["ProcessID"]),
                ProcessName = e.NewEvent["ProcessName"]?.ToString()
            });
        };
        _startWatcher.Start();

        // Monitora encerramento de processos
        _stopWatcher = new ManagementEventWatcher(
            new WqlEventQuery("SELECT * FROM Win32_ProcessStopTrace"));
        _stopWatcher.EventArrived += (s, e) =>
        {
            ProcessStopped?.Invoke(this, new ProcessEventArgs
            {
                ProcessId = Convert.ToInt32(e.NewEvent["ProcessID"]),
                ProcessName = e.NewEvent["ProcessName"]?.ToString()
            });
        };
        _stopWatcher.Start();
    }

    public void Dispose()
    {
        _startWatcher?.Stop();
        _startWatcher?.Dispose();
        _stopWatcher?.Stop();
        _stopWatcher?.Dispose();
    }
}

public class ProcessEventArgs : EventArgs
{
    public int ProcessId { get; set; }
    public string ProcessName { get; set; }
}
```

## 2. Manipulação de Memória

### 2.1 Ler Memória de Outro Processo

```csharp
public class MemoryReader
{
    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern IntPtr OpenProcess(uint dwDesiredAccess, bool bInheritHandle, int dwProcessId);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool ReadProcessMemory(
        IntPtr hProcess, IntPtr lpBaseAddress,
        [Out] byte[] lpBuffer, int dwSize,
        out int lpNumberOfBytesRead);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool CloseHandle(IntPtr hObject);

    private const uint PROCESS_VM_READ = 0x0010;
    private const uint PROCESS_VM_WRITE = 0x0020;
    private const uint PROCESS_VM_OPERATION = 0x0008;
    private const uint PROCESS_QUERY_INFORMATION = 0x0400;
    private const uint PROCESS_ALL_ACCESS = 0x1F0FFF;

    private IntPtr _processHandle;
    private int _processId;

    public MemoryReader(int processId)
    {
        _processId = processId;
        _processHandle = OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, false, processId);

        if (_processHandle == IntPtr.Zero)
            throw new Exception($"Não foi possível abrir processo. Erro: {Marshal.GetLastWin32Error()}");
    }

    // Ler bytes
    public byte[] ReadBytes(IntPtr address, int size)
    {
        byte[] buffer = new byte[size];
        if (ReadProcessMemory(_processHandle, address, buffer, size, out int bytesRead))
            return buffer;

        throw new Exception($"Erro ao ler memória. Erro: {Marshal.GetLastWin32Error()}");
    }

    // Ler tipos específicos
    public int ReadInt32(IntPtr address)
    {
        byte[] buffer = ReadBytes(address, 4);
        return BitConverter.ToInt32(buffer, 0);
    }

    public long ReadInt64(IntPtr address)
    {
        byte[] buffer = ReadBytes(address, 8);
        return BitConverter.ToInt64(buffer, 0);
    }

    public float ReadFloat(IntPtr address)
    {
        byte[] buffer = ReadBytes(address, 4);
        return BitConverter.ToSingle(buffer, 0);
    }

    public double ReadDouble(IntPtr address)
    {
        byte[] buffer = ReadBytes(address, 8);
        return BitConverter.ToDouble(buffer, 0);
    }

    public string ReadString(IntPtr address, int maxLength, Encoding encoding = null)
    {
        encoding = encoding ?? Encoding.UTF8;
        byte[] buffer = ReadBytes(address, maxLength);

        int nullIndex = Array.IndexOf(buffer, (byte)0);
        if (nullIndex > 0)
            return encoding.GetString(buffer, 0, nullIndex);

        return encoding.GetString(buffer);
    }

    // Ler ponteiro e seguir
    public IntPtr ReadPointer(IntPtr address)
    {
        byte[] buffer = ReadBytes(address, IntPtr.Size);
        return IntPtr.Size == 4
            ? new IntPtr(BitConverter.ToInt32(buffer, 0))
            : new IntPtr(BitConverter.ToInt64(buffer, 0));
    }

    // Ler com offset chain (multi-level pointer)
    public IntPtr ReadPointerChain(IntPtr baseAddress, params int[] offsets)
    {
        IntPtr address = baseAddress;

        for (int i = 0; i < offsets.Length - 1; i++)
        {
            address = ReadPointer(IntPtr.Add(address, offsets[i]));
        }

        return IntPtr.Add(address, offsets[offsets.Length - 1]);
    }

    // Ler estrutura
    public T ReadStruct<T>(IntPtr address) where T : struct
    {
        byte[] buffer = ReadBytes(address, Marshal.SizeOf<T>());
        GCHandle handle = GCHandle.Alloc(buffer, GCHandleType.Pinned);
        try
        {
            return Marshal.PtrToStructure<T>(handle.AddrOfPinnedObject());
        }
        finally
        {
            handle.Free();
        }
    }

    public void Close()
    {
        if (_processHandle != IntPtr.Zero)
        {
            CloseHandle(_processHandle);
            _processHandle = IntPtr.Zero;
        }
    }
}
```

### 2.2 Escrever Memória de Outro Processo

```csharp
public class MemoryWriter
{
    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern IntPtr OpenProcess(uint dwDesiredAccess, bool bInheritHandle, int dwProcessId);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool WriteProcessMemory(
        IntPtr hProcess, IntPtr lpBaseAddress,
        byte[] lpBuffer, int dwSize,
        out int lpNumberOfBytesWritten);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool CloseHandle(IntPtr hObject);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool VirtualProtectEx(
        IntPtr hProcess, IntPtr lpAddress,
        int dwSize, uint flNewProtect,
        out uint lpflOldProtect);

    private const uint PROCESS_VM_WRITE = 0x0020;
    private const uint PROCESS_VM_OPERATION = 0x0008;
    private const uint PAGE_EXECUTE_READWRITE = 0x40;

    private IntPtr _processHandle;

    public MemoryWriter(int processId)
    {
        _processHandle = OpenProcess(
            PROCESS_VM_WRITE | PROCESS_VM_OPERATION, false, processId);

        if (_processHandle == IntPtr.Zero)
            throw new Exception($"Erro ao abrir processo: {Marshal.GetLastWin32Error()}");
    }

    // Escrever bytes
    public bool WriteBytes(IntPtr address, byte[] data)
    {
        // Alterar proteção da memória
        VirtualProtectEx(_processHandle, address, data.Length,
            PAGE_EXECUTE_READWRITE, out uint oldProtect);

        bool result = WriteProcessMemory(_processHandle, address,
            data, data.Length, out int bytesWritten);

        // Restaurar proteção
        VirtualProtectEx(_processHandle, address, data.Length,
            oldProtect, out _);

        return result && bytesWritten == data.Length;
    }

    // Escrever tipos específicos
    public bool WriteInt32(IntPtr address, int value)
    {
        return WriteBytes(address, BitConverter.GetBytes(value));
    }

    public bool WriteInt64(IntPtr address, long value)
    {
        return WriteBytes(address, BitConverter.GetBytes(value));
    }

    public bool WriteFloat(IntPtr address, float value)
    {
        return WriteBytes(address, BitConverter.GetBytes(value));
    }

    public bool WriteDouble(IntPtr address, double value)
    {
        return WriteBytes(address, BitConverter.GetBytes(value));
    }

    public bool WriteString(IntPtr address, string value, Encoding encoding = null)
    {
        encoding = encoding ?? Encoding.UTF8;
        byte[] data = encoding.GetBytes(value + '\0');
        return WriteBytes(address, data);
    }

    // Escrever estrutura
    public bool WriteStruct<T>(IntPtr address, T value) where T : struct
    {
        int size = Marshal.SizeOf<T>();
        byte[] buffer = new byte[size];

        GCHandle handle = GCHandle.Alloc(buffer, GCHandleType.Pinned);
        try
        {
            Marshal.StructureToPtr(value, handle.AddrOfPinnedObject(), false);
            return WriteBytes(address, buffer);
        }
        finally
        {
            handle.Free();
        }
    }

    // NOP instruction (para patching)
    public bool WriteNop(IntPtr address, int count)
    {
        byte[] nops = new byte[count];
        for (int i = 0; i < count; i++)
            nops[i] = 0x90; // NOP instruction
        return WriteBytes(address, nops);
    }

    public void Close()
    {
        if (_processHandle != IntPtr.Zero)
        {
            CloseHandle(_processHandle);
            _processHandle = IntPtr.Zero;
        }
    }
}
```

### 2.3 Scanner de Memória

```csharp
public class MemoryScanner
{
    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern IntPtr OpenProcess(uint dwDesiredAccess, bool bInheritHandle, int dwProcessId);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool ReadProcessMemory(
        IntPtr hProcess, IntPtr lpBaseAddress,
        [Out] byte[] lpBuffer, int dwSize,
        out int lpNumberOfBytesRead);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern int VirtualQueryEx(
        IntPtr hProcess, IntPtr lpAddress,
        out MEMORY_BASIC_INFORMATION lpBuffer,
        int dwLength);

    [StructLayout(LayoutKind.Sequential)]
    private struct MEMORY_BASIC_INFORMATION
    {
        public IntPtr BaseAddress;
        public IntPtr AllocationBase;
        public uint AllocationProtect;
        public IntPtr RegionSize;
        public uint State;
        public uint Protect;
        public uint Type;
    }

    private const uint MEM_COMMIT = 0x1000;
    private const uint PAGE_READABLE = 0x02 | 0x04 | 0x20 | 0x40;

    private IntPtr _processHandle;
    private Process _process;

    public MemoryScanner(int processId)
    {
        _process = Process.GetProcessById(processId);
        _processHandle = OpenProcess(0x1F0FFF, false, processId);
    }

    // Escanear por valor
    public List<IntPtr> ScanForValue<T>(T value) where T : struct
    {
        List<IntPtr> results = new List<IntPtr>();
        byte[] searchBytes = StructToBytes(value);

        IntPtr address = IntPtr.Zero;
        IntPtr maxAddress = new IntPtr(0x7FFFFFFF);

        while (address.ToInt64() < maxAddress.ToInt64())
        {
            if (VirtualQueryEx(_processHandle, address,
                out MEMORY_BASIC_INFORMATION mbi, Marshal.SizeOf<MEMORY_BASIC_INFORMATION>()) == 0)
                break;

            if (mbi.State == MEM_COMMIT && (mbi.Protect & PAGE_READABLE) != 0)
            {
                byte[] buffer = new byte[(int)mbi.RegionSize];
                if (ReadProcessMemory(_processHandle, mbi.BaseAddress,
                    buffer, buffer.Length, out int bytesRead))
                {
                    for (int i = 0; i <= bytesRead - searchBytes.Length; i++)
                    {
                        bool match = true;
                        for (int j = 0; j < searchBytes.Length; j++)
                        {
                            if (buffer[i + j] != searchBytes[j])
                            {
                                match = false;
                                break;
                            }
                        }
                        if (match)
                        {
                            results.Add(IntPtr.Add(mbi.BaseAddress, i));
                        }
                    }
                }
            }

            address = IntPtr.Add(mbi.BaseAddress, (int)mbi.RegionSize);
        }

        return results;
    }

    // Escanear por padrão (com wildcards)
    public List<IntPtr> ScanForPattern(string pattern)
    {
        // Padrão: "8B 45 ?? 89 45 FC"
        // ?? = wildcard
        List<IntPtr> results = new List<IntPtr>();

        string[] parts = pattern.Split(' ');
        byte[] bytes = new byte[parts.Length];
        bool[] mask = new bool[parts.Length];

        for (int i = 0; i < parts.Length; i++)
        {
            if (parts[i] == "??" || parts[i] == "?")
            {
                mask[i] = true;
                bytes[i] = 0;
            }
            else
            {
                mask[i] = false;
                bytes[i] = Convert.ToByte(parts[i], 16);
            }
        }

        IntPtr address = IntPtr.Zero;
        IntPtr maxAddress = new IntPtr(0x7FFFFFFF);

        while (address.ToInt64() < maxAddress.ToInt64())
        {
            if (VirtualQueryEx(_processHandle, address,
                out MEMORY_BASIC_INFORMATION mbi, Marshal.SizeOf<MEMORY_BASIC_INFORMATION>()) == 0)
                break;

            if (mbi.State == MEM_COMMIT && (mbi.Protect & PAGE_READABLE) != 0)
            {
                byte[] buffer = new byte[(int)mbi.RegionSize];
                if (ReadProcessMemory(_processHandle, mbi.BaseAddress,
                    buffer, buffer.Length, out int bytesRead))
                {
                    for (int i = 0; i <= bytesRead - bytes.Length; i++)
                    {
                        bool match = true;
                        for (int j = 0; j < bytes.Length; j++)
                        {
                            if (!mask[j] && buffer[i + j] != bytes[j])
                            {
                                match = false;
                                break;
                            }
                        }
                        if (match)
                        {
                            results.Add(IntPtr.Add(mbi.BaseAddress, i));
                        }
                    }
                }
            }

            address = IntPtr.Add(mbi.BaseAddress, (int)mbi.RegionSize);
        }

        return results;
    }

    // Filtrar resultados (para scan progressivo)
    public List<IntPtr> FilterResults<T>(List<IntPtr> addresses, T newValue) where T : struct
    {
        List<IntPtr> filtered = new List<IntPtr>();
        byte[] searchBytes = StructToBytes(newValue);
        byte[] buffer = new byte[searchBytes.Length];

        foreach (IntPtr address in addresses)
        {
            if (ReadProcessMemory(_processHandle, address,
                buffer, buffer.Length, out _))
            {
                bool match = true;
                for (int i = 0; i < searchBytes.Length; i++)
                {
                    if (buffer[i] != searchBytes[i])
                    {
                        match = false;
                        break;
                    }
                }
                if (match)
                    filtered.Add(address);
            }
        }

        return filtered;
    }

    private byte[] StructToBytes<T>(T value) where T : struct
    {
        int size = Marshal.SizeOf<T>();
        byte[] buffer = new byte[size];
        GCHandle handle = GCHandle.Alloc(buffer, GCHandleType.Pinned);
        try
        {
            Marshal.StructureToPtr(value, handle.AddrOfPinnedObject(), false);
            return buffer;
        }
        finally
        {
            handle.Free();
        }
    }
}
```

## 3. Injeção de DLL

### 3.1 Injeção via CreateRemoteThread

```csharp
public class DllInjector
{
    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern IntPtr OpenProcess(uint dwDesiredAccess, bool bInheritHandle, int dwProcessId);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern IntPtr VirtualAllocEx(
        IntPtr hProcess, IntPtr lpAddress, int dwSize,
        uint flAllocationType, uint flProtect);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool WriteProcessMemory(
        IntPtr hProcess, IntPtr lpBaseAddress,
        byte[] lpBuffer, int dwSize,
        out int lpNumberOfBytesWritten);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern IntPtr GetProcAddress(IntPtr hModule, string lpProcName);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern IntPtr GetModuleHandle(string lpModuleName);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern IntPtr CreateRemoteThread(
        IntPtr hProcess, IntPtr lpThreadAttributes,
        uint dwStackSize, IntPtr lpStartAddress,
        IntPtr lpParameter, uint dwCreationFlags,
        out uint lpThreadId);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern uint WaitForSingleObject(IntPtr hHandle, uint dwMilliseconds);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool VirtualFreeEx(
        IntPtr hProcess, IntPtr lpAddress,
        int dwSize, uint dwFreeType);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool CloseHandle(IntPtr hObject);

    private const uint PROCESS_ALL_ACCESS = 0x1F0FFF;
    private const uint MEM_COMMIT = 0x1000;
    private const uint MEM_RESERVE = 0x2000;
    private const uint MEM_RELEASE = 0x8000;
    private const uint PAGE_READWRITE = 0x04;
    private const uint INFINITE = 0xFFFFFFFF;

    public bool Inject(int processId, string dllPath)
    {
        // Converter para caminho absoluto
        dllPath = Path.GetFullPath(dllPath);

        if (!File.Exists(dllPath))
            throw new FileNotFoundException("DLL não encontrada", dllPath);

        IntPtr hProcess = IntPtr.Zero;
        IntPtr allocatedMemory = IntPtr.Zero;

        try
        {
            // Abrir processo
            hProcess = OpenProcess(PROCESS_ALL_ACCESS, false, processId);
            if (hProcess == IntPtr.Zero)
                throw new Exception($"Erro ao abrir processo: {Marshal.GetLastWin32Error()}");

            // Alocar memória no processo remoto
            byte[] dllPathBytes = Encoding.Unicode.GetBytes(dllPath + '\0');
            allocatedMemory = VirtualAllocEx(hProcess, IntPtr.Zero, dllPathBytes.Length,
                MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);

            if (allocatedMemory == IntPtr.Zero)
                throw new Exception($"Erro ao alocar memória: {Marshal.GetLastWin32Error()}");

            // Escrever caminho da DLL na memória
            if (!WriteProcessMemory(hProcess, allocatedMemory, dllPathBytes,
                dllPathBytes.Length, out _))
                throw new Exception($"Erro ao escrever memória: {Marshal.GetLastWin32Error()}");

            // Obter endereço de LoadLibraryW
            IntPtr kernel32 = GetModuleHandle("kernel32.dll");
            IntPtr loadLibraryAddr = GetProcAddress(kernel32, "LoadLibraryW");

            if (loadLibraryAddr == IntPtr.Zero)
                throw new Exception("Não foi possível encontrar LoadLibraryW");

            // Criar thread remota
            IntPtr hThread = CreateRemoteThread(hProcess, IntPtr.Zero, 0,
                loadLibraryAddr, allocatedMemory, 0, out _);

            if (hThread == IntPtr.Zero)
                throw new Exception($"Erro ao criar thread: {Marshal.GetLastWin32Error()}");

            // Aguardar thread terminar
            WaitForSingleObject(hThread, INFINITE);
            CloseHandle(hThread);

            return true;
        }
        finally
        {
            // Limpar
            if (allocatedMemory != IntPtr.Zero)
                VirtualFreeEx(hProcess, allocatedMemory, 0, MEM_RELEASE);

            if (hProcess != IntPtr.Zero)
                CloseHandle(hProcess);
        }
    }
}
```

### 3.2 Injeção de Shellcode

```csharp
public class ShellcodeInjector
{
    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern IntPtr OpenProcess(uint dwDesiredAccess, bool bInheritHandle, int dwProcessId);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern IntPtr VirtualAllocEx(
        IntPtr hProcess, IntPtr lpAddress, int dwSize,
        uint flAllocationType, uint flProtect);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool WriteProcessMemory(
        IntPtr hProcess, IntPtr lpBaseAddress,
        byte[] lpBuffer, int dwSize,
        out int lpNumberOfBytesWritten);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern IntPtr CreateRemoteThread(
        IntPtr hProcess, IntPtr lpThreadAttributes,
        uint dwStackSize, IntPtr lpStartAddress,
        IntPtr lpParameter, uint dwCreationFlags,
        out uint lpThreadId);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool CloseHandle(IntPtr hObject);

    private const uint PROCESS_ALL_ACCESS = 0x1F0FFF;
    private const uint MEM_COMMIT = 0x1000;
    private const uint MEM_RESERVE = 0x2000;
    private const uint PAGE_EXECUTE_READWRITE = 0x40;

    public bool InjectShellcode(int processId, byte[] shellcode)
    {
        IntPtr hProcess = OpenProcess(PROCESS_ALL_ACCESS, false, processId);
        if (hProcess == IntPtr.Zero)
            return false;

        try
        {
            // Alocar memória executável
            IntPtr allocatedMemory = VirtualAllocEx(hProcess, IntPtr.Zero,
                shellcode.Length, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);

            if (allocatedMemory == IntPtr.Zero)
                return false;

            // Escrever shellcode
            if (!WriteProcessMemory(hProcess, allocatedMemory,
                shellcode, shellcode.Length, out _))
                return false;

            // Executar shellcode
            IntPtr hThread = CreateRemoteThread(hProcess, IntPtr.Zero, 0,
                allocatedMemory, IntPtr.Zero, 0, out _);

            if (hThread == IntPtr.Zero)
                return false;

            CloseHandle(hThread);
            return true;
        }
        finally
        {
            CloseHandle(hProcess);
        }
    }

    // Exemplo de shellcode que exibe MessageBox
    public byte[] GetMessageBoxShellcode()
    {
        // Este é apenas um exemplo - em produção use shellcode real
        // Este shellcode x86 chama MessageBoxA
        return new byte[]
        {
            0x31, 0xd2,                         // xor edx, edx
            0x52,                               // push edx
            0x68, 0x48, 0x65, 0x6c, 0x6f,       // push "oleH"
            0x89, 0xe6,                         // mov esi, esp
            0x52,                               // push edx
            0x56,                               // push esi
            0x56,                               // push esi
            0x52,                               // push edx
            0xb8, 0x00, 0x00, 0x00, 0x00,       // mov eax, addr of MessageBoxA
            0xff, 0xd0,                         // call eax
            0xc3                                // ret
        };
    }
}
```

## 4. Hooking de Funções

### 4.1 IAT Hooking (Import Address Table)

```csharp
public class IATHook
{
    [DllImport("kernel32.dll")]
    private static extern IntPtr GetModuleHandle(string lpModuleName);

    [DllImport("kernel32.dll")]
    private static extern bool VirtualProtect(
        IntPtr lpAddress, int dwSize,
        uint flNewProtect, out uint lpflOldProtect);

    [DllImport("dbghelp.dll", SetLastError = true)]
    private static extern IntPtr ImageDirectoryEntryToData(
        IntPtr Base, bool MappedAsImage, ushort DirectoryEntry,
        out uint Size);

    private const ushort IMAGE_DIRECTORY_ENTRY_IMPORT = 1;
    private const uint PAGE_EXECUTE_READWRITE = 0x40;

    public bool HookImport(string moduleName, string functionName, IntPtr newAddress)
    {
        IntPtr moduleHandle = GetModuleHandle(null); // Módulo atual
        if (moduleHandle == IntPtr.Zero)
            return false;

        // Encontrar IAT
        IntPtr importTable = ImageDirectoryEntryToData(
            moduleHandle, true, IMAGE_DIRECTORY_ENTRY_IMPORT, out uint size);

        if (importTable == IntPtr.Zero)
            return false;

        // Percorrer imports e encontrar função
        // (Implementação completa requer parsing do PE)
        // ...

        return true;
    }
}
```

### 4.2 Inline Hooking (Detour)

```csharp
public class InlineHook
{
    [DllImport("kernel32.dll")]
    private static extern bool VirtualProtect(
        IntPtr lpAddress, int dwSize,
        uint flNewProtect, out uint lpflOldProtect);

    private const uint PAGE_EXECUTE_READWRITE = 0x40;

    private IntPtr _targetAddress;
    private byte[] _originalBytes;
    private byte[] _hookBytes;

    public bool Hook(IntPtr targetAddress, IntPtr hookAddress)
    {
        _targetAddress = targetAddress;

        // Salvar bytes originais
        _originalBytes = new byte[5];
        Marshal.Copy(targetAddress, _originalBytes, 0, 5);

        // Criar JMP para nossa função
        // JMP rel32 = E9 xx xx xx xx
        _hookBytes = new byte[5];
        _hookBytes[0] = 0xE9; // JMP opcode
        int offset = (int)(hookAddress.ToInt64() - targetAddress.ToInt64() - 5);
        BitConverter.GetBytes(offset).CopyTo(_hookBytes, 1);

        // Alterar proteção e escrever hook
        if (!VirtualProtect(targetAddress, 5, PAGE_EXECUTE_READWRITE, out uint oldProtect))
            return false;

        Marshal.Copy(_hookBytes, 0, targetAddress, 5);

        VirtualProtect(targetAddress, 5, oldProtect, out _);

        return true;
    }

    public bool Unhook()
    {
        if (_originalBytes == null)
            return false;

        if (!VirtualProtect(_targetAddress, 5, PAGE_EXECUTE_READWRITE, out uint oldProtect))
            return false;

        Marshal.Copy(_originalBytes, 0, _targetAddress, 5);

        VirtualProtect(_targetAddress, 5, oldProtect, out _);

        return true;
    }
}
```

## 5. Módulos e DLLs

### 5.1 Listar Módulos de um Processo

```csharp
public class ModuleManager
{
    [DllImport("psapi.dll", SetLastError = true)]
    private static extern bool EnumProcessModulesEx(
        IntPtr hProcess, [Out] IntPtr[] lphModule,
        int cb, out int lpcbNeeded, uint dwFilterFlag);

    [DllImport("psapi.dll", SetLastError = true)]
    private static extern uint GetModuleFileNameEx(
        IntPtr hProcess, IntPtr hModule,
        StringBuilder lpFilename, uint nSize);

    [DllImport("psapi.dll", SetLastError = true)]
    private static extern bool GetModuleInformation(
        IntPtr hProcess, IntPtr hModule,
        out MODULEINFO lpmodinfo, int cb);

    [StructLayout(LayoutKind.Sequential)]
    public struct MODULEINFO
    {
        public IntPtr lpBaseOfDll;
        public uint SizeOfImage;
        public IntPtr EntryPoint;
    }

    private const uint LIST_MODULES_ALL = 0x03;

    public List<ModuleInfo> ListModules(int processId)
    {
        var modules = new List<ModuleInfo>();

        Process proc = Process.GetProcessById(processId);
        IntPtr hProcess = proc.Handle;

        IntPtr[] moduleHandles = new IntPtr[1024];
        if (!EnumProcessModulesEx(hProcess, moduleHandles,
            moduleHandles.Length * IntPtr.Size, out int needed, LIST_MODULES_ALL))
            return modules;

        int count = needed / IntPtr.Size;

        for (int i = 0; i < count; i++)
        {
            StringBuilder fileName = new StringBuilder(260);
            GetModuleFileNameEx(hProcess, moduleHandles[i], fileName, (uint)fileName.Capacity);

            GetModuleInformation(hProcess, moduleHandles[i],
                out MODULEINFO modInfo, Marshal.SizeOf<MODULEINFO>());

            modules.Add(new ModuleInfo
            {
                Handle = moduleHandles[i],
                FileName = fileName.ToString(),
                BaseAddress = modInfo.lpBaseOfDll,
                Size = modInfo.SizeOfImage,
                EntryPoint = modInfo.EntryPoint
            });
        }

        return modules;
    }

    public ModuleInfo FindModule(int processId, string moduleName)
    {
        return ListModules(processId)
            .FirstOrDefault(m => m.FileName.EndsWith(moduleName, StringComparison.OrdinalIgnoreCase));
    }
}

public class ModuleInfo
{
    public IntPtr Handle { get; set; }
    public string FileName { get; set; }
    public IntPtr BaseAddress { get; set; }
    public uint Size { get; set; }
    public IntPtr EntryPoint { get; set; }
}
```

## 6. Debug e Debugging API

```csharp
public class ProcessDebugger
{
    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool DebugActiveProcess(int dwProcessId);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool DebugActiveProcessStop(int dwProcessId);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool WaitForDebugEvent(
        out DEBUG_EVENT lpDebugEvent, uint dwMilliseconds);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool ContinueDebugEvent(
        int dwProcessId, int dwThreadId, uint dwContinueStatus);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool IsDebuggerPresent();

    [StructLayout(LayoutKind.Sequential)]
    private struct DEBUG_EVENT
    {
        public uint dwDebugEventCode;
        public int dwProcessId;
        public int dwThreadId;
        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 164)]
        public byte[] u;
    }

    private const uint EXCEPTION_DEBUG_EVENT = 1;
    private const uint CREATE_THREAD_DEBUG_EVENT = 2;
    private const uint CREATE_PROCESS_DEBUG_EVENT = 3;
    private const uint EXIT_THREAD_DEBUG_EVENT = 4;
    private const uint EXIT_PROCESS_DEBUG_EVENT = 5;
    private const uint LOAD_DLL_DEBUG_EVENT = 6;
    private const uint UNLOAD_DLL_DEBUG_EVENT = 7;
    private const uint OUTPUT_DEBUG_STRING_EVENT = 8;

    private const uint DBG_CONTINUE = 0x00010002;
    private const uint DBG_EXCEPTION_NOT_HANDLED = 0x80010001;

    private int _processId;
    private bool _isDebugging;

    public void Attach(int processId)
    {
        _processId = processId;

        if (!DebugActiveProcess(processId))
            throw new Exception($"Erro ao anexar: {Marshal.GetLastWin32Error()}");

        _isDebugging = true;
    }

    public void Detach()
    {
        if (_isDebugging)
        {
            DebugActiveProcessStop(_processId);
            _isDebugging = false;
        }
    }

    public void Run()
    {
        while (_isDebugging)
        {
            if (WaitForDebugEvent(out DEBUG_EVENT debugEvent, 1000))
            {
                HandleDebugEvent(debugEvent);
                ContinueDebugEvent(debugEvent.dwProcessId,
                    debugEvent.dwThreadId, DBG_CONTINUE);
            }
        }
    }

    private void HandleDebugEvent(DEBUG_EVENT evt)
    {
        switch (evt.dwDebugEventCode)
        {
            case EXCEPTION_DEBUG_EVENT:
                Console.WriteLine($"Exceção no processo {evt.dwProcessId}");
                break;

            case CREATE_PROCESS_DEBUG_EVENT:
                Console.WriteLine($"Processo criado: {evt.dwProcessId}");
                break;

            case EXIT_PROCESS_DEBUG_EVENT:
                Console.WriteLine($"Processo encerrado: {evt.dwProcessId}");
                _isDebugging = false;
                break;

            case LOAD_DLL_DEBUG_EVENT:
                Console.WriteLine("DLL carregada");
                break;
        }
    }
}
```

Este guia cobre manipulação avançada de processos e memória em C#!
