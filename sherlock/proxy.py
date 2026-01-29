"""HTTP relay proxy for intercepting LLM API traffic."""

import asyncio
import json
import ssl
from datetime import datetime
from typing import Callable

import aiohttp
from aiohttp import web

from sherlock.config import DEFAULT_PROXY_PORT, PROVIDERS
from sherlock.parser import count_tokens, parse_anthropic_request


class ProxyServer:
    """HTTP relay proxy that forwards requests to upstream HTTPS APIs."""

    def __init__(
        self,
        port: int = DEFAULT_PROXY_PORT,
        on_request: Callable[[dict], None] | None = None,
    ):
        """Initialize the proxy server.

        Args:
            port: Local port to listen on
            on_request: Callback function called with parsed request data
        """
        self.port = port
        self.on_request = on_request
        self.app = web.Application()
        self.app.router.add_route("*", "/{path:.*}", self.handle_request)
        self._runner = None
        self._site = None

    def _detect_provider(self, path: str) -> str | None:
        """Detect the provider from the request path."""
        if "/v1/messages" in path:
            return "anthropic"
        elif "/v1/chat/completions" in path or "/v1/responses" in path:
            return "openai"
        elif "generateContent" in path or "streamGenerateContent" in path:
            return "gemini"
        return None

    async def handle_request(self, request: web.Request) -> web.Response:
        """Handle incoming request and forward to upstream."""
        path = "/" + request.match_info.get("path", "")
        if request.query_string:
            path += "?" + request.query_string

        # Detect provider from path
        provider = self._detect_provider(path)
        if not provider:
            return web.Response(
                status=400,
                text=f"Unknown API path: {path}. Supported: Anthropic, OpenAI, Gemini",
            )

        upstream_base = PROVIDERS[provider]["base_url"]
        upstream_url = upstream_base + path

        # Read request body
        body = await request.read()

        # Parse and count tokens for supported endpoints
        if body and self.on_request:
            self._process_request(body, path, provider)

        # Forward request to upstream
        headers = dict(request.headers)
        headers.pop("Host", None)
        headers.pop("Content-Length", None)

        ssl_context = ssl.create_default_context()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=request.method,
                    url=upstream_url,
                    headers=headers,
                    data=body,
                    ssl=ssl_context,
                ) as upstream_response:
                    response_body = await upstream_response.read()

                    # Build response headers
                    response_headers = dict(upstream_response.headers)
                    response_headers.pop("Content-Encoding", None)
                    response_headers.pop("Transfer-Encoding", None)
                    response_headers.pop("Content-Length", None)

                    return web.Response(
                        status=upstream_response.status,
                        headers=response_headers,
                        body=response_body,
                    )
        except aiohttp.ClientError as e:
            return web.Response(
                status=502,
                text=f"Upstream error: {e}",
            )

    def _process_request(self, body: bytes, path: str, provider: str) -> None:
        """Process request body for token counting and logging."""
        try:
            body_dict = json.loads(body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return

        parsed = None
        if provider == "anthropic":
            parsed = parse_anthropic_request(body_dict)
        elif provider == "openai":
            parsed = self._parse_openai_request(body_dict)
        elif provider == "gemini":
            parsed = self._parse_gemini_request(body_dict)

        if parsed and self.on_request:
            tokens = count_tokens(parsed.get("total_text", ""))
            event = {
                "timestamp": datetime.now().isoformat(),
                "provider": provider,
                "model": parsed.get("model", "unknown"),
                "tokens": tokens,
                "messages": parsed.get("messages", []),
                "raw_body": body_dict,
                "path": path,
            }
            self.on_request(event)

    def _parse_openai_request(self, body: dict) -> dict:
        """Parse OpenAI API request body."""
        result = {
            "provider": "openai",
            "messages": [],
            "model": body.get("model", "unknown"),
            "total_text": "",
        }

        texts = []
        messages = body.get("messages", [])
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            if isinstance(content, str):
                result["messages"].append({"role": role, "content": content})
                texts.append(content)
            elif isinstance(content, list):
                # Handle multimodal content
                text_parts = [
                    p.get("text", "") for p in content if p.get("type") == "text"
                ]
                combined = " ".join(text_parts)
                result["messages"].append({"role": role, "content": combined})
                texts.append(combined)

        result["total_text"] = "\n".join(texts)
        return result

    def _parse_gemini_request(self, body: dict) -> dict:
        """Parse Gemini API request body."""
        result = {
            "provider": "gemini",
            "messages": [],
            "model": "gemini",
            "total_text": "",
        }

        texts = []
        contents = body.get("contents", [])
        for content in contents:
            role = content.get("role", "user")
            parts = content.get("parts", [])
            text_parts = [p.get("text", "") for p in parts if "text" in p]
            combined = " ".join(text_parts)
            result["messages"].append({"role": role, "content": combined})
            texts.append(combined)

        # System instruction
        system_instruction = body.get("systemInstruction", {})
        if system_instruction:
            parts = system_instruction.get("parts", [])
            text_parts = [p.get("text", "") for p in parts if "text" in p]
            if text_parts:
                system_text = " ".join(text_parts)
                result["messages"].insert(
                    0, {"role": "system", "content": system_text}
                )
                texts.insert(0, system_text)

        result["total_text"] = "\n".join(texts)
        return result

    async def start(self) -> None:
        """Start the proxy server."""
        self._runner = web.AppRunner(self.app)
        await self._runner.setup()
        self._site = web.TCPSite(self._runner, "127.0.0.1", self.port)
        await self._site.start()

    async def stop(self) -> None:
        """Stop the proxy server."""
        if self._runner:
            await self._runner.cleanup()
