# Tribby – My personal finance sidekick

Hey! 👋 I built Tribby because I got tired of spreadsheets and wanted something that actually *felt* good to use. It’s a desktop app that helps you track money, set budgets, save for goals, and automate those annoying recurring bills – all without sending your data anywhere. Everything stays on your machine.

## What it does

- **Dashboard** – see your balance, income, expenses, and how much of your budget you've used, all in one place.
- **Transactions** – add, edit, delete, search, and filter your spending. You can even export everything to CSV if you need to.
- **Budgeting** – set a monthly spending limit and also set caps for individual categories (like Food, Bills, etc.).
- **Savings Goals** – name a goal, set a target, and chip away at it. Add funds in custom amounts whenever you want.
- **Recurring transactions** – rent, subscriptions, salary… set them once and they’ll automatically pop up on schedule.
- **Dark / Light theme** – because we all have that one friend who hates dark mode.

## Download and run (Windows)

If you just want to use the app, grab the `.exe` file from the [`dist` folder](dist/Tribby.exe) right here in the repo.  

**No installation needed** – just download, double‑click, and you're off.

> *If the direct link above doesn't work, navigate to the `dist/` folder in the repo and grab `Tribby.exe` from there.*

## For the curious: building from source

If you want to peek under the hood or make your own tweaks:

1. Clone this repo.
2. Make sure you have Python 3.7+ installed.
3. Install the required libraries:
   ```bash
   pip install customtkinter matplotlib
