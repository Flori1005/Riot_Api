# League of Legends Live Tracker

This project is a Python-based League of Legends tracker that listens for an active match through the Riot API and monitors in-game events in real time. It integrates with n8n to automate data handling, notifications, and AI-generated Discord messages.

## Features

* Tracks when the player starts a new League of Legends match
* Monitors the player’s **KDA** and **item purchases** during the game
* Allows selecting an additional teammate to track
* Sends a webhook to **n8n** whenever the selected teammate dies
* Sends the complete match history to n8n when the game finishes
* Stores all collected data in a database via n8n
* Uses an AI agent inside n8n to generate a “mean” message for the tracked teammate after every death
* Optionally sends the message to the teammate via **Discord**

## Purpose

This script combines live game data with workflow automation to create a playful mix of analytics, notifications, and AI-generated interactions.

## Requirements

* Python
* Riot Games API key
* n8n instance with a webhook
* Discord integration (optional for messages)

## How it works

1. The script polls the Riot API until a match starts.
2. Once in-game, it continuously tracks stats and purchases.
3. When the selected teammate dies, death data is pushed to n8n.
4. After the match ends, a full summary is sent to n8n.
5. n8n stores the data and may generate a personalized Discord message.

## Notes

This project is intended for educational and entertainment purposes. Use responsibly and comply with Riot API usage policies.
