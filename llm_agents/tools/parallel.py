"""Anonymous Parallel Search MCP tools using Streamable HTTP, without new deps."""
import json
from uuid import uuid4
from urllib.parse import urlsplit

import requests
from pydantic import Field

from llm_agents.tools.base import ToolInterface, tool_run_id


MCP_URL = 'https://search.parallel.ai/mcp'
USER_AGENT = 'llm-agents/0.1.0 (+https://github.com/mpaepper/llm_agents)'
PROTOCOL_VERSION = '2025-03-26'


def _response(response, request_id):
    """Read the matching JSON-RPC response from JSON or an SSE message stream."""
    response.raise_for_status()
    if response.headers.get('Content-Type', '').split(';')[0] == 'text/event-stream':
        response.encoding = 'utf-8'
        data = []
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith('data:'):
                data.append(line[5:].lstrip(' '))
            elif not line and data:
                message = json.loads('\n'.join(data))
                data = []
                if message.get('id') == request_id:
                    break
        else:
            raise ValueError('Parallel MCP stream ended without a response')
    else:
        message = response.json()
    if not isinstance(message, dict) or message.get('id') != request_id:
        raise ValueError('Invalid Parallel MCP response')
    if 'error' in message:
        raise ValueError('Parallel MCP error: {}'.format(message['error']))
    if not isinstance(message.get('result'), dict):
        raise ValueError('Parallel MCP response has no result')
    return message['result']


def _call(name, arguments, timeout):
    # This is a conversation ID, independent of the transport session below.
    arguments['session_id'] = tool_run_id.get() or str(uuid4())
    with requests.Session() as client:
        # Skip .netrc authentication while preserving proxy and CA settings.
        client.auth = lambda request: request
        client.headers.update({'User-Agent': USER_AGENT,
                               'Accept': 'application/json, text/event-stream'})

        def post(body):
            return client.post(MCP_URL, json=body, timeout=timeout,
                               stream=True, allow_redirects=False)

        with post({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {
            'protocolVersion': PROTOCOL_VERSION, 'capabilities': {},
            'clientInfo': {'name': 'llm-agents', 'version': '0.1.0'}}}) as response:
            initialized = _response(response, 1)
            transport_id = response.headers.get('Mcp-Session-Id')
        if initialized.get('protocolVersion') != PROTOCOL_VERSION:
            raise ValueError('Unsupported Parallel MCP protocol version')
        client.headers['MCP-Protocol-Version'] = PROTOCOL_VERSION
        if transport_id:
            client.headers['Mcp-Session-Id'] = transport_id
        with post({'jsonrpc': '2.0', 'method': 'notifications/initialized'}) as response:
            response.raise_for_status()
        with post({'jsonrpc': '2.0', 'id': 2, 'method': 'tools/call',
                   'params': {'name': name, 'arguments': arguments}}) as response:
            result = _response(response, 2)
        text = '\n'.join(block['text'] for block in result.get('content', [])
                         if block.get('type') == 'text')
        if result.get('isError'):
            raise ValueError('Parallel {} failed: {}'.format(name, text))
        if not text:
            raise ValueError('Parallel MCP returned no text')
        return text


class ParallelSearchTool(ToolInterface):
    """Keyless web search, including source URLs and relevant excerpts."""

    name: str = 'Parallel Search'
    description: str = ('Search the web for current information. Input is a search '
                        'question. Results include source URLs and excerpts.')
    timeout: float = Field(default=30.0, gt=0)

    def use(self, input_text: str) -> str:
        if not input_text.strip():
            raise ValueError('A search query is required')
        return _call('web_search', {'objective': input_text,
                                   'search_queries': [input_text]}, self.timeout)


class ParallelFetchTool(ToolInterface):
    """Read a specific page when search excerpts are insufficient."""

    name: str = 'Parallel Fetch'
    description: str = ('Read a web page when search excerpts are insufficient. '
                        'Input must be one complete HTTP or HTTPS URL.')
    timeout: float = Field(default=30.0, gt=0)

    def use(self, input_text: str) -> str:
        url = input_text.strip()
        parsed = urlsplit(url)
        if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError('An HTTP or HTTPS URL without credentials is required')
        return _call('web_fetch', {'urls': [url]}, self.timeout)
