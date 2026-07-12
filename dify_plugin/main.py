"""
PayPack Dify Plugin — Entry point.

Usage:
    dify-plugin run          # Local debug
    dify-plugin package      # Package as .difypkg
"""
from dify_plugin import Plugin, DifyPluginEnv

# Plugin entry — auto-loaded by Dify runtime
# Providers and tools are auto-discovered from manifest.yaml
plugin = Plugin(DifyPluginEnv())

# Start
if __name__ == "__main__":
    plugin.run()
