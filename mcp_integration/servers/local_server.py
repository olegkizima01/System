
"""
Local Fallback MCP Server implementation.
Provides basic tools when other servers are unavailable.
"""
import sys
import logging
from typing import List, Dict, Any

# Configure logging to stderr
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("local_server")

def main():
    logger.info("Starting Local Fallback MCP Server...")
    # Avoid printing to stdout as it breaks MCP protocol
    pass

if __name__ == "__main__":
    main()
