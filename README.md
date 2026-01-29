<p align="center">
  <h1 align="center">Sherlock</h1>
  <p align="center">
    <strong>Token Tracker for LLM CLI Tools</strong>
  </p>
  <p align="center">
    <img src="https://img.shields.io/badge/python-3.10+-3776AB?logo=python&logoColor=white" alt="Python">
    <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
    <img src="https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey.svg" alt="Platform">
    <img src="https://img.shields.io/badge/Claude_Code-supported-blueviolet.svg" alt="Claude Code">
    <img src="https://img.shields.io/badge/Gemini_CLI-supported-blue.svg" alt="Gemini">
    <img src="https://img.shields.io/badge/Codex-supported-green.svg" alt="Codex">
  </p>
  <p align="center">
    <a href="#installation">Installation</a> •
    <a href="#quick-start">Quick Start</a> •
    <a href="#features">Features</a> •
    <a href="#commands">Commands</a> •
    <a href="#contributing">Contributing</a>
  </p>
</p>

---

Sherlock tracks token usage for LLM CLI tools with a live terminal dashboard. See exactly how many tokens you're using in real-time.

## Why Sherlock?

- **Track Token Usage**: See exactly how many tokens each request consumes
- **Monitor Context Windows**: Visual fuel gauge shows cumulative usage against your limit
- **Debug Prompts**: Automatically saves every prompt as markdown and JSON for review
- **Zero Configuration**: No certificates, no setup - just install and go

## Installation

```bash
pip install sherlock
```

### Requirements

- Python 3.10+

## Quick Start

### Terminal 1: Start the Dashboard

```bash
sherlock start
```

You'll be prompted to choose where to save captured prompts, then the dashboard appears:

```
┌─────────────────────────────────────────────────────────────┐
│  SHERLOCK - LLM Traffic Inspector                           │
├─────────────────────────────────────────────────────────────┤
│  Context Usage  ████████████░░░░░░░░░░░░░░░░  42%           │
│                 (84,231 / 200,000 tokens)                   │
├─────────────────────────────────────────────────────────────┤
│  Time     Provider    Model                      Tokens     │
│  14:23:01 Anthropic   claude-sonnet-4-20250514   12,847     │
│  14:23:45 Anthropic   claude-sonnet-4-20250514   8,234      │
│  14:24:12 Anthropic   claude-sonnet-4-20250514   15,102     │
├─────────────────────────────────────────────────────────────┤
│  Last Prompt: "Can you help me refactor this function..."   │
└─────────────────────────────────────────────────────────────┘
```

### Terminal 2: Run Your LLM Tool

```bash
# For Claude Code
sherlock claude

# For Gemini CLI (see known issues)
sherlock gemini

# For OpenAI Codex
sherlock codex
```

That's it! Watch the dashboard update in real-time as you work.

## Features

### Live Terminal Dashboard

Real-time token tracking with color-coded fuel gauge:
- Green: < 50% of limit
- Yellow: 50-80% of limit
- Red: > 80% of limit

### Prompt Archive

Every intercepted request is saved to your chosen directory:
- **Markdown** - Human-readable format with metadata
- **JSON** - Raw API request body for debugging

### Session Summary

When you exit, see your total usage:

```
Session complete. Total: 84,231 tokens across 12 requests.
```

## Commands

| Command | Description |
|---------|-------------|
| `sherlock start` | Start the proxy and dashboard |
| `sherlock claude` | Run Claude Code with proxy configured |
| `sherlock gemini` | Run Gemini CLI with proxy configured |
| `sherlock codex` | Run OpenAI Codex CLI with proxy configured |
| `sherlock run --provider <name> <cmd>` | Run any command with proxy configured |

### Options

```bash
sherlock start [OPTIONS]

Options:
  -p, --port NUM    Proxy port (default: 8080)
  -l, --limit NUM   Token limit for fuel gauge (default: 200000)
```

```bash
sherlock claude [OPTIONS] [ARGS]...

Options:
  -p, --port NUM    Proxy port (default: 8080)
```

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│  Terminal 1: sherlock start                                      │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  HTTP Proxy (localhost:8080)                                ││
│  │  + Dashboard                                                ││
│  │  + Prompt Archive                                           ││
│  └─────────────────────────────────────────────────────────────┘│
└───────────────────────────────┬─────────────────────────────────┘
                                │ HTTP
                                │
┌───────────────────────────────┴─────────────────────────────────┐
│  Terminal 2: sherlock claude                                     │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Sets ANTHROPIC_BASE_URL=http://localhost:8080              ││
│  │  Runs: claude                                               ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ HTTPS
                                ▼
                      ┌───────────────────┐
                      │ api.anthropic.com │
                      └───────────────────┘
```

## Supported Providers

| Provider | Command | Status |
|----------|---------|--------|
| Anthropic (Claude Code) | `sherlock claude` | Supported |
| Google (Gemini CLI) | `sherlock gemini` | Blocked by upstream issue |
| OpenAI (Codex) | `sherlock codex` | Supported |

## Known Issues

### Gemini CLI

Gemini CLI currently has a [known issue](https://github.com/google-gemini/gemini-cli/issues/15430) where it ignores custom base URLs when using OAuth authentication. Sherlock's Gemini support will work automatically once the Gemini CLI team fixes this issue.

## Contributing

Contributions are welcome! Here's how you can help:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Development Setup

```bash
git clone https://github.com/yourusername/sherlock.git
cd sherlock
python -m venv venv
source venv/bin/activate
pip install -e .
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  <em>See what's really being sent to the LLM. Track. Learn. Optimize.</em>
</p>
