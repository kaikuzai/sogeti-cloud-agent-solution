import asyncio
import os
from typing import Annotated, Any, Dict, List

from agent_framework import ai_function
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from dotenv import load_dotenv
from pydantic import Field

load_dotenv()

credential = DefaultAzureCredential()
subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")

@ai_function(
    name="list_resource_groups", 
    description="Use this function when the user requests the resource groups in their subscription. This function will list all of the available resoure groups in the subscription.", 
    approval_mode="never_require"
)
async def list_resource_groups(
    subscription_id: Annotated[str, Field(description="The subscription ID for the requested resource groups")]
) -> List[Dict[str, Any]]:
    """ List all of the resources in a specific subscription."""
    try:
        resource_group_list = []
        resource_client = ResourceManagementClient(credential=credential, subscription_id=subscription_id)

        for resource_group in resource_client.resource_groups.list():
            resource_group_list.append({
                "id": resource_group.id, 
                "name": resource_group.name, 
                "location": resource_group.location
            })

        return resource_group_list
    except Exception as e:
        return [{"error": f"An error occured trying to get resources in {subscription_id}: {e}"}]

@ai_function(
        name="get_resources_in_resource_group", 
        description="This function list all of the resources in a resource group. It cannot give specific information about individual resources", 
        approval_mode="never_require"
)
async def get_resources_in_resource_group(
    resource_group: Annotated[str, Field(description="The resource group name for the requested resources")], 
    subscription_id: Annotated[str, Field(description="The subscription ID for the requested resource group")]
) -> List[Dict[str, Any]]:
    """Return the resources with a specific resource group."""
    try:
        resource_client = ResourceManagementClient(credential=credential, subscription_id=subscription_id)

        resources = resource_client.resources.list_by_resource_group(resource_group_name=resource_group)

        resource_list = []
        for resource in resources:
            resource_list.append({
                "name": resource.name, 
                "type": resource.type, 
                "location": resource.location, 
                "kind": resource.kind, 
                "id": resource.id, 
            })

        return resource_list 
    except Exception as e:
        return[{"error":f"Error listing resources in {resource_group}: {e}"}]



if __name__ == '__main__':
    asyncio.run(list_resource_groups())