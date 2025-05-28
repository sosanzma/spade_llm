# Installation

## Requirements

- Python 3.10+
- 4GB+ RAM (8GB+ for local models)

## Install

```bash
pip install spade_llm
```

## Verify Installation

```python
import spade_llm
from spade_llm import LLMAgent, LLMProvider

print(f"SPADE_LLM version: {spade_llm.__version__}")
```

## LLM Provider Setup

Choose one provider:

### OpenAI
```bash
export OPENAI_API_KEY="your-api-key"
```

### Ollama (Local)
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Download a model
ollama pull llama3.1:8b
ollama serve
```

### LM Studio (Local)
1. Download [LM Studio](https://lmstudio.ai/)
2. Download a model through the GUI
3. Start the local server

## XMPP Server

For development, use a public XMPP server like `jabber.at` or set up [Prosody](https://prosody.im/) locally.

## Development Install

```bash
git clone https://github.com/sosanzma/spade_llm.git
cd spade_llm
pip install -e ".[dev]"
```

## Troubleshooting

**Import errors**: Ensure you're in the correct Python environment
```bash
python -m pip install spade_llm
```

**SSL errors**: For development only, disable SSL verification:
```python
agent = LLMAgent(..., verify_security=False)
```

**Ollama connection**: Check if Ollama is running:
```bash
curl http://localhost:11434/v1/models
```
