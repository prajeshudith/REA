from src.agents.agent import rea_agent
import asyncio

user_prompt = """
Project: aimetlab
Team: aimetlab Team

User Request: 
1. Get the User story/Epic id 3
2. Check what are the existing task under this
3. Analyse and find whether anyother tasks can be created
4. If So breakdown the user story in to further tasks apart from the existing
5. Groom the tasks with proper titles, descriptions , acceptance criteria and estimates
6. Push everything into the Boards with proper title, description, acceptance criteria and estimates
7. Check the capacity of the team for the current sprint and see if these tasks can be accomodated
8. Finally assign the tasks to the team members based on their capacity and roles
"""

# """
# Project: aimetlab
# Team: aimetlab Team

# User Request:
# 1. Get the task details for the task id 25 
# 2. Check the capacity of the team for the current sprint and see if these tasks can be accomodated
# 3. Finally assign the tasks to the team members based on their capacity and roles
# """




response = asyncio.run(rea_agent(user_prompt))