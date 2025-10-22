from src.agents.agent import rea_agent
import asyncio
import sys

def product_owner_agent():
    # user_prompt = """
    # Project: aimetlab
    # Team: aimetlab Team

    # User Request: 
    # 1. Get the User story/Epic id 3
    # 2. Check what are the existing task under this
    # 3. Analyse and find whether anyother tasks can be created
    # 4. Only If additional tasks are required so badly, breakdown the user story in to further tasks apart from the existing
    # 5. Groom the tasks with proper titles, descriptions , acceptance criteria, priority and work estimates
    # 6. Push everything into the Boards with proper title, description, acceptance criteria, priority and work estimates
    # 7. Check the capacity of the team for the current sprint and see if these tasks can be accomodated
    # 8. Finally assign the tasks to the team members based on their capacity and roles
    # 9. Finally prepare a report named "User_Stories_Report.html" on the created tasks and their assignments
    # """

    user_prompt = """
    Project: aimetlab2
    Team: aimetlab2 Team

    User Request:
    1. Get the Feature id 18
    2. Check what are the existing user stories under this
    3. Analyse and find whether any other user stories can be created
    4. Only If additional user stories are required so badly, breakdown the feature into further user stories apart from the existing
    5. Groom the user stories with proper titles, descriptions , acceptance criteria and story points
    6. Push everything into the Boards with proper title, description and priority
    7. Update the user stories with story points based on the complexity
    8. Check the capacity of the team for the current sprint and see if these user stories can be accomodated
    9. Assign the user stories to the team members based on their capacity and roles and tag them in this current sprint
    10. Finally prepare a report named "User_Stories_Report.html" on the created user stories and their assignments
    """

    response = asyncio.run(rea_agent(user_prompt, role="product owner"))
    return response

def scrum_lead_agent():
    # user_prompt = """
    # Project: aimetlab
    # Team: aimetlab Team

    # User Request: 
    # 1. Review the current sprint progress
    # 2. Identify any blockers or issues faced by the team members
    # 3. Check whether team members are committing their codes regularly
    # 4. Ensure that daily standup updates are being provided by all team members in the task comments
    # 5. Track the completion status of tasks assigned to each team member
    # 6. Identify any tasks that are at risk of not being completed within the sprint timeline
    # 7. Finally prepare a report on the sprint progress and whether we are on track to meet our sprint goals
    # """

    user_prompt = """
    Project: aimetlab2
    Team: aimetlab2 Team

    User Request:
    1. Does all User Stories in the current sprint have tasks created under them?
    2. Does all team members have tasks assigned in the current sprint?
    3. Do all team members provide daily standup updates in the task comments?
    4. Are team members committing their code regularly?
    5. Identify any blockers or issues faced by the team members if any specified in the comments
    6. Finally prepare a report named "Sprint_Report.html" on the sprint progress with all the above details and whether we are on track to meet our sprint goals
    """
    response = asyncio.run(rea_agent(user_prompt, role="scrum lead"))
    return response

def peer_reviewer_agent():
    user_prompt = """
    Project: aimetlab
    Team: aimetlab Team

    User Request: 
    1. Review the code changes made in the last 3 days
    2. Identify any potential issues or improvements in the code quality
    3. Check whether the code changes are following the best practices and coding standards
    4. Finally prepare a report on the code review findings and suggest any necessary actions
    """
    response = asyncio.run(rea_agent(user_prompt, role="peer review"))
    return response

if __name__ == "__main__":
    if len(sys.argv) > 1:
        function_to_call = sys.argv[1]
        if function_to_call == "product_owner_agent":
            product_owner_agent()
        elif function_to_call == "scrum_lead_agent":
            scrum_lead_agent()
        elif function_to_call == "peer_reviewer_agent":
            peer_reviewer_agent()
        else:
            print(f"Unknown function: {function_to_call}")
    else:
        print("Please provide a function to call: product_owner_agent, scrum_lead_agent, or peer_reviewer_agent")