# start_server.py
import sys
from pathlib import Path

# Add project root to sys.path so 'agents' module can be imported
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from os import environ
from microsoft_agents.hosting.core import AgentApplication, AgentAuthConfiguration
from microsoft_agents.hosting.aiohttp import (
   start_agent_process,
   jwt_authorization_middleware,
   CloudAdapter,
)
from aiohttp.web import Request, Response, Application, run_app
from semantic_kernel.contents import ChatHistory

# 1 Createg the AIOHTTP Server 
def start_server(
   agent_application: AgentApplication, auth_configuration: AgentAuthConfiguration
):
   async def entry_point(req: Request) -> Response:
      agent: AgentApplication = req.app["agent_app"]
      adapter: CloudAdapter = req.app["adapter"]
      return await start_agent_process(
            req,
            agent,
            adapter,
      )

   APP = Application(middlewares=[jwt_authorization_middleware])
   APP.router.add_post("/api/messages", entry_point)
   APP.router.add_get("/api/messages", lambda _: Response(status=200))
   APP["agent_configuration"] = auth_configuration
   APP["agent_app"] = agent_application
   APP["adapter"] = agent_application.adapter

   try:
      run_app(APP, host="localhost", port=environ.get("PORT", 3978))
   except Exception as error:
      raise error
   
# Memory and context imports for chat 
from microsoft_agents.hosting.core import (
   TurnState,
   TurnContext,
   MemoryStorage,
)

from agents.cloud_helper_agent import cloud_helper_agent
from agent_framework import AgentThread, ChatMessage

# Store agent threads per conversation
conversation_threads = {}

AGENT_APP = AgentApplication[TurnState](
    storage=MemoryStorage(), adapter=CloudAdapter()
)

async def _help(context: TurnContext, state: TurnState):
    await context.send_activity(
        "Hey I'm Cloud Helper I help you understand your cloud environment better!"
    )


AGENT_APP.conversation_update("membersAdded")(_help)

AGENT_APP.message("/help")(_help)


@AGENT_APP.activity("message")
async def on_message(context: TurnContext, state: TurnState):
    
    try:
        user_id = context.activity.from_property.id
        user_message = context.activity.text

        agent = cloud_helper_agent
        if user_id not in conversation_threads:
            conversation_threads[user_id] = agent.get_new_thread()
        agent_thread = conversation_threads[user_id]

        result = await agent.run(user_message, store=True, thread=agent_thread)
        await context.send_activity(result.messages[-1].text)
    
    except Exception as e:
        error_message = f"Sorry, I encountered an error: {str(e)}"
        print(f"Error in on_message: {e}")  # Log the error
        await context.send_activity(error_message)

if __name__ == "__main__":
    try:
        start_server(AGENT_APP, None)
    except Exception as error:
        raise error