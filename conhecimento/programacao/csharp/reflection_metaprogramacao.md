# Reflection e Metaprogramação em C#

## 1. Fundamentos de Reflection

### 1.1 Obtendo Informações de Tipos

```csharp
using System;
using System.Reflection;

public class ReflectionBasico
{
    // Obter Type de várias formas
    public void ObterTypes()
    {
        // Via typeof
        Type tipo1 = typeof(string);

        // Via GetType()
        string texto = "hello";
        Type tipo2 = texto.GetType();

        // Via nome
        Type tipo3 = Type.GetType("System.String");

        // Via assembly
        Assembly assembly = Assembly.GetExecutingAssembly();
        Type tipo4 = assembly.GetType("MeuNamespace.MinhaClasse");
    }

    // Informações básicas do tipo
    public void InfoTipo(Type tipo)
    {
        Console.WriteLine($"Nome: {tipo.Name}");
        Console.WriteLine($"FullName: {tipo.FullName}");
        Console.WriteLine($"Namespace: {tipo.Namespace}");
        Console.WriteLine($"Assembly: {tipo.Assembly.FullName}");

        Console.WriteLine($"IsClass: {tipo.IsClass}");
        Console.WriteLine($"IsInterface: {tipo.IsInterface}");
        Console.WriteLine($"IsAbstract: {tipo.IsAbstract}");
        Console.WriteLine($"IsSealed: {tipo.IsSealed}");
        Console.WriteLine($"IsPublic: {tipo.IsPublic}");
        Console.WriteLine($"IsGenericType: {tipo.IsGenericType}");
        Console.WriteLine($"IsValueType: {tipo.IsValueType}");
        Console.WriteLine($"IsEnum: {tipo.IsEnum}");
        Console.WriteLine($"IsArray: {tipo.IsArray}");

        // Herança
        Console.WriteLine($"BaseType: {tipo.BaseType?.Name}");

        // Interfaces implementadas
        foreach (Type iface in tipo.GetInterfaces())
            Console.WriteLine($"  Implementa: {iface.Name}");
    }
}
```

### 1.2 Membros (Properties, Fields, Methods)

```csharp
public class MembrosReflection
{
    // Listar propriedades
    public void ListarPropriedades(Type tipo)
    {
        PropertyInfo[] props = tipo.GetProperties(
            BindingFlags.Public | BindingFlags.NonPublic |
            BindingFlags.Instance | BindingFlags.Static);

        foreach (PropertyInfo prop in props)
        {
            Console.WriteLine($"Propriedade: {prop.Name}");
            Console.WriteLine($"  Tipo: {prop.PropertyType.Name}");
            Console.WriteLine($"  CanRead: {prop.CanRead}");
            Console.WriteLine($"  CanWrite: {prop.CanWrite}");

            // Atributos
            foreach (Attribute attr in prop.GetCustomAttributes())
                Console.WriteLine($"  Atributo: {attr.GetType().Name}");
        }
    }

    // Listar campos
    public void ListarCampos(Type tipo)
    {
        FieldInfo[] fields = tipo.GetFields(
            BindingFlags.Public | BindingFlags.NonPublic |
            BindingFlags.Instance | BindingFlags.Static);

        foreach (FieldInfo field in fields)
        {
            Console.WriteLine($"Campo: {field.Name}");
            Console.WriteLine($"  Tipo: {field.FieldType.Name}");
            Console.WriteLine($"  IsPublic: {field.IsPublic}");
            Console.WriteLine($"  IsPrivate: {field.IsPrivate}");
            Console.WriteLine($"  IsStatic: {field.IsStatic}");
            Console.WriteLine($"  IsReadOnly: {field.IsInitOnly}");
        }
    }

    // Listar métodos
    public void ListarMetodos(Type tipo)
    {
        MethodInfo[] methods = tipo.GetMethods(
            BindingFlags.Public | BindingFlags.NonPublic |
            BindingFlags.Instance | BindingFlags.Static |
            BindingFlags.DeclaredOnly);

        foreach (MethodInfo method in methods)
        {
            Console.WriteLine($"Método: {method.Name}");
            Console.WriteLine($"  Retorno: {method.ReturnType.Name}");
            Console.WriteLine($"  IsPublic: {method.IsPublic}");
            Console.WriteLine($"  IsStatic: {method.IsStatic}");
            Console.WriteLine($"  IsVirtual: {method.IsVirtual}");
            Console.WriteLine($"  IsAbstract: {method.IsAbstract}");

            // Parâmetros
            foreach (ParameterInfo param in method.GetParameters())
            {
                Console.WriteLine($"  Param: {param.Name} ({param.ParameterType.Name})");
                Console.WriteLine($"    IsOptional: {param.IsOptional}");
                if (param.HasDefaultValue)
                    Console.WriteLine($"    Default: {param.DefaultValue}");
            }
        }
    }

    // Listar construtores
    public void ListarConstrutores(Type tipo)
    {
        ConstructorInfo[] ctors = tipo.GetConstructors(
            BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);

        foreach (ConstructorInfo ctor in ctors)
        {
            Console.Write($"Construtor: {tipo.Name}(");
            var parameters = ctor.GetParameters();
            Console.Write(string.Join(", ",
                parameters.Select(p => $"{p.ParameterType.Name} {p.Name}")));
            Console.WriteLine(")");
        }
    }

    // Listar eventos
    public void ListarEventos(Type tipo)
    {
        EventInfo[] events = tipo.GetEvents();
        foreach (EventInfo evt in events)
        {
            Console.WriteLine($"Evento: {evt.Name}");
            Console.WriteLine($"  EventHandlerType: {evt.EventHandlerType?.Name}");
        }
    }
}
```

### 1.3 Invocando Membros Dinamicamente

```csharp
public class InvocacaoDinamica
{
    // Criar instância
    public object CriarInstancia(Type tipo)
    {
        // Com construtor padrão
        object obj1 = Activator.CreateInstance(tipo);

        // Com parâmetros
        object obj2 = Activator.CreateInstance(tipo, "param1", 123);

        // Via construtor específico
        ConstructorInfo ctor = tipo.GetConstructor(new[] { typeof(string) });
        object obj3 = ctor.Invoke(new object[] { "param" });

        return obj1;
    }

    // Criar instância genérica
    public T CriarInstancia<T>() where T : new()
    {
        return Activator.CreateInstance<T>();
    }

    // Criar tipo genérico em runtime
    public object CriarTipoGenerico(Type genericType, Type typeArg)
    {
        // Exemplo: List<T> com T = string
        Type constructed = genericType.MakeGenericType(typeArg);
        return Activator.CreateInstance(constructed);
    }

    // Acessar propriedade
    public object ObterPropriedade(object obj, string propName)
    {
        Type tipo = obj.GetType();
        PropertyInfo prop = tipo.GetProperty(propName);
        return prop?.GetValue(obj);
    }

    public void DefinirPropriedade(object obj, string propName, object value)
    {
        Type tipo = obj.GetType();
        PropertyInfo prop = tipo.GetProperty(propName);
        prop?.SetValue(obj, value);
    }

    // Acessar campo
    public object ObterCampo(object obj, string fieldName)
    {
        Type tipo = obj.GetType();
        FieldInfo field = tipo.GetField(fieldName,
            BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
        return field?.GetValue(obj);
    }

    public void DefinirCampo(object obj, string fieldName, object value)
    {
        Type tipo = obj.GetType();
        FieldInfo field = tipo.GetField(fieldName,
            BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
        field?.SetValue(obj, value);
    }

    // Invocar método
    public object InvocarMetodo(object obj, string methodName, params object[] args)
    {
        Type tipo = obj.GetType();
        MethodInfo method = tipo.GetMethod(methodName);
        return method?.Invoke(obj, args);
    }

    // Invocar método com tipos específicos
    public object InvocarMetodo(object obj, string methodName,
        Type[] paramTypes, object[] args)
    {
        Type tipo = obj.GetType();
        MethodInfo method = tipo.GetMethod(methodName, paramTypes);
        return method?.Invoke(obj, args);
    }

    // Invocar método estático
    public object InvocarMetodoEstatico(Type tipo, string methodName, params object[] args)
    {
        MethodInfo method = tipo.GetMethod(methodName,
            BindingFlags.Public | BindingFlags.Static);
        return method?.Invoke(null, args);
    }

    // Invocar método genérico
    public object InvocarMetodoGenerico(object obj, string methodName,
        Type[] typeArgs, object[] args)
    {
        Type tipo = obj.GetType();
        MethodInfo method = tipo.GetMethod(methodName);
        MethodInfo genericMethod = method.MakeGenericMethod(typeArgs);
        return genericMethod.Invoke(obj, args);
    }
}
```

## 2. Atributos Customizados

### 2.1 Definindo Atributos

```csharp
// Atributo simples
[AttributeUsage(AttributeTargets.Class | AttributeTargets.Method)]
public class MeuAtributoAttribute : Attribute
{
    public string Nome { get; }
    public int Versao { get; set; }

    public MeuAtributoAttribute(string nome)
    {
        Nome = nome;
    }
}

// Atributo com múltiplas ocorrências permitidas
[AttributeUsage(AttributeTargets.Property, AllowMultiple = true)]
public class ValidacaoAttribute : Attribute
{
    public string Regra { get; }
    public string Mensagem { get; set; }

    public ValidacaoAttribute(string regra)
    {
        Regra = regra;
    }
}

// Atributo herdável
[AttributeUsage(AttributeTargets.Class, Inherited = true)]
public class AuditavelAttribute : Attribute
{
    public bool LogarCriacao { get; set; } = true;
    public bool LogarAlteracao { get; set; } = true;
}

// Uso
[MeuAtributo("Exemplo", Versao = 2)]
[Auditavel(LogarAlteracao = false)]
public class MinhaClasse
{
    [Validacao("required", Mensagem = "Campo obrigatório")]
    [Validacao("maxlength:50", Mensagem = "Máximo 50 caracteres")]
    public string Nome { get; set; }

    [MeuAtributo("MetodoEspecial")]
    public void MeuMetodo() { }
}
```

### 2.2 Lendo Atributos

```csharp
public class LeitorAtributos
{
    // Verificar se tem atributo
    public bool TemAtributo<T>(Type tipo) where T : Attribute
    {
        return tipo.IsDefined(typeof(T), inherit: true);
    }

    // Obter atributo
    public T ObterAtributo<T>(Type tipo) where T : Attribute
    {
        return tipo.GetCustomAttribute<T>(inherit: true);
    }

    // Obter múltiplos atributos
    public IEnumerable<T> ObterAtributos<T>(MemberInfo membro) where T : Attribute
    {
        return membro.GetCustomAttributes<T>(inherit: true);
    }

    // Ler atributos de propriedades
    public void LerAtributosPropriedades(Type tipo)
    {
        foreach (PropertyInfo prop in tipo.GetProperties())
        {
            var validacoes = prop.GetCustomAttributes<ValidacaoAttribute>();
            foreach (var val in validacoes)
            {
                Console.WriteLine($"{prop.Name}: {val.Regra} - {val.Mensagem}");
            }
        }
    }

    // Sistema de validação baseado em atributos
    public List<string> Validar(object obj)
    {
        var erros = new List<string>();
        Type tipo = obj.GetType();

        foreach (PropertyInfo prop in tipo.GetProperties())
        {
            object valor = prop.GetValue(obj);

            foreach (ValidacaoAttribute val in prop.GetCustomAttributes<ValidacaoAttribute>())
            {
                if (!ValidarRegra(val.Regra, valor))
                {
                    erros.Add(val.Mensagem ?? $"Erro em {prop.Name}");
                }
            }
        }

        return erros;
    }

    private bool ValidarRegra(string regra, object valor)
    {
        if (regra == "required")
            return valor != null && !string.IsNullOrEmpty(valor.ToString());

        if (regra.StartsWith("maxlength:"))
        {
            int max = int.Parse(regra.Split(':')[1]);
            return valor == null || valor.ToString().Length <= max;
        }

        return true;
    }
}
```

## 3. Assemblies

### 3.1 Carregando e Explorando Assemblies

```csharp
public class AssemblyManager
{
    // Carregar assembly
    public Assembly CarregarAssembly(string path)
    {
        // Por arquivo
        Assembly asm1 = Assembly.LoadFrom(path);

        // Por nome
        Assembly asm2 = Assembly.Load("System.Text.Json");

        // Por bytes (útil para carregar da memória)
        byte[] bytes = File.ReadAllBytes(path);
        Assembly asm3 = Assembly.Load(bytes);

        return asm1;
    }

    // Listar tipos do assembly
    public void ListarTipos(Assembly assembly)
    {
        foreach (Type tipo in assembly.GetTypes())
        {
            Console.WriteLine($"{tipo.FullName}");
            Console.WriteLine($"  IsPublic: {tipo.IsPublic}");
            Console.WriteLine($"  IsClass: {tipo.IsClass}");
        }
    }

    // Apenas tipos públicos exportados
    public Type[] ObterTiposPublicos(Assembly assembly)
    {
        return assembly.GetExportedTypes();
    }

    // Encontrar tipos que implementam interface
    public Type[] EncontrarImplementacoes<TInterface>(Assembly assembly)
    {
        return assembly.GetTypes()
            .Where(t => typeof(TInterface).IsAssignableFrom(t) &&
                       !t.IsInterface && !t.IsAbstract)
            .ToArray();
    }

    // Encontrar tipos com atributo
    public Type[] EncontrarComAtributo<TAtributo>(Assembly assembly)
        where TAtributo : Attribute
    {
        return assembly.GetTypes()
            .Where(t => t.IsDefined(typeof(TAtributo), true))
            .ToArray();
    }

    // Informações do assembly
    public void InfoAssembly(Assembly assembly)
    {
        Console.WriteLine($"Nome: {assembly.GetName().Name}");
        Console.WriteLine($"Versão: {assembly.GetName().Version}");
        Console.WriteLine($"Location: {assembly.Location}");
        Console.WriteLine($"FullName: {assembly.FullName}");

        // Assemblies referenciadas
        foreach (AssemblyName refAsm in assembly.GetReferencedAssemblies())
        {
            Console.WriteLine($"  Referencia: {refAsm.Name} v{refAsm.Version}");
        }

        // Recursos embutidos
        foreach (string resource in assembly.GetManifestResourceNames())
        {
            Console.WriteLine($"  Recurso: {resource}");
        }
    }

    // Ler recurso embutido
    public string LerRecursoEmbutido(Assembly assembly, string resourceName)
    {
        using Stream stream = assembly.GetManifestResourceStream(resourceName);
        using StreamReader reader = new StreamReader(stream);
        return reader.ReadToEnd();
    }
}
```

### 3.2 Plugin System com Reflection

```csharp
// Interface do plugin
public interface IPlugin
{
    string Nome { get; }
    void Executar();
}

// Gerenciador de plugins
public class PluginManager
{
    private List<IPlugin> _plugins = new List<IPlugin>();

    public void CarregarPlugins(string pasta)
    {
        foreach (string arquivo in Directory.GetFiles(pasta, "*.dll"))
        {
            try
            {
                Assembly assembly = Assembly.LoadFrom(arquivo);
                CarregarPluginsDeAssembly(assembly);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Erro ao carregar {arquivo}: {ex.Message}");
            }
        }
    }

    private void CarregarPluginsDeAssembly(Assembly assembly)
    {
        Type[] tipos = assembly.GetTypes()
            .Where(t => typeof(IPlugin).IsAssignableFrom(t) &&
                       !t.IsInterface && !t.IsAbstract)
            .ToArray();

        foreach (Type tipo in tipos)
        {
            IPlugin plugin = (IPlugin)Activator.CreateInstance(tipo);
            _plugins.Add(plugin);
            Console.WriteLine($"Plugin carregado: {plugin.Nome}");
        }
    }

    public void ExecutarTodos()
    {
        foreach (IPlugin plugin in _plugins)
        {
            try
            {
                plugin.Executar();
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Erro no plugin {plugin.Nome}: {ex.Message}");
            }
        }
    }

    public IEnumerable<IPlugin> Plugins => _plugins;
}
```

## 4. Geração Dinâmica de Código

### 4.1 Reflection.Emit - Gerando IL Dinamicamente

```csharp
using System.Reflection.Emit;

public class EmitExemplos
{
    // Criar método dinâmico simples
    public Func<int, int, int> CriarMetodoSoma()
    {
        DynamicMethod dm = new DynamicMethod(
            "Somar",
            typeof(int),
            new[] { typeof(int), typeof(int) });

        ILGenerator il = dm.GetILGenerator();

        il.Emit(OpCodes.Ldarg_0);  // Carrega primeiro argumento
        il.Emit(OpCodes.Ldarg_1);  // Carrega segundo argumento
        il.Emit(OpCodes.Add);      // Soma
        il.Emit(OpCodes.Ret);      // Retorna

        return (Func<int, int, int>)dm.CreateDelegate(typeof(Func<int, int, int>));
    }

    // Criar tipo dinâmico completo
    public Type CriarTipoDinamico()
    {
        AssemblyName assemblyName = new AssemblyName("DynamicAssembly");
        AssemblyBuilder assemblyBuilder = AssemblyBuilder.DefineDynamicAssembly(
            assemblyName, AssemblyBuilderAccess.Run);

        ModuleBuilder moduleBuilder = assemblyBuilder.DefineDynamicModule("MainModule");

        TypeBuilder typeBuilder = moduleBuilder.DefineType(
            "DynamicClass",
            TypeAttributes.Public | TypeAttributes.Class);

        // Adicionar campo
        FieldBuilder fieldBuilder = typeBuilder.DefineField(
            "_valor", typeof(int), FieldAttributes.Private);

        // Adicionar propriedade
        PropertyBuilder propBuilder = typeBuilder.DefineProperty(
            "Valor", PropertyAttributes.HasDefault, typeof(int), null);

        // Getter
        MethodBuilder getMethod = typeBuilder.DefineMethod(
            "get_Valor",
            MethodAttributes.Public | MethodAttributes.SpecialName | MethodAttributes.HideBySig,
            typeof(int), Type.EmptyTypes);

        ILGenerator getIL = getMethod.GetILGenerator();
        getIL.Emit(OpCodes.Ldarg_0);
        getIL.Emit(OpCodes.Ldfld, fieldBuilder);
        getIL.Emit(OpCodes.Ret);

        // Setter
        MethodBuilder setMethod = typeBuilder.DefineMethod(
            "set_Valor",
            MethodAttributes.Public | MethodAttributes.SpecialName | MethodAttributes.HideBySig,
            null, new[] { typeof(int) });

        ILGenerator setIL = setMethod.GetILGenerator();
        setIL.Emit(OpCodes.Ldarg_0);
        setIL.Emit(OpCodes.Ldarg_1);
        setIL.Emit(OpCodes.Stfld, fieldBuilder);
        setIL.Emit(OpCodes.Ret);

        propBuilder.SetGetMethod(getMethod);
        propBuilder.SetSetMethod(setMethod);

        // Adicionar método
        MethodBuilder methodBuilder = typeBuilder.DefineMethod(
            "Dobrar",
            MethodAttributes.Public,
            typeof(int), Type.EmptyTypes);

        ILGenerator methodIL = methodBuilder.GetILGenerator();
        methodIL.Emit(OpCodes.Ldarg_0);
        methodIL.Emit(OpCodes.Ldfld, fieldBuilder);
        methodIL.Emit(OpCodes.Ldc_I4_2);
        methodIL.Emit(OpCodes.Mul);
        methodIL.Emit(OpCodes.Ret);

        return typeBuilder.CreateType();
    }

    // Usar tipo dinâmico
    public void UsarTipoDinamico()
    {
        Type tipo = CriarTipoDinamico();
        object instancia = Activator.CreateInstance(tipo);

        // Definir propriedade
        tipo.GetProperty("Valor").SetValue(instancia, 10);

        // Chamar método
        int resultado = (int)tipo.GetMethod("Dobrar").Invoke(instancia, null);
        Console.WriteLine($"Resultado: {resultado}"); // 20
    }
}
```

### 4.2 Expression Trees

```csharp
using System.Linq.Expressions;

public class ExpressionTreeExemplos
{
    // Criar expressão lambda simples
    public Func<int, int, int> CriarSoma()
    {
        ParameterExpression a = Expression.Parameter(typeof(int), "a");
        ParameterExpression b = Expression.Parameter(typeof(int), "b");

        BinaryExpression soma = Expression.Add(a, b);

        Expression<Func<int, int, int>> lambda =
            Expression.Lambda<Func<int, int, int>>(soma, a, b);

        return lambda.Compile();
    }

    // Criar getter dinâmico (muito mais rápido que reflection)
    public Func<T, TProperty> CriarGetter<T, TProperty>(string propertyName)
    {
        ParameterExpression param = Expression.Parameter(typeof(T), "x");
        MemberExpression property = Expression.Property(param, propertyName);

        return Expression.Lambda<Func<T, TProperty>>(property, param).Compile();
    }

    // Criar setter dinâmico
    public Action<T, TProperty> CriarSetter<T, TProperty>(string propertyName)
    {
        ParameterExpression param = Expression.Parameter(typeof(T), "x");
        ParameterExpression value = Expression.Parameter(typeof(TProperty), "value");

        MemberExpression property = Expression.Property(param, propertyName);
        BinaryExpression assign = Expression.Assign(property, value);

        return Expression.Lambda<Action<T, TProperty>>(assign, param, value).Compile();
    }

    // Criar filtro dinâmico (Where)
    public Func<T, bool> CriarFiltro<T>(string propertyName, object valor)
    {
        ParameterExpression param = Expression.Parameter(typeof(T), "x");
        MemberExpression property = Expression.Property(param, propertyName);
        ConstantExpression constant = Expression.Constant(valor);
        BinaryExpression equals = Expression.Equal(property, constant);

        return Expression.Lambda<Func<T, bool>>(equals, param).Compile();
    }

    // Construtor de queries dinâmicas
    public class QueryBuilder<T>
    {
        private ParameterExpression _param = Expression.Parameter(typeof(T), "x");
        private Expression _filter = Expression.Constant(true);

        public QueryBuilder<T> Where(string property, string op, object value)
        {
            MemberExpression prop = Expression.Property(_param, property);
            ConstantExpression val = Expression.Constant(value);

            Expression comparison = op switch
            {
                "==" => Expression.Equal(prop, val),
                "!=" => Expression.NotEqual(prop, val),
                ">" => Expression.GreaterThan(prop, val),
                "<" => Expression.LessThan(prop, val),
                ">=" => Expression.GreaterThanOrEqual(prop, val),
                "<=" => Expression.LessThanOrEqual(prop, val),
                "contains" => Expression.Call(prop,
                    typeof(string).GetMethod("Contains", new[] { typeof(string) }),
                    val),
                _ => throw new ArgumentException($"Operador desconhecido: {op}")
            };

            _filter = Expression.AndAlso(_filter, comparison);
            return this;
        }

        public Func<T, bool> Build()
        {
            return Expression.Lambda<Func<T, bool>>(_filter, _param).Compile();
        }

        public Expression<Func<T, bool>> BuildExpression()
        {
            return Expression.Lambda<Func<T, bool>>(_filter, _param);
        }
    }

    // Uso
    public void ExemploQueryBuilder()
    {
        var filtro = new QueryBuilder<Pessoa>()
            .Where("Idade", ">=", 18)
            .Where("Nome", "contains", "Silva")
            .Build();

        var pessoas = new List<Pessoa>();
        var resultado = pessoas.Where(filtro).ToList();
    }
}
```

## 5. Source Generators (C# 9+)

### 5.1 Básico de Source Generator

```csharp
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp.Syntax;
using Microsoft.CodeAnalysis.Text;
using System.Text;

// Este código vai em um projeto separado (analyzer)
[Generator]
public class HelloSourceGenerator : ISourceGenerator
{
    public void Initialize(GeneratorInitializationContext context)
    {
        // Opcional: registrar syntax receiver para filtrar nós
        context.RegisterForSyntaxNotifications(() => new SyntaxReceiver());
    }

    public void Execute(GeneratorExecutionContext context)
    {
        // Gerar código
        string source = @"
namespace Generated
{
    public static class HelloWorld
    {
        public static void SayHello() =>
            System.Console.WriteLine(""Hello from generated code!"");
    }
}";
        context.AddSource("HelloWorld.g.cs", SourceText.From(source, Encoding.UTF8));
    }

    private class SyntaxReceiver : ISyntaxReceiver
    {
        public List<ClassDeclarationSyntax> Classes { get; } = new();

        public void OnVisitSyntaxNode(SyntaxNode syntaxNode)
        {
            if (syntaxNode is ClassDeclarationSyntax classDecl)
            {
                Classes.Add(classDecl);
            }
        }
    }
}
```

### 5.2 Source Generator para Auto-Implementar Interface

```csharp
[Generator]
public class AutoImplementGenerator : ISourceGenerator
{
    public void Initialize(GeneratorInitializationContext context)
    {
        context.RegisterForSyntaxNotifications(() => new InterfaceReceiver());
    }

    public void Execute(GeneratorExecutionContext context)
    {
        if (context.SyntaxReceiver is not InterfaceReceiver receiver)
            return;

        foreach (var interfaceDecl in receiver.Interfaces)
        {
            // Obter modelo semântico
            SemanticModel model = context.Compilation
                .GetSemanticModel(interfaceDecl.SyntaxTree);

            INamedTypeSymbol symbol = model
                .GetDeclaredSymbol(interfaceDecl) as INamedTypeSymbol;

            if (symbol == null) continue;

            // Gerar implementação
            string className = $"{symbol.Name}Impl";
            StringBuilder sb = new StringBuilder();

            sb.AppendLine($"namespace {symbol.ContainingNamespace}");
            sb.AppendLine("{");
            sb.AppendLine($"    public class {className} : {symbol.Name}");
            sb.AppendLine("    {");

            // Gerar propriedades
            foreach (var member in symbol.GetMembers().OfType<IPropertySymbol>())
            {
                sb.AppendLine($"        public {member.Type} {member.Name} {{ get; set; }}");
            }

            // Gerar métodos
            foreach (var member in symbol.GetMembers().OfType<IMethodSymbol>())
            {
                if (member.MethodKind == MethodKind.PropertyGet ||
                    member.MethodKind == MethodKind.PropertySet)
                    continue;

                string parameters = string.Join(", ",
                    member.Parameters.Select(p => $"{p.Type} {p.Name}"));

                string returnType = member.ReturnType.ToDisplayString();

                sb.AppendLine($"        public {returnType} {member.Name}({parameters})");
                sb.AppendLine("        {");

                if (returnType != "void")
                    sb.AppendLine($"            return default;");

                sb.AppendLine("        }");
            }

            sb.AppendLine("    }");
            sb.AppendLine("}");

            context.AddSource($"{className}.g.cs",
                SourceText.From(sb.ToString(), Encoding.UTF8));
        }
    }

    private class InterfaceReceiver : ISyntaxReceiver
    {
        public List<InterfaceDeclarationSyntax> Interfaces { get; } = new();

        public void OnVisitSyntaxNode(SyntaxNode syntaxNode)
        {
            if (syntaxNode is InterfaceDeclarationSyntax interfaceDecl)
            {
                // Filtrar por atributo específico se necessário
                Interfaces.Add(interfaceDecl);
            }
        }
    }
}
```

## 6. Performance: Delegates vs Reflection

```csharp
public class PerformanceComparison
{
    private PropertyInfo _propertyInfo;
    private Func<Pessoa, string> _compiledGetter;
    private Action<Pessoa, string> _compiledSetter;

    public PerformanceComparison()
    {
        // Setup reflection
        _propertyInfo = typeof(Pessoa).GetProperty("Nome");

        // Setup compiled expression
        _compiledGetter = CreateGetter();
        _compiledSetter = CreateSetter();
    }

    private Func<Pessoa, string> CreateGetter()
    {
        var param = Expression.Parameter(typeof(Pessoa));
        var property = Expression.Property(param, "Nome");
        return Expression.Lambda<Func<Pessoa, string>>(property, param).Compile();
    }

    private Action<Pessoa, string> CreateSetter()
    {
        var param = Expression.Parameter(typeof(Pessoa));
        var value = Expression.Parameter(typeof(string));
        var property = Expression.Property(param, "Nome");
        var assign = Expression.Assign(property, value);
        return Expression.Lambda<Action<Pessoa, string>>(assign, param, value).Compile();
    }

    // Teste de performance
    public void Benchmark()
    {
        Pessoa pessoa = new Pessoa { Nome = "Teste" };
        int iterations = 1000000;

        // Acesso direto (mais rápido)
        var sw1 = Stopwatch.StartNew();
        for (int i = 0; i < iterations; i++)
        {
            string nome = pessoa.Nome;
            pessoa.Nome = nome;
        }
        sw1.Stop();
        Console.WriteLine($"Direto: {sw1.ElapsedMilliseconds}ms");

        // Expression compilada (quase igual)
        var sw2 = Stopwatch.StartNew();
        for (int i = 0; i < iterations; i++)
        {
            string nome = _compiledGetter(pessoa);
            _compiledSetter(pessoa, nome);
        }
        sw2.Stop();
        Console.WriteLine($"Expression: {sw2.ElapsedMilliseconds}ms");

        // Reflection (mais lento)
        var sw3 = Stopwatch.StartNew();
        for (int i = 0; i < iterations; i++)
        {
            string nome = (string)_propertyInfo.GetValue(pessoa);
            _propertyInfo.SetValue(pessoa, nome);
        }
        sw3.Stop();
        Console.WriteLine($"Reflection: {sw3.ElapsedMilliseconds}ms");
    }
}
```

## 7. Serialização com Reflection

```csharp
public class SimpleSerializer
{
    // Serializar para dicionário
    public Dictionary<string, object> ToDictionary(object obj)
    {
        var dict = new Dictionary<string, object>();
        Type tipo = obj.GetType();

        foreach (PropertyInfo prop in tipo.GetProperties(BindingFlags.Public | BindingFlags.Instance))
        {
            if (prop.CanRead)
            {
                dict[prop.Name] = prop.GetValue(obj);
            }
        }

        return dict;
    }

    // Deserializar de dicionário
    public T FromDictionary<T>(Dictionary<string, object> dict) where T : new()
    {
        T obj = new T();
        Type tipo = typeof(T);

        foreach (var kvp in dict)
        {
            PropertyInfo prop = tipo.GetProperty(kvp.Key);
            if (prop != null && prop.CanWrite)
            {
                object value = Convert.ChangeType(kvp.Value, prop.PropertyType);
                prop.SetValue(obj, value);
            }
        }

        return obj;
    }

    // Clone profundo usando reflection
    public T DeepClone<T>(T obj)
    {
        if (obj == null) return default;

        Type tipo = obj.GetType();

        if (tipo.IsValueType || tipo == typeof(string))
            return obj;

        if (tipo.IsArray)
        {
            Type elementType = tipo.GetElementType();
            Array array = obj as Array;
            Array copied = Array.CreateInstance(elementType, array.Length);
            for (int i = 0; i < array.Length; i++)
            {
                copied.SetValue(DeepClone(array.GetValue(i)), i);
            }
            return (T)(object)copied;
        }

        object clone = Activator.CreateInstance(tipo);

        foreach (FieldInfo field in tipo.GetFields(
            BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance))
        {
            object value = field.GetValue(obj);
            field.SetValue(clone, DeepClone(value));
        }

        return (T)clone;
    }
}
```

Este guia cobre Reflection e Metaprogramação avançada em C#!
