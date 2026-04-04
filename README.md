# JuiceBot2

JuiceBot 2.0 is an autonomous conversational agent for task automation and AI-assisted workflows.

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
