# Fundamentos de C# - Guia Completo

## 1. Tipos de Dados

### 1.1 Tipos Primitivos

```csharp
// Inteiros
byte b = 255;           // 0 a 255
sbyte sb = -128;        // -128 a 127
short s = 32000;        // -32,768 a 32,767
ushort us = 65000;      // 0 a 65,535
int i = 2000000000;     // -2.1 bi a 2.1 bi
uint ui = 4000000000;   // 0 a 4.2 bi
long l = 9000000000L;   // muito grande
ulong ul = 18000000000; // muito grande positivo

// Decimais
float f = 3.14f;        // 7 dígitos precisão
double d = 3.14159265;  // 15-17 dígitos
decimal m = 3.14159265358979m; // 28-29 dígitos (financeiro)

// Outros
bool verdadeiro = true;
char letra = 'A';
string texto = "Hello World";
```

### 1.2 Strings

```csharp
// Declaração
string nome = "João";
string vazia = "";
string nula = null;
string interpolada = $"Olá {nome}!";
string verbatim = @"C:\Users\Pasta";
string raw = """
    Texto em
    múltiplas linhas
    """;

// Métodos úteis
string upper = nome.ToUpper();        // "JOÃO"
string lower = nome.ToLower();        // "joão"
int tamanho = nome.Length;            // 4
bool contem = nome.Contains("oã");    // true
string sub = nome.Substring(0, 2);    // "Jo"
string[] partes = "a,b,c".Split(','); // ["a", "b", "c"]
string junto = string.Join("-", partes); // "a-b-c"
string trim = "  texto  ".Trim();     // "texto"
string replace = nome.Replace("o", "0"); // "J0ã0"

// StringBuilder (performance)
var sb = new StringBuilder();
sb.Append("Hello ");
sb.Append("World");
sb.AppendLine("!");
string resultado = sb.ToString();
```

### 1.3 Arrays

```csharp
// Declaração
int[] numeros = new int[5];
int[] inicializado = { 1, 2, 3, 4, 5 };
int[] tambem = new int[] { 1, 2, 3 };

// Acesso
numeros[0] = 10;
int primeiro = inicializado[0];
int tamanho = inicializado.Length;

// Multidimensional
int[,] matriz = new int[3, 3];
matriz[0, 0] = 1;
int[,] init = { { 1, 2 }, { 3, 4 } };

// Jagged (array de arrays)
int[][] jagged = new int[3][];
jagged[0] = new int[] { 1, 2 };
jagged[1] = new int[] { 3, 4, 5 };

// Métodos úteis
Array.Sort(numeros);
Array.Reverse(numeros);
int indice = Array.IndexOf(numeros, 3);
Array.Copy(origem, destino, quantidade);
```

## 2. Coleções

### 2.1 List<T>

```csharp
// Criação
List<int> lista = new List<int>();
List<string> nomes = new List<string> { "Ana", "Bob" };
var auto = new List<int> { 1, 2, 3 };

// Operações
lista.Add(1);
lista.AddRange(new[] { 2, 3, 4 });
lista.Insert(0, 0);           // Insere no índice
lista.Remove(2);              // Remove valor
lista.RemoveAt(0);            // Remove por índice
lista.Clear();                // Limpa tudo

// Consultas
int quantidade = lista.Count;
bool existe = lista.Contains(3);
int indice = lista.IndexOf(3);
int primeiro = lista.First();
int ultimo = lista.Last();
List<int> filtrado = lista.FindAll(x => x > 2);
```

### 2.2 Dictionary<K,V>

```csharp
// Criação
var dict = new Dictionary<string, int>();
var init = new Dictionary<string, int>
{
    { "um", 1 },
    { "dois", 2 }
};

// Operações
dict["tres"] = 3;             // Add ou update
dict.Add("quatro", 4);        // Só add (erro se existe)
dict.Remove("um");
bool existe = dict.ContainsKey("dois");
bool temValor = dict.ContainsValue(2);

// Acesso seguro
if (dict.TryGetValue("dois", out int valor))
{
    Console.WriteLine(valor);
}

// Iteração
foreach (var kvp in dict)
{
    Console.WriteLine($"{kvp.Key}: {kvp.Value}");
}
```

### 2.3 Outras Coleções

```csharp
// Queue (FIFO)
var fila = new Queue<string>();
fila.Enqueue("primeiro");
fila.Enqueue("segundo");
string proximo = fila.Dequeue(); // "primeiro"
string peek = fila.Peek();       // Olha sem remover

// Stack (LIFO)
var pilha = new Stack<int>();
pilha.Push(1);
pilha.Push(2);
int topo = pilha.Pop();  // 2
int ver = pilha.Peek();  // 1

// HashSet (únicos)
var set = new HashSet<int> { 1, 2, 3 };
set.Add(3);              // Não adiciona (já existe)
set.Add(4);              // Adiciona
bool tem = set.Contains(2);

// LinkedList
var linked = new LinkedList<int>();
linked.AddFirst(1);
linked.AddLast(3);
linked.AddAfter(linked.First, 2);
```

## 3. Classes e Objetos

### 3.1 Classe Básica

```csharp
public class Pessoa
{
    // Campos
    private string nome;
    private int idade;

    // Propriedades
    public string Nome
    {
        get { return nome; }
        set { nome = value; }
    }

    // Propriedade automática
    public int Idade { get; set; }

    // Propriedade somente leitura
    public string Descricao => $"{Nome}, {Idade} anos";

    // Construtor padrão
    public Pessoa()
    {
        Nome = "Sem nome";
        Idade = 0;
    }

    // Construtor com parâmetros
    public Pessoa(string nome, int idade)
    {
        Nome = nome;
        Idade = idade;
    }

    // Método
    public void Apresentar()
    {
        Console.WriteLine($"Olá, sou {Nome}!");
    }

    // Método com retorno
    public bool EhMaiorDeIdade()
    {
        return Idade >= 18;
    }

    // Método estático
    public static Pessoa Criar(string nome)
    {
        return new Pessoa(nome, 0);
    }
}

// Uso
var pessoa = new Pessoa("João", 25);
pessoa.Apresentar();
bool maior = pessoa.EhMaiorDeIdade();
var outra = Pessoa.Criar("Maria");
```

### 3.2 Herança

```csharp
// Classe base
public class Animal
{
    public string Nome { get; set; }

    public virtual void EmitirSom()
    {
        Console.WriteLine("Som genérico");
    }
}

// Classe derivada
public class Cachorro : Animal
{
    public string Raca { get; set; }

    public override void EmitirSom()
    {
        Console.WriteLine("Au au!");
    }

    public void Correr()
    {
        Console.WriteLine($"{Nome} está correndo!");
    }
}

// Uso
Cachorro dog = new Cachorro { Nome = "Rex", Raca = "Pastor" };
dog.EmitirSom();  // "Au au!"
dog.Correr();

Animal animal = dog;  // Polimorfismo
animal.EmitirSom();   // "Au au!" (método virtual)
```

### 3.3 Interfaces

```csharp
public interface IVoador
{
    void Voar();
    int Altitude { get; }
}

public interface INadador
{
    void Nadar();
}

// Implementação múltipla
public class Pato : Animal, IVoador, INadador
{
    public int Altitude { get; private set; }

    public void Voar()
    {
        Altitude = 100;
        Console.WriteLine("Pato voando!");
    }

    public void Nadar()
    {
        Console.WriteLine("Pato nadando!");
    }
}
```

### 3.4 Classes Abstratas

```csharp
public abstract class Forma
{
    public abstract double CalcularArea();

    public void Descrever()
    {
        Console.WriteLine($"Área: {CalcularArea()}");
    }
}

public class Circulo : Forma
{
    public double Raio { get; set; }

    public override double CalcularArea()
    {
        return Math.PI * Raio * Raio;
    }
}

public class Retangulo : Forma
{
    public double Largura { get; set; }
    public double Altura { get; set; }

    public override double CalcularArea()
    {
        return Largura * Altura;
    }
}
```

## 4. LINQ

### 4.1 Sintaxe de Método

```csharp
var numeros = new List<int> { 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 };

// Where - Filtrar
var pares = numeros.Where(x => x % 2 == 0);

// Select - Projetar
var dobrados = numeros.Select(x => x * 2);

// OrderBy / OrderByDescending
var ordenados = numeros.OrderBy(x => x);
var desc = numeros.OrderByDescending(x => x);

// First / Last / Single
int primeiro = numeros.First();
int ultimoPar = numeros.Last(x => x % 2 == 0);
int unico = numeros.Single(x => x == 5);

// FirstOrDefault (retorna default se não achar)
int? resultado = numeros.FirstOrDefault(x => x > 100);

// Any / All
bool temPar = numeros.Any(x => x % 2 == 0);
bool todosMenores = numeros.All(x => x < 100);

// Count / Sum / Average / Min / Max
int quantidade = numeros.Count();
int soma = numeros.Sum();
double media = numeros.Average();
int minimo = numeros.Min();
int maximo = numeros.Max();

// Take / Skip
var primeiros3 = numeros.Take(3);
var pulando3 = numeros.Skip(3);

// Distinct
var unicos = new[] { 1, 1, 2, 2, 3 }.Distinct();

// GroupBy
var pessoas = new List<Pessoa>();
var porIdade = pessoas.GroupBy(p => p.Idade);

// Join
var pedidos = new List<Pedido>();
var clientes = new List<Cliente>();
var join = pedidos.Join(
    clientes,
    p => p.ClienteId,
    c => c.Id,
    (pedido, cliente) => new { pedido, cliente }
);

// Aggregate
int fatorial = Enumerable.Range(1, 5).Aggregate((a, b) => a * b);
```

### 4.2 Sintaxe de Query

```csharp
var numeros = new List<int> { 1, 2, 3, 4, 5 };

var resultado = from n in numeros
                where n > 2
                orderby n descending
                select n * 2;

// Com join
var query = from p in pedidos
            join c in clientes on p.ClienteId equals c.Id
            where c.Ativo
            select new { p.Numero, c.Nome };
```

## 5. Async/Await

### 5.1 Métodos Assíncronos

```csharp
// Método async básico
public async Task<string> BuscarDadosAsync()
{
    await Task.Delay(1000); // Simula operação lenta
    return "Dados carregados";
}

// Chamada
string dados = await BuscarDadosAsync();

// Método com HttpClient
public async Task<string> BuscarUrlAsync(string url)
{
    using var client = new HttpClient();
    return await client.GetStringAsync(url);
}

// Múltiplas tarefas paralelas
public async Task ProcessarMultiplosAsync()
{
    Task<string> task1 = BuscarDadosAsync();
    Task<string> task2 = BuscarDadosAsync();
    Task<string> task3 = BuscarDadosAsync();

    string[] resultados = await Task.WhenAll(task1, task2, task3);
}

// Primeira que completar
public async Task<string> PrimeiroResultadoAsync()
{
    Task<string> task1 = BuscarDadosAsync();
    Task<string> task2 = BuscarDadosAsync();

    Task<string> primeira = await Task.WhenAny(task1, task2);
    return await primeira;
}
```

### 5.2 Cancelamento

```csharp
public async Task ProcessarComCancelamentoAsync(CancellationToken token)
{
    for (int i = 0; i < 100; i++)
    {
        token.ThrowIfCancellationRequested();
        await Task.Delay(100, token);
        Console.WriteLine($"Processando {i}...");
    }
}

// Uso
var cts = new CancellationTokenSource();

// Cancela após 5 segundos
cts.CancelAfter(5000);

try
{
    await ProcessarComCancelamentoAsync(cts.Token);
}
catch (OperationCanceledException)
{
    Console.WriteLine("Operação cancelada!");
}
```

## 6. Tratamento de Exceções

```csharp
try
{
    int resultado = int.Parse("abc"); // Vai dar erro
}
catch (FormatException ex)
{
    Console.WriteLine($"Formato inválido: {ex.Message}");
}
catch (Exception ex) when (ex.Message.Contains("algo"))
{
    // Catch condicional
    Console.WriteLine("Erro específico");
}
catch (Exception ex)
{
    Console.WriteLine($"Erro geral: {ex.Message}");
    throw; // Re-lança a exceção
}
finally
{
    Console.WriteLine("Sempre executa");
}

// Exceção customizada
public class MinhaExcecao : Exception
{
    public int Codigo { get; }

    public MinhaExcecao(string mensagem, int codigo)
        : base(mensagem)
    {
        Codigo = codigo;
    }
}

// Lançar exceção
throw new MinhaExcecao("Algo deu errado", 500);
```

## 7. Delegates e Eventos

### 7.1 Delegates

```csharp
// Declaração
public delegate int Operacao(int a, int b);

// Implementação
int Somar(int a, int b) => a + b;
int Multiplicar(int a, int b) => a * b;

// Uso
Operacao op = Somar;
int resultado = op(2, 3); // 5

op = Multiplicar;
resultado = op(2, 3); // 6

// Delegates genéricos
Func<int, int, int> soma = (a, b) => a + b;
Action<string> print = msg => Console.WriteLine(msg);
Predicate<int> ehPar = n => n % 2 == 0;
```

### 7.2 Eventos

```csharp
public class Botao
{
    // Evento
    public event EventHandler<string> Clicado;

    // Método que dispara evento
    public void Clicar()
    {
        Clicado?.Invoke(this, "Botão foi clicado!");
    }
}

// Uso
var botao = new Botao();
botao.Clicado += (sender, msg) => Console.WriteLine(msg);
botao.Clicar();
```

## 8. Generics

```csharp
// Classe genérica
public class Repositorio<T> where T : class
{
    private List<T> items = new List<T>();

    public void Adicionar(T item) => items.Add(item);
    public T Obter(int index) => items[index];
    public IEnumerable<T> ObterTodos() => items;
}

// Método genérico
public T Clonar<T>(T objeto) where T : ICloneable
{
    return (T)objeto.Clone();
}

// Constraints
public class Exemplo<T>
    where T : class, new()     // Tipo de referência com construtor vazio
{
    public T Criar() => new T();
}

public class Outro<T, U>
    where T : IComparable<T>
    where U : struct           // Tipo de valor
{
}
```

## 9. Records (C# 9+)

```csharp
// Record simples (imutável por padrão)
public record Pessoa(string Nome, int Idade);

// Uso
var p1 = new Pessoa("João", 30);
var p2 = p1 with { Idade = 31 }; // Cria cópia com modificação

// Comparação por valor
var p3 = new Pessoa("João", 30);
bool iguais = p1 == p3; // true

// Record com mais controle
public record Produto
{
    public string Nome { get; init; }
    public decimal Preco { get; init; }

    public Produto(string nome, decimal preco)
    {
        Nome = nome;
        Preco = preco;
    }
}
```

## 10. Pattern Matching

```csharp
object obj = "teste";

// is pattern
if (obj is string s)
{
    Console.WriteLine(s.ToUpper());
}

// switch expression
string resultado = obj switch
{
    string texto => $"É string: {texto}",
    int numero => $"É int: {numero}",
    null => "É nulo",
    _ => "Tipo desconhecido"
};

// Property pattern
var pessoa = new Pessoa("João", 25);

string categoria = pessoa switch
{
    { Idade: < 18 } => "Menor",
    { Idade: >= 18 and < 60 } => "Adulto",
    { Idade: >= 60 } => "Idoso",
    _ => "Desconhecido"
};

// Tuple pattern
(int x, int y) ponto = (1, 2);

string quadrante = ponto switch
{
    (> 0, > 0) => "Primeiro",
    (< 0, > 0) => "Segundo",
    (< 0, < 0) => "Terceiro",
    (> 0, < 0) => "Quarto",
    _ => "Origem"
};
```

## 11. Nullable Types

```csharp
// Nullable value type
int? numero = null;
numero = 5;

// Verificação
if (numero.HasValue)
{
    int valor = numero.Value;
}

// Operador null-coalescing
int resultado = numero ?? 0;

// Operador null-conditional
string? nome = null;
int? tamanho = nome?.Length;

// Null-coalescing assignment
List<int>? lista = null;
lista ??= new List<int>();

// Nullable reference types (C# 8+)
#nullable enable
string? podeSerNulo = null;
string naoNulo = "texto";
#nullable disable
```

## 12. Expressões Lambda e LINQ Avançado

```csharp
// Lambda
Func<int, int, int> soma = (a, b) => a + b;
Action<string> print = msg => Console.WriteLine(msg);

// Lambda com corpo
Func<int, bool> complexo = n =>
{
    var resultado = n * 2;
    return resultado > 10;
};

// Closure
int multiplicador = 2;
Func<int, int> multiplicar = n => n * multiplicador;

// Expression trees
Expression<Func<int, bool>> expr = n => n > 5;
```

Este guia cobre os fundamentos essenciais do C#. Para desenvolvimento de Remote Desktop, combine este conhecimento com o guia específico de Remote Desktop!
