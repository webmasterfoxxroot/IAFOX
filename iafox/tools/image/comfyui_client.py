"""Cliente para comunicar com ComfyUI API"""
import httpx
import json
import uuid
import asyncio
import websockets
from pathlib import Path
from typing import Optional, Dict, Any
import base64


class ComfyUIClient:
    """Cliente para interagir com ComfyUI via API"""

    def __init__(self, host: str = "127.0.0.1", port: int = 8188):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.ws_url = f"ws://{host}:{port}/ws"
        self.client_id = str(uuid.uuid4())

    async def is_available(self) -> bool:
        """Verifica se ComfyUI esta rodando"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/system_stats")
                return response.status_code == 200
        except:
            return False

    async def queue_prompt(self, workflow: Dict[str, Any]) -> str:
        """Envia workflow para fila de execucao"""
        payload = {
            "prompt": workflow,
            "client_id": self.client_id
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/prompt",
                json=payload
            )
            result = response.json()
            return result.get("prompt_id")

    async def get_history(self, prompt_id: str) -> Dict[str, Any]:
        """Busca historico de um prompt"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self.base_url}/history/{prompt_id}")
            return response.json()

    async def get_image(self, filename: str, subfolder: str = "", folder_type: str = "output") -> bytes:
        """Baixa imagem gerada"""
        params = {
            "filename": filename,
            "subfolder": subfolder,
            "type": folder_type
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(f"{self.base_url}/view", params=params)
            return response.content

    async def generate_and_wait(self, workflow: Dict[str, Any], timeout: int = 300) -> Optional[bytes]:
        """Gera imagem e aguarda resultado"""
        prompt_id = await self.queue_prompt(workflow)

        if not prompt_id:
            return None

        # Conecta via WebSocket para receber atualizacoes
        try:
            async with websockets.connect(f"{self.ws_url}?clientId={self.client_id}") as ws:
                start_time = asyncio.get_event_loop().time()

                while True:
                    # Timeout check
                    if asyncio.get_event_loop().time() - start_time > timeout:
                        raise TimeoutError("Timeout gerando imagem")

                    try:
                        message = await asyncio.wait_for(ws.recv(), timeout=1.0)
                        data = json.loads(message)

                        if data.get("type") == "executing":
                            exec_data = data.get("data", {})
                            if exec_data.get("prompt_id") == prompt_id:
                                if exec_data.get("node") is None:
                                    # Execucao completa
                                    break

                        elif data.get("type") == "execution_error":
                            error_data = data.get("data", {})
                            raise Exception(f"Erro ComfyUI: {error_data}")

                    except asyncio.TimeoutError:
                        continue

        except Exception as e:
            # Fallback: polling do historico
            for _ in range(timeout):
                await asyncio.sleep(1)
                history = await self.get_history(prompt_id)
                if prompt_id in history:
                    break

        # Busca resultado no historico
        history = await self.get_history(prompt_id)

        if prompt_id not in history:
            return None

        outputs = history[prompt_id].get("outputs", {})

        # Procura por imagens no output
        for node_id, output in outputs.items():
            if "images" in output:
                for img in output["images"]:
                    filename = img.get("filename")
                    subfolder = img.get("subfolder", "")
                    if filename:
                        return await self.get_image(filename, subfolder)

        return None

    def create_flux_workflow(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 1024,
        height: int = 1024,
        steps: int = 20,
        cfg: float = 1.0,
        seed: int = -1,
        model: str = "flux1-dev.safetensors"
    ) -> Dict[str, Any]:
        """Cria workflow para FLUX.1"""

        if seed == -1:
            import random
            seed = random.randint(0, 2**32 - 1)

        workflow = {
            "6": {
                "inputs": {
                    "text": prompt,
                    "clip": ["11", 0]
                },
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "CLIP Text Encode (Prompt)"}
            },
            "8": {
                "inputs": {
                    "samples": ["13", 0],
                    "vae": ["10", 0]
                },
                "class_type": "VAEDecode",
                "_meta": {"title": "VAE Decode"}
            },
            "9": {
                "inputs": {
                    "filename_prefix": "IAFOX_FLUX",
                    "images": ["8", 0]
                },
                "class_type": "SaveImage",
                "_meta": {"title": "Save Image"}
            },
            "10": {
                "inputs": {
                    "vae_name": "ae.safetensors"
                },
                "class_type": "VAELoader",
                "_meta": {"title": "Load VAE"}
            },
            "11": {
                "inputs": {
                    "clip_name1": "t5xxl_fp16.safetensors",
                    "clip_name2": "clip_l.safetensors",
                    "type": "flux"
                },
                "class_type": "DualCLIPLoader",
                "_meta": {"title": "DualCLIPLoader"}
            },
            "12": {
                "inputs": {
                    "unet_name": model,
                    "weight_dtype": "default"
                },
                "class_type": "UNETLoader",
                "_meta": {"title": "Load Diffusion Model"}
            },
            "13": {
                "inputs": {
                    "noise": ["25", 0],
                    "guider": ["22", 0],
                    "sampler": ["16", 0],
                    "sigmas": ["17", 0],
                    "latent_image": ["27", 0]
                },
                "class_type": "SamplerCustomAdvanced",
                "_meta": {"title": "SamplerCustomAdvanced"}
            },
            "16": {
                "inputs": {
                    "sampler_name": "euler"
                },
                "class_type": "KSamplerSelect",
                "_meta": {"title": "KSamplerSelect"}
            },
            "17": {
                "inputs": {
                    "scheduler": "simple",
                    "steps": steps,
                    "denoise": 1.0,
                    "model": ["12", 0]
                },
                "class_type": "BasicScheduler",
                "_meta": {"title": "BasicScheduler"}
            },
            "22": {
                "inputs": {
                    "model": ["12", 0],
                    "conditioning": ["26", 0]
                },
                "class_type": "BasicGuider",
                "_meta": {"title": "BasicGuider"}
            },
            "25": {
                "inputs": {
                    "noise_seed": seed
                },
                "class_type": "RandomNoise",
                "_meta": {"title": "RandomNoise"}
            },
            "26": {
                "inputs": {
                    "guidance": cfg,
                    "conditioning": ["6", 0]
                },
                "class_type": "FluxGuidance",
                "_meta": {"title": "FluxGuidance"}
            },
            "27": {
                "inputs": {
                    "width": width,
                    "height": height,
                    "batch_size": 1
                },
                "class_type": "EmptySD3LatentImage",
                "_meta": {"title": "EmptySD3LatentImage"}
            }
        }

        return workflow
