import asyncio
import os
from typing import Annotated, Any, Dict, List
import json 

from agent_framework import ai_function
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from pydantic import Field

from azure.mgmt.compute import ComputeManagementClient

load_dotenv()

credential = DefaultAzureCredential()

@ai_function(
    name="get_virtual_machine_information",
    description="""This tool can be used when more information is requested of a specific virtual machine.""",
    approval_mode="never_require"
)
async def get_virtual_machine_profile(
    virtual_machine_name: Annotated[str, Field(description="The name of the Virtual Machine")],
    resource_group: Annotated[str, Field(description="The name of the resource group of the Virtual Machine")],
    subscription_id: Annotated[str, Field(description="The subscription ID of the Virtual Machine")]
) -> str:
    """Return basic profile information for the virtual machine including max IOPS"""
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

        # Get VM size capabilities including max IOPS
        vm_size = virtual_machine.hardware_profile.vm_size
        max_iops = "Unknown"
        max_throughput_mbps = "Unknown"
        max_data_disk_count = "Unknown"
        
        try:
            # Get VM size capabilities
            vm_sizes = compute.virtual_machine_sizes.list(location=virtual_machine.location)
            for size in vm_sizes:
                if size.name == vm_size:
                    max_iops = getattr(size, 'max_data_disk_count', 'Unknown')
                    max_data_disk_count = getattr(size, 'max_data_disk_count', 'Unknown')
                    # Note: Azure VM sizes don't directly expose IOPS limits in the sizes API
                    # IOPS limits are typically based on VM size and disk type
                    break
                    
            # Try to get more detailed VM size info if available
            try:
                # Get resource SKUs for more detailed specs
                from azure.mgmt.compute.models import ResourceSkuRestrictionsType
                resource_skus = compute.resource_skus.list(filter=f"location eq '{virtual_machine.location}'")
                for sku in resource_skus:
                    if sku.resource_type == "virtualMachines" and sku.name == vm_size:
                        # Look for IOPS capabilities in the SKU
                        if sku.capabilities:
                            for capability in sku.capabilities:
                                if capability.name == "UncachedDiskIOPS":
                                    max_iops = capability.value
                                elif capability.name == "UncachedDiskBytesPerSecond":
                                    # Convert bytes to MB/s
                                    max_throughput_mbps = str(int(capability.value) // (1024 * 1024))
                        break
            except Exception:
                # If resource SKUs API fails, continue with basic info
                pass
                
        except Exception as e:
            # If we can't get size info, continue with basic VM info
            max_iops = f"Error getting IOPS info: {str(e)}"

        virtual_machine_profile = f"""
            vm_name: {virtual_machine.name},
            vm_size: {virtual_machine.hardware_profile.vm_size},
            location: {virtual_machine.location},
            os_type: {os_type},
            power_state: {power_state},
            provisioning_state: {virtual_machine.provisioning_state},
            resource_group: {resource_group},
            max_iops: {max_iops},
            max_throughput_mbps: {max_throughput_mbps},
            max_data_disk_count: {max_data_disk_count}
        """

        return virtual_machine_profile
    except Exception as e:
        return {"error": f"Failed to get VM profile: {str(e)}", "vm_name": virtual_machine_name}


@ai_function(
    name="get_virtual_machine_logs",
    description="This function can be used to retrieve the logs of a specific virtual machine",
    approval_mode="never_require"
)
async def get_virtual_machine_logs(
     virtual_machine_name: Annotated[str, Field(description="The name of the Virtual Machine")],
):
    """ Return log information regarding specific virtual machine"""
    file_path = "/Users/dylan/Documents/school/internship/development/cloud-solution-v1/data/vm_data.json"
    try:
        with open(file_path, "r") as f:
            data = json.load(f)

        return data.get(virtual_machine_name, None)

    except Exception as e:
        return f"something went wrong: {e}"