import sys
from pathlib import Path

# Ensure the project root is on sys.path when this test is run from the
# `testing` directory. This makes the top-level `tools` package importable.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


from agent_framework.devui import serve
from agents.cloud_helper_agent import cloud_helper_agent
from agent_framework.observability import setup_observability




def main():

    setup_observability()


    serve(entities=[cloud_helper_agent], port=8090, auto_open=True)

if __name__ == '__main__':
    main()