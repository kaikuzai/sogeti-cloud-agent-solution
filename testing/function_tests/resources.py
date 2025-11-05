import os 
import asyncio
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from agent_framework import ai_function

from dotenv import load_dotenv

load_dotenv()

credential = DefaultAzureCredential()
subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")

@ai_function(name="List resource groups in subscription", description="This function will list all of the available resoure groups in the subscription, it cannot give any information about what is in those resource groups.", approval_mode="always_require")
async def list_resource_groups():
    resource_group_list = []
    resource_client = ResourceManagementClient(credential=credential, subscription_id=subscription_id)

    for rg in resource_client.resource_groups.list():
        resource_group_list.append(rg.name)

    return resource_group_list

if __name__ == '__main__':
    asyncio.run(list_resource_groups())