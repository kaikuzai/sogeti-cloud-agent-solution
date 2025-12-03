import sys
from pathlib import Path

# Ensure the project root is on sys.path when this test is run from the
# `testing` directory. This makes the top-level `tools` package importable.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agent_framework.devui import serve
from agent_framework.observability import setup_observability
from workflows.fetch_resource_groups_wf_as_agent import create_resource_group_flow

def main():


    workflow = create_resource_group_flow()
    agent = workflow.as_agent(name="resource_location_agent")

    
    serve(entities=[agent], port=8091, auto_open=True)

if __name__ == '__main__':
    main()