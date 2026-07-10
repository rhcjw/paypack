"""
PayPack Dify Plugin — 入口文件。

使用方式:
    dify-plugin run          # 本地调试
    dify-plugin package      # 打包为 .difypkg
"""
from dify_plugin import Plugin, DifyPluginEnv

# 插件入口 — Dify 运行时自动加载
plugin = Plugin(DifyPluginEnv())

# 注册 Provider 和 Tools
plugin.register_provider("paypack", __name__ + ".provider.paypack:PaypackProvider")
plugin.register_tool("paypack_pay", __name__ + ".tools.paypack_pay:PaypackPayTool")
plugin.register_tool("paypack_query", __name__ + ".tools.paypack_query:PaypackQueryTool")
plugin.register_tool("paypack_refund", __name__ + ".tools.paypack_refund:PaypackRefundTool")

# 启动
if __name__ == "__main__":
    plugin.run()
