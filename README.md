# JuiceBot2

[![CI](https://github.com/GitJuicedUp/JuiceBot2/actions/workflows/ci.yml/badge.svg)](https://github.com/GitJuicedUp/JuiceBot2/actions/workflows/ci.yml)

JuiceBot 2.0 is an autonomous conversational agent for task automation and AI-assisted workflows.

## Requirements

- Python 3.11 or 3.12
- An [OpenAI API key](https://platform.openai.com/account/api-keys) (set as `OPENAI_API_KEY`)

## Setup

```bash
# 1. Clone the repository
git clone https://github.com/GitJuicedUp/JuiceBot2.git
cd JuiceBot2

# 2. Create and activate a virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install runtime dependencies
pip install -r requirements.txt

# 4. Set your OpenAI API key
export OPENAI_API_KEY="sk-..."   # Windows: set OPENAI_API_KEY=sk-...
```

## Run

```bash
python main.py          # interactive chat mode
python main.py --mic    # microphone streaming mode (requires pyaudio)
```

## Development

```bash
# Install development dependencies (includes pytest + flake8)
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v

# Run linter
flake8 main.py src/ tests/
```

## Features

- **Task Automation** — run multi-step workflows hands-free
- **Web Search** — retrieve and summarize live information
- **Code Generation** — scaffold and write code on demand
- **Data Analysis** — process and interpret structured data
- **File Management** — read, write, and organize files

## Configuration

Agent settings live in [`config/juicebot.manifest.json`](config/juicebot.manifest.json).  
Key runtime options:

| Option | Default | Description |
|---|---|---|
| `model` | `gpt-4` | Underlying language model |
| `maxTokens` | `4096` | Maximum tokens per response |
| `temperature` | `0.7` | Sampling temperature |
| `logLevel` | `info` | Logging verbosity |
| `timeout` | `30000` | Request timeout in milliseconds |
| `retryAttempts` | `3` | Number of automatic retries on failure |
| `outputFormat` | `markdown` | Default response format |

## Commands

| Command | Description |
|---|---|
| `help` | Display available commands and usage information |
| `run <task>` | Execute a task or workflow |
| `status` | Check the current status of JuiceBot |
| `reset` | Reset the agent state and conversation history |

## License

MIT © [HustleHack](https://github.com/HustleHack)
