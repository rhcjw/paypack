from setuptools import setup, find_packages

setup(
    name="paypack-langchain",
    version="0.2.0",
    description="Universal payment tool for AI Agents - LangChain integration",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="PayPack Authors",
    url="https://gitee.com/rhcjw_com/paypack",
    packages=find_packages(),
    install_requires=[
        "langchain-core>=0.1.0",
        "web3>=6.0.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Intended Audience :: Developers",
    ],
    python_requires=">=3.10",
)