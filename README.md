# 🦊 IAFOX

**IA Local sem Restrições para Desenvolvimento**

IAFOX é um assistente de IA que roda 100% no seu computador, pode editar arquivos localmente e não tem as restrições de APIs comerciais.

## ✨ Funcionalidades

- 🤖 **IA Local** - Roda no seu PC usando Ollama
- 📁 **Gerenciamento de Arquivos** - Lê, cria e edita arquivos
- 💻 **Execução de Comandos** - Roda comandos no terminal
- 🧠 **Sistema RAG** - Aprende com seus documentos
- 🔒 **100% Privado** - Seus dados nunca saem do seu PC
- 🚀 **Sem Restrições** - Ajuda com qualquer código

## 📋 Requisitos

### Hardware Recomendado
- **GPU**: NVIDIA com 8GB+ VRAM (24GB para modelos grandes)
- **RAM**: 32GB+ (64GB recomendado)
- **Storage**: 50GB+ livre para modelos

### Software
- Windows 10/11 ou Linux
- Python 3.10+
- [Ollama](https://ollama.com/download)
- NVIDIA CUDA (para GPU)

## 🚀 Instalação Rápida (Windows)

### Opção 1: Script Automático

```powershell
# Execute no PowerShell como Administrador
.\scripts\install_windows.ps1
```

### Opção 2: Instalação Manual

1. **Instale o Ollama**
   - Baixe em: https://ollama.com/download
   - Execute o instalador

2. **Baixe um modelo**
   ```bash
   # Para GPU com 24GB (RTX 4090)
   ollama pull qwen2.5-coder:32b

   # Para GPU com 12GB
   ollama pull qwen2.5-coder:14b

   # Para GPU com 8GB
   ollama pull qwen2.5-coder:7b
   ```

3. **Instale o IAFOX**
   ```bash
   # Clone o repositório
   git clone https://github.com/seu-usuario/IAFOX.git
   cd IAFOX

   # Crie ambiente virtual
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # source .venv/bin/activate  # Linux

   # Instale dependências
   pip install -e ".[dev]"
   ```

## 🎮 Como Usar

### Interface CLI (Terminal)

```bash
# Ative o ambiente virtual
.venv\Scripts\activate

# Inicie o IAFOX
iafox chat

# Ou com modelo específico
iafox chat --model qwen2.5-coder:32b

# Ou em um diretório específico
iafox chat --workspace C:\meus\projetos
```

**Comandos no chat:**
- `/help` - Mostra ajuda
- `/clear` - Limpa conversa
- `/model` - Lista modelos
- `/tree` - Mostra arquivos
- `/exit` - Sai

### Interface Web (Navegador)

```bash
# Ative o ambiente virtual
.venv\Scripts\activate

# Inicie o servidor
python -m uvicorn iafox.web.api:app --host 0.0.0.0 --port 8000

# Ou use o script
start_web.bat  # Windows
```

Acesse: http://localhost:8000

### API REST

```bash
# Chat
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Crie uma função de fibonacci"}'

# Ler arquivo
curl http://localhost:8000/api/files/read?path=main.py

# Listar arquivos
curl http://localhost:8000/api/files?path=.

# Executar comando
curl -X POST http://localhost:8000/api/execute \
  -H "Content-Type: application/json" \
  -d '{"command": "dir"}'
```

## 🧠 Sistema RAG (Base de Conhecimento)

O RAG permite que a IA "aprenda" consultando seus documentos antes de responder.

```python
from iafox.rag.knowledge_base import knowledge_base

# Adiciona arquivo
await knowledge_base.add_file("documentacao.pdf")

# Adiciona diretório inteiro
await knowledge_base.add_directory("./meus_projetos", pattern="*.py")

# Busca informações
results = await knowledge_base.search("como fazer autenticação")

# Obtém contexto para o prompt
context = await knowledge_base.get_context("como usar a API")
```

## 📁 Estrutura do Projeto

```
IAFOX/
├── iafox/
│   ├── core/           # Lógica principal
│   │   ├── agent.py    # Agente IA
│   │   └── config.py   # Configurações
│   ├── cli/            # Interface terminal
│   │   └── main.py
│   ├── web/            # Interface web
│   │   ├── api.py      # API REST
│   │   └── templates/  # HTML
│   ├── llm/            # Integração Ollama
│   │   └── ollama_client.py
│   ├── files/          # Gerenciamento arquivos
│   │   └── manager.py
│   └── rag/            # Base de conhecimento
│       └── knowledge_base.py
├── scripts/            # Scripts instalação
├── tests/              # Testes
├── data/               # Dados RAG
└── pyproject.toml
```

## ⚙️ Configuração

Crie `~/.iafox/config.json`:

```json
{
  "ollama": {
    "host": "http://localhost:11434",
    "model": "qwen2.5-coder:32b",
    "timeout": 300
  },
  "files": {
    "workspace": "C:\\meus\\projetos",
    "max_file_size": 10485760
  },
  "rag": {
    "enabled": true,
    "chunk_size": 1000
  },
  "web": {
    "host": "0.0.0.0",
    "port": 8000
  }
}
```

## 🔧 Modelos Recomendados

| Modelo | VRAM | Qualidade | Velocidade |
|--------|------|-----------|------------|
| qwen2.5-coder:32b | 20GB | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| qwen2.5-coder:14b | 10GB | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| qwen2.5-coder:7b | 6GB | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| deepseek-coder-v2:16b | 12GB | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| codestral:22b | 14GB | ⭐⭐⭐⭐ | ⭐⭐⭐ |

## 🐛 Troubleshooting

### Ollama não conecta
```bash
# Verifique se está rodando
ollama serve

# Teste
curl http://localhost:11434/api/tags
```

### Modelo muito lento
- Use modelo menor (7b ou 14b)
- Verifique se GPU está sendo usada
- Feche outros programas

### Erro de memória
- Use modelo quantizado (q4_0, q4_k_m)
- Reduza tamanho do contexto
- Feche aplicativos pesados

## 📜 Licença

MIT License - Use como quiser!

## 🤝 Contribuindo

1. Fork o projeto
2. Crie sua branch (`git checkout -b feature/nova-feature`)
3. Commit (`git commit -m 'Adiciona nova feature'`)
4. Push (`git push origin feature/nova-feature`)
5. Abra um Pull Request

---

Feito com 🦊 por IAFOX Team
