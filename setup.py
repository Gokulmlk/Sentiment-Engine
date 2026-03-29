from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="sentiment-engine",
    version="1.0.0",
    author="Sentiment Engine Team",
    author_email="team@sentimentengine.com",
    description="Fear & Greed Sentiment Analysis Engine for Financial Markets",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sentiment-engine/sentiment-engine",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "sentiment-engine=sentiment_engine.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "sentiment_engine": ["configs/*.yml"],
    },
)