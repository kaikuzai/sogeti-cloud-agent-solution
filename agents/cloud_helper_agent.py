import os 

from agent_framework import ChatAgent
from agent_framework.azure import AzureOpenAIAssistantsClient
from azure.identity import DefaultAzureCredential

from dotenv import load_dotenv

from tools.get_cloud_resources import list_resource_groups, get_resources_in_resource_group
from tools.get_virtual_machine_context import get_virtual_machine_profile

credential = DefaultAzureCredential()

load_dotenv()

cloud_helper_agent = ChatAgent(
    name="Cloud Helper Agent", 
    description="An agent which helps employees understand their cloud infrastructure and resources", 
    instructions= "You're an agent which helps employees from the Multi Client Azure Team (MCAT-team) help understand their cloud environment. When listing resource groups, only show the names in a simple list format unless the user specifically asks for additional details like location or ID. Format resource group names as a simple bulleted list. If you don't have the capabilities to perform certain requested actions. Tell the user that you don't have the capibilities and to contact Dylan to add them",
    temperature=0,
    tool_choice="auto",
    tools=[list_resource_groups, 
           get_resources_in_resource_group,
           get_virtual_machine_profile, 
           ],
 
    chat_client=AzureOpenAIAssistantsClient(
       credential=credential, 
       api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
       deployment_name=os.environ.get("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"),
       endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
        )
    )
