# Networking e Sockets em C# - Guia Completo

## 1. TCP/IP Básico

### 1.1 TcpListener (Servidor)

```csharp
using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading.Tasks;

public class TcpServerExample
{
    private TcpListener listener;
    private bool running;

    public async Task Start(int port)
    {
        listener = new TcpListener(IPAddress.Any, port);
        listener.Start();
        running = true;

        Console.WriteLine($"Servidor TCP iniciado na porta {port}");

        while (running)
        {
            try
            {
                TcpClient client = await listener.AcceptTcpClientAsync();
                Console.WriteLine($"Cliente conectado: {client.Client.RemoteEndPoint}");

                // Processa cliente em thread separada
                _ = Task.Run(() => HandleClient(client));
            }
            catch (Exception ex)
            {
                if (running)
                    Console.WriteLine($"Erro: {ex.Message}");
            }
        }
    }

    private async Task HandleClient(TcpClient client)
    {
        NetworkStream stream = client.GetStream();
        byte[] buffer = new byte[4096];

        try
        {
            while (client.Connected)
            {
                int bytesRead = await stream.ReadAsync(buffer, 0, buffer.Length);
                if (bytesRead == 0) break;

                string mensagem = Encoding.UTF8.GetString(buffer, 0, bytesRead);
                Console.WriteLine($"Recebido: {mensagem}");

                // Echo - envia de volta
                byte[] response = Encoding.UTF8.GetBytes($"Echo: {mensagem}");
                await stream.WriteAsync(response, 0, response.Length);
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Erro no cliente: {ex.Message}");
        }
        finally
        {
            client.Close();
            Console.WriteLine("Cliente desconectado");
        }
    }

    public void Stop()
    {
        running = false;
        listener?.Stop();
    }
}
```

### 1.2 TcpClient (Cliente)

```csharp
public class TcpClientExample
{
    private TcpClient client;
    private NetworkStream stream;

    public async Task<bool> Connect(string host, int port)
    {
        try
        {
            client = new TcpClient();
            await client.ConnectAsync(host, port);
            stream = client.GetStream();
            Console.WriteLine($"Conectado a {host}:{port}");
            return true;
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Erro ao conectar: {ex.Message}");
            return false;
        }
    }

    public async Task<string> SendAndReceive(string mensagem)
    {
        byte[] data = Encoding.UTF8.GetBytes(mensagem);
        await stream.WriteAsync(data, 0, data.Length);

        byte[] buffer = new byte[4096];
        int bytesRead = await stream.ReadAsync(buffer, 0, buffer.Length);

        return Encoding.UTF8.GetString(buffer, 0, bytesRead);
    }

    public void Disconnect()
    {
        stream?.Close();
        client?.Close();
    }
}

// Uso
var cliente = new TcpClientExample();
await cliente.Connect("127.0.0.1", 8080);
string resposta = await cliente.SendAndReceive("Olá servidor!");
Console.WriteLine(resposta);
cliente.Disconnect();
```

## 2. UDP

### 2.1 UdpClient (Servidor e Cliente)

```csharp
public class UdpServerExample
{
    private UdpClient udp;
    private bool running;

    public async Task Start(int port)
    {
        udp = new UdpClient(port);
        running = true;
        Console.WriteLine($"Servidor UDP iniciado na porta {port}");

        while (running)
        {
            try
            {
                UdpReceiveResult result = await udp.ReceiveAsync();
                string mensagem = Encoding.UTF8.GetString(result.Buffer);
                Console.WriteLine($"Recebido de {result.RemoteEndPoint}: {mensagem}");

                // Responde
                byte[] response = Encoding.UTF8.GetBytes($"Echo: {mensagem}");
                await udp.SendAsync(response, response.Length, result.RemoteEndPoint);
            }
            catch (Exception ex)
            {
                if (running)
                    Console.WriteLine($"Erro: {ex.Message}");
            }
        }
    }

    public void Stop()
    {
        running = false;
        udp?.Close();
    }
}

public class UdpClientExample
{
    public async Task Send(string host, int port, string mensagem)
    {
        using var udp = new UdpClient();

        byte[] data = Encoding.UTF8.GetBytes(mensagem);
        await udp.SendAsync(data, data.Length, host, port);

        // Recebe resposta (com timeout)
        udp.Client.ReceiveTimeout = 5000;
        IPEndPoint remoteEP = null;
        byte[] response = udp.Receive(ref remoteEP);

        Console.WriteLine($"Resposta: {Encoding.UTF8.GetString(response)}");
    }
}
```

## 3. Sockets de Baixo Nível

### 3.1 Socket TCP

```csharp
public class RawSocketServer
{
    public async Task Start(int port)
    {
        Socket serverSocket = new Socket(
            AddressFamily.InterNetwork,
            SocketType.Stream,
            ProtocolType.Tcp);

        serverSocket.Bind(new IPEndPoint(IPAddress.Any, port));
        serverSocket.Listen(10); // Backlog de 10 conexões

        Console.WriteLine($"Socket TCP escutando na porta {port}");

        while (true)
        {
            Socket clientSocket = await serverSocket.AcceptAsync();
            Console.WriteLine($"Conexão aceita: {clientSocket.RemoteEndPoint}");

            _ = Task.Run(() => HandleSocket(clientSocket));
        }
    }

    private async Task HandleSocket(Socket socket)
    {
        byte[] buffer = new byte[4096];

        try
        {
            while (socket.Connected)
            {
                int received = await socket.ReceiveAsync(buffer, SocketFlags.None);
                if (received == 0) break;

                // Echo
                await socket.SendAsync(buffer.AsMemory(0, received), SocketFlags.None);
            }
        }
        finally
        {
            socket.Shutdown(SocketShutdown.Both);
            socket.Close();
        }
    }
}
```

### 3.2 Socket com Options

```csharp
public Socket CreateConfiguredSocket()
{
    Socket socket = new Socket(
        AddressFamily.InterNetwork,
        SocketType.Stream,
        ProtocolType.Tcp);

    // Configurações
    socket.SetSocketOption(SocketOptionLevel.Socket, SocketOptionName.ReuseAddress, true);
    socket.SetSocketOption(SocketOptionLevel.Socket, SocketOptionName.KeepAlive, true);
    socket.SetSocketOption(SocketOptionLevel.Tcp, SocketOptionName.NoDelay, true);

    // Timeouts
    socket.SendTimeout = 5000;
    socket.ReceiveTimeout = 5000;

    // Buffer sizes
    socket.SendBufferSize = 65536;
    socket.ReceiveBufferSize = 65536;

    // Linger (espera enviar dados antes de fechar)
    socket.LingerState = new LingerOption(true, 10);

    return socket;
}
```

## 4. Protocolos de Aplicação

### 4.1 Protocolo Customizado com Header

```csharp
public class ProtocoloCustomizado
{
    // Estrutura: [4 bytes tamanho][1 byte tipo][N bytes dados]

    public enum TipoMensagem : byte
    {
        Texto = 0x01,
        Binario = 0x02,
        Comando = 0x03,
        Resposta = 0x04
    }

    public class Mensagem
    {
        public TipoMensagem Tipo { get; set; }
        public byte[] Dados { get; set; }
    }

    public static byte[] Serializar(Mensagem msg)
    {
        using var ms = new MemoryStream();
        using var writer = new BinaryWriter(ms);

        writer.Write(msg.Dados.Length);
        writer.Write((byte)msg.Tipo);
        writer.Write(msg.Dados);

        return ms.ToArray();
    }

    public static async Task<Mensagem> Deserializar(NetworkStream stream)
    {
        // Lê header
        byte[] header = new byte[5];
        await stream.ReadAsync(header, 0, 5);

        int tamanho = BitConverter.ToInt32(header, 0);
        TipoMensagem tipo = (TipoMensagem)header[4];

        // Lê dados
        byte[] dados = new byte[tamanho];
        int totalLido = 0;
        while (totalLido < tamanho)
        {
            int lido = await stream.ReadAsync(dados, totalLido, tamanho - totalLido);
            if (lido == 0) throw new Exception("Conexão fechada");
            totalLido += lido;
        }

        return new Mensagem { Tipo = tipo, Dados = dados };
    }
}
```

### 4.2 Servidor com Protocolo

```csharp
public class ServidorComProtocolo
{
    public async Task HandleClient(TcpClient client)
    {
        NetworkStream stream = client.GetStream();

        while (client.Connected)
        {
            var mensagem = await ProtocoloCustomizado.Deserializar(stream);

            switch (mensagem.Tipo)
            {
                case ProtocoloCustomizado.TipoMensagem.Texto:
                    string texto = Encoding.UTF8.GetString(mensagem.Dados);
                    Console.WriteLine($"Texto: {texto}");
                    break;

                case ProtocoloCustomizado.TipoMensagem.Comando:
                    ProcessarComando(mensagem.Dados);
                    break;
            }

            // Envia resposta
            var resposta = new ProtocoloCustomizado.Mensagem
            {
                Tipo = ProtocoloCustomizado.TipoMensagem.Resposta,
                Dados = Encoding.UTF8.GetBytes("OK")
            };
            byte[] dados = ProtocoloCustomizado.Serializar(resposta);
            await stream.WriteAsync(dados, 0, dados.Length);
        }
    }

    private void ProcessarComando(byte[] dados)
    {
        // Processa comando
    }
}
```

## 5. HTTP Client

### 5.1 HttpClient Básico

```csharp
public class HttpClientExample
{
    private readonly HttpClient client;

    public HttpClientExample()
    {
        // HttpClient deve ser reutilizado
        client = new HttpClient
        {
            BaseAddress = new Uri("https://api.exemplo.com"),
            Timeout = TimeSpan.FromSeconds(30)
        };
        client.DefaultRequestHeaders.Add("User-Agent", "MeuApp/1.0");
    }

    // GET
    public async Task<string> Get(string url)
    {
        HttpResponseMessage response = await client.GetAsync(url);
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadAsStringAsync();
    }

    // POST JSON
    public async Task<string> PostJson<T>(string url, T dados)
    {
        string json = System.Text.Json.JsonSerializer.Serialize(dados);
        var content = new StringContent(json, Encoding.UTF8, "application/json");

        HttpResponseMessage response = await client.PostAsync(url, content);
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadAsStringAsync();
    }

    // POST Form
    public async Task<string> PostForm(string url, Dictionary<string, string> form)
    {
        var content = new FormUrlEncodedContent(form);
        HttpResponseMessage response = await client.PostAsync(url, content);
        return await response.Content.ReadAsStringAsync();
    }

    // Download arquivo
    public async Task DownloadFile(string url, string destino)
    {
        using var response = await client.GetAsync(url);
        response.EnsureSuccessStatusCode();

        using var fs = File.Create(destino);
        await response.Content.CopyToAsync(fs);
    }

    // Upload arquivo
    public async Task<string> UploadFile(string url, string arquivo)
    {
        using var form = new MultipartFormDataContent();
        using var fs = File.OpenRead(arquivo);
        using var streamContent = new StreamContent(fs);

        form.Add(streamContent, "file", Path.GetFileName(arquivo));

        HttpResponseMessage response = await client.PostAsync(url, form);
        return await response.Content.ReadAsStringAsync();
    }
}
```

### 5.2 HttpClient com Retry e Timeout

```csharp
public class ResilientHttpClient
{
    private readonly HttpClient client;
    private readonly int maxRetries = 3;

    public ResilientHttpClient()
    {
        var handler = new SocketsHttpHandler
        {
            PooledConnectionLifetime = TimeSpan.FromMinutes(2),
            PooledConnectionIdleTimeout = TimeSpan.FromMinutes(1),
            MaxConnectionsPerServer = 10
        };

        client = new HttpClient(handler)
        {
            Timeout = TimeSpan.FromSeconds(30)
        };
    }

    public async Task<string> GetWithRetry(string url)
    {
        Exception lastException = null;

        for (int i = 0; i < maxRetries; i++)
        {
            try
            {
                return await client.GetStringAsync(url);
            }
            catch (HttpRequestException ex)
            {
                lastException = ex;
                await Task.Delay(TimeSpan.FromSeconds(Math.Pow(2, i))); // Exponential backoff
            }
        }

        throw lastException;
    }
}
```

## 6. WebSocket

### 6.1 WebSocket Cliente

```csharp
using System.Net.WebSockets;

public class WebSocketClientExample
{
    private ClientWebSocket socket;
    private CancellationTokenSource cts;

    public event Action<string> OnMessage;
    public event Action OnDisconnected;

    public async Task Connect(string url)
    {
        socket = new ClientWebSocket();
        cts = new CancellationTokenSource();

        await socket.ConnectAsync(new Uri(url), cts.Token);
        Console.WriteLine("WebSocket conectado");

        _ = Task.Run(ReceiveLoop);
    }

    private async Task ReceiveLoop()
    {
        var buffer = new byte[4096];

        while (socket.State == WebSocketState.Open)
        {
            try
            {
                var result = await socket.ReceiveAsync(buffer, cts.Token);

                if (result.MessageType == WebSocketMessageType.Close)
                {
                    await socket.CloseAsync(WebSocketCloseStatus.NormalClosure, "", cts.Token);
                    OnDisconnected?.Invoke();
                    break;
                }

                string mensagem = Encoding.UTF8.GetString(buffer, 0, result.Count);
                OnMessage?.Invoke(mensagem);
            }
            catch
            {
                OnDisconnected?.Invoke();
                break;
            }
        }
    }

    public async Task Send(string mensagem)
    {
        byte[] data = Encoding.UTF8.GetBytes(mensagem);
        await socket.SendAsync(data, WebSocketMessageType.Text, true, cts.Token);
    }

    public async Task Disconnect()
    {
        cts.Cancel();
        if (socket.State == WebSocketState.Open)
        {
            await socket.CloseAsync(WebSocketCloseStatus.NormalClosure, "", CancellationToken.None);
        }
        socket.Dispose();
    }
}
```

### 6.2 WebSocket Servidor (ASP.NET Core)

```csharp
// Em Startup.cs ou Program.cs
app.UseWebSockets();

app.Map("/ws", async context =>
{
    if (context.WebSockets.IsWebSocketRequest)
    {
        WebSocket ws = await context.WebSockets.AcceptWebSocketAsync();
        await HandleWebSocket(ws);
    }
    else
    {
        context.Response.StatusCode = 400;
    }
});

async Task HandleWebSocket(WebSocket ws)
{
    var buffer = new byte[4096];

    while (ws.State == WebSocketState.Open)
    {
        var result = await ws.ReceiveAsync(buffer, CancellationToken.None);

        if (result.MessageType == WebSocketMessageType.Close)
        {
            await ws.CloseAsync(WebSocketCloseStatus.NormalClosure, "", CancellationToken.None);
            break;
        }

        // Echo
        await ws.SendAsync(buffer.AsMemory(0, result.Count),
            result.MessageType, result.EndOfMessage, CancellationToken.None);
    }
}
```

## 7. SSL/TLS

### 7.1 TCP com SSL

```csharp
using System.Net.Security;
using System.Security.Cryptography.X509Certificates;

public class SslServer
{
    public async Task Start(int port, string certPath, string certPassword)
    {
        var cert = new X509Certificate2(certPath, certPassword);
        var listener = new TcpListener(IPAddress.Any, port);
        listener.Start();

        while (true)
        {
            TcpClient client = await listener.AcceptTcpClientAsync();
            _ = Task.Run(() => HandleSecureClient(client, cert));
        }
    }

    private async Task HandleSecureClient(TcpClient client, X509Certificate2 cert)
    {
        var sslStream = new SslStream(client.GetStream(), false);

        try
        {
            await sslStream.AuthenticateAsServerAsync(cert);

            // Agora pode usar sslStream para comunicação segura
            byte[] buffer = new byte[4096];
            int read = await sslStream.ReadAsync(buffer, 0, buffer.Length);

            string mensagem = Encoding.UTF8.GetString(buffer, 0, read);
            Console.WriteLine($"Recebido (SSL): {mensagem}");
        }
        finally
        {
            sslStream.Close();
            client.Close();
        }
    }
}

public class SslClient
{
    public async Task Connect(string host, int port)
    {
        var client = new TcpClient();
        await client.ConnectAsync(host, port);

        var sslStream = new SslStream(
            client.GetStream(),
            false,
            ValidateServerCertificate);

        await sslStream.AuthenticateAsClientAsync(host);

        // Envia dados
        byte[] data = Encoding.UTF8.GetBytes("Olá seguro!");
        await sslStream.WriteAsync(data, 0, data.Length);
    }

    private bool ValidateServerCertificate(
        object sender,
        X509Certificate certificate,
        X509Chain chain,
        SslPolicyErrors errors)
    {
        // Em produção, valide corretamente!
        return true;
    }
}
```

## 8. DNS e Resolução de Nomes

```csharp
using System.Net;

public class DnsExample
{
    public static async Task ResolverNome(string hostname)
    {
        // Resolve hostname para IPs
        IPAddress[] addresses = await Dns.GetHostAddressesAsync(hostname);

        foreach (var ip in addresses)
        {
            Console.WriteLine($"{hostname} -> {ip}");
        }

        // Resolve IP para hostname
        IPHostEntry entry = await Dns.GetHostEntryAsync(addresses[0]);
        Console.WriteLine($"Hostname: {entry.HostName}");

        // Aliases
        foreach (string alias in entry.Aliases)
        {
            Console.WriteLine($"Alias: {alias}");
        }
    }

    public static string GetLocalIP()
    {
        string hostName = Dns.GetHostName();
        IPHostEntry host = Dns.GetHostEntry(hostName);

        foreach (IPAddress ip in host.AddressList)
        {
            if (ip.AddressFamily == AddressFamily.InterNetwork)
            {
                return ip.ToString();
            }
        }

        return "127.0.0.1";
    }
}
```

## 9. Multicast UDP

```csharp
public class MulticastExample
{
    private const string MulticastGroup = "239.0.0.1";
    private const int Port = 5000;

    public async Task SendMulticast(string mensagem)
    {
        using var client = new UdpClient();
        var endpoint = new IPEndPoint(IPAddress.Parse(MulticastGroup), Port);

        byte[] data = Encoding.UTF8.GetBytes(mensagem);
        await client.SendAsync(data, data.Length, endpoint);
    }

    public async Task ReceiveMulticast()
    {
        using var client = new UdpClient(Port);
        client.JoinMulticastGroup(IPAddress.Parse(MulticastGroup));

        Console.WriteLine($"Escutando multicast em {MulticastGroup}:{Port}");

        while (true)
        {
            UdpReceiveResult result = await client.ReceiveAsync();
            string mensagem = Encoding.UTF8.GetString(result.Buffer);
            Console.WriteLine($"Multicast de {result.RemoteEndPoint}: {mensagem}");
        }
    }
}
```

## 10. Network Information

```csharp
using System.Net.NetworkInformation;

public class NetworkInfoExample
{
    public static void ListarInterfaces()
    {
        foreach (NetworkInterface ni in NetworkInterface.GetAllNetworkInterfaces())
        {
            Console.WriteLine($"Nome: {ni.Name}");
            Console.WriteLine($"  Descrição: {ni.Description}");
            Console.WriteLine($"  Tipo: {ni.NetworkInterfaceType}");
            Console.WriteLine($"  Status: {ni.OperationalStatus}");
            Console.WriteLine($"  MAC: {ni.GetPhysicalAddress()}");
            Console.WriteLine($"  Velocidade: {ni.Speed / 1000000} Mbps");

            IPInterfaceProperties props = ni.GetIPProperties();
            foreach (UnicastIPAddressInformation ip in props.UnicastAddresses)
            {
                Console.WriteLine($"  IP: {ip.Address}");
            }
            Console.WriteLine();
        }
    }

    public static async Task<bool> PingHost(string host)
    {
        using var ping = new Ping();
        PingReply reply = await ping.SendPingAsync(host, 1000);

        Console.WriteLine($"Ping {host}: {reply.Status}, {reply.RoundtripTime}ms");
        return reply.Status == IPStatus.Success;
    }

    public static void MonitorarConexao()
    {
        NetworkChange.NetworkAvailabilityChanged += (s, e) =>
        {
            Console.WriteLine($"Rede disponível: {e.IsAvailable}");
        };

        NetworkChange.NetworkAddressChanged += (s, e) =>
        {
            Console.WriteLine("Endereço de rede mudou");
        };
    }
}
```

Este guia cobre os principais conceitos de networking em C#, essenciais para desenvolvimento de aplicações de acesso remoto!
