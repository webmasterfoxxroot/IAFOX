"""Tool para gerar imagens com FLUX.1 via ComfyUI"""
import asyncio
import base64
from pathlib import Path
from datetime import datetime
from typing import Optional
from .comfyui_client import ComfyUIClient


class GeradorImagem:
    """Gera imagens usando FLUX.1 via ComfyUI"""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8188,
        output_dir: str = "./imagens_geradas"
    ):
        self.client = ComfyUIClient(host, port)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def verificar_comfyui(self) -> bool:
        """Verifica se ComfyUI esta disponivel"""
        return await self.client.is_available()

    async def gerar(
        self,
        prompt: str,
        negative_prompt: str = "",
        largura: int = 1024,
        altura: int = 1024,
        passos: int = 20,
        cfg: float = 3.5,
        seed: int = -1,
        modelo: str = "flux1-dev.safetensors",
        salvar: bool = True
    ) -> dict:
        """
        Gera uma imagem usando FLUX.1

        Args:
            prompt: Descricao da imagem (em ingles funciona melhor)
            negative_prompt: O que NAO quer na imagem
            largura: Largura em pixels (padrao 1024)
            altura: Altura em pixels (padrao 1024)
            passos: Numero de passos de inferencia (padrao 20)
            cfg: Guidance scale (padrao 3.5 para FLUX)
            seed: Seed para reproducibilidade (-1 = aleatorio)
            modelo: Nome do modelo FLUX
            salvar: Se deve salvar a imagem em disco

        Returns:
            dict com status, caminho do arquivo e base64 da imagem
        """

        # Verifica se ComfyUI esta rodando
        if not await self.verificar_comfyui():
            return {
                "sucesso": False,
                "erro": "ComfyUI nao esta rodando! Inicie o ComfyUI primeiro.",
                "instrucoes": [
                    "1. Abra o ComfyUI",
                    "2. Certifique-se que FLUX.1 esta instalado",
                    "3. O ComfyUI deve estar rodando em http://127.0.0.1:8188"
                ]
            }

        try:
            # Cria o workflow para FLUX.1
            workflow = self.client.create_flux_workflow(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=largura,
                height=altura,
                steps=passos,
                cfg=cfg,
                seed=seed,
                model=modelo
            )

            # Gera a imagem
            image_bytes = await self.client.generate_and_wait(workflow, timeout=300)

            if not image_bytes:
                return {
                    "sucesso": False,
                    "erro": "Falha ao gerar imagem - nenhum resultado retornado"
                }

            result = {
                "sucesso": True,
                "prompt": prompt,
                "largura": largura,
                "altura": altura,
                "passos": passos,
                "modelo": modelo
            }

            # Salva em disco se solicitado
            if salvar:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"flux_{timestamp}.png"
                filepath = self.output_dir / filename

                with open(filepath, "wb") as f:
                    f.write(image_bytes)

                result["arquivo"] = str(filepath.absolute())

            # Retorna base64 para exibicao
            result["imagem_base64"] = base64.b64encode(image_bytes).decode("utf-8")

            return result

        except TimeoutError:
            return {
                "sucesso": False,
                "erro": "Timeout - a geracao demorou muito. Tente reduzir passos ou resolucao."
            }
        except Exception as e:
            return {
                "sucesso": False,
                "erro": f"Erro ao gerar imagem: {str(e)}"
            }


# Funcao de conveniencia para uso como tool
async def gerar_imagem(
    prompt: str,
    largura: int = 1024,
    altura: int = 1024,
    passos: int = 20,
    seed: int = -1
) -> dict:
    """
    Tool para gerar imagens com FLUX.1

    Parametros:
        prompt: Descricao detalhada da imagem desejada (ingles funciona melhor)
        largura: Largura em pixels (padrao 1024, max 2048)
        altura: Altura em pixels (padrao 1024, max 2048)
        passos: Qualidade/tempo (10=rapido, 20=normal, 30=alta qualidade)
        seed: Numero para reproduzir mesma imagem (-1=aleatorio)

    Retorna:
        Caminho da imagem salva e preview em base64
    """
    gerador = GeradorImagem()
    return await gerador.gerar(
        prompt=prompt,
        largura=min(largura, 2048),
        altura=min(altura, 2048),
        passos=min(passos, 50),
        seed=seed
    )
