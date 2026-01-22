# Guia Completo de C# para Desenvolvimento de Remote Desktop

## 1. Fundamentos do Remote Desktop em C#

### 1.1 Bibliotecas Principais

```csharp
// Bibliotecas necessárias
using System;
using System.Net;
using System.Net.Sockets;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Runtime.InteropServices;
using System.Windows.Forms;
using System.Threading;
using System.Threading.Tasks;
```

### 1.2 Captura de Tela (Screenshot)

```csharp
public class ScreenCapture
{
    // Captura a tela inteira
    public static Bitmap CaptureScreen()
    {
        Rectangle bounds = Screen.PrimaryScreen.Bounds;
        Bitmap screenshot = new Bitmap(bounds.Width, bounds.Height, PixelFormat.Format32bppArgb);

        using (Graphics g = Graphics.FromImage(screenshot))
        {
            g.CopyFromScreen(bounds.X, bounds.Y, 0, 0, bounds.Size, CopyPixelOperation.SourceCopy);
        }

        return screenshot;
    }

    // Captura uma região específica
    public static Bitmap CaptureRegion(int x, int y, int width, int height)
    {
        Bitmap screenshot = new Bitmap(width, height, PixelFormat.Format32bppArgb);

        using (Graphics g = Graphics.FromImage(screenshot))
        {
            g.CopyFromScreen(x, y, 0, 0, new Size(width, height), CopyPixelOperation.SourceCopy);
        }

        return screenshot;
    }

    // Captura com compressão JPEG
    public static byte[] CaptureScreenAsJpeg(int quality = 50)
    {
        using (Bitmap screenshot = CaptureScreen())
        using (MemoryStream ms = new MemoryStream())
        {
            ImageCodecInfo jpegCodec = GetEncoder(ImageFormat.Jpeg);
            EncoderParameters encoderParams = new EncoderParameters(1);
            encoderParams.Param[0] = new EncoderParameter(Encoder.Quality, quality);

            screenshot.Save(ms, jpegCodec, encoderParams);
            return ms.ToArray();
        }
    }

    private static ImageCodecInfo GetEncoder(ImageFormat format)
    {
        ImageCodecInfo[] codecs = ImageCodecInfo.GetImageDecoders();
        foreach (ImageCodecInfo codec in codecs)
        {
            if (codec.FormatID == format.Guid)
                return codec;
        }
        return null;
    }
}
```

### 1.3 Captura de Tela Otimizada (Diferencial)

```csharp
public class DifferentialScreenCapture
{
    private Bitmap previousScreen;
    private readonly object lockObj = new object();

    // Captura apenas as diferenças
    public byte[] CaptureChanges()
    {
        Bitmap currentScreen = ScreenCapture.CaptureScreen();

        lock (lockObj)
        {
            if (previousScreen == null)
            {
                previousScreen = currentScreen;
                return CompressScreen(currentScreen);
            }

            // Encontra regiões que mudaram
            List<Rectangle> changedRegions = FindChangedRegions(previousScreen, currentScreen);

            if (changedRegions.Count == 0)
            {
                currentScreen.Dispose();
                return null; // Sem mudanças
            }

            // Captura apenas as regiões alteradas
            byte[] data = CompressChangedRegions(currentScreen, changedRegions);

            previousScreen.Dispose();
            previousScreen = currentScreen;

            return data;
        }
    }

    private List<Rectangle> FindChangedRegions(Bitmap old, Bitmap current, int blockSize = 32)
    {
        List<Rectangle> changed = new List<Rectangle>();

        for (int y = 0; y < old.Height; y += blockSize)
        {
            for (int x = 0; x < old.Width; x += blockSize)
            {
                int w = Math.Min(blockSize, old.Width - x);
                int h = Math.Min(blockSize, old.Height - y);

                if (IsBlockDifferent(old, current, x, y, w, h))
                {
                    changed.Add(new Rectangle(x, y, w, h));
                }
            }
        }

        return changed;
    }

    private bool IsBlockDifferent(Bitmap old, Bitmap current, int x, int y, int w, int h)
    {
        for (int py = y; py < y + h; py++)
        {
            for (int px = x; px < x + w; px++)
            {
                if (old.GetPixel(px, py) != current.GetPixel(px, py))
                    return true;
            }
        }
        return false;
    }

    private byte[] CompressScreen(Bitmap screen)
    {
        using (MemoryStream ms = new MemoryStream())
        {
            screen.Save(ms, ImageFormat.Jpeg);
            return ms.ToArray();
        }
    }

    private byte[] CompressChangedRegions(Bitmap screen, List<Rectangle> regions)
    {
        using (MemoryStream ms = new MemoryStream())
        using (BinaryWriter writer = new BinaryWriter(ms))
        {
            writer.Write(regions.Count);

            foreach (Rectangle region in regions)
            {
                writer.Write(region.X);
                writer.Write(region.Y);
                writer.Write(region.Width);
                writer.Write(region.Height);

                using (Bitmap regionBitmap = screen.Clone(region, screen.PixelFormat))
                using (MemoryStream regionMs = new MemoryStream())
                {
                    regionBitmap.Save(regionMs, ImageFormat.Jpeg);
                    byte[] regionData = regionMs.ToArray();
                    writer.Write(regionData.Length);
                    writer.Write(regionData);
                }
            }

            return ms.ToArray();
        }
    }
}
```

## 2. Controle de Mouse e Teclado

### 2.1 Simulação de Mouse (Win32 API)

```csharp
public class MouseController
{
    [DllImport("user32.dll")]
    private static extern void mouse_event(uint dwFlags, int dx, int dy, uint dwData, int dwExtraInfo);

    [DllImport("user32.dll")]
    private static extern bool SetCursorPos(int X, int Y);

    [DllImport("user32.dll")]
    private static extern bool GetCursorPos(out POINT lpPoint);

    [StructLayout(LayoutKind.Sequential)]
    public struct POINT
    {
        public int X;
        public int Y;
    }

    private const uint MOUSEEVENTF_MOVE = 0x0001;
    private const uint MOUSEEVENTF_LEFTDOWN = 0x0002;
    private const uint MOUSEEVENTF_LEFTUP = 0x0004;
    private const uint MOUSEEVENTF_RIGHTDOWN = 0x0008;
    private const uint MOUSEEVENTF_RIGHTUP = 0x0010;
    private const uint MOUSEEVENTF_MIDDLEDOWN = 0x0020;
    private const uint MOUSEEVENTF_MIDDLEUP = 0x0040;
    private const uint MOUSEEVENTF_WHEEL = 0x0800;
    private const uint MOUSEEVENTF_ABSOLUTE = 0x8000;

    // Move o mouse para posição
    public static void MoveTo(int x, int y)
    {
        SetCursorPos(x, y);
    }

    // Clique esquerdo
    public static void LeftClick(int x, int y)
    {
        SetCursorPos(x, y);
        mouse_event(MOUSEEVENTF_LEFTDOWN, x, y, 0, 0);
        Thread.Sleep(50);
        mouse_event(MOUSEEVENTF_LEFTUP, x, y, 0, 0);
    }

    // Clique duplo
    public static void DoubleClick(int x, int y)
    {
        LeftClick(x, y);
        Thread.Sleep(100);
        LeftClick(x, y);
    }

    // Clique direito
    public static void RightClick(int x, int y)
    {
        SetCursorPos(x, y);
        mouse_event(MOUSEEVENTF_RIGHTDOWN, x, y, 0, 0);
        Thread.Sleep(50);
        mouse_event(MOUSEEVENTF_RIGHTUP, x, y, 0, 0);
    }

    // Clique do meio
    public static void MiddleClick(int x, int y)
    {
        SetCursorPos(x, y);
        mouse_event(MOUSEEVENTF_MIDDLEDOWN, x, y, 0, 0);
        Thread.Sleep(50);
        mouse_event(MOUSEEVENTF_MIDDLEUP, x, y, 0, 0);
    }

    // Scroll
    public static void Scroll(int delta)
    {
        mouse_event(MOUSEEVENTF_WHEEL, 0, 0, (uint)delta, 0);
    }

    // Arrastar
    public static void Drag(int startX, int startY, int endX, int endY)
    {
        SetCursorPos(startX, startY);
        mouse_event(MOUSEEVENTF_LEFTDOWN, startX, startY, 0, 0);
        Thread.Sleep(50);

        // Move suavemente
        int steps = 10;
        for (int i = 1; i <= steps; i++)
        {
            int x = startX + (endX - startX) * i / steps;
            int y = startY + (endY - startY) * i / steps;
            SetCursorPos(x, y);
            Thread.Sleep(10);
        }

        mouse_event(MOUSEEVENTF_LEFTUP, endX, endY, 0, 0);
    }

    // Obter posição atual
    public static Point GetPosition()
    {
        POINT p;
        GetCursorPos(out p);
        return new Point(p.X, p.Y);
    }
}
```

### 2.2 Simulação de Teclado (Win32 API)

```csharp
public class KeyboardController
{
    [DllImport("user32.dll")]
    private static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, int dwExtraInfo);

    [DllImport("user32.dll")]
    private static extern short VkKeyScan(char ch);

    private const uint KEYEVENTF_KEYDOWN = 0x0000;
    private const uint KEYEVENTF_KEYUP = 0x0002;
    private const uint KEYEVENTF_EXTENDEDKEY = 0x0001;

    // Teclas especiais
    public static class Keys
    {
        public const byte VK_BACK = 0x08;
        public const byte VK_TAB = 0x09;
        public const byte VK_RETURN = 0x0D;
        public const byte VK_SHIFT = 0x10;
        public const byte VK_CONTROL = 0x11;
        public const byte VK_MENU = 0x12; // ALT
        public const byte VK_ESCAPE = 0x1B;
        public const byte VK_SPACE = 0x20;
        public const byte VK_DELETE = 0x2E;
        public const byte VK_LWIN = 0x5B;
        public const byte VK_F1 = 0x70;
        public const byte VK_F2 = 0x71;
        public const byte VK_F3 = 0x72;
        public const byte VK_F4 = 0x73;
        public const byte VK_F5 = 0x74;
        public const byte VK_F6 = 0x75;
        public const byte VK_F7 = 0x76;
        public const byte VK_F8 = 0x77;
        public const byte VK_F9 = 0x78;
        public const byte VK_F10 = 0x79;
        public const byte VK_F11 = 0x7A;
        public const byte VK_F12 = 0x7B;
    }

    // Pressionar e soltar tecla
    public static void PressKey(byte keyCode)
    {
        keybd_event(keyCode, 0, KEYEVENTF_KEYDOWN, 0);
        Thread.Sleep(50);
        keybd_event(keyCode, 0, KEYEVENTF_KEYUP, 0);
    }

    // Segurar tecla
    public static void KeyDown(byte keyCode)
    {
        keybd_event(keyCode, 0, KEYEVENTF_KEYDOWN, 0);
    }

    // Soltar tecla
    public static void KeyUp(byte keyCode)
    {
        keybd_event(keyCode, 0, KEYEVENTF_KEYUP, 0);
    }

    // Digitar texto
    public static void Type(string text)
    {
        foreach (char c in text)
        {
            short vk = VkKeyScan(c);
            byte keyCode = (byte)(vk & 0xFF);
            bool shift = (vk & 0x100) != 0;

            if (shift)
                KeyDown(Keys.VK_SHIFT);

            PressKey(keyCode);

            if (shift)
                KeyUp(Keys.VK_SHIFT);

            Thread.Sleep(10);
        }
    }

    // Combinações de teclas (ex: Ctrl+C)
    public static void SendCombination(params byte[] keys)
    {
        // Pressiona todas
        foreach (byte key in keys)
            KeyDown(key);

        Thread.Sleep(50);

        // Solta todas (ordem inversa)
        for (int i = keys.Length - 1; i >= 0; i--)
            KeyUp(keys[i]);
    }

    // Ctrl+C
    public static void Copy()
    {
        SendCombination(Keys.VK_CONTROL, 0x43); // C
    }

    // Ctrl+V
    public static void Paste()
    {
        SendCombination(Keys.VK_CONTROL, 0x56); // V
    }

    // Ctrl+A
    public static void SelectAll()
    {
        SendCombination(Keys.VK_CONTROL, 0x41); // A
    }

    // Alt+Tab
    public static void SwitchWindow()
    {
        SendCombination(Keys.VK_MENU, Keys.VK_TAB);
    }

    // Alt+F4
    public static void CloseWindow()
    {
        SendCombination(Keys.VK_MENU, Keys.VK_F4);
    }
}
```

## 3. Comunicação Cliente-Servidor

### 3.1 Servidor TCP

```csharp
public class RemoteDesktopServer
{
    private TcpListener listener;
    private bool isRunning;
    private List<TcpClient> clients = new List<TcpClient>();
    private readonly object clientsLock = new object();

    public event EventHandler<string> OnLog;

    public RemoteDesktopServer(int port = 5900)
    {
        listener = new TcpListener(IPAddress.Any, port);
    }

    public void Start()
    {
        isRunning = true;
        listener.Start();
        Log($"Servidor iniciado na porta {((IPEndPoint)listener.LocalEndpoint).Port}");

        // Thread para aceitar conexões
        Task.Run(AcceptClients);
    }

    public void Stop()
    {
        isRunning = false;
        listener.Stop();

        lock (clientsLock)
        {
            foreach (var client in clients)
                client.Close();
            clients.Clear();
        }

        Log("Servidor parado");
    }

    private async Task AcceptClients()
    {
        while (isRunning)
        {
            try
            {
                TcpClient client = await listener.AcceptTcpClientAsync();
                Log($"Cliente conectado: {client.Client.RemoteEndPoint}");

                lock (clientsLock)
                    clients.Add(client);

                _ = Task.Run(() => HandleClient(client));
            }
            catch (Exception ex)
            {
                if (isRunning)
                    Log($"Erro ao aceitar cliente: {ex.Message}");
            }
        }
    }

    private async Task HandleClient(TcpClient client)
    {
        NetworkStream stream = client.GetStream();
        byte[] buffer = new byte[1024];

        // Inicia thread de envio de tela
        var screenTask = Task.Run(() => SendScreenUpdates(client));

        try
        {
            while (client.Connected && isRunning)
            {
                int bytesRead = await stream.ReadAsync(buffer, 0, buffer.Length);
                if (bytesRead == 0) break;

                // Processa comandos recebidos
                ProcessCommand(buffer, bytesRead);
            }
        }
        catch (Exception ex)
        {
            Log($"Erro no cliente: {ex.Message}");
        }
        finally
        {
            lock (clientsLock)
                clients.Remove(client);
            client.Close();
            Log("Cliente desconectado");
        }
    }

    private void SendScreenUpdates(TcpClient client)
    {
        NetworkStream stream = client.GetStream();

        while (client.Connected && isRunning)
        {
            try
            {
                byte[] screenData = ScreenCapture.CaptureScreenAsJpeg(40);

                // Envia tamanho + dados
                byte[] sizeBytes = BitConverter.GetBytes(screenData.Length);
                stream.Write(sizeBytes, 0, 4);
                stream.Write(screenData, 0, screenData.Length);

                Thread.Sleep(100); // ~10 FPS
            }
            catch
            {
                break;
            }
        }
    }

    private void ProcessCommand(byte[] data, int length)
    {
        using (MemoryStream ms = new MemoryStream(data, 0, length))
        using (BinaryReader reader = new BinaryReader(ms))
        {
            byte commandType = reader.ReadByte();

            switch (commandType)
            {
                case 0x01: // Mouse move
                    int mx = reader.ReadInt32();
                    int my = reader.ReadInt32();
                    MouseController.MoveTo(mx, my);
                    break;

                case 0x02: // Mouse click
                    int cx = reader.ReadInt32();
                    int cy = reader.ReadInt32();
                    byte button = reader.ReadByte();
                    if (button == 0)
                        MouseController.LeftClick(cx, cy);
                    else if (button == 1)
                        MouseController.RightClick(cx, cy);
                    else
                        MouseController.MiddleClick(cx, cy);
                    break;

                case 0x03: // Key press
                    byte keyCode = reader.ReadByte();
                    KeyboardController.PressKey(keyCode);
                    break;

                case 0x04: // Type text
                    string text = reader.ReadString();
                    KeyboardController.Type(text);
                    break;

                case 0x05: // Scroll
                    int delta = reader.ReadInt32();
                    MouseController.Scroll(delta);
                    break;
            }
        }
    }

    private void Log(string message)
    {
        OnLog?.Invoke(this, message);
    }
}
```

### 3.2 Cliente TCP

```csharp
public class RemoteDesktopClient
{
    private TcpClient client;
    private NetworkStream stream;
    private bool isConnected;

    public event EventHandler<Bitmap> OnScreenUpdate;
    public event EventHandler<string> OnLog;
    public event EventHandler OnDisconnected;

    public async Task<bool> Connect(string host, int port = 5900)
    {
        try
        {
            client = new TcpClient();
            await client.ConnectAsync(host, port);
            stream = client.GetStream();
            isConnected = true;

            Log($"Conectado a {host}:{port}");

            // Inicia recebimento de tela
            _ = Task.Run(ReceiveScreenUpdates);

            return true;
        }
        catch (Exception ex)
        {
            Log($"Erro ao conectar: {ex.Message}");
            return false;
        }
    }

    public void Disconnect()
    {
        isConnected = false;
        stream?.Close();
        client?.Close();
        OnDisconnected?.Invoke(this, EventArgs.Empty);
        Log("Desconectado");
    }

    private async Task ReceiveScreenUpdates()
    {
        byte[] sizeBuffer = new byte[4];

        while (isConnected && client.Connected)
        {
            try
            {
                // Lê tamanho
                int read = await stream.ReadAsync(sizeBuffer, 0, 4);
                if (read == 0) break;

                int size = BitConverter.ToInt32(sizeBuffer, 0);

                // Lê dados da imagem
                byte[] imageData = new byte[size];
                int totalRead = 0;
                while (totalRead < size)
                {
                    int chunk = await stream.ReadAsync(imageData, totalRead, size - totalRead);
                    if (chunk == 0) break;
                    totalRead += chunk;
                }

                // Converte para Bitmap
                using (MemoryStream ms = new MemoryStream(imageData))
                {
                    Bitmap screen = new Bitmap(ms);
                    OnScreenUpdate?.Invoke(this, screen);
                }
            }
            catch
            {
                break;
            }
        }

        Disconnect();
    }

    // Envia movimento do mouse
    public void SendMouseMove(int x, int y)
    {
        if (!isConnected) return;

        using (MemoryStream ms = new MemoryStream())
        using (BinaryWriter writer = new BinaryWriter(ms))
        {
            writer.Write((byte)0x01);
            writer.Write(x);
            writer.Write(y);
            SendData(ms.ToArray());
        }
    }

    // Envia clique do mouse
    public void SendMouseClick(int x, int y, int button = 0)
    {
        if (!isConnected) return;

        using (MemoryStream ms = new MemoryStream())
        using (BinaryWriter writer = new BinaryWriter(ms))
        {
            writer.Write((byte)0x02);
            writer.Write(x);
            writer.Write(y);
            writer.Write((byte)button);
            SendData(ms.ToArray());
        }
    }

    // Envia tecla
    public void SendKey(byte keyCode)
    {
        if (!isConnected) return;

        using (MemoryStream ms = new MemoryStream())
        using (BinaryWriter writer = new BinaryWriter(ms))
        {
            writer.Write((byte)0x03);
            writer.Write(keyCode);
            SendData(ms.ToArray());
        }
    }

    // Envia texto
    public void SendText(string text)
    {
        if (!isConnected) return;

        using (MemoryStream ms = new MemoryStream())
        using (BinaryWriter writer = new BinaryWriter(ms))
        {
            writer.Write((byte)0x04);
            writer.Write(text);
            SendData(ms.ToArray());
        }
    }

    // Envia scroll
    public void SendScroll(int delta)
    {
        if (!isConnected) return;

        using (MemoryStream ms = new MemoryStream())
        using (BinaryWriter writer = new BinaryWriter(ms))
        {
            writer.Write((byte)0x05);
            writer.Write(delta);
            SendData(ms.ToArray());
        }
    }

    private void SendData(byte[] data)
    {
        try
        {
            stream.Write(data, 0, data.Length);
        }
        catch
        {
            Disconnect();
        }
    }

    private void Log(string message)
    {
        OnLog?.Invoke(this, message);
    }
}
```

## 4. Interface do Cliente (Windows Forms)

### 4.1 Formulário Principal do Cliente

```csharp
public class RemoteDesktopForm : Form
{
    private PictureBox screenBox;
    private RemoteDesktopClient client;
    private float scaleX = 1, scaleY = 1;
    private Size remoteScreenSize;

    public RemoteDesktopForm()
    {
        InitializeComponents();
        SetupClient();
    }

    private void InitializeComponents()
    {
        this.Text = "Remote Desktop";
        this.Size = new Size(1280, 720);
        this.FormBorderStyle = FormBorderStyle.Sizable;
        this.KeyPreview = true;

        screenBox = new PictureBox
        {
            Dock = DockStyle.Fill,
            SizeMode = PictureBoxSizeMode.Zoom,
            BackColor = Color.Black
        };

        screenBox.MouseMove += ScreenBox_MouseMove;
        screenBox.MouseClick += ScreenBox_MouseClick;
        screenBox.MouseDoubleClick += ScreenBox_MouseDoubleClick;
        screenBox.MouseWheel += ScreenBox_MouseWheel;

        this.KeyDown += Form_KeyDown;
        this.KeyPress += Form_KeyPress;

        this.Controls.Add(screenBox);
    }

    private void SetupClient()
    {
        client = new RemoteDesktopClient();

        client.OnScreenUpdate += (s, bitmap) =>
        {
            if (remoteScreenSize.IsEmpty)
            {
                remoteScreenSize = bitmap.Size;
                CalculateScale();
            }

            this.Invoke(new Action(() =>
            {
                screenBox.Image?.Dispose();
                screenBox.Image = bitmap;
            }));
        };

        client.OnDisconnected += (s, e) =>
        {
            this.Invoke(new Action(() =>
            {
                MessageBox.Show("Desconectado do servidor");
            }));
        };
    }

    public async Task Connect(string host, int port)
    {
        await client.Connect(host, port);
    }

    private void CalculateScale()
    {
        if (screenBox.Image == null) return;

        scaleX = (float)remoteScreenSize.Width / screenBox.Width;
        scaleY = (float)remoteScreenSize.Height / screenBox.Height;
    }

    protected override void OnResize(EventArgs e)
    {
        base.OnResize(e);
        CalculateScale();
    }

    private Point GetRemotePoint(Point localPoint)
    {
        // Converte coordenada local para remota
        int remoteX = (int)(localPoint.X * scaleX);
        int remoteY = (int)(localPoint.Y * scaleY);
        return new Point(remoteX, remoteY);
    }

    private void ScreenBox_MouseMove(object sender, MouseEventArgs e)
    {
        Point remote = GetRemotePoint(e.Location);
        client.SendMouseMove(remote.X, remote.Y);
    }

    private void ScreenBox_MouseClick(object sender, MouseEventArgs e)
    {
        Point remote = GetRemotePoint(e.Location);
        int button = e.Button == MouseButtons.Left ? 0 :
                     e.Button == MouseButtons.Right ? 1 : 2;
        client.SendMouseClick(remote.X, remote.Y, button);
    }

    private void ScreenBox_MouseDoubleClick(object sender, MouseEventArgs e)
    {
        Point remote = GetRemotePoint(e.Location);
        client.SendMouseClick(remote.X, remote.Y, 0);
        client.SendMouseClick(remote.X, remote.Y, 0);
    }

    private void ScreenBox_MouseWheel(object sender, MouseEventArgs e)
    {
        client.SendScroll(e.Delta);
    }

    private void Form_KeyDown(object sender, KeyEventArgs e)
    {
        // Teclas especiais
        if (e.KeyCode == System.Windows.Forms.Keys.F1)
            client.SendKey(0x70);
        else if (e.KeyCode == System.Windows.Forms.Keys.Escape)
            client.SendKey(0x1B);
        else if (e.KeyCode == System.Windows.Forms.Keys.Delete)
            client.SendKey(0x2E);
        else if (e.KeyCode == System.Windows.Forms.Keys.Back)
            client.SendKey(0x08);
        else if (e.KeyCode == System.Windows.Forms.Keys.Tab)
            client.SendKey(0x09);
        else if (e.KeyCode == System.Windows.Forms.Keys.Enter)
            client.SendKey(0x0D);
    }

    private void Form_KeyPress(object sender, KeyPressEventArgs e)
    {
        // Caracteres normais
        if (!char.IsControl(e.KeyChar))
        {
            client.SendText(e.KeyChar.ToString());
        }
    }

    protected override void OnFormClosed(FormClosedEventArgs e)
    {
        client.Disconnect();
        base.OnFormClosed(e);
    }
}
```

## 5. Criptografia e Segurança

### 5.1 Criptografia AES

```csharp
public class AesCrypto
{
    private readonly byte[] key;
    private readonly byte[] iv;

    public AesCrypto(string password)
    {
        // Deriva chave da senha
        using (var sha256 = System.Security.Cryptography.SHA256.Create())
        {
            key = sha256.ComputeHash(Encoding.UTF8.GetBytes(password));
            iv = sha256.ComputeHash(Encoding.UTF8.GetBytes(password + "IV")).Take(16).ToArray();
        }
    }

    public byte[] Encrypt(byte[] data)
    {
        using (var aes = System.Security.Cryptography.Aes.Create())
        {
            aes.Key = key;
            aes.IV = iv;
            aes.Mode = System.Security.Cryptography.CipherMode.CBC;
            aes.Padding = System.Security.Cryptography.PaddingMode.PKCS7;

            using (var encryptor = aes.CreateEncryptor())
            using (var ms = new MemoryStream())
            using (var cs = new System.Security.Cryptography.CryptoStream(
                ms, encryptor, System.Security.Cryptography.CryptoStreamMode.Write))
            {
                cs.Write(data, 0, data.Length);
                cs.FlushFinalBlock();
                return ms.ToArray();
            }
        }
    }

    public byte[] Decrypt(byte[] data)
    {
        using (var aes = System.Security.Cryptography.Aes.Create())
        {
            aes.Key = key;
            aes.IV = iv;
            aes.Mode = System.Security.Cryptography.CipherMode.CBC;
            aes.Padding = System.Security.Cryptography.PaddingMode.PKCS7;

            using (var decryptor = aes.CreateDecryptor())
            using (var ms = new MemoryStream(data))
            using (var cs = new System.Security.Cryptography.CryptoStream(
                ms, decryptor, System.Security.Cryptography.CryptoStreamMode.Read))
            using (var output = new MemoryStream())
            {
                cs.CopyTo(output);
                return output.ToArray();
            }
        }
    }
}
```

### 5.2 Autenticação

```csharp
public class Authentication
{
    private readonly Dictionary<string, string> users = new Dictionary<string, string>();

    public void AddUser(string username, string password)
    {
        string hash = HashPassword(password);
        users[username] = hash;
    }

    public bool ValidateUser(string username, string password)
    {
        if (!users.ContainsKey(username))
            return false;

        string hash = HashPassword(password);
        return users[username] == hash;
    }

    private string HashPassword(string password)
    {
        using (var sha256 = System.Security.Cryptography.SHA256.Create())
        {
            byte[] bytes = sha256.ComputeHash(Encoding.UTF8.GetBytes(password + "SALT123"));
            return Convert.ToBase64String(bytes);
        }
    }

    // Gera token de sessão
    public string GenerateToken()
    {
        byte[] tokenBytes = new byte[32];
        using (var rng = System.Security.Cryptography.RandomNumberGenerator.Create())
        {
            rng.GetBytes(tokenBytes);
        }
        return Convert.ToBase64String(tokenBytes);
    }
}
```

## 6. Compressão de Dados

### 6.1 Compressão GZip

```csharp
public static class Compression
{
    public static byte[] Compress(byte[] data)
    {
        using (var output = new MemoryStream())
        {
            using (var gzip = new System.IO.Compression.GZipStream(
                output, System.IO.Compression.CompressionLevel.Fastest))
            {
                gzip.Write(data, 0, data.Length);
            }
            return output.ToArray();
        }
    }

    public static byte[] Decompress(byte[] data)
    {
        using (var input = new MemoryStream(data))
        using (var gzip = new System.IO.Compression.GZipStream(
            input, System.IO.Compression.CompressionMode.Decompress))
        using (var output = new MemoryStream())
        {
            gzip.CopyTo(output);
            return output.ToArray();
        }
    }
}
```

## 7. Transferência de Arquivos

### 7.1 Classe de Transferência

```csharp
public class FileTransfer
{
    private readonly NetworkStream stream;
    private readonly int bufferSize = 65536; // 64KB

    public FileTransfer(NetworkStream stream)
    {
        this.stream = stream;
    }

    // Envia arquivo
    public async Task SendFile(string filePath, IProgress<double> progress = null)
    {
        FileInfo fileInfo = new FileInfo(filePath);

        using (BinaryWriter writer = new BinaryWriter(stream, Encoding.UTF8, true))
        {
            // Envia nome e tamanho
            writer.Write(fileInfo.Name);
            writer.Write(fileInfo.Length);
        }

        // Envia conteúdo
        using (FileStream fs = File.OpenRead(filePath))
        {
            byte[] buffer = new byte[bufferSize];
            long totalSent = 0;
            int bytesRead;

            while ((bytesRead = await fs.ReadAsync(buffer, 0, buffer.Length)) > 0)
            {
                await stream.WriteAsync(buffer, 0, bytesRead);
                totalSent += bytesRead;
                progress?.Report((double)totalSent / fileInfo.Length * 100);
            }
        }
    }

    // Recebe arquivo
    public async Task<string> ReceiveFile(string destinationFolder, IProgress<double> progress = null)
    {
        using (BinaryReader reader = new BinaryReader(stream, Encoding.UTF8, true))
        {
            // Lê nome e tamanho
            string fileName = reader.ReadString();
            long fileSize = reader.ReadInt64();

            string filePath = Path.Combine(destinationFolder, fileName);

            // Recebe conteúdo
            using (FileStream fs = File.Create(filePath))
            {
                byte[] buffer = new byte[bufferSize];
                long totalReceived = 0;

                while (totalReceived < fileSize)
                {
                    int toRead = (int)Math.Min(buffer.Length, fileSize - totalReceived);
                    int bytesRead = await stream.ReadAsync(buffer, 0, toRead);

                    if (bytesRead == 0) break;

                    await fs.WriteAsync(buffer, 0, bytesRead);
                    totalReceived += bytesRead;
                    progress?.Report((double)totalReceived / fileSize * 100);
                }
            }

            return filePath;
        }
    }
}
```

## 8. Projeto Completo - Exemplo

### 8.1 Program.cs (Servidor)

```csharp
using System;

class Program
{
    static void Main(string[] args)
    {
        Console.WriteLine("=== Remote Desktop Server ===");
        Console.Write("Porta (padrão 5900): ");
        string portInput = Console.ReadLine();
        int port = string.IsNullOrEmpty(portInput) ? 5900 : int.Parse(portInput);

        var server = new RemoteDesktopServer(port);
        server.OnLog += (s, msg) => Console.WriteLine($"[LOG] {msg}");

        server.Start();

        Console.WriteLine("Pressione ENTER para parar...");
        Console.ReadLine();

        server.Stop();
    }
}
```

### 8.2 Program.cs (Cliente)

```csharp
using System;
using System.Windows.Forms;

class Program
{
    [STAThread]
    static async Task Main(string[] args)
    {
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);

        // Diálogo de conexão
        string host = Microsoft.VisualBasic.Interaction.InputBox(
            "Digite o IP do servidor:", "Conectar", "127.0.0.1");

        if (string.IsNullOrEmpty(host)) return;

        var form = new RemoteDesktopForm();

        try
        {
            await form.Connect(host, 5900);
            Application.Run(form);
        }
        catch (Exception ex)
        {
            MessageBox.Show($"Erro: {ex.Message}");
        }
    }
}
```

## 9. Dicas de Otimização

### 9.1 Performance

1. **Captura de tela**: Use DirectX ou DXGI para captura mais rápida
2. **Compressão**: JPEG para velocidade, PNG para qualidade
3. **Diferencial**: Envie apenas regiões alteradas
4. **Threading**: Use async/await e ThreadPool
5. **Buffer**: Use buffers de tamanho adequado (64KB+)

### 9.2 Segurança

1. **Sempre use criptografia** (AES-256)
2. **Autenticação obrigatória** com hash de senha
3. **Tokens de sessão** com expiração
4. **Limite de tentativas** de login
5. **Log de conexões** e ações

### 9.3 Recursos Avançados

1. **Áudio remoto**: Use NAudio ou WASAPI
2. **Clipboard compartilhado**: IDataObject
3. **Multi-monitor**: Screen.AllScreens
4. **Qualidade adaptativa**: Ajusta compressão pela banda

## 10. Bibliotecas Úteis

- **SharpDX** - DirectX para C# (captura rápida)
- **NAudio** - Áudio
- **OpenCV** - Processamento de imagem
- **WebSocket4Net** - WebSocket
- **LiteDB** - Banco de dados local
- **Newtonsoft.Json** - JSON
