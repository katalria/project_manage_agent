from langchain.agents import AgentExecutor

agent_executor = AgentExecutor.from_agent_and_tools(
    agent=agent,
    tools=[search_tool, calculator_tool],
    verbose=True,
)