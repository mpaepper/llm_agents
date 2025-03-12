## LLM Agent Server

A simple FastAPI server for interacting with LLM agents.

### Features

- Simple API for querying LLM agents
- Support for multiple LLM models
- Extensible tool system
- Configurable with environment variables
- Comprehensive logging
- Compatible with OpenAI API v1.0+

### Project Structure

```
.
├── Makefile                # Common development tasks
├── environment.yml         # Conda environment configuration
├── pyproject.toml          # Poetry configuration
├── .env                    # Environment variables
└── src/
    ├── __init__.py         # Package initialization
    ├── fast_api_server/    # FastAPI server package
    │   ├── __init__.py
    │   ├── config.py       # Application configuration
    │   ├── logging_config.py # Logging setup
    │   ├── main.py         # FastAPI application
    │   └── services/       # Business logic
    │       ├── __init__.py
    │       ├── agent_service.py # Agent service
    │       └── agent_wrapper.py # Agent wrapper (optional)
    └── llm_agents/         # Modified LLM agents library
```

### Setup

1. Clone the repository
2. Create a conda environment:

```bash
conda env create -f environment.yml
conda activate llm-agent-server
```

3. Install dependencies with Poetry:

```bash
poetry install
```

Or use the Makefile:

```bash
make install
```

4. Ensure your `.env` file has the required API keys:

```
OPENAI_API_KEY=your-openai-api-key
SERPAPI_API_KEY=your-serpapi-api-key (optional)
```

5. Run the server:

```bash
poetry run uvicorn src.fast_api_server.main:app --reload
```

Or use the Makefile:

```bash
make run
```

### API Documentation

Once the server is running, you can access the API documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Using the API

The API provides a simple endpoint for querying an agent:

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the weather in New York?",
    "max_iterations": 5,
    "tools": ["python_repl", "google_search"]
  }'
```

The response includes:
- `result`: The final answer from the agent
- `thinking`: Basic information about the agent's process
- `iterations`: The number of steps the agent took
- `execution_time`: How long the query took to process

You can also list available tools:

```bash
curl -X GET "http://localhost:8000/tools"
```

### Development

- Run linting: `make lint`
- Run tests: `make test`
- Clean up: `make clean`

### Environment Variables

The application uses the following environment variables:

- `OPENAI_API_KEY` - Your OpenAI API key (required)
- `SERPAPI_API_KEY` - Your SerpAPI key (optional)
- `APP_DEFAULT_MODEL` - Default LLM model to use
- `APP_API_TITLE` - API title
- `APP_API_DESCRIPTION` - API description
- `APP_API_VERSION` - API version
- `APP_HOST` - Server host
- `APP_PORT` - Server port
- `APP_DEBUG` - Debug mode
- `APP_LOG_LEVEL` - Logging level

### Built With

- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Data validation
- [Poetry](https://python-poetry.org/) - Dependency management
- [Conda](https://docs.conda.io/) - Environment management
- [OpenAI API](https://platform.openai.com/) - LLM provider (v1.0+)
