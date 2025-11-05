import asyncio

from typing import Dict, List 

from agent_framework import (
    Executor,
    WorkflowBuilder, 
    WorkflowContext, 
    handler,
    WorkflowEvent,
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
    async def __call__(self, subscription_id: str, ctx: WorkflowContext[List[Dict[str,str]]]) -> None: 
        """ List all resource groups based on subscription ID"""
        print(subscription_id)
        credential = DefaultAzureCredential()

        try:
            await ctx.add_event(CustomEvent(f"Starting to fetch resource groups for subscription: {subscription_id}"))
            print("try block")
            resource_group_list = []
            resource_client = ResourceManagementClient(credential=credential, subscription_id=subscription_id)

            print(resource_client)

            for resource_group in resource_client.resource_groups.list():
                resource_group_list.append({
                    "id": resource_group.id, 
                    "name": resource_group.name, 
                    "location": resource_group.location
                })

            await ctx.add_event(CustomEvent(f"Found {len(resource_group_list)} resource groups"))
            await ctx.yield_output(resource_group_list)

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
            await ctx.yield_output(location_list)
        except Exception as e:
            await ctx.add_event(CustomEvent(f"Error extracting locations: {e}"))
            print(f"Something went wrong in location extract: {e}")


def fetch_resource_groups_workflow():

    fetch_rgs = ResourceGroupFetcher(id="fetch_resource_groups")
    fetch_locations = LocationExtractor(id="fetch_resource_group_locations")

    return (WorkflowBuilder(
        name="Resource group fetching workflow",
        description="This workflow fetches all of the resourcegroups in a subscription"
    )
    .set_start_executor(fetch_rgs)
    .add_edge(fetch_rgs, fetch_locations)
    .build()
    )



if __name__ == '__main__':
    asyncio.run(fetch_resource_groups_workflow())

