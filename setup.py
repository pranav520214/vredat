from setuptools import setup, find_packages

setup(
    name="vredat",
    version="0.1.0",
    description="Terminal AI Coding Environment powered by Laya, Ponytail, and Llama",
    py_modules=["cli", "engine_laya", "engine_llm", "memory_ponytail", "tools"],
    entry_points={
        "console_scripts": [
            "vredat=cli:main",
            "verdeta=cli:main",
        ],
    },
    install_requires=[
        "rich",
        "requests",
    ],
)
