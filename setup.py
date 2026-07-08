from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="langchain-paypack",  # 改为 langchain- 前缀，更符合搜索习惯
    version="0.5.0",           # RPC 故障转移 + 交易重试 + 限额持久化
    description="LangChain tool for PayPack: AI Agent autonomous payments (HTTP 402, x402, AP2)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="ronghua",
    author_email="2283794147@qq.com",  # 替换为你的真实邮箱
    license="Apache-2.0",
    url="https://github.com/rhcjw/paypack",   # 主仓库
    project_urls={
        "Source": "https://github.com/rhcjw/paypack",
        "Tracker": "https://github.com/rhcjw/paypack/issues",
        "Gitee Mirror": "https://gitee.com/rhcjw_com/paypack",
    },
    packages=find_packages(),
    install_requires=[
        "langchain-core>=0.1.0,<0.3.0",
        "web3>=6.0.0,<7.0.0",
        # "paypack>=0.3.0",                   # TODO: 核心包发布到 PyPI 后取消注释
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Intended Audience :: Developers",
    ],
    python_requires=">=3.10",
)