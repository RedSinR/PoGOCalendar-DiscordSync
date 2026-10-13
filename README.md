PoGOCalendar-DiscordSync

Automatically synchronize Pokémon GO events with Discord Scheduled Events.

PoGOCalendar-DiscordSync is a Python automation project that retrieves Pokémon GO event information and keeps a Discord server's Scheduled Events up to date.

It uses GitHub Actions to run automatically, so you don't need to leave your computer running.

✨ Features

Automatic synchronization: Retrieves Pokémon GO event data and syncs it with Discord.

Scheduled automation: Runs through GitHub Actions without requiring a local computer to be online.

Event management: Helps keep Discord events aligned with the source calendar.

Easy configuration: Uses GitHub repository settings to store the information needed to connect to Discord.

Python-based: Uses a Python script to process event data and communicate with Discord.

⚙️ How It Works

The project connects an existing Pokémon GO event data source to Discord.

The general workflow is:

Retrieve event data — The Python script downloads the available Pokémon GO event calendar data.

Process events — The script reads the source data and identifies upcoming events to synchronize.

Connect to Discord — The script authenticates with Discord using a bot token.

Synchronize scheduled events — The script checks the relevant Discord events and applies the synchronization logic.

Repeat automatically — GitHub Actions runs the workflow again according to its schedule.

This allows a Discord server's event calendar to stay updated without someone manually creating every event.

🐍 Project Structure

The main components are:

File or component

Purpose

sync_events.py

Main Python script that retrieves and synchronizes events.

.github/workflows/

Contains the GitHub Actions workflow configuration.

requirements.txt

Lists the Python packages required by the script.

GitHub Actions

Runs the automation on GitHub-hosted runners.

Discord bot

Provides access to the target server's Scheduled Events.

🚀 Running the Automation

Automatic execution

GitHub Actions runs the configured workflow automatically.

To view a run:

Open this repository on GitHub.

Select Actions.

Select the synchronization workflow.

Open a run to inspect its output and any errors.

If the workflow supports manual execution, you can also start a run from the Actions page.

Running locally

You'll need Python installed, along with the packages listed in requirements.txt.

Install the dependencies:

python -m pip install -r requirements.txt

Configure the required environment variables, then run:

python sync_events.py

The script must have valid Discord credentials and permission to manage Scheduled Events in the target server.

🔐 Configuration and Security

The project requires the configuration values used by its script and GitHub Actions workflow.

These may include:

A Discord bot token.

The Discord server (guild) ID.

Any additional configuration required by the workflow.

Store sensitive credentials in GitHub → Settings → Secrets and variables → Actions.

Never commit a Discord bot token to the repository or publish it in logs, screenshots, or documentation.

The bot must be invited to the intended Discord server and granted the necessary permissions.

📅 Event Data Source

This project uses Pokémon GO event information provided by ScrapedDuck.

Original project:
https://github.com/bigfoott/ScrapedDuck

Public event data:
https://raw.githubusercontent.com/bigfoott/ScrapedDuck/data/events.json

ScrapedDuck provides event data that this project can consume for synchronization. The Discord integration and automation in this repository serve a separate purpose: bringing event information into a Discord server's Scheduled Events.

🙏 Credits and Acknowledgments

ScrapedDuck — bigfoott

A huge thank-you to bigfoott/ScrapedDuck for maintaining the Pokémon GO event data resource.

This project builds on the availability of that event data. Please visit the original repositorys to learn more about the upstream project and its licensing terms.

LeekDuck

LeekDuck is a fantastic Pokémon GO community resource for event information and updates.

It is acknowledged here as a community resource; this project does not claim ownership of LeekDuck's content or imply an official affiliation.

Pokémon GO Community

Thanks to the Pokémon GO community members who maintain event resources, contribute to open-source projects, and help make useful community tools possible.

🛠️ Troubleshooting

The workflow fails

Open the GitHub Actions run and inspect the logs for the first error.

Discord events aren't updating

Check that the bot token is valid, the server ID is correct, and the bot has the required permissions.

Event data can't be retrieved

Check whether the upstream event data is accessible and whether its format has changed.

The workflow doesn't run automatically

Review the workflow configuration under .github/workflows/ and check the repository's Actions settings.

📜 Licensing

This repository and its dependencies may have separate licensing terms.

Please consult the license files and usage terms of this project and the upstream resources before redistributing code or data. Attribution does not replace any license requirements.

PoGOCalendar-DiscordSync
An independent community project for automating Pokémon GO event synchronization with Discord.


-GPT did all the work, I'm just the monkey working the keyboard.
