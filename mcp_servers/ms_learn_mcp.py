import asyncio
from agent_framework import ChatAgent, MCPStreamableHTTPTool
from agent_framework.azure import AzureAIAgentClient
from azure.identity.aio import AzureCliCredential

async def create_mslearn_mcp_tool():
    """Create and return an HTTP-based MCP tool for Microsoft Learn."""
    mcp_tool = MCPStreamableHTTPTool(
        name="Microsoft Learn MCP",
        url="https://learn.microsoft.com/api/mcp",
        # Note: You may need to adjust headers or authentication based on actual API requirements
        headers={
            "User-Agent": "Cloud-Helper-Agent/1.0",
            "Accept": "application/json"
        }
    )
    return mcp_tool

async def test_mslearn_agent():
    """Example function to test the Microsoft Learn MCP integration."""
    async with (
        AzureCliCredential() as credential,
        create_mslearn_mcp_tool() as mcp_server,
        ChatAgent(
            chat_client=AzureAIAgentClient(async_credential=credential),
            name="MSLearnAgent",
            instructions="You are a helpful assistant that can search and answer questions using Microsoft Learn documentation. Use the Microsoft Learn MCP tool to find relevant information.",
        ) as agent,
    ):
        result = await agent.run(
            "How do I create an Azure storage account using Azure CLI?",
            tools=mcp_server
        )
        print("Agent Response:")
        print(result.messages[-1].content if result.messages else "No response")
        return result

def get_mslearn_mcp_tool():
    """Synchronous function to get the MCP tool for use in other agents."""
    return MCPStreamableHTTPTool(
        name="Microsoft Learn MCP",
        url="https://learn.microsoft.com/api/mcp",
        headers={
            "User-Agent": "Cloud-Helper-Agent/1.0",
            "Accept": "application/json"
        }
    )

async def http_mcp_example():
    """Original example using an HTTP-based MCP server."""
    async with (
        AzureCliCredential() as credential,
        MCPStreamableHTTPTool(
            name="Microsoft Learn MCP",
            url="https://learn.microsoft.com/api/mcp",
            headers={"Authorization": "Bearer your-token"},
        ) as mcp_server,
        ChatAgent(
            chat_client=AzureAIAgentClient(async_credential=credential),
            name="DocsAgent",
            instructions="You help with Microsoft documentation questions.",
        ) as agent,
    ):
        result = await agent.run(
            "How to create an Azure storage account using az cli?",
            tools=mcp_server
        )
        print(result)

if __name__ == "__main__":
    print("Testing Microsoft Learn MCP integration...")
    asyncio.run(test_mslearn_agent())

