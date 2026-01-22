"""
Indexador de documentos para o sistema RAG do IAFOX.
Lê PDFs e arquivos Markdown da pasta conhecimento e cria um índice pesquisável.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict

# Diretórios
BASE_DIR = Path(__file__).parent.parent.parent.parent
CONHECIMENTO_DIR = BASE_DIR / "conhecimento"
LIVROS_DIR = CONHECIMENTO_DIR / "livros_8ano"
PROGRAMACAO_DIR = CONHECIMENTO_DIR / "programacao"
INDEX_DIR = CONHECIMENTO_DIR / "index"


def extrair_texto_pdf(pdf_path: str) -> List[Dict]:
    """Extrai texto de um PDF, retornando lista de chunks com metadados."""
    from PyPDF2 import PdfReader

    chunks = []
    try:
        reader = PdfReader(pdf_path)
        nome_arquivo = Path(pdf_path).stem

        # Detectar matéria pelo nome do arquivo ou pasta
        materia = detectar_materia(pdf_path)

        texto_acumulado = ""
        pagina_inicio = 1

        for i, page in enumerate(reader.pages):
            texto = page.extract_text() or ""
            texto_acumulado += texto + "\n"

            # Criar chunk a cada ~1000 caracteres ou a cada 3 páginas
            if len(texto_acumulado) >= 1000 or (i + 1) % 3 == 0:
                if texto_acumulado.strip():
                    chunks.append({
                        "texto": texto_acumulado.strip(),
                        "arquivo": nome_arquivo,
                        "materia": materia,
                        "paginas": f"{pagina_inicio}-{i+1}",
                        "fonte": pdf_path
                    })
                texto_acumulado = ""
                pagina_inicio = i + 2

        # Último chunk
        if texto_acumulado.strip():
            chunks.append({
                "texto": texto_acumulado.strip(),
                "arquivo": nome_arquivo,
                "materia": materia,
                "paginas": f"{pagina_inicio}-{len(reader.pages)}",
                "fonte": pdf_path
            })

        print(f"  ✓ {nome_arquivo}: {len(chunks)} chunks extraídos")

    except Exception as e:
        print(f"  ✗ Erro ao ler {pdf_path}: {e}")

    return chunks


def detectar_materia(caminho: str) -> str:
    """Detecta a matéria baseado no caminho ou nome do arquivo."""
    caminho_lower = caminho.lower()

    materias = {
        "matematica": ["matematica", "math", "mat"],
        "portugues": ["portugues", "portugus", "lingua", "redacao"],
        "ciencias": ["ciencias", "ciencia", "biologia", "fisica", "quimica"],
        "historia": ["historia", "hist"],
        "geografia": ["geografia", "geo"],
        "ingles": ["ingles", "english", "ing"],
        "arte": ["arte", "artes"],
        "educacao_fisica": ["educacao_fisica", "ed_fisica", "edfisica"],
    }

    for materia, keywords in materias.items():
        for keyword in keywords:
            if keyword in caminho_lower:
                return materia

    return "geral"


def encontrar_pdfs(diretorio: Path) -> List[str]:
    """Encontra todos os PDFs em um diretório e subdiretórios."""
    pdfs = []
    for root, dirs, files in os.walk(diretorio):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdfs.append(os.path.join(root, file))
    return pdfs


def extrair_texto_markdown(md_path: str) -> List[Dict]:
    """Extrai texto de um arquivo Markdown, retornando lista de chunks com metadados."""
    chunks = []
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            conteudo = f.read()

        nome_arquivo = Path(md_path).stem
        categoria = detectar_categoria(md_path)

        # Divide por seções (## ou ###)
        secoes = []
        secao_atual = ""
        titulo_atual = nome_arquivo

        for linha in conteudo.split('\n'):
            if linha.startswith('## ') or linha.startswith('### '):
                if secao_atual.strip():
                    secoes.append((titulo_atual, secao_atual.strip()))
                titulo_atual = linha.lstrip('#').strip()
                secao_atual = linha + '\n'
            else:
                secao_atual += linha + '\n'

        if secao_atual.strip():
            secoes.append((titulo_atual, secao_atual.strip()))

        # Cria chunks das seções
        for titulo, texto in secoes:
            # Se seção muito grande, divide em chunks menores
            if len(texto) > 1500:
                partes = [texto[i:i+1500] for i in range(0, len(texto), 1200)]
                for i, parte in enumerate(partes):
                    chunks.append({
                        "texto": parte,
                        "arquivo": nome_arquivo,
                        "materia": categoria,
                        "paginas": f"{titulo} (parte {i+1})",
                        "fonte": md_path
                    })
            else:
                chunks.append({
                    "texto": texto,
                    "arquivo": nome_arquivo,
                    "materia": categoria,
                    "paginas": titulo,
                    "fonte": md_path
                })

        print(f"  ✓ {nome_arquivo}.md: {len(chunks)} chunks extraídos")

    except Exception as e:
        print(f"  ✗ Erro ao ler {md_path}: {e}")

    return chunks


def encontrar_markdowns(diretorio: Path) -> List[str]:
    """Encontra todos os arquivos Markdown em um diretório e subdiretórios."""
    mds = []
    for root, dirs, files in os.walk(diretorio):
        for file in files:
            if file.lower().endswith('.md'):
                mds.append(os.path.join(root, file))
    return mds


def detectar_categoria(caminho: str) -> str:
    """Detecta a categoria baseado no caminho."""
    caminho_lower = caminho.lower()

    categorias = {
        "csharp": ["csharp", "c#", "dotnet", ".net"],
        "python": ["python", "py"],
        "javascript": ["javascript", "js", "node", "typescript", "ts"],
        "java": ["java"],
        "remote_desktop": ["remote", "desktop", "rdp", "vnc"],
        "networking": ["network", "socket", "tcp", "udp", "http"],
        "matematica": ["matematica", "math", "mat"],
        "portugues": ["portugues", "portugus", "lingua", "redacao"],
        "ciencias": ["ciencias", "ciencia", "biologia", "fisica", "quimica"],
        "historia": ["historia", "hist"],
        "geografia": ["geografia", "geo"],
        "ingles": ["ingles", "english", "ing"],
    }

    for categoria, keywords in categorias.items():
        for keyword in keywords:
            if keyword in caminho_lower:
                return categoria

    return "geral"


def criar_index(chunks: List[Dict]):
    """Cria o índice vetorial usando ChromaDB."""
    import chromadb
    from chromadb.config import Settings

    print("\n📊 Criando índice vetorial...")

    # Criar cliente ChromaDB persistente
    client = chromadb.PersistentClient(
        path=str(INDEX_DIR),
        settings=Settings(anonymized_telemetry=False)
    )

    # Deletar coleção existente se houver
    try:
        client.delete_collection("conhecimento_iafox")
        print("  → Índice anterior removido")
    except:
        pass

    # Criar nova coleção
    collection = client.create_collection(
        name="conhecimento_iafox",
        metadata={"description": "Base de conhecimento IAFOX"}
    )

    # Adicionar chunks ao índice
    print(f"  → Indexando {len(chunks)} chunks...")

    # Processar em lotes de 100
    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]

        ids = [f"chunk_{i+j}" for j in range(len(batch))]
        documents = [c["texto"] for c in batch]
        metadatas = [{
            "arquivo": c["arquivo"],
            "materia": c["materia"],
            "paginas": c["paginas"],
            "fonte": c["fonte"]
        } for c in batch]

        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

        print(f"  → Lote {i//batch_size + 1}/{(len(chunks)-1)//batch_size + 1} indexado")

    print(f"\n✅ Índice criado com sucesso!")
    print(f"   Total de chunks: {len(chunks)}")
    print(f"   Local: {INDEX_DIR}")


def main():
    """Função principal do indexador."""
    print("=" * 50)
    print("🦊 IAFOX - Indexador de Conhecimento RAG")
    print("=" * 50)

    # Criar pastas se não existirem
    LIVROS_DIR.mkdir(parents=True, exist_ok=True)
    PROGRAMACAO_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    todos_chunks = []

    # 1. Buscar PDFs (livros)
    pdfs = encontrar_pdfs(LIVROS_DIR)
    if pdfs:
        print(f"\n📚 Encontrados {len(pdfs)} PDFs:")
        for pdf in pdfs:
            print(f"   • {Path(pdf).name}")

        print("\n📖 Extraindo texto dos PDFs...")
        for pdf in pdfs:
            chunks = extrair_texto_pdf(pdf)
            todos_chunks.extend(chunks)

    # 2. Buscar Markdowns (programação e outros)
    mds = encontrar_markdowns(CONHECIMENTO_DIR)
    if mds:
        print(f"\n📄 Encontrados {len(mds)} arquivos Markdown:")
        for md in mds:
            print(f"   • {Path(md).name}")

        print("\n📖 Extraindo texto dos Markdowns...")
        for md in mds:
            chunks = extrair_texto_markdown(md)
            todos_chunks.extend(chunks)

    if not todos_chunks:
        print("\n❌ Nenhum documento encontrado para indexar.")
        print("\nAdicione documentos nas pastas:")
        print("   • conhecimento/livros_8ano/ (PDFs)")
        print("   • conhecimento/programacao/ (Markdown)")
        return

    print(f"\n📝 Total de chunks extraídos: {len(todos_chunks)}")

    # Criar índice
    criar_index(todos_chunks)

    print("\n🎉 Indexação concluída!")
    print("   A IAFOX agora pode consultar o conhecimento usando:")
    print("   • 'buscar_livros' para matérias escolares")
    print("   • 'buscar_conhecimento' para programação e outros")


if __name__ == "__main__":
    main()
