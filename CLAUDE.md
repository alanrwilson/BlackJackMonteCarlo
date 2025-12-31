# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Blackjack simulator with Monte Carlo simulation capabilities built in Python using Tkinter for the GUI. The project includes two main implementations:

1. **blackjack.py** - Basic Blackjack game with GUI
2. **blackjack_monte_carlo.py** - Advanced version with Monte Carlo simulation for expected value (EV) analysis

## Running the Application

```bash
# Run the basic blackjack game
python blackjack.py

# Run the Monte Carlo enhanced version
python blackjack_monte_carlo.py
```

## Dependencies

The project uses standard Python libraries:
- `tkinter` - GUI framework
- `PIL` (Pillow) - Image manipulation for card rendering (Monte Carlo version only)
- `random` - Card shuffling and simulation
- `copy` - Deep copying game state for simulations

Install Pillow if needed:
```bash
pip install Pillow
```

## Architecture

### Core Game Components

**Card, Deck, Hand Classes** (shared across both versions)
- `Card`: Represents a single playing card with suit, rank, and value
- `Deck`: 52-card deck with shuffle and deal functionality
- `Hand`: Manages a collection of cards with automatic ace adjustment (ace counted as 11 or 1)

### Monte Carlo Simulation Architecture

**MonteCarloSimulator Class** (blackjack_monte_carlo.py:99-304)
- Simulates thousands of hands to calculate expected value (EV) for each action
- `create_fresh_deck()`: Creates deck with known cards removed for accurate probability
- `simulate_hit/stand/double/split()`: Simulates outcomes for each possible action
- `basic_strategy_decision()`: Implements basic blackjack strategy for post-simulation play
- `calculate_expected_value()`: Returns EV with win/loss/push statistics

**Key Simulation Features:**
- Tracks known cards (visible cards) to adjust deck composition
- Runs configurable number of simulations (1K-50K)
- Provides EV analysis with W-L-P (Win-Loss-Push) breakdown
- Auto-simulator can play thousands of hands using basic strategy

### GUI Architecture

**BlackjackMonteCarloGUI Class** (blackjack_monte_carlo.py:306-1775)
- Three-panel layout: Left (Card Analysis), Center (Game), Right (Monte Carlo Stats)
- Card rendering using PIL to generate visual playing cards
- Real-time EV calculation and display
- Hand filtering system (pairs, soft hands, hard hands, specific dealer/player cards)

**Auto-Simulator** (blackjack_monte_carlo.py:929-1202)
- Automated gameplay using basic strategy
- Tracks aggregate EV data across multiple hands
- Results grouped by player hand total and dealer upcard
- `auto_sim_ev_data` dictionary structure: `(player_hand, dealer_upcard, action) -> [outcomes]`

### Game State Management

**Split Hand Handling:**
- Multiple hands stored in `player_hands` list
- `current_hand_index` tracks active hand
- Each hand played sequentially after split
- Bet amount applies per hand when split

**Dealer Logic:**
- Dealer must hit on 16 or less, stand on 17+
- Hidden card revealed only during dealer's turn
- Dealer skips turn if all player hands bust

## Key Implementation Details

**Ace Handling** (Hand.adjust_for_ace at line 69/59)
- Initially counted as 11
- Automatically converted to 1 when hand would bust
- `hand.aces` tracks number of "usable" aces (counted as 11)

**Card Counting Analysis** (blackjack_monte_carlo.py:778-846)
- Analyzes remaining deck to calculate bust/safe card probabilities
- Accounts for soft hands when determining bust cards
- Displays rank-by-rank breakdown of remaining cards

**EV Calculation Methodology:**
- Creates fresh deck for each simulation with known cards removed
- Simulates complete hand play using basic strategy
- Averages outcomes across all simulations
- Returns dollar EV relative to current bet amount

**Filter System** (blackjack_monte_carlo.py:709-776)
- Allows targeting specific hand scenarios
- Attempts up to 1000 deals to find matching hand
- Filters: pairs, ace-containing, soft hands, hard hands, specific dealer upcard, specific player first card

## Code Organization

- Backup files (`backup 171225.py`, `backup 211225.py`) represent previous versions
- Main game logic in GUI class methods
- Simulation logic isolated in `MonteCarloSimulator` class
- All card rendering done in `create_card_image()` method using PIL

## Common Modification Patterns

When adding features to the Monte Carlo simulator:
1. New simulation scenarios should extend `MonteCarloSimulator` class
2. GUI updates should maintain three-panel layout structure
3. EV data collection follows pattern: decision context -> outcomes list
4. Use `deck.copy()` and `hand.copy()` for simulation to avoid state mutation
