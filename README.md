# An-Chan

An is a Discord bot that acts as an interface to specific scheduling sheets made for Project Sekai

An does a variety of tasks in managing a Project Sekai run. These include
- Automatically checking in users before they need to play
- Customizing the message sent on check in
- Automatically calculating and displaying the users order in an hour
- Listing a user's given hours in their time zone
- Listing open slots on the scheduling sheet
- Listing all users that signed up for a specific day

These tasks are all simply a discord command and don't require any external tools aside from the Google Sheet

# Usage

An.py is the main file that is able to run on multiple servers at once.
An currently has two main types of "requests" which work with different formats of Google Sheets, requests have the same methods but read data off the sheets in different ways.
