# League of Legends Live Tracker 🎮

This project is a Python-based League of Legends tracker that listens for an active match through the Riot API and monitors in-game events in real time. It integrates with **n8n** to automate data handling, notifications, and AI-generated Discord messages.

## Features 

* Detects when you start a new League of Legends match
* Tracks your **KDA** and **item purchases** during gameplay
* Lets you select a teammate to monitor
* Sends an automatic webhook to **n8n** whenever the selected teammate dies
* Sends the complete match history to n8n after the game ends
* Saves all collected data to a database via n8n
* Uses an AI agent to craft a “mean” message for the tracked teammate after each death
* Optionally sends that message to the teammate via **Discord**

## Purpose 

A playful combination of live game analytics and automation workflows, turning match events into dynamic notifications and AI-generated reactions.

## Requirements 

* Python
* Riot Games API key
* Running n8n instance with webhook
* Discord integration (optional)

## How it works 

1. The script polls the Riot API until a match starts.
2. Once in-game, it continuously monitors your stats and item purchases.
3. When the selected teammate dies, a webhook is triggered and sent to n8n.
4. After the match, a full summary is pushed to n8n.
5. n8n stores the data and may generate a custom Discord message.

## Notes 

This project is made for educational and entertainment purposes. Follow Riot’s API guidelines and use responsibly.
