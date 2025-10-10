# LALO AI Platform

**Enterprise AI Automation Platform with 100% Local Inference**

[![CI](https://github.com/Josh-lalosystems/LALO-ES/actions/workflows/python-tests.yml/badge.svg)](https://github.com/Josh-lalosystems/LALO-ES/actions)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

---

## 🚀 Overview

**LALO AI Platform** is an advanced, privacy-first AI automation system designed for enterprise deployment. Built by **LALO AI SYSTEMS, LLC**, LALO combines cutting-edge local AI inference with intelligent orchestration, self-improvement capabilities, and extensible architecture.

### Key Differentiators

- **🔒 100% Local Inference** - Complete privacy, no data leaves your infrastructure
- **🧠 Intelligent Router Architecture** - Automatic model selection based on request complexity
- **🔄 Self-Improvement Engine** - Learns from feedback and continuously improves responses
- **🛡️ Multi-Agent Orchestration** - Specialized agent pools for complex workflows
- **🔌 Extensible Tool System** - Users can create custom tools and connectors
- **📦 Sandboxed Execution** - Secure isolated environments for code execution
- **⚡ Real-Time Streaming** - Server-Sent Events for responsive AI interactions
- **📊 Confidence Validation** - AI-powered quality scoring and hallucination detection

---

## 🏗️ Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────────┐
│                     LALO AI Platform                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐  │
│  │   Router     │→ │ Agent        │→ │  Confidence         │  │
│  │   Model      │  │ Orchestrator │  │  Validator          │  │
│  └──────────────┘  └──────────────┘  └─────────────────────┘  │
│         │                  │                      │            │
│         ↓                  ↓                      ↓            │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │              Local LLM Service                            │ │
│  │  • TinyLlama (1.1B) - Fast chat                          │ │
│  │  • Qwen (0.5B) - Validation                              │ │
│  │  • DeepSeek Coder (6.7B) - Code generation               │ │
│  │  • MetaMath (7B) - Mathematical reasoning                │ │
│  │  • OpenChat (7B) - Research & analysis                   │ │
│  │  • Mistral (7B) - General reasoning                      │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │              Extension Layer                              │ │
│  │  • Custom Tools & Connectors                             │ │
│  │  • Sandboxed Execution Environment                       │ │
│  │  • Database Connectors (SQL, NoSQL)                      │ │
│  │  • Cloud Storage (SharePoint, S3, Azure)                 │ │
│  │  • API Integrations                                       │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │          Self-Improvement & Learning                      │ │
│  │  • Feedback Analysis Engine                              │ │
│  │  • Response Quality Tracking                             │ │
│  │  • Automatic Fine-tuning Suggestions                     │ │
│  │  • Performance Analytics                                 │ │
│  └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Request Flow

1. **Routing**: Intelligent classification (simple/complex/specialized)
2. **Orchestration**: Multi-agent coordination for complex requests
3. **Execution**: Local model inference or specialized tool usage
4. **Validation**: Confidence scoring and quality assurance
5. **Learning**: Feedback collection and continuous improvement

---

## ✨ Features

### 🎯 Core Capabilities

#### **Intelligent Request Routing**
- Automatic complexity analysis
- Dynamic model selection
- Heuristic fallback for offline operation
- Support for simple, complex, and specialized paths

#### **Multi-Agent Orchestration**
- **Specialized Agent Pools**: Research, coding, analysis, creation
- **Dynamic Agent Creation**: Runtime agent instantiation
- **Agent Workflows**: Multi-step coordination
- **Tool Integration**: Agents can use custom tools

#### **Local AI Inference**
- **8+ Pre-configured Models**: Math, coding, research, general
- **GPU & CPU Support**: Optimized for various hardware
- **Streaming Responses**: Real-time output via SSE
- **Model Quantization**: GGUF Q4_K_M for efficiency

#### **Self-Improvement System**
- **Feedback Collection**: User ratings and detailed feedback
- **Response Analysis**: Automatic quality assessment
- **Learning Engine**: Continuous improvement from interactions
- **Performance Tracking**: Analytics and optimization suggestions

#### **Security & Privacy**
- **100% Local Processing**: No external API calls required
- **Encrypted Key Storage**: Fernet encryption for API keys
- **Role-Based Access Control (RBAC)**: Fine-grained permissions
- **Audit Logging**: Complete action tracking
- **Sandboxed Execution**: Isolated code execution environments

### 🔌 Extensibility

#### **Custom Tool Creation**
Users can create tools for:
- Web scraping and automation
- Database queries and updates
- File operations and processing
- API integrations
- Custom business logic

#### **Connector Framework**
Built-in connectors for:
- **Databases**: PostgreSQL, MySQL, MongoDB, SQLite
- **Cloud Storage**: SharePoint, OneDrive, S3, Azure Blob
- **Enterprise Systems**: SAP, Workday, Salesforce
- **Communication**: Email, Slack, Teams
- **File Systems**: Local, network, cloud

#### **Sandbox Execution**
- Isolated Python environments
- Resource limits (CPU, memory, time)
- Secure code execution
- File system restrictions

### 📊 Enterprise Features

#### **Confidence & Quality**
- AI-powered hallucination detection
- Response quality scoring
- Evasive text detection
- Multi-model validation

#### **Analytics & Reporting**
- Usage statistics and trends
- Cost tracking per model
- Performance metrics
- User behavior analysis

#### **Administration**
- User management
- API key management
- System configuration
- Model management

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- 8 GB RAM minimum (16 GB recommended for multiple models)
- 30 GB disk space (for models)
- Windows 10/11, macOS, or Linux

### Installation

#### Option 1: Windows Installer (Recommended)

Download and run the installer:
```
LALO-AI-Setup-1.0.0.exe
```

The installer will:
- Install Python 3.11 embedded runtime
- Set up the application
- Download AI models (optional)
- Create desktop shortcuts

#### Option 2: Manual Installation

1. **Clone the repository**
```bash
git clone https://github.com/Josh-lalosystems/LALO-ES.git
cd LALO-ES
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Download AI models**
```bash
python scripts/download_models.py --all
```

Or download specific models:
```bash
python scripts/download_models.py --model tinyllama
python scripts/download_models.py --model deepseek-coder
```

4. **Initialize database**
```bash
python scripts/init_db.py
```

5. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your settings
```

6. **Start the server**
```bash
python app.py
```

7. **Access the application**
Navigate to [http://localhost:8000](http://localhost:8000)

### First Run

1. **Get Demo Token** (development mode)
   - Click "Get Demo Token" on login page
   - Or set `DEMO_MODE=true` in `.env`

2. **Add API Keys** (optional, for cloud models)
   - Go to Settings → API Keys
   - Add OpenAI or Anthropic keys for cloud fallback

3. **Download Models** (if not done during installation)
   - Go to Settings → Model Management
   - Select models to download
   - Essential models: ~8 GB, All models: ~25 GB

### Database migration (important)

When upgrading the codebase you may need to apply database schema changes. Two safe options are provided:

- Using Alembic (recommended for production):

```powershell
# from repo root, using the project's virtualenv
.\venv\Scripts\python.exe -m alembic upgrade head
```

- For SQLite-only environments (quick helper):

```powershell
# This script will add the `fallback_attempts` JSON column to the `requests` table
python scripts/apply_fallback_column.py
```

If you use a different database (Postgres, MySQL), prefer running Alembic or create an equivalent migration for your platform.

4. **Submit Your First Request**
   - Select "Auto (Router Decides)" for intelligent routing
   - Enter your question or task
   - Watch the AI respond using local models!

---

## 📚 Documentation

### User Guides
- [User Manual](docs/USER_MANUAL.md) - Complete user guide
- [Deployment Guide](docs/DEPLOYMENT_GUIDE.md) - Production deployment
- [API Documentation](docs/API_DOCUMENTATION.md) - API reference

### Developer Docs
- [Architecture Overview](docs/ARCHITECTURE.md) - System design
- [Development Guide](docs/DEVELOPMENT.md) - Contributing guidelines
- [Tool Creation Guide](docs/TOOL_CREATION.md) - Creating custom tools
- [Connector Guide](docs/CONNECTOR_GUIDE.md) - Building connectors

### Demo Materials
- [Demo Script](docs/demo/DEMO_SCRIPT.md) - Walkthrough
- [Use Cases](docs/demo/USE_CASES.md) - Example scenarios
- [Investor Pitch](docs/demo/INVESTOR_PITCH.md) - Business overview

---

## 🛠️ Configuration

### Environment Variables

```bash
# Application
APP_ENV=production              # development | production
PORT=8000                       # Server port
HOST=127.0.0.1                 # Bind address

# Security
JWT_SECRET_KEY=<random-string>  # Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
ENCRYPTION_KEY=<fernet-key>     # Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Database
DATABASE_URL=sqlite:///./data/lalo.db

# Models
MODEL_DIR=./models              # Model storage location
DEFAULT_SIMPLE_MODEL=tinyllama
DEFAULT_COMPLEX_MODEL=openchat
DEFAULT_CODE_MODEL=deepseek-coder
DEFAULT_MATH_MODEL=metamath

# Development (DO NOT use in production!)
DEMO_MODE=false                 # Bypass authentication
DEBUG=false                     # Enable debug logging
```

### Model Configuration

Models are automatically configured based on available GGUF files in `models/` directory:

| Model | Size | Specialty | Use Case |
|-------|------|-----------|----------|
| TinyLlama 1.1B | 669 MB | General | Fast chat, simple queries |
| Qwen 0.5B | 352 MB | Validation | Confidence scoring |
| Phi-2 2.7B | 1.6 GB | Routing | Request classification |
| DeepSeek Coder 6.7B | 4.0 GB | Coding | Code generation, debugging |
| MetaMath 7B | 4.4 GB | Math | Mathematical reasoning |
| OpenChat 7B | 4.4 GB | Research | Analysis, synthesis |
| Mistral 7B | 4.4 GB | General | Advanced reasoning |
| BGE-Small | 133 MB | Embeddings | RAG, semantic search |

---

## 🧪 Testing

### Run Tests

```bash
# All tests
pytest tests/ -v

# Specific test suite
pytest tests/test_demo_mode_heuristics.py -v
pytest tests/test_confidence_model.py -v

# With coverage
pytest tests/ --cov=core --cov-report=html
```

### Manual Testing

1. **Demo Mode Testing**
```bash
# Enable demo mode
export DEMO_MODE=true
python app.py
```

2. **Local Model Testing**
```bash
# Test model download
python scripts/download_models.py --list

# Test inference
python scripts/test_local_inference.py
```

3. **Seed Demo Data**
```bash
python scripts/seed_demo_data.py
```

---

## 🏢 Enterprise Deployment

### Production Checklist

- [ ] Change `JWT_SECRET_KEY` from default
- [ ] Set strong `ENCRYPTION_KEY`
- [ ] Disable `DEMO_MODE` (`DEMO_MODE=false`)
- [ ] Configure CORS for production domains
- [ ] Enable HTTPS with valid SSL certificate
- [ ] Set up PostgreSQL (recommended over SQLite)
- [ ] Configure backup strategy
- [ ] Enable monitoring and logging
- [ ] Set up rate limiting
- [ ] Configure firewall rules

### Docker Deployment

```bash
# Build image
docker build -t lalo-ai:latest .

# Run container
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/data:/app/data \
  -e JWT_SECRET_KEY=<your-secret> \
  -e ENCRYPTION_KEY=<your-key> \
  --name lalo-ai \
  lalo-ai:latest
```

### Kubernetes Deployment

See [k8s/](k8s/) for Kubernetes manifests.

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Install dev dependencies (`pip install -r requirements-dev.txt`)
4. Make your changes
5. Run tests (`pytest tests/ -v`)
6. Commit with clear messages (`git commit -m 'feat: Add amazing feature'`)
7. Push to your fork (`git push origin feature/amazing-feature`)
8. Open a Pull Request

---

## 📊 System Requirements

### Minimum Requirements
- **OS**: Windows 10 (1809+), macOS 11+, Ubuntu 20.04+
- **CPU**: 4 cores, 2.0 GHz
- **RAM**: 8 GB
- **Storage**: 30 GB free space
- **Python**: 3.11 or later

### Recommended Configuration
- **OS**: Windows 11, macOS 13+, Ubuntu 22.04+
- **CPU**: 8+ cores, 3.0+ GHz
- **RAM**: 16 GB
- **Storage**: 50 GB SSD
- **GPU**: NVIDIA GPU with CUDA support (optional, for acceleration)

### Model Storage Requirements
- **Essential Models**: ~8 GB
- **All Models**: ~25 GB
- **With Optional Models**: ~35 GB

---

## 🔐 Security

### Security Features

- **Encrypted Storage**: All API keys encrypted with Fernet (AES-128)
- **JWT Authentication**: Secure token-based auth
- **RBAC**: Role-based access control
- **Audit Logging**: Complete action tracking
- **Sandboxed Execution**: Isolated code execution
- **Input Validation**: Pydantic schema validation
- **Rate Limiting**: Protection against abuse

### Security Best Practices

1. Never commit `.env` files
2. Rotate JWT secrets regularly
3. Use strong encryption keys
4. Enable HTTPS in production
5. Keep dependencies updated
6. Monitor audit logs
7. Review user permissions regularly

### Reporting Security Issues

Please report security vulnerabilities to: security@laloai.com

---

## 📜 License

**Proprietary Software**

Copyright © 2025 **LALO AI SYSTEMS, LLC**. All rights reserved.

This software is proprietary and confidential. Unauthorized copying, modification, distribution, or use of this software, via any medium, is strictly prohibited without the express written permission of LALO AI SYSTEMS, LLC.

See [LICENSE](LICENSE) for full terms.

### Third-Party Licenses

This software uses open-source components. See [licenses/](licenses/) for third-party license information and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for attribution.

---

## 🌟 Roadmap

### Current Version (v1.0)
- ✅ Local AI inference with 8+ models
- ✅ Intelligent router architecture
- ✅ Multi-agent orchestration
- ✅ Self-improvement engine
- ✅ Custom tools & connectors
- ✅ Sandboxed execution
- ✅ Windows installer

### Upcoming (v1.1)
- 🔄 macOS and Linux installers
- 🔄 Enhanced RAG with vector databases
- 🔄 Multi-user collaboration
- 🔄 Advanced workflow designer
- 🔄 Plugin marketplace

### Future (v2.0)
- 🔮 Fine-tuning interface
- 🔮 Federated learning support
- 🔮 Advanced agent swarms
- 🔮 Enterprise SSO integration
- 🔮 Multi-language support

---

## 💬 Support

### Community
- **GitHub Issues**: [Bug reports and feature requests](https://github.com/Josh-lalosystems/LALO-ES/issues)
- **Discussions**: [Community Q&A](https://github.com/Josh-lalosystems/LALO-ES/discussions)

### Commercial Support
- **Email**: support@laloai.com
- **Enterprise**: enterprise@laloai.com
- **Website**: https://laloai.com

---

## 🙏 Acknowledgments

LALO AI Platform is built with:

- **FastAPI** - Modern web framework
- **React** - Frontend framework
- **llama.cpp** - Efficient LLM inference
- **Pydantic** - Data validation
- **SQLAlchemy** - Database ORM
- **Material-UI** - UI components

Special thanks to the open-source AI community for their contributions to model development and tooling.

---

## 📈 Stats

![GitHub stars](https://img.shields.io/github/stars/Josh-lalosystems/LALO-ES?style=social)
![GitHub forks](https://img.shields.io/github/forks/Josh-lalosystems/LALO-ES?style=social)
![GitHub issues](https://img.shields.io/github/issues/Josh-lalosystems/LALO-ES)
![GitHub pull requests](https://img.shields.io/github/issues-pr/Josh-lalosystems/LALO-ES)

---

<div align="center">

**Built with ❤️ by [LALO AI SYSTEMS, LLC](https://laloai.com)**

*Empowering enterprises with privacy-first AI automation*

[Documentation](docs/) · [Report Bug](https://github.com/Josh-lalosystems/LALO-ES/issues) · [Request Feature](https://github.com/Josh-lalosystems/LALO-ES/issues)

</div>
