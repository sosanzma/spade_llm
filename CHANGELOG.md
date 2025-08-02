# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-07-11

### Added
- Initial release of SPADE_LLM
- LLM integration with SPADE multi-agent framework
- Support for multiple LLM providers:
  - OpenAI (GPT-4o, o3, etc.)
  - Ollama (local LLM hosting)
  - LM Studio (local LLM hosting)
  - Any OpenAI-compatible API
- Dual memory system:
  - Agent Base Memory (persistent, cross-conversation)
  - Interaction Memory (conversation-specific)
- Model Context Protocol (MCP) integration
- Tool calling system with optional LangChain adapter
- Guardrails system for content filtering
- Human-in-the-loop capabilities
- Smart context management with windowing strategies
- Multi-agent orchestration with routing
- Comprehensive examples and documentation

### Features
- Multi-conversation support with isolated contexts
- Tool execution loops (up to 20 iterations)
- Async/sync tool function bridge
- Provider abstraction for easy LLM switching
- SQLite backend for persistent memory
- Web interface for human expert consultation
- Valencia Smart City integration examples
- GitHub Actions integration examples
- Comprehensive test suite

### Dependencies
- spade>=4.0.0
- openai>=1.0.0
- pydantic>=2.0.0
- aiohttp>=3.8.0
- python-dateutil>=2.8.2
- mcp>=1.8.0
- aiosqlite>=0.17.0

### Optional Dependencies
- langchain_community>=0.3.2 (for LangChain tools adapter)

[0.1.0]: https://github.com/sosanzma/spade_llm/releases/tag/v0.1.0