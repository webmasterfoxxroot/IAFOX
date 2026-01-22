# Multithreading e Paralelismo Avançado em C#

## 1. Threads de Baixo Nível

### 1.1 Criação e Gerenciamento de Threads

```csharp
using System;
using System.Threading;

public class ThreadBasico
{
    // Criar thread simples
    public void CriarThread()
    {
        Thread thread = new Thread(() =>
        {
            for (int i = 0; i < 10; i++)
            {
                Console.WriteLine($"Thread: {i}");
                Thread.Sleep(100);
            }
        });

        thread.Name = "MinhaThread";
        thread.Priority = ThreadPriority.Normal;
        thread.IsBackground = true; // Não impede app de fechar

        thread.Start();
        thread.Join(); // Espera thread terminar
    }

    // Thread com parâmetros
    public void ThreadComParametros()
    {
        Thread thread = new Thread(ProcessarDados);
        thread.Start(new { Id = 1, Nome = "Teste" });
    }

    private void ProcessarDados(object dados)
    {
        dynamic d = dados;
        Console.WriteLine($"Processando: {d.Id} - {d.Nome}");
    }

    // Thread com retorno (usando closure)
    public int ThreadComRetorno()
    {
        int resultado = 0;
        Thread thread = new Thread(() =>
        {
            resultado = CalculoComplexo();
        });

        thread.Start();
        thread.Join();
        return resultado;
    }

    private int CalculoComplexo() => 42;
}
```

### 1.2 ThreadPool

```csharp
public class ThreadPoolExemplo
{
    public void UsarThreadPool()
    {
        // Enfileira trabalho no pool
        ThreadPool.QueueUserWorkItem(state =>
        {
            Console.WriteLine($"Executando no ThreadPool: {Thread.CurrentThread.ManagedThreadId}");
        });

        // Com parâmetro
        ThreadPool.QueueUserWorkItem(ProcessarItem, "dados");

        // Configurar pool
        ThreadPool.GetMinThreads(out int workerMin, out int ioMin);
        ThreadPool.GetMaxThreads(out int workerMax, out int ioMax);

        ThreadPool.SetMinThreads(4, 4);
        ThreadPool.SetMaxThreads(100, 100);
    }

    private void ProcessarItem(object state)
    {
        string dados = (string)state;
        Console.WriteLine($"Processando: {dados}");
    }

    // Aguardar conclusão com ManualResetEvent
    public void AguardarConclusao()
    {
        int pendentes = 5;
        ManualResetEvent concluido = new ManualResetEvent(false);

        for (int i = 0; i < 5; i++)
        {
            int id = i;
            ThreadPool.QueueUserWorkItem(_ =>
            {
                Console.WriteLine($"Tarefa {id} executando");
                Thread.Sleep(100);

                if (Interlocked.Decrement(ref pendentes) == 0)
                    concluido.Set();
            });
        }

        concluido.WaitOne(); // Espera todas terminarem
        Console.WriteLine("Todas as tarefas concluídas!");
    }
}
```

## 2. Sincronização

### 2.1 Lock e Monitor

```csharp
public class SincronizacaoBasica
{
    private readonly object _lock = new object();
    private int _contador = 0;

    // Lock básico
    public void Incrementar()
    {
        lock (_lock)
        {
            _contador++;
        }
    }

    // Monitor com timeout
    public bool IncrementarComTimeout(int timeoutMs)
    {
        bool lockTaken = false;
        try
        {
            Monitor.TryEnter(_lock, timeoutMs, ref lockTaken);
            if (lockTaken)
            {
                _contador++;
                return true;
            }
            return false;
        }
        finally
        {
            if (lockTaken)
                Monitor.Exit(_lock);
        }
    }

    // Monitor com Wait/Pulse (produtor-consumidor)
    private Queue<int> _fila = new Queue<int>();
    private const int MaxSize = 10;

    public void Produzir(int item)
    {
        lock (_lock)
        {
            while (_fila.Count >= MaxSize)
                Monitor.Wait(_lock); // Espera espaço

            _fila.Enqueue(item);
            Monitor.PulseAll(_lock); // Notifica consumidores
        }
    }

    public int Consumir()
    {
        lock (_lock)
        {
            while (_fila.Count == 0)
                Monitor.Wait(_lock); // Espera item

            int item = _fila.Dequeue();
            Monitor.PulseAll(_lock); // Notifica produtores
            return item;
        }
    }
}
```

### 2.2 Mutex, Semaphore e outros

```csharp
public class SincronizacaoAvancada
{
    // Mutex - sincronização entre processos
    public void UsarMutex()
    {
        // Mutex nomeado (sistema todo)
        using var mutex = new Mutex(false, "Global\\MeuAppMutex");

        if (mutex.WaitOne(1000))
        {
            try
            {
                Console.WriteLine("Região crítica");
            }
            finally
            {
                mutex.ReleaseMutex();
            }
        }
        else
        {
            Console.WriteLine("Outra instância já está executando");
        }
    }

    // Semaphore - limita número de acessos simultâneos
    private SemaphoreSlim _semaphore = new SemaphoreSlim(3, 3); // Max 3

    public async Task AcessarRecursoLimitado()
    {
        await _semaphore.WaitAsync();
        try
        {
            Console.WriteLine($"Acessando recurso. Disponíveis: {_semaphore.CurrentCount}");
            await Task.Delay(1000);
        }
        finally
        {
            _semaphore.Release();
        }
    }

    // ReaderWriterLockSlim - múltiplos leitores, um escritor
    private ReaderWriterLockSlim _rwLock = new ReaderWriterLockSlim();
    private Dictionary<string, string> _cache = new Dictionary<string, string>();

    public string Ler(string chave)
    {
        _rwLock.EnterReadLock();
        try
        {
            return _cache.TryGetValue(chave, out var valor) ? valor : null;
        }
        finally
        {
            _rwLock.ExitReadLock();
        }
    }

    public void Escrever(string chave, string valor)
    {
        _rwLock.EnterWriteLock();
        try
        {
            _cache[chave] = valor;
        }
        finally
        {
            _rwLock.ExitWriteLock();
        }
    }

    // Atualização com upgrade de lock
    public void AtualizarSeNecessario(string chave, Func<string, string> transformar)
    {
        _rwLock.EnterUpgradeableReadLock();
        try
        {
            if (_cache.TryGetValue(chave, out var valor))
            {
                string novoValor = transformar(valor);
                if (novoValor != valor)
                {
                    _rwLock.EnterWriteLock();
                    try
                    {
                        _cache[chave] = novoValor;
                    }
                    finally
                    {
                        _rwLock.ExitWriteLock();
                    }
                }
            }
        }
        finally
        {
            _rwLock.ExitUpgradeableReadLock();
        }
    }
}

// ManualResetEventSlim e AutoResetEvent
public class EventosExemplo
{
    private ManualResetEventSlim _manualReset = new ManualResetEventSlim(false);
    private AutoResetEvent _autoReset = new AutoResetEvent(false);

    public void Produtor()
    {
        Console.WriteLine("Preparando dados...");
        Thread.Sleep(1000);
        Console.WriteLine("Dados prontos!");
        _manualReset.Set(); // Libera TODOS que estão esperando
    }

    public void Consumidor(int id)
    {
        Console.WriteLine($"Consumidor {id} esperando...");
        _manualReset.Wait();
        Console.WriteLine($"Consumidor {id} processando!");
    }

    public void ProducerAuto()
    {
        for (int i = 0; i < 5; i++)
        {
            Thread.Sleep(500);
            _autoReset.Set(); // Libera UM que está esperando
        }
    }

    public void ConsumerAuto(int id)
    {
        while (true)
        {
            _autoReset.WaitOne();
            Console.WriteLine($"Worker {id} executou tarefa");
        }
    }
}

// CountdownEvent
public class CountdownExemplo
{
    public void ExecutarParalelo()
    {
        int numTarefas = 5;
        using var countdown = new CountdownEvent(numTarefas);

        for (int i = 0; i < numTarefas; i++)
        {
            int id = i;
            ThreadPool.QueueUserWorkItem(_ =>
            {
                Console.WriteLine($"Tarefa {id} executando");
                Thread.Sleep(100 * id);
                countdown.Signal(); // Decrementa
            });
        }

        countdown.Wait(); // Espera chegar a zero
        Console.WriteLine("Todas tarefas concluídas!");
    }
}

// Barrier - sincronização em fases
public class BarrierExemplo
{
    public void ProcessamentoEmFases()
    {
        int participantes = 3;
        using var barrier = new Barrier(participantes, b =>
        {
            Console.WriteLine($"=== Fase {b.CurrentPhaseNumber} concluída ===");
        });

        for (int i = 0; i < participantes; i++)
        {
            int id = i;
            new Thread(() =>
            {
                for (int fase = 0; fase < 3; fase++)
                {
                    Console.WriteLine($"Worker {id} - Fase {fase}");
                    Thread.Sleep(100 * (id + 1));
                    barrier.SignalAndWait(); // Espera todos
                }
            }).Start();
        }
    }
}
```

### 2.3 Interlocked - Operações Atômicas

```csharp
public class OperacoesAtomicas
{
    private long _contador = 0;
    private int _flag = 0;

    public void Incrementar()
    {
        Interlocked.Increment(ref _contador);
    }

    public void Decrementar()
    {
        Interlocked.Decrement(ref _contador);
    }

    public void Adicionar(long valor)
    {
        Interlocked.Add(ref _contador, valor);
    }

    public long ObterEZerar()
    {
        return Interlocked.Exchange(ref _contador, 0);
    }

    public bool TentarAdquirirLock()
    {
        // CompareExchange retorna valor original
        // Se era 0, troca para 1 e retorna 0 (sucesso)
        return Interlocked.CompareExchange(ref _flag, 1, 0) == 0;
    }

    public void LiberarLock()
    {
        Interlocked.Exchange(ref _flag, 0);
    }

    // SpinLock - lock sem context switch
    private SpinLock _spinLock = new SpinLock();

    public void OperacaoRapida()
    {
        bool lockTaken = false;
        try
        {
            _spinLock.Enter(ref lockTaken);
            // Operação muito rápida
            _contador++;
        }
        finally
        {
            if (lockTaken)
                _spinLock.Exit();
        }
    }
}
```

## 3. Task Parallel Library (TPL)

### 3.1 Tasks Avançadas

```csharp
public class TasksAvancadas
{
    // Task com opções
    public void TaskComOpcoes()
    {
        var task = Task.Factory.StartNew(
            () => OperacaoPesada(),
            CancellationToken.None,
            TaskCreationOptions.LongRunning, // Thread dedicada
            TaskScheduler.Default
        );
    }

    // Continuações complexas
    public async Task ContinuacoesComplexas()
    {
        var task1 = Task.Run(() => BuscarDados());
        var task2 = Task.Run(() => BuscarOutrosDados());

        // Continua quando qualquer uma terminar
        await Task.WhenAny(task1, task2);
        Console.WriteLine("Primeira concluída!");

        // Continua quando todas terminarem
        var resultados = await Task.WhenAll(task1, task2);

        // Continuação com opções
        var task = Task.Run(() => Processar())
            .ContinueWith(t =>
            {
                if (t.IsFaulted)
                    Console.WriteLine($"Erro: {t.Exception}");
                else if (t.IsCanceled)
                    Console.WriteLine("Cancelado");
                else
                    Console.WriteLine($"Resultado: {t.Result}");
            }, TaskContinuationOptions.ExecuteSynchronously);
    }

    // Task com resultado tipado
    public async Task<List<int>> ProcessarComResultado()
    {
        return await Task.Run(() =>
        {
            var lista = new List<int>();
            for (int i = 0; i < 1000; i++)
                lista.Add(i * 2);
            return lista;
        });
    }

    // Encadeamento de tasks
    public Task<string> ProcessamentoPipeline(string input)
    {
        return Task.Run(() => Etapa1(input))
            .ContinueWith(t => Etapa2(t.Result))
            .ContinueWith(t => Etapa3(t.Result));
    }

    private string Etapa1(string s) => s.ToUpper();
    private string Etapa2(string s) => s.Trim();
    private string Etapa3(string s) => $"[{s}]";

    private object OperacaoPesada() => null;
    private string BuscarDados() => "dados1";
    private string BuscarOutrosDados() => "dados2";
    private int Processar() => 42;
}
```

### 3.2 Parallel Class

```csharp
public class ParallelExemplos
{
    // Parallel.For
    public void ParallelFor()
    {
        var resultado = new int[1000];

        Parallel.For(0, 1000, i =>
        {
            resultado[i] = i * 2;
        });

        // Com opções
        var options = new ParallelOptions
        {
            MaxDegreeOfParallelism = Environment.ProcessorCount,
            CancellationToken = CancellationToken.None
        };

        Parallel.For(0, 1000, options, i =>
        {
            resultado[i] = Calcular(i);
        });
    }

    // Parallel.ForEach
    public void ParallelForEach()
    {
        var itens = Enumerable.Range(0, 1000).ToList();

        Parallel.ForEach(itens, item =>
        {
            Processar(item);
        });

        // Com particionamento otimizado
        var partitioner = Partitioner.Create(itens, true);
        Parallel.ForEach(partitioner, item =>
        {
            Processar(item);
        });

        // Com estado local (para agregação)
        long total = 0;
        Parallel.ForEach(
            itens,
            () => 0L, // Inicializa estado local
            (item, state, localTotal) => localTotal + item, // Processa
            localTotal => Interlocked.Add(ref total, localTotal) // Combina
        );
    }

    // Parallel.Invoke
    public void ParallelInvoke()
    {
        Parallel.Invoke(
            () => Tarefa1(),
            () => Tarefa2(),
            () => Tarefa3()
        );
    }

    // Controle de execução
    public void ParallelComControle()
    {
        Parallel.For(0, 1000, (i, state) =>
        {
            if (i == 500)
            {
                state.Stop(); // Para imediatamente
                return;
            }

            if (DeveParar())
            {
                state.Break(); // Completa iterações menores
                return;
            }

            Processar(i);
        });
    }

    private int Calcular(int i) => i * 2;
    private void Processar(int i) { }
    private void Tarefa1() { }
    private void Tarefa2() { }
    private void Tarefa3() { }
    private bool DeveParar() => false;
}
```

### 3.3 PLINQ (Parallel LINQ)

```csharp
public class PLINQExemplos
{
    public void QueriesParalelas()
    {
        var numeros = Enumerable.Range(0, 1000000);

        // Query paralela básica
        var pares = numeros
            .AsParallel()
            .Where(n => n % 2 == 0)
            .Select(n => n * 2)
            .ToList();

        // Com grau de paralelismo
        var resultado = numeros
            .AsParallel()
            .WithDegreeOfParallelism(4)
            .Where(n => EPrimo(n))
            .ToList();

        // Ordenado (mais lento, mas mantém ordem)
        var ordenado = numeros
            .AsParallel()
            .AsOrdered()
            .Where(n => n % 3 == 0)
            .ToList();

        // ForAll (sem materializar)
        numeros
            .AsParallel()
            .Where(n => n % 2 == 0)
            .ForAll(n => Console.WriteLine(n));

        // Agregação paralela
        var soma = numeros
            .AsParallel()
            .Aggregate(
                0L,
                (subtotal, item) => subtotal + item,
                (total, subtotal) => total + subtotal,
                total => total
            );

        // Com cancelamento
        var cts = new CancellationTokenSource();
        try
        {
            var res = numeros
                .AsParallel()
                .WithCancellation(cts.Token)
                .Select(n => ProcessarLento(n))
                .ToList();
        }
        catch (OperationCanceledException)
        {
            Console.WriteLine("Cancelado!");
        }

        // Merge options
        var stream = numeros
            .AsParallel()
            .WithMergeOptions(ParallelMergeOptions.NotBuffered)
            .Select(n => n * 2);
    }

    private bool EPrimo(int n)
    {
        if (n < 2) return false;
        for (int i = 2; i * i <= n; i++)
            if (n % i == 0) return false;
        return true;
    }

    private int ProcessarLento(int n)
    {
        Thread.Sleep(1);
        return n * 2;
    }
}
```

## 4. Dataflow (TPL Dataflow)

```csharp
using System.Threading.Tasks.Dataflow;

public class DataflowExemplos
{
    // Pipeline básico
    public async Task PipelineBasico()
    {
        // Bloco de transformação
        var multiplicar = new TransformBlock<int, int>(n => n * 2);
        var adicionar = new TransformBlock<int, int>(n => n + 1);
        var imprimir = new ActionBlock<int>(n => Console.WriteLine(n));

        // Conecta os blocos
        multiplicar.LinkTo(adicionar);
        adicionar.LinkTo(imprimir);

        // Envia dados
        for (int i = 0; i < 10; i++)
            multiplicar.Post(i);

        multiplicar.Complete();
        await imprimir.Completion;
    }

    // Pipeline com múltiplos consumidores
    public async Task PipelineComBroadcast()
    {
        var broadcast = new BroadcastBlock<int>(n => n);
        var consumer1 = new ActionBlock<int>(n => Console.WriteLine($"C1: {n}"));
        var consumer2 = new ActionBlock<int>(n => Console.WriteLine($"C2: {n}"));

        broadcast.LinkTo(consumer1);
        broadcast.LinkTo(consumer2);

        for (int i = 0; i < 5; i++)
            broadcast.Post(i);

        broadcast.Complete();
        await Task.WhenAll(consumer1.Completion, consumer2.Completion);
    }

    // BufferBlock como fila
    public async Task FilaComBuffer()
    {
        var buffer = new BufferBlock<string>();

        // Produtor
        var produtor = Task.Run(async () =>
        {
            for (int i = 0; i < 10; i++)
            {
                await buffer.SendAsync($"Item {i}");
                await Task.Delay(100);
            }
            buffer.Complete();
        });

        // Consumidor
        var consumidor = Task.Run(async () =>
        {
            while (await buffer.OutputAvailableAsync())
            {
                var item = await buffer.ReceiveAsync();
                Console.WriteLine($"Recebido: {item}");
            }
        });

        await Task.WhenAll(produtor, consumidor);
    }

    // BatchBlock - agrupa itens
    public async Task ProcessamentoEmLotes()
    {
        var batcher = new BatchBlock<int>(5); // Lotes de 5
        var processor = new ActionBlock<int[]>(batch =>
        {
            Console.WriteLine($"Lote: [{string.Join(", ", batch)}]");
        });

        batcher.LinkTo(processor);

        for (int i = 0; i < 23; i++)
            batcher.Post(i);

        batcher.Complete();
        await processor.Completion;
    }

    // JoinBlock - combina múltiplas fontes
    public async Task CombinarFontes()
    {
        var join = new JoinBlock<int, string>();

        var processor = new ActionBlock<Tuple<int, string>>(tuple =>
        {
            Console.WriteLine($"ID: {tuple.Item1}, Nome: {tuple.Item2}");
        });

        join.LinkTo(processor);

        join.Target1.Post(1);
        join.Target2.Post("Um");
        join.Target1.Post(2);
        join.Target2.Post("Dois");

        join.Complete();
        await processor.Completion;
    }

    // TransformManyBlock - um para muitos
    public async Task UmParaMuitos()
    {
        var splitter = new TransformManyBlock<string, string>(
            texto => texto.Split(' ')
        );

        var printer = new ActionBlock<string>(palavra =>
            Console.WriteLine(palavra)
        );

        splitter.LinkTo(printer);

        splitter.Post("Hello World from Dataflow");
        splitter.Complete();
        await printer.Completion;
    }

    // Pipeline completo com controle de fluxo
    public async Task PipelineCompleto()
    {
        var options = new ExecutionDataflowBlockOptions
        {
            MaxDegreeOfParallelism = 4,
            BoundedCapacity = 10
        };

        var download = new TransformBlock<string, byte[]>(
            async url =>
            {
                using var client = new HttpClient();
                return await client.GetByteArrayAsync(url);
            },
            options
        );

        var processar = new TransformBlock<byte[], string>(
            data => Encoding.UTF8.GetString(data),
            options
        );

        var salvar = new ActionBlock<string>(
            async conteudo =>
            {
                await File.WriteAllTextAsync($"output_{Guid.NewGuid()}.txt", conteudo);
            },
            options
        );

        var linkOptions = new DataflowLinkOptions { PropagateCompletion = true };
        download.LinkTo(processar, linkOptions);
        processar.LinkTo(salvar, linkOptions);

        // Enviar URLs
        var urls = new[] { "https://example.com", "https://example.org" };
        foreach (var url in urls)
            await download.SendAsync(url);

        download.Complete();
        await salvar.Completion;
    }
}
```

## 5. Channels (Produtor-Consumidor Moderno)

```csharp
using System.Threading.Channels;

public class ChannelExemplos
{
    // Channel básico
    public async Task ChannelBasico()
    {
        var channel = Channel.CreateUnbounded<int>();

        // Produtor
        var produtor = Task.Run(async () =>
        {
            for (int i = 0; i < 10; i++)
            {
                await channel.Writer.WriteAsync(i);
                Console.WriteLine($"Produzido: {i}");
            }
            channel.Writer.Complete();
        });

        // Consumidor
        var consumidor = Task.Run(async () =>
        {
            await foreach (var item in channel.Reader.ReadAllAsync())
            {
                Console.WriteLine($"Consumido: {item}");
                await Task.Delay(100);
            }
        });

        await Task.WhenAll(produtor, consumidor);
    }

    // Channel com capacidade limitada (backpressure)
    public async Task ChannelComLimite()
    {
        var options = new BoundedChannelOptions(5)
        {
            FullMode = BoundedChannelFullMode.Wait
        };
        var channel = Channel.CreateBounded<int>(options);

        var produtor = Task.Run(async () =>
        {
            for (int i = 0; i < 20; i++)
            {
                await channel.Writer.WriteAsync(i);
                Console.WriteLine($"Produzido: {i}");
            }
            channel.Writer.Complete();
        });

        var consumidor = Task.Run(async () =>
        {
            await foreach (var item in channel.Reader.ReadAllAsync())
            {
                Console.WriteLine($"Consumido: {item}");
                await Task.Delay(200); // Consumidor lento
            }
        });

        await Task.WhenAll(produtor, consumidor);
    }

    // Múltiplos produtores e consumidores
    public async Task MultiplosWorkers()
    {
        var channel = Channel.CreateUnbounded<int>();

        // 3 produtores
        var produtores = Enumerable.Range(0, 3)
            .Select(id => Task.Run(async () =>
            {
                for (int i = 0; i < 10; i++)
                {
                    await channel.Writer.WriteAsync(id * 100 + i);
                }
            }))
            .ToArray();

        // 2 consumidores
        var consumidores = Enumerable.Range(0, 2)
            .Select(id => Task.Run(async () =>
            {
                await foreach (var item in channel.Reader.ReadAllAsync())
                {
                    Console.WriteLine($"Consumer {id}: {item}");
                }
            }))
            .ToArray();

        await Task.WhenAll(produtores);
        channel.Writer.Complete();
        await Task.WhenAll(consumidores);
    }

    // Pipeline com channels
    public async Task PipelineComChannels()
    {
        var channel1 = Channel.CreateUnbounded<int>();
        var channel2 = Channel.CreateUnbounded<int>();

        // Etapa 1: Gerar números
        var etapa1 = Task.Run(async () =>
        {
            for (int i = 0; i < 100; i++)
                await channel1.Writer.WriteAsync(i);
            channel1.Writer.Complete();
        });

        // Etapa 2: Filtrar pares
        var etapa2 = Task.Run(async () =>
        {
            await foreach (var item in channel1.Reader.ReadAllAsync())
            {
                if (item % 2 == 0)
                    await channel2.Writer.WriteAsync(item);
            }
            channel2.Writer.Complete();
        });

        // Etapa 3: Processar
        var etapa3 = Task.Run(async () =>
        {
            await foreach (var item in channel2.Reader.ReadAllAsync())
            {
                Console.WriteLine($"Resultado: {item * 2}");
            }
        });

        await Task.WhenAll(etapa1, etapa2, etapa3);
    }
}
```

## 6. Async Streams

```csharp
public class AsyncStreamsExemplos
{
    // IAsyncEnumerable básico
    public async IAsyncEnumerable<int> GerarNumerosAsync(
        int quantidade,
        [EnumeratorCancellation] CancellationToken ct = default)
    {
        for (int i = 0; i < quantidade; i++)
        {
            ct.ThrowIfCancellationRequested();
            await Task.Delay(100, ct);
            yield return i;
        }
    }

    // Consumir async stream
    public async Task ConsumirStream()
    {
        await foreach (var numero in GerarNumerosAsync(10))
        {
            Console.WriteLine(numero);
        }
    }

    // Com cancelamento
    public async Task ConsumirComCancelamento()
    {
        var cts = new CancellationTokenSource(2000); // 2 segundos

        try
        {
            await foreach (var numero in GerarNumerosAsync(100, cts.Token))
            {
                Console.WriteLine(numero);
            }
        }
        catch (OperationCanceledException)
        {
            Console.WriteLine("Cancelado!");
        }
    }

    // Transformar async stream
    public async IAsyncEnumerable<string> TransformarStream(
        IAsyncEnumerable<int> source)
    {
        await foreach (var item in source)
        {
            yield return $"Valor: {item}";
        }
    }

    // Combinar múltiplos streams
    public async IAsyncEnumerable<int> MergeStreams(
        params IAsyncEnumerable<int>[] streams)
    {
        var channel = Channel.CreateUnbounded<int>();

        var tasks = streams.Select(async stream =>
        {
            await foreach (var item in stream)
            {
                await channel.Writer.WriteAsync(item);
            }
        }).ToArray();

        _ = Task.WhenAll(tasks).ContinueWith(_ => channel.Writer.Complete());

        await foreach (var item in channel.Reader.ReadAllAsync())
        {
            yield return item;
        }
    }
}
```

## 7. Concurrent Collections

```csharp
using System.Collections.Concurrent;

public class ConcurrentCollectionsExemplos
{
    // ConcurrentDictionary
    public void UsarConcurrentDictionary()
    {
        var dict = new ConcurrentDictionary<string, int>();

        // AddOrUpdate
        dict.AddOrUpdate("chave",
            key => 1,              // Se não existe, adiciona 1
            (key, old) => old + 1  // Se existe, incrementa
        );

        // GetOrAdd
        var valor = dict.GetOrAdd("outra", key =>
        {
            // Calcula valor inicial
            return key.Length;
        });

        // TryUpdate
        dict.TryUpdate("chave", 10, 1); // Só atualiza se valor atual é 1

        // TryRemove
        if (dict.TryRemove("chave", out var removido))
        {
            Console.WriteLine($"Removido: {removido}");
        }
    }

    // ConcurrentQueue
    public void UsarConcurrentQueue()
    {
        var queue = new ConcurrentQueue<int>();

        // Enqueue é thread-safe
        Parallel.For(0, 100, i => queue.Enqueue(i));

        // TryDequeue
        while (queue.TryDequeue(out var item))
        {
            Console.WriteLine(item);
        }
    }

    // ConcurrentStack
    public void UsarConcurrentStack()
    {
        var stack = new ConcurrentStack<int>();

        stack.Push(1);
        stack.PushRange(new[] { 2, 3, 4, 5 });

        if (stack.TryPop(out var item))
            Console.WriteLine(item);

        var items = new int[3];
        int count = stack.TryPopRange(items);
    }

    // ConcurrentBag (não ordenado, otimizado para mesmo thread adicionar/remover)
    public void UsarConcurrentBag()
    {
        var bag = new ConcurrentBag<int>();

        Parallel.For(0, 100, i =>
        {
            bag.Add(i);
            if (bag.TryTake(out var item))
                Console.WriteLine($"Thread {Thread.CurrentThread.ManagedThreadId}: {item}");
        });
    }

    // BlockingCollection (produtor-consumidor)
    public void UsarBlockingCollection()
    {
        using var collection = new BlockingCollection<int>(boundedCapacity: 10);

        // Produtor
        var produtor = Task.Run(() =>
        {
            for (int i = 0; i < 100; i++)
            {
                collection.Add(i); // Bloqueia se cheio
            }
            collection.CompleteAdding();
        });

        // Consumidor
        var consumidor = Task.Run(() =>
        {
            foreach (var item in collection.GetConsumingEnumerable())
            {
                Console.WriteLine(item);
            }
        });

        Task.WaitAll(produtor, consumidor);
    }

    // Múltiplas filas com BlockingCollection
    public void MultiplasFontes()
    {
        var queues = new[]
        {
            new BlockingCollection<int>(),
            new BlockingCollection<int>(),
            new BlockingCollection<int>()
        };

        // Consumir de qualquer fila que tiver dados
        Task.Run(() =>
        {
            while (true)
            {
                int item;
                int index = BlockingCollection<int>.TryTakeFromAny(
                    queues, out item, TimeSpan.FromSeconds(1));

                if (index >= 0)
                    Console.WriteLine($"Da fila {index}: {item}");
            }
        });
    }
}
```

## 8. Padrões Avançados

### 8.1 Actor Pattern

```csharp
public class Actor<T>
{
    private readonly Channel<(T message, TaskCompletionSource<object> tcs)> _channel;
    private readonly Func<T, Task<object>> _handler;

    public Actor(Func<T, Task<object>> handler)
    {
        _handler = handler;
        _channel = Channel.CreateUnbounded<(T, TaskCompletionSource<object>)>();
        _ = ProcessMessages();
    }

    private async Task ProcessMessages()
    {
        await foreach (var (message, tcs) in _channel.Reader.ReadAllAsync())
        {
            try
            {
                var result = await _handler(message);
                tcs.SetResult(result);
            }
            catch (Exception ex)
            {
                tcs.SetException(ex);
            }
        }
    }

    public async Task<object> SendAsync(T message)
    {
        var tcs = new TaskCompletionSource<object>();
        await _channel.Writer.WriteAsync((message, tcs));
        return await tcs.Task;
    }
}

// Uso
public class ContaBancaria
{
    private readonly Actor<(string op, decimal valor)> _actor;
    private decimal _saldo;

    public ContaBancaria(decimal saldoInicial)
    {
        _saldo = saldoInicial;
        _actor = new Actor<(string, decimal)>(ProcessarOperacao);
    }

    private Task<object> ProcessarOperacao((string op, decimal valor) msg)
    {
        switch (msg.op)
        {
            case "deposito":
                _saldo += msg.valor;
                break;
            case "saque":
                if (_saldo >= msg.valor)
                    _saldo -= msg.valor;
                else
                    throw new InvalidOperationException("Saldo insuficiente");
                break;
        }
        return Task.FromResult((object)_saldo);
    }

    public Task<object> Depositar(decimal valor) =>
        _actor.SendAsync(("deposito", valor));

    public Task<object> Sacar(decimal valor) =>
        _actor.SendAsync(("saque", valor));
}
```

### 8.2 Pipeline Pattern

```csharp
public interface IPipelineStep<TIn, TOut>
{
    Task<TOut> ProcessAsync(TIn input);
}

public class Pipeline<TIn, TOut>
{
    private readonly Func<TIn, Task<TOut>> _process;

    private Pipeline(Func<TIn, Task<TOut>> process)
    {
        _process = process;
    }

    public static Pipeline<TIn, TIn> Create() =>
        new Pipeline<TIn, TIn>(x => Task.FromResult(x));

    public Pipeline<TIn, TNext> AddStep<TNext>(
        IPipelineStep<TOut, TNext> step)
    {
        return new Pipeline<TIn, TNext>(async input =>
        {
            var result = await _process(input);
            return await step.ProcessAsync(result);
        });
    }

    public Task<TOut> ExecuteAsync(TIn input) => _process(input);
}
```

Este guia cobre multithreading e paralelismo avançado em C#!
