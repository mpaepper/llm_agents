"""Exercise the shipped resolver and Agent loop with a scripted model and HTTP peer."""
import io
import json
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
import requests


@pytest.fixture
def runtime(monkeypatch, tmp_path):
    # Imports happen after the existing environment-isolation fixture has run.
    from llm_agents import Agent, ChatLLM, ParallelSearchTool, ParallelFetchTool
    from llm_agents.tools.base import tool_run_id
    from run_agent import default_tools

    monkeypatch.delenv('SERPAPI_API_KEY', raising=False)
    monkeypatch.setenv('PARALLEL_API_KEY', 'must-not-be-sent')
    netrc = tmp_path / 'netrc'
    netrc.write_text('machine search.parallel.ai login private password secret\n')
    monkeypatch.setenv('NETRC', str(netrc))
    calls = []
    mode = {'response': 'json'}

    def send(client, request, **kwargs):
        body = json.loads(request.body)
        calls.append((request, body, kwargs))
        assert request.url == 'https://search.parallel.ai/mcp'
        assert request.headers['User-Agent'] == 'llm-agents/0.1.0 (+https://github.com/mpaepper/llm_agents)'
        assert 'Authorization' not in request.headers
        assert 'x-api-key' not in request.headers
        assert kwargs['timeout'] > 0
        response = requests.Response()
        response.status_code = 200
        response.request = request
        response.raw = io.BytesIO(b'')
        response.headers['Content-Type'] = 'application/json'
        method = body['method']
        if method == 'initialize':
            result = {'protocolVersion': mode.get('protocol', '2025-03-26')}
            response.headers['Mcp-Session-Id'] = 'transport-only'
        else:
            assert request.headers['MCP-Protocol-Version'] == '2025-03-26'
            assert request.headers['Mcp-Session-Id'] == 'transport-only'
            if method == 'notifications/initialized':
                response.status_code = 202
                response._content = b''
                return response
            if mode.get('exception'):
                raise mode['exception']
            if mode.get('barrier'):
                mode['barrier'].wait(timeout=5)
            if mode.get('http_status'):
                response.status_code = mode['http_status']
            result = mode.get('result', {'content': [{'type': 'text', 'text':
                'Source: https://www.python.org/\nPython is a programming language.'}]})
        payload = {'jsonrpc': '2.0', 'id': body['id'], 'result': result}
        if mode.get('rpc_error') and method == 'tools/call':
            payload = {'jsonrpc': '2.0', 'id': body['id'], 'error': {'code': -1, 'message': 'bad request'}}
        if mode.get('wrong_id') and method == 'tools/call':
            payload['id'] = 999
        data = json.dumps(payload).encode()
        if mode['response'] == 'sse':
            response.headers['Content-Type'] = 'text/event-stream; charset=utf-8'
            response.encoding = 'utf-8'
            data = b': keepalive\n\nevent: message\ndata: ' + data + b'\n\n'
        response._content = data
        response.raw = io.BytesIO(data)
        return response

    monkeypatch.setattr(requests.Session, 'send', send)
    return Agent, ChatLLM, ParallelSearchTool, ParallelFetchTool, default_tools, calls, mode, tool_run_id


def scripted_agent(runtime, monkeypatch, actions, tools=None):
    Agent, ChatLLM, _, _, default_tools, *_ = runtime
    outputs = iter(actions)
    prompts = []

    def generate(self, prompt, stop=None):
        prompts.append(prompt)
        return next(outputs)

    monkeypatch.setattr(ChatLLM, 'generate', generate)
    return Agent(llm=ChatLLM(), tools=default_tools() if tools is None else tools), prompts


def action(name, value):
    return 'Thought: use a tool\nAction: {}\nAction Input: {}'.format(name, value)


@pytest.mark.parametrize('encoding', ['json', 'sse'])
def test_cli_resolver_to_observation_and_session_lifecycle(runtime, monkeypatch, encoding):
    *_, calls, mode, run_id = runtime
    mode['response'] = encoding
    agent, prompts = scripted_agent(runtime, monkeypatch, [
        action('Parallel Search', 'Python programming language'),
        action('Parallel Fetch', 'https://www.python.org/'),
        action('Parallel Search', 'Python language documentation'),
        'Final Answer: Python is a programming language.',
        action('Parallel Search', 'Python release information'), 'Final Answer: done'])
    assert agent.run('What is Python?') == 'Python is a programming language.'
    assert 'Observation: Source: https://www.python.org/' in prompts[1]
    assert 'Python is a programming language.' in prompts[3]
    requests_ = [body for _, body, _ in calls if body['method'] == 'tools/call']
    ids = [body['params']['arguments']['session_id'] for body in requests_]
    assert len(set(ids)) == 1
    assert len(ids[0]) == 36 and ids[0] != 'transport-only'
    assert requests_[0]['params']['arguments']['search_queries'] == ['Python programming language']
    assert requests_[1]['params']['arguments']['urls'] == ['https://www.python.org/']
    assert agent.run('New question') == 'done'
    last_id = calls[-1][1]['params']['arguments']['session_id']
    assert last_id != ids[0]
    assert run_id.get() is None


def test_configured_serpapi_and_explicit_tools_are_preserved(runtime, monkeypatch):
    Agent, ChatLLM, Search, Fetch, default_tools, calls, *_ = runtime
    from llm_agents import SerpAPITool
    monkeypatch.setenv('SERPAPI_API_KEY', 'configured-key')
    assert any(isinstance(tool, SerpAPITool) for tool in default_tools())
    assert not any(isinstance(tool, (Search, Fetch)) for tool in default_tools())
    monkeypatch.setattr(SerpAPITool, 'use', lambda *args: (_ for _ in ()).throw(ValueError('provider failed')))
    agent, _ = scripted_agent(runtime, monkeypatch, [action('Google Search', 'question')])
    with pytest.raises(ValueError, match='provider failed'):
        agent.run('question')
    assert not calls  # Explicit provider failure must not fall back.
    agent, _ = scripted_agent(runtime, monkeypatch, ['Final Answer: no search'], tools=[])
    assert agent.tools == [] and agent.run('offline') == 'no search'
    agent, _ = scripted_agent(runtime, monkeypatch, [action('Parallel Search', 'question')], tools=[])
    with pytest.raises(ValueError, match='Unknown tool'):
        agent.run('disallowed search')
    assert not calls


@pytest.mark.parametrize('failure', [requests.Timeout('timeout'), requests.ConnectionError('offline'), KeyboardInterrupt()])
def test_caller_propagates_timeout_error_and_cancellation(runtime, monkeypatch, failure):
    *_, calls, mode, run_id = runtime
    mode['exception'] = failure
    agent, _ = scripted_agent(runtime, monkeypatch, [action('Parallel Search', 'question')])
    with pytest.raises(type(failure)):
        agent.run('question')
    assert len([b for _, b, _ in calls if b['method'] == 'tools/call']) == 1
    assert run_id.get() is None


@pytest.mark.parametrize('change,error', [
    ({'http_status': 429}, requests.HTTPError),
    ({'rpc_error': True}, ValueError),
    ({'wrong_id': True}, ValueError),
    ({'protocol': 'unknown'}, ValueError),
    ({'result': {'isError': True, 'content': [{'type': 'text', 'text': 'quota exceeded'}]}}, ValueError),
    ({'result': {'content': []}}, ValueError),
])
def test_caller_rejects_protocol_and_service_errors(runtime, monkeypatch, change, error):
    *_, calls, mode, run_id = runtime
    mode.update(change)
    agent, _ = scripted_agent(runtime, monkeypatch, [action('Parallel Search', 'question')])
    with pytest.raises(error):
        agent.run('question')
    assert run_id.get() is None


@pytest.mark.parametrize('url', ['file:///etc/passwd', 'javascript:alert(1)', 'https://', 'https://user:secret@example.com'])
def test_fetch_rejects_invalid_urls_without_network(runtime, url):
    _, _, _, Fetch, _, calls, *_ = runtime
    with pytest.raises(ValueError):
        Fetch().use(url)
    assert not calls


def test_empty_query_and_timeout_validation(runtime):
    _, _, Search, _, _, calls, *_ = runtime
    with pytest.raises(ValueError):
        Search().use(' ')
    with pytest.raises(ValueError):
        Search(timeout=0)
    assert not calls


def test_standalone_calls_have_independent_ids(runtime):
    _, _, Search, _, _, calls, *_ = runtime
    tool = Search()
    tool.use('first question')
    tool.use('second question')
    ids = [b['params']['arguments']['session_id'] for _, b, _ in calls if b['method'] == 'tools/call']
    assert ids[0] != ids[1]


def test_concurrent_runs_with_shared_tool_keep_ids(runtime, monkeypatch):
    Agent, ChatLLM, Search, _, _, calls, mode, *_ = runtime
    tool = Search()
    mode['barrier'] = Barrier(2)

    def generate(self, prompt, stop=None):
        history = prompt.split('Begin!')[1]
        if history.count('Observation:') == 2:
            return 'Final Answer: done'
        question = history.split('Question: ')[1].split('\n')[0]
        return action('Parallel Search', question)

    monkeypatch.setattr(ChatLLM, 'generate', generate)
    agents = [Agent(llm=ChatLLM(), tools=[tool]) for _ in range(2)]
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert list(pool.map(lambda pair: pair[1].run(pair[0]),
                             zip(['first', 'second'], agents))) == ['done', 'done']
    by_question = {}
    for _, body, _ in calls:
        if body['method'] == 'tools/call':
            args = body['params']['arguments']
            by_question.setdefault(args['objective'], []).append(args['session_id'])
    assert all(len(ids) == 2 and len(set(ids)) == 1 for ids in by_question.values())
    assert by_question['first'][0] != by_question['second'][0]
