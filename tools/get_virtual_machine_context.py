import asyncio
import os
from typing import Annotated, Any, Dict, List

from agent_framework import ai_function
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from pydantic import Field

from azure.mgmt.compute import ComputeManagementClient

load_dotenv()

credential = DefaultAzureCredential()

@ai_function(
    name="get_virtual_machine_profile",
    description="Returns basic profile information for an Azure Virtual Machine including size, location, OS type, and current status",
    approval_mode="never_require"
)
async def get_virtual_machine_profile(
    virtual_machine_name: Annotated[str, Field(description="The name of the Virtual Machine")],
    resource_group: Annotated[str, Field(description="The name of the resource group of the Virtual Machine")],
    subscription_id: Annotated[str, Field(description="The subscription ID of the Virtual Machine")]
) -> Dict[str, Any]:
    """Return basic profile information for the virtual machine"""
    try:
        compute = ComputeManagementClient(credential=credential, subscription_id=subscription_id)
        
        # Get VM with instance view for power state
        virtual_machine = compute.virtual_machines.get(
            resource_group_name=resource_group, 
            vm_name=virtual_machine_name,
            expand='instanceView'
        )

        # Extract power state
        power_state = "Unknown"
        if virtual_machine.instance_view and virtual_machine.instance_view.statuses:
            for status in virtual_machine.instance_view.statuses:
                if status.code and status.code.startswith("PowerState/"):
                    power_state = status.display_status

        # Determine OS type
        os_type = "Unknown"
        if virtual_machine.os_profile:
            os_type = "Linux" if virtual_machine.os_profile.linux_configuration else "Windows"

        virtual_machine_profile = {
            "vm_name": virtual_machine.name,
            "vm_size": virtual_machine.hardware_profile.vm_size,
            "location": virtual_machine.location,
            "os_type": os_type,
            "power_state": power_state,
            "provisioning_state": virtual_machine.provisioning_state,
            "resource_group": resource_group
        }

        return virtual_machine_profile
    except Exception as e:
        return {"error": f"Failed to get VM profile: {str(e)}", "vm_name": virtual_machine_name}


@ai_function(
    name="",
    description="",
    approval_mode="never_require"
)
async def list_virtual_machine_disks(
    
):
    pass 