import asyncio 

from agent_framework import (
    Executor, 
    WorkflowBuilder, 
    WorkflowContext, 
    executor, 
    handler, 
)

from typing_extensions import Never

# Executors can be created with either a Subclass of the executor class 

class UpperCase(Executor): 
    def __init__(self, id: str):
        super().__init__(id=id)
    
    @handler
    async def to_upper_case(self, text: str, ctx: WorkflowContext[str]) -> None: 
        """ Conver the input to uppercase and forward it to the next node
        
        Note: The WorkflowContext is parameterized with the type this handler will emit. Here WorkflowContext[str] means downstream nodes should expect str. 
        """

        result = text.upper()
        
        # Send the result to the next executor in the workflow 
        await ctx.send_message(result)



# Executors can also be created with a standalone function with the @executor in the signatur 

@executor(id="reverse_text_executor")
async def reverse_text(text: str, ctx: WorkflowContext[str]) -> None: 
    """ Revers a the input string and yield the workflow output
    
    This node yields the final output using ctx.yield_output(result).
    The workflow will complete when it becomes idle (no more work to do)

    The WorkflowContext is parameterized with two types:
    - T_Out = Never: this node does not send messages to downstream nodes 
    - T_W_Out = str: this node yields workflow output of type str 
    
    """

    result = text[::-1]

    await ctx.yield_output(result)

async def main():
    """ Build a simple two step workflow using the fluent builder API"""

    upper_case = UpperCase(id="upper_case_executor")

    workflow = (WorkflowBuilder()
                .add_edge(upper_case, reverse_text)
                .set_start_executor(upper_case)
                .build())
    
    events = await workflow.run("hello world")
    print(events.get_outputs())

    print("Final state: ", events.get_final_state())


if __name__ == "__main__":
    asyncio.run(main())