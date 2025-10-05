"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

from setuptools import setup, find_packages

setup(
    name="lalo_ai",
    version="0.1.0",
    author="LALO AI, LLC",
    author_email="legal@lalo-ai.com",
    description="Agentic legacy layer overlay system architecture stubs—LALO AI core modules",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(include=["lalo_ai", "lalo_ai.*"]),
    install_requires=[
        "fastapi",
        "pydantic",
        "redis",
        "chromadb",
        "grpcio",
        "requests",
        "transformers",
        "uvicorn",
        "python-dotenv",
    ],
    python_requires=">=3.9",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
    ],
)
