import os
from typing import Annotated, List, Dict, Any
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.web import WebSiteManagementClient
from azure.core.exceptions import AzureError
from agent_framework.azure import AzureOpenAIChatClient
from dotenv import load_dotenv

load_dotenv()

class AzureResourceService:
    """Service for interacting with Azure resources."""
    
    def __init__(self, subscription_id: str, resource_group_name: str):
        self.subscription_id = subscription_id
        self.resource_group_name = resource_group_name
        
        # Use Managed Identity in production, DefaultAzureCredential for development
        self.credential = DefaultAzureCredential()
        
        # Initialize Azure management clients
        self.resource_client = ResourceManagementClient(
            self.credential, 
            subscription_id
        )
        self.compute_client = ComputeManagementClient(
            self.credential, 
            subscription_id
        )
        self.storage_client = StorageManagementClient(
            self.credential, 
            subscription_id
        )
        self.web_client = WebSiteManagementClient(
            self.credential, 
            subscription_id
        )

# Initialize Azure service
azure_service = AzureResourceService(
    subscription_id=os.environ.get("AZURE_SUBSCRIPTION_ID"),
    resource_group_name=os.environ.get("AZURE_RESOURCE_GROUP_NAME")
)

async def list_resource_group_resources(
    resource_group: Annotated[str, "Name of the Azure resource group"] = None
) -> str:
    """List all resources in the specified Azure resource group."""
    try:
        rg_name = resource_group or azure_service.resource_group_name
        
        resources = azure_service.resource_client.resources.list_by_resource_group(
            rg_name,
            expand="properties"
        )
        
        resource_list = []
        for resource in resources:
            resource_info = {
                "name": resource.name,
                "type": resource.type,
                "location": resource.location,
                "tags": resource.tags or {},
                "provisioning_state": getattr(resource.properties, 'provisioning_state', 'Unknown') if resource.properties else 'Unknown'
            }
            resource_list.append(resource_info)
        
        if not resource_list:
            return f"No resources found in resource group '{rg_name}'"
        
        # Format for agent consumption
        result = f"Found {len(resource_list)} resources in '{rg_name}':\n\n"
        for resource in resource_list:
            result += f"**{resource['name']}**\n"
            result += f"  - Type: {resource['type']}\n"
            result += f"  - Location: {resource['location']}\n"
            result += f"  - Status: {resource['provisioning_state']}\n"
            if resource['tags']:
                result += f"  - Tags: {', '.join([f'{k}={v}' for k, v in resource['tags'].items()])}\n"
            result += "\n"
        
        return result
        
    except AzureError as e:
        return f"Azure API error: {str(e)}"
    except Exception as e:
        return f"Error listing resources: {str(e)}"

async def get_virtual_machines_status(
    resource_group: Annotated[str, "Name of the Azure resource group"] = None
) -> str:
    """Get status and details of virtual machines in the resource group."""
    try:
        rg_name = resource_group or azure_service.resource_group_name
        
        vms = azure_service.compute_client.virtual_machines.list(rg_name)
        
        vm_list = []
        for vm in vms:
            # Get instance view for power state
            instance_view = azure_service.compute_client.virtual_machines.instance_view(
                rg_name, vm.name
            )
            
            power_state = "Unknown"
            for status in instance_view.statuses:
                if status.code.startswith('PowerState/'):
                    power_state = status.display_status
                    break
            
            vm_info = {
                "name": vm.name,
                "size": vm.hardware_profile.vm_size,
                "location": vm.location,
                "power_state": power_state,
                "os_type": vm.storage_profile.os_disk.os_type.value if vm.storage_profile.os_disk.os_type else "Unknown"
            }
            vm_list.append(vm_info)
        
        if not vm_list:
            return f"No virtual machines found in resource group '{rg_name}'"
        
        result = f"Found {len(vm_list)} virtual machines in '{rg_name}':\n\n"
        for vm in vm_list:
            result += f"**{vm['name']}**\n"
            result += f"  - Size: {vm['size']}\n"
            result += f"  - OS: {vm['os_type']}\n"
            result += f"  - Location: {vm['location']}\n"
            result += f"  - Power State: {vm['power_state']}\n\n"
        
        return result
        
    except AzureError as e:
        return f"Azure API error: {str(e)}"
    except Exception as e:
        return f"Error getting VM status: {str(e)}"

async def get_storage_accounts_info(
    resource_group: Annotated[str, "Name of the Azure resource group"] = None
) -> str:
    """Get information about storage accounts in the resource group."""
    try:
        rg_name = resource_group or azure_service.resource_group_name
        
        storage_accounts = azure_service.storage_client.storage_accounts.list_by_resource_group(rg_name)
        
        storage_list = []
        for account in storage_accounts:
            storage_info = {
                "name": account.name,
                "location": account.location,
                "sku": account.sku.name,
                "kind": account.kind.value,
                "provisioning_state": account.provisioning_state.value,
                "primary_endpoints": {}
            }
            
            if account.primary_endpoints:
                storage_info["primary_endpoints"] = {
                    "blob": account.primary_endpoints.blob,
                    "file": account.primary_endpoints.file,
                    "queue": account.primary_endpoints.queue,
                    "table": account.primary_endpoints.table
                }
            
            storage_list.append(storage_info)
        
        if not storage_list:
            return f"No storage accounts found in resource group '{rg_name}'"
        
        result = f"Found {len(storage_list)} storage accounts in '{rg_name}':\n\n"
        for storage in storage_list:
            result += f"**{storage['name']}**\n"
            result += f"  - SKU: {storage['sku']}\n"
            result += f"  - Kind: {storage['kind']}\n"
            result += f"  - Location: {storage['location']}\n"
            result += f"  - Status: {storage['provisioning_state']}\n"
            if storage['primary_endpoints'].get('blob'):
                result += f"  - Blob Endpoint: {storage['primary_endpoints']['blob']}\n"
            result += "\n"
        
        return result
        
    except AzureError as e:
        return f"Azure API error: {str(e)}"
    except Exception as e:
        return f"Error getting storage accounts: {str(e)}"

async def get_app_services_info(
    resource_group: Annotated[str, "Name of the Azure resource group"] = None
) -> str:
    """Get information about App Services in the resource group."""
    try:
        rg_name = resource_group or azure_service.resource_group_name
        
        web_apps = azure_service.web_client.web_apps.list_by_resource_group(rg_name)
        
        app_list = []
        for app in web_apps:
            app_info = {
                "name": app.name,
                "location": app.location,
                "state": app.state,
                "default_host_name": app.default_host_name,
                "app_service_plan": app.server_farm_id.split('/')[-1] if app.server_farm_id else "Unknown",
                "runtime_stack": getattr(app.site_config, 'linux_fx_version', 'Unknown') if app.site_config else 'Unknown'
            }
            app_list.append(app_info)
        
        if not app_list:
            return f"No App Services found in resource group '{rg_name}'"
        
        result = f"Found {len(app_list)} App Services in '{rg_name}':\n\n"
        for app in app_list:
            result += f"**{app['name']}**\n"
            result += f"  - URL: https://{app['default_host_name']}\n"
            result += f"  - State: {app['state']}\n"
            result += f"  - Location: {app['location']}\n"
            result += f"  - App Service Plan: {app['app_service_plan']}\n"
            result += f"  - Runtime: {app['runtime_stack']}\n\n"
        
        return result
        
    except AzureError as e:
        return f"Azure API error: {str(e)}"
    except Exception as e:
        return f"Error getting App Services: {str(e)}"

# Create Azure Resource Agent
chat_client = AzureOpenAIChatClient(api_key=os.environ.get("AZURE_OPENAI_API_KEY", ""))

azure_resource_agent = chat_client.create_agent(
    name="Azure Resource Specialist",
    instructions=(
        "You are an Azure resource management specialist. You can help users:\n"
        "1. List all resources in a resource group\n"
        "2. Check virtual machine status and details\n"
        "3. Get storage account information\n"
        "4. Monitor App Services status\n\n"
        "You have access to Azure management APIs through secure tools. "
        "Always provide clear, actionable information about Azure resources. "
        "If you encounter errors, explain them in user-friendly terms and suggest solutions."
    ),
    tools=[
        list_resource_group_resources,
        get_virtual_machines_status,
        get_storage_accounts_info,
        get_app_services_info
    ]
)

def main():
    """Launch the Azure Resource Agent."""
    import logging
    from agent_framework.devui import serve
    
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger = logging.getLogger(__name__)
    
    logger.info("🚀 Starting Azure Resource Management Agent")
    logger.info("📊 Available at: http://localhost:8097")
    logger.info("\n🔧 Capabilities:")
    logger.info("   - List all resources in resource group")
    logger.info("   - Check VM status and details")
    logger.info("   - Monitor storage accounts")
    logger.info("   - Get App Services information")
    logger.info(f"\n📍 Target Resource Group: {azure_service.resource_group_name}")
    
    serve(entities=[azure_resource_agent], port=8097, auto_open=True)

if __name__ == "__main__":
    main()