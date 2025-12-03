import asyncio
import json 

from typing import Dict, List 

from agent_framework import (
    Executor,
    Workflow, 
    WorkflowBuilder, 
    WorkflowContext, 
    handler,
    WorkflowEvent,
    ChatMessage
)

from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient


class CustomEvent(WorkflowEvent):
    def __init__(self, message: str):
        super().__init__(message)

class ResourceGroupFetcher(Executor):
    def __init__(self, id:str):
        super().__init__(id=id)

    @handler 
    async def __call__(self, input: list[ChatMessage], ctx: WorkflowContext[List[Dict[str,str]]]) -> None: 
        """ List all resource groups based on subscription ID"""
        print(input)
        credential = DefaultAzureCredential()

        subscription_id = input[-1].text

        try:
            data = json.loads(subscription_id)
            value = data['input']
            subscription_id = value 
        except Exception as e: 
            print(f"couldn't use json because: {e}")

        try:
            await ctx.add_event(CustomEvent(f"Starting to fetch resource groups for subscription: {subscription_id}"))
            print("try block")
            resource_group_list = []
            resource_client = ResourceManagementClient(credential=credential, subscription_id=subscription_id)

            for resource_group in resource_client.resource_groups.list():
                resource_group_list.append({
                    "id": resource_group.id, 
                    "name": resource_group.name, 
                    "location": resource_group.location
                })

            await ctx.send_message(ChatMessage(text=resource_group_list, role="assistant"))

            await ctx.add_event(CustomEvent(f"Found {len(resource_group_list)} resource groups"))
            await ctx.send_message(resource_group_list)

        except Exception as e:
            await ctx.add_event(CustomEvent(f"Error fetching resource groups: {e}"))
            print(f"something went wrong: {e}")

class LocationExtractor(Executor):
    def __init__(self, id:str):
        super().__init__(id=id)
        
    @handler
    async def __call__(self, resource_groups: List[Dict[str, str]], ctx: WorkflowContext[list]) -> None: 
        try:
            await ctx.add_event(CustomEvent(f"Processing {len(resource_groups)} resource groups for location extraction"))
            location_list = []
            for rg in resource_groups:
                location = rg.get("location")
                if location:
                    location_list.append(location)

            await ctx.add_event(CustomEvent(f"Extracted {len(location_list)} unique locations"))
            print(location_list)
            await ctx.yield_output(location_list)
            await ctx.send_message(location_list)

        except Exception as e:
            await ctx.add_event(CustomEvent(f"Error extracting locations: {e}"))
            print(f"Something went wrong in location extract: {e}")


def create_resource_group_flow() -> Workflow: 
    fetch_rgs = ResourceGroupFetcher(id="fetch_resource_groups")
    fetch_locations = LocationExtractor(id="fetch_resource_group_locations")

    workflow = (WorkflowBuilder(
        name="Resource group fetching workflow",
        description="This workflow fetches all of the resourcegroups in a subscription"
    )
    .set_start_executor(fetch_rgs)
    .add_edge(fetch_rgs, fetch_locations)
    .build()
    )

    return workflow 


async def fetch_resource_groups_workflow():

    fetch_rgs = ResourceGroupFetcher(id="fetch_resource_groups")
    fetch_locations = LocationExtractor(id="fetch_resource_group_locations")

    workflow = (WorkflowBuilder(
        name="Resource group fetching workflow",
        description="This workflow fetches all of the resourcegroups in a subscription"
    )
    .set_start_executor(fetch_rgs)
    .add_edge(fetch_rgs, fetch_locations)
    .build()
    )

    res = await workflow.run(message="0818ef22-4784-4365-8a35-1f03e8c5e27d")

    print(res.get_outputs())

if __name__ == '__main__':
    asyncio.run(fetch_resource_groups_workflow())

