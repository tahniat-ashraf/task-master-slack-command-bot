# Task Manager Slack Command Bot

## Description

Task Manager Slack Command Bot is an innovative Slack bot developed using Python and the FastAPI framework. It empowers your team with seamless task management, code review, and collaboration capabilities, enhancing productivity and team dynamics. The bot integrates seamlessly with Slack's API set through the Slack Python library, ensuring a smooth and efficient user experience.

## Features

- **/review Command:**
  - Triggered with `/review` command followed by a Git Pull Request (PR) link.
  - Randomly selects a team member to review the provided Git PR link.
  - Mention a specific member's name after `/review` to assign the review task precisely.
  - Handles multiple member mentions by randomly picking one for equitable task distribution.

- **/inspect Command:**
  - Highlight any valid URL in a Slack channel with the `/inspect` command.
  - Randomly assigns a team member to inspect the mentioned URL.
  - Most speculated use case: Randomly pick a team mate to take a look at a Slack conversation gaining momentum, adding a fun twist to collaboration.

## Future Expansion

We are committed to continually expanding the capabilities of the Task Manager Slack Command Bot. Future planned features include:

- Random Task Assignment: Randomly pick a Slack group member for a requested task to ensure fair distribution of assignments and foster collaboration.
- Agile Story Pointing: Streamline sprint planning sessions with Agile story pointing, enabling efficient estimation of user stories.

## Getting Started

1. Clone this repository and navigate to the project directory.
2. Set up the virtual environment using Python's virtualenv or your preferred method.
3. Install the required dependencies, including FastAPI and the Slack Python library.
4. Create a .env file in the project root directory and add your Slack token and signing secret. Make sure to keep this information secure and do not share it publicly.
5. Customize the bot's behavior, appearance, and Slack API integration to align with your team's preferences.
6. Launch the bot using FastAPI and deploy it on your chosen hosting service.
7. Configure your Slack workspace to interact with the Task Manager Slack Command Bot via its Slack API integration.

## Contributions

We welcome and encourage contributions to this open-source project. To contribute, please submit pull requests, suggest new features, or share your ideas to expand the capabilities of the Task Manager Slack Command Bot. Together, we can create a powerful and versatile tool to streamline your team's workflow and boost productivity.

Let's build the future of collaborative team experiences! Happy task managing, reviewing, inspecting, and planning! 🚀🔍📈
