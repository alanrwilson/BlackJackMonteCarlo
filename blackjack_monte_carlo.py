import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import random
import copy
from PIL import Image, ImageDraw, ImageFont, ImageTk
import threading
import csv
from datetime import datetime


class Card:
    """Represents a playing card"""
    SUITS = ['♠', '♥', '♦', '♣']
    RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
    VALUES = {'A': 11, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 10, 'Q': 10, 'K': 10}

    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank
        self.value = self.VALUES[rank]

    def __str__(self):
        return f"{self.rank}{self.suit}"

    def copy(self):
        return Card(self.suit, self.rank)


class Deck:
    """Represents a deck of cards (can be multi-deck shoe)"""
    def __init__(self, num_decks=1):
        self.num_decks = num_decks
        self.initial_card_count = 52 * num_decks
        self.cards = []
        self.build()

    def build(self):
        """Build a shoe with num_decks decks"""
        self.cards = []
        for _ in range(self.num_decks):
            for suit in Card.SUITS:
                for rank in Card.RANKS:
                    self.cards.append(Card(suit, rank))
        self.shuffle()

    def shuffle(self):
        """Shuffle the deck"""
        random.shuffle(self.cards)

    def deal(self):
        """Deal a card from the shoe (no auto-rebuild)"""
        if len(self.cards) == 0:
            raise ValueError("Deck is empty! Reshuffle needed.")
        return self.cards.pop()

    def reshuffle_needed(self):
        """Check if shoe needs reshuffling (<=25% remaining)"""
        return len(self.cards) <= self.initial_card_count * 0.25

    def get_cards_remaining(self):
        """Get number of cards remaining in shoe"""
        return len(self.cards)

    def get_decks_remaining(self):
        """Get number of decks remaining (as float)"""
        return len(self.cards) / 52.0

    def copy(self):
        """Create a deep copy of the deck"""
        new_deck = Deck.__new__(Deck)
        new_deck.num_decks = self.num_decks
        new_deck.initial_card_count = self.initial_card_count
        new_deck.cards = [card.copy() for card in self.cards]
        return new_deck


class Hand:
    """Represents a hand of cards"""
    def __init__(self):
        self.cards = []
        self.value = 0
        self.aces = 0

    def add_card(self, card):
        """Add a card to the hand"""
        self.cards.append(card)
        self.value += card.value
        if card.rank == 'A':
            self.aces += 1
        self.adjust_for_ace()

    def adjust_for_ace(self):
        """Adjust value if there are aces and total is over 21"""
        while self.value > 21 and self.aces:
            self.value -= 10
            self.aces -= 1

    def is_blackjack(self):
        """Check if hand is a blackjack (21 with 2 cards)"""
        return len(self.cards) == 2 and self.value == 21

    def is_busted(self):
        """Check if hand is busted (over 21)"""
        return self.value > 21

    def can_split(self):
        """Check if hand can be split (two cards of same rank)"""
        return len(self.cards) == 2 and self.cards[0].rank == self.cards[1].rank

    def copy(self):
        """Create a deep copy of the hand"""
        new_hand = Hand()
        new_hand.cards = [card.copy() for card in self.cards]
        new_hand.value = self.value
        new_hand.aces = self.aces
        return new_hand

    def __str__(self):
        return ' '.join(str(card) for card in self.cards)


class MonteCarloSimulator:
    """Simulates blackjack outcomes using Monte Carlo method"""

    def __init__(self, num_simulations=10000, use_depleting_shoe=False):
        self.num_simulations = num_simulations
        self.use_depleting_shoe = use_depleting_shoe

    def create_fresh_deck(self, known_cards):
        """Create a deck with known cards removed"""
        # Start with all 52 cards
        all_cards = [Card(suit, rank) for suit in Card.SUITS for rank in Card.RANKS]

        # Remove known cards
        for known_card in known_cards:
            for i, card in enumerate(all_cards):
                if card.suit == known_card.suit and card.rank == known_card.rank:
                    all_cards.pop(i)
                    break

        # Shuffle
        random.shuffle(all_cards)

        # Create deck object (always single deck for simulations)
        deck = Deck.__new__(Deck)
        deck.num_decks = 1
        deck.initial_card_count = 52
        deck.cards = all_cards
        return deck

    def create_deck_from_shoe(self, actual_deck, known_cards):
        """Create a simulation deck from actual remaining shoe cards

        Args:
            actual_deck: The real game deck (potentially multi-deck shoe)
            known_cards: Visible cards to remove (player cards + dealer upcard)

        Returns:
            Deck object with actual remaining cards minus known cards
        """
        # Start with ALL remaining cards from actual shoe
        remaining_cards = [card.copy() for card in actual_deck.cards]

        # Remove known visible cards
        for known_card in known_cards:
            for i, card in enumerate(remaining_cards):
                if card.suit == known_card.suit and card.rank == known_card.rank:
                    remaining_cards.pop(i)
                    break

        # Shuffle
        random.shuffle(remaining_cards)

        # Create deck object preserving multi-deck properties
        deck = Deck.__new__(Deck)
        deck.num_decks = actual_deck.num_decks
        deck.initial_card_count = actual_deck.initial_card_count
        deck.cards = remaining_cards
        return deck

    def simulate_dealer(self, dealer_hand, deck):
        """Simulate dealer's turn following standard rules"""
        dealer_hand = dealer_hand.copy()
        deck = deck.copy()

        while dealer_hand.value < 17:
            dealer_hand.add_card(deck.deal())

        return dealer_hand

    def basic_strategy_decision(self, player_hand, dealer_upcard_value):
        """Simple basic strategy for continued play after hit"""
        player_value = player_hand.value

        # Hard totals
        if player_hand.aces == 0:
            if player_value >= 17:
                return "STAND"
            elif player_value >= 13 and dealer_upcard_value <= 6:
                return "STAND"
            elif player_value == 12 and 4 <= dealer_upcard_value <= 6:
                return "STAND"
            else:
                return "HIT"
        # Soft totals
        else:
            if player_value >= 19:
                return "STAND"
            elif player_value == 18 and dealer_upcard_value <= 8:
                return "STAND"
            else:
                return "HIT"

    def play_hand_optimally(self, player_hand, dealer_upcard_value, deck):
        """Play out a hand using basic strategy"""
        player_hand = player_hand.copy()
        deck = deck.copy()

        while True:
            decision = self.basic_strategy_decision(player_hand, dealer_upcard_value)

            if decision == "STAND" or player_hand.is_busted():
                break
            elif decision == "HIT":
                player_hand.add_card(deck.deal())

        return player_hand

    def simulate_hit(self, player_hand, dealer_upcard, deck, bet):
        """Simulate outcome after hitting"""
        player_hand = player_hand.copy()
        deck = deck.copy()

        player_hand.add_card(deck.deal())

        if player_hand.is_busted():
            return -bet

        # Continue with basic strategy
        dealer_upcard_value = dealer_upcard.cards[0].value
        player_hand = self.play_hand_optimally(player_hand, dealer_upcard_value, deck)

        if player_hand.is_busted():
            return -bet

        # Complete dealer hand (add hidden card + play)
        dealer_hand = dealer_upcard.copy()
        dealer_hand.add_card(deck.deal())  # Hidden card
        dealer_final = self.simulate_dealer(dealer_hand, deck)

        return self.calculate_outcome(player_hand, dealer_final, bet)

    def simulate_stand(self, player_hand, dealer_upcard, deck, bet):
        """Simulate outcome after standing"""
        # Complete dealer hand (add hidden card + play)
        dealer_hand = dealer_upcard.copy()
        deck = deck.copy()
        dealer_hand.add_card(deck.deal())  # Hidden card
        dealer_final = self.simulate_dealer(dealer_hand, deck)

        return self.calculate_outcome(player_hand, dealer_final, bet)

    def simulate_double(self, player_hand, dealer_upcard, deck, bet):
        """Simulate outcome after doubling down"""
        player_hand = player_hand.copy()
        deck = deck.copy()

        player_hand.add_card(deck.deal())

        if player_hand.is_busted():
            return -bet * 2

        # Complete dealer hand
        dealer_hand = dealer_upcard.copy()
        dealer_hand.add_card(deck.deal())  # Hidden card
        dealer_final = self.simulate_dealer(dealer_hand, deck)

        return self.calculate_outcome(player_hand, dealer_final, bet * 2)

    def simulate_split(self, player_hand, dealer_upcard, deck, bet):
        """Simulate outcome after splitting"""
        deck = deck.copy()
        dealer_upcard_value = dealer_upcard.cards[0].value

        hand1 = Hand()
        hand2 = Hand()

        hand1.add_card(player_hand.cards[0].copy())
        hand2.add_card(player_hand.cards[1].copy())

        # Check if splitting aces
        splitting_aces = player_hand.cards[0].rank == 'A'

        hand1.add_card(deck.deal())
        hand2.add_card(deck.deal())

        # Split aces get one card only and cannot hit further
        if not splitting_aces:
            # Play out both hands with basic strategy (non-aces)
            hand1 = self.play_hand_optimally(hand1, dealer_upcard_value, deck)
            hand2 = self.play_hand_optimally(hand2, dealer_upcard_value, deck)

        # Complete dealer hand
        dealer_hand = dealer_upcard.copy()
        dealer_hand.add_card(deck.deal())  # Hidden card
        dealer_final = self.simulate_dealer(dealer_hand, deck)

        # Calculate outcomes for both hands
        outcome1 = self.calculate_outcome(hand1, dealer_final, bet) if not hand1.is_busted() else -bet
        outcome2 = self.calculate_outcome(hand2, dealer_final, bet) if not hand2.is_busted() else -bet

        return outcome1 + outcome2

    def calculate_outcome(self, player_hand, dealer_hand, bet):
        """Calculate the outcome of a hand"""
        if player_hand.is_busted():
            return -bet
        elif dealer_hand.is_busted():
            return bet
        elif player_hand.value > dealer_hand.value:
            return bet
        elif player_hand.value < dealer_hand.value:
            return -bet
        else:
            return 0  # Push

    def calculate_expected_value(self, action, player_hand, dealer_upcard, known_cards, bet, cancel_flag=None, actual_deck=None):
        """Calculate expected value for a specific action and return EV with W-L-P stats

        Args:
            action: Action to evaluate (HIT, STAND, DOUBLE, SPLIT)
            player_hand: Player's hand
            dealer_upcard: Dealer's upcard
            known_cards: List of known visible cards
            bet: Current bet amount
            cancel_flag: Optional flag to cancel calculation
            actual_deck: Optional - the real game deck for depleting shoe mode
        """
        # Handle 0 simulations case
        if self.num_simulations == 0:
            return {
                'ev': 0,
                'wins': 0,
                'losses': 0,
                'pushes': 0
            }

        total = 0
        wins = 0
        losses = 0
        pushes = 0

        for _ in range(self.num_simulations):
            # Check if calculation should be cancelled
            if cancel_flag and cancel_flag():
                return None

            # Choose deck creation method based on mode
            if self.use_depleting_shoe and actual_deck is not None:
                deck = self.create_deck_from_shoe(actual_deck, known_cards)
            else:
                deck = self.create_fresh_deck(known_cards)

            if action == "HIT":
                outcome = self.simulate_hit(player_hand, dealer_upcard, deck, bet)
            elif action == "STAND":
                outcome = self.simulate_stand(player_hand, dealer_upcard, deck, bet)
            elif action == "DOUBLE":
                outcome = self.simulate_double(player_hand, dealer_upcard, deck, bet)
            elif action == "SPLIT":
                outcome = self.simulate_split(player_hand, dealer_upcard, deck, bet)
            else:
                outcome = 0

            total += outcome

            # Track wins, losses, pushes
            if outcome > 0:
                wins += 1
            elif outcome < 0:
                losses += 1
            else:
                pushes += 1

        return {
            'ev': total / self.num_simulations,
            'wins': wins,
            'losses': losses,
            'pushes': pushes
        }


class BlackjackMonteCarloGUI:
    """Blackjack game with Monte Carlo simulation for expected value"""

    def __init__(self, root):
        self.root = root
        self.root.title("Blackjack - Monte Carlo Simulator")
        self.root.geometry("1200x675")
        self.root.configure(bg='#0B6623')
        self.root.resizable(True, True)

        # Set custom icon
        self.set_window_icon()

        # Game state
        self.deck = Deck(num_decks=4)
        self.dealer_hand = Hand()
        self.player_hands = [Hand()]
        self.current_hand_index = 0
        self.chips = 1000
        self.current_bet = 0
        self.game_in_progress = False
        self.dealer_hidden = True
        self.stand_count = 0
        self.has_split = False

        # Card counting
        self.running_count = 0

        # Simulation settings
        self.num_simulations = 10000
        self.simulator = MonteCarloSimulator(self.num_simulations, use_depleting_shoe=False)
        self.show_ev = tk.BooleanVar(value=True)

        # Hand category filters
        self.filter_pairs = tk.BooleanVar(value=False)
        self.filter_ace = tk.BooleanVar(value=False)
        self.filter_soft = tk.BooleanVar(value=False)
        self.filter_hard = tk.BooleanVar(value=False)

        # Card filters (using "Any" to disable)
        self.dealer_upcard_value = tk.StringVar(value="Any")
        self.player_upcard_value = tk.StringVar(value="Any")
        self.player_second_card_value = tk.StringVar(value="Any")

        # Auto-simulator state
        self.auto_sim_running = False
        self.auto_sim_hands_to_play = 0
        self.auto_sim_hands_played = 0
        self.auto_sim_wins = 0
        self.auto_sim_losses = 0
        self.auto_sim_pushes = 0
        self.auto_sim_starting_chips = 0
        self.auto_sim_start_time = None
        self.auto_sim_timer_id = None

        # EV tracking: {(player_total, dealer_upcard, action): [outcomes]}
        self.auto_sim_ev_data = {}

        # Card image cache
        self.card_images = {}

        # EV calculation state
        self.ev_calculation_in_progress = False
        self.cancel_ev_calculation = False
        self.ev_calculation_thread = None

        self.setup_gui()

        # Initialize count display
        self.update_count_display()

    def set_window_icon(self):
        """Create and set custom window icon - save as .ico for best quality"""
        try:
            import os
            icon_path = "blackjack_icon.ico"

            # Only create if doesn't exist
            if not os.path.exists(icon_path):
                # Create multiple sizes for .ico (256, 128, 64, 48, 32, 16)
                sizes = [256, 128, 64, 48, 32, 16]
                icons = []

                for size in sizes:
                    img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
                    draw = ImageDraw.Draw(img)

                    # Green background (felt table color)
                    draw.rectangle([0, 0, size, size], fill='#0B6623')

                    # White card overlay - vertical rectangle
                    card_margin = size // 8
                    draw.rectangle([card_margin, card_margin, size-card_margin, size-card_margin],
                                  fill='white', outline='black', width=max(2, size//32))

                    # Load appropriate font size
                    font_size = size // 2
                    try:
                        font = ImageFont.truetype("arialbd.ttf", font_size)
                    except:
                        try:
                            font = ImageFont.truetype("arial.ttf", font_size)
                        except:
                            font = ImageFont.load_default()

                    # Draw "21" in center for blackjack
                    text = "21"
                    # Get text bounding box for centering
                    bbox = draw.textbbox((0, 0), text, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    x = (size - text_width) // 2
                    y = (size - text_height) // 2 - size // 16

                    draw.text((x, y), text, fill='#CC0000', font=font)

                    icons.append(img)

                # Save as .ico with multiple sizes
                icons[0].save(icon_path, format='ICO', sizes=[(s, s) for s in sizes])

            # Set the icon
            self.root.iconbitmap(icon_path)

        except Exception as e:
            # If icon creation fails, silently continue
            pass

    def create_card_image(self, card, hidden=False):
        """Create a card image using PIL"""
        width, height = 66, 99

        # Create card background
        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)

        if hidden:
            # Draw card back
            img = Image.new('RGB', (width, height), '#0000AA')
            draw = ImageDraw.Draw(img)
            draw.rectangle([3, 3, width-3, height-3], outline='white', width=2)
            draw.rectangle([6, 6, width-6, height-6], outline='white', width=1)
        else:
            # Draw card border
            draw.rectangle([0, 0, width-1, height-1], outline='black', width=2)

            # Set color based on suit
            color = 'red' if card.suit in ['♥', '♦'] else 'black'

            # Draw rank in top-left
            try:
                font = ImageFont.truetype("arial.ttf", 16)
                small_font = ImageFont.truetype("arial.ttf", 22)
            except:
                font = ImageFont.load_default()
                small_font = ImageFont.load_default()

            # Top left
            draw.text((5, 3), card.rank, fill=color, font=font)
            draw.text((5, 20), card.suit, fill=color, font=font)

            # Center
            draw.text((width//2 - 10, height//2 - 15), card.suit, fill=color, font=small_font)

            # Bottom right (upside down)
            draw.text((width - 18, height - 25), card.rank, fill=color, font=font)
            draw.text((width - 18, height - 42), card.suit, fill=color, font=font)

        return ImageTk.PhotoImage(img)

    def setup_gui(self):
        """Setup the GUI elements"""
        # Main container
        main_frame = tk.Frame(self.root, bg='#0B6623')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left side - Card Analysis
        left_stats_frame = tk.Frame(main_frame, bg='#1a4d2e', highlightbackground='gold', highlightthickness=2, width=300, height=635)
        left_stats_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_stats_frame.pack_propagate(False)

        # Center - Game
        game_frame = tk.Frame(main_frame, bg='#1a4d2e', highlightbackground='gold', highlightthickness=2)
        game_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        # Right side - Monte Carlo Stats
        stats_frame = tk.Frame(main_frame, bg='#1a4d2e', highlightbackground='gold', highlightcolor='gold', highlightthickness=2, width=450, height=635)
        stats_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        stats_frame.pack_propagate(False)

        # Title
        title_label = tk.Label(game_frame, text="BLACKJACK - Monte Carlo", font=('Arial', 22, 'bold'),
                               bg='#1a4d2e', fg='white')
        title_label.pack(pady=5)

        # Dealer section
        dealer_frame = tk.Frame(game_frame, bg='#1a4d2e')
        dealer_frame.pack(pady=2)

        tk.Label(dealer_frame, text="Dealer's Hand", font=('Arial', 14, 'bold'),
                bg='#1a4d2e', fg='white').pack()

        # Canvas for dealer cards
        self.dealer_canvas = tk.Canvas(dealer_frame, width=500, height=110,
                                       bg='#1a4d2e', highlightthickness=2, highlightbackground='gold')
        self.dealer_canvas.pack(pady=2)

        self.dealer_value_label = tk.Label(dealer_frame, text="Value: 0", font=('Arial', 12),
                                          bg='#1a4d2e', fg='white')
        self.dealer_value_label.pack()

        # Player section
        player_frame = tk.Frame(game_frame, bg='#1a4d2e')
        player_frame.pack(pady=2)

        tk.Label(player_frame, text="Your Hand", font=('Arial', 14, 'bold'),
                bg='#1a4d2e', fg='white').pack()

        # Canvas for player cards
        self.player_canvas = tk.Canvas(player_frame, width=500, height=165,
                                       bg='#1a4d2e', highlightthickness=2, highlightbackground='gold')
        self.player_canvas.pack(pady=2)

        self.player_value_label = tk.Label(player_frame, text="Value: 0", font=('Arial', 12),
                                          bg='#1a4d2e', fg='white')
        self.player_value_label.pack()

        # Status message - expandable area
        status_frame = tk.Frame(game_frame, bg='#1a4d2e')
        status_frame.pack(pady=5, fill=tk.BOTH, expand=True)

        # Current bet display
        self.current_bet_label = tk.Label(status_frame, text="Current Bet: $0",
                                         font=('Arial', 11, 'bold'), bg='#1a4d2e', fg='#FFD700')
        self.current_bet_label.pack(pady=2)

        self.status_label = tk.Label(status_frame, text="Place your bet to start!",
                                    font=('Arial', 12, 'bold'), bg='#1a4d2e', fg='yellow',
                                    wraplength=500, justify=tk.CENTER)
        self.status_label.pack(expand=True)

        # Game action buttons - at bottom
        buttons_frame = tk.Frame(game_frame, bg='#1a4d2e')
        buttons_frame.pack(side=tk.BOTTOM, pady=10)

        self.deal_button = tk.Button(buttons_frame, text="Deal", font=('Arial', 12, 'bold'),
                                     command=self.deal_cards, width=9, bg='green', fg='white')
        self.deal_button.pack(side=tk.LEFT, padx=4)

        self.hit_button = tk.Button(buttons_frame, text="Hit", font=('Arial', 12, 'bold'),
                                    command=self.hit, width=9, state=tk.DISABLED)
        self.hit_button.pack(side=tk.LEFT, padx=4)

        self.stand_button = tk.Button(buttons_frame, text="Stand", font=('Arial', 12, 'bold'),
                                      command=self.stand, width=9, state=tk.DISABLED)
        self.stand_button.pack(side=tk.LEFT, padx=4)

        self.double_button = tk.Button(buttons_frame, text="Double Down", font=('Arial', 12, 'bold'),
                                       command=self.double_down, width=11, state=tk.DISABLED)
        self.double_button.pack(side=tk.LEFT, padx=4)

        self.split_button = tk.Button(buttons_frame, text="Split", font=('Arial', 12, 'bold'),
                                      command=self.split, width=9, state=tk.DISABLED)
        self.split_button.pack(side=tk.LEFT, padx=4)

        # Monte Carlo Stats Panel
        tk.Label(stats_frame, text="Simulation & Betting", font=('Arial', 16, 'bold'),
                bg='#1a4d2e', fg='white').pack(pady=5)

        # Chips and betting section
        bet_section = tk.Frame(stats_frame, bg='#1a4d2e')
        bet_section.pack(pady=5, padx=10, fill=tk.X)

        self.chips_label = tk.Label(bet_section, text=f"Chips: ${self.chips}",
                                    font=('Arial', 12, 'bold'), bg='#1a4d2e', fg='gold')
        self.chips_label.pack(pady=3)

        # Bet amount - compact layout on one line
        bet_row = tk.Frame(bet_section, bg='#1a4d2e')
        bet_row.pack(pady=3, fill=tk.X)

        tk.Label(bet_row, text="Bet:", font=('Arial', 10, 'bold'),
                bg='#1a4d2e', fg='white').pack(side=tk.LEFT, padx=(0, 5))

        self.bet_entry = tk.Entry(bet_row, font=('Arial', 10), width=6, justify='center')
        self.bet_entry.insert(0, "10")
        self.bet_entry.pack(side=tk.LEFT, padx=(0, 5))

        # Betting buttons on same line
        bet_amounts = [10, 25, 50, 100]
        for i, amount in enumerate(bet_amounts):
            btn = tk.Button(bet_row, text=f"${amount}", font=('Arial', 8),
                          command=lambda a=amount: self.quick_bet(a), width=4,
                          borderwidth=1, padx=1, pady=2)
            btn.pack(side=tk.LEFT, padx=1)

        # Separator
        tk.Frame(stats_frame, bg='gold', height=2).pack(fill=tk.X, padx=10, pady=5)

        # Simulation settings - using grid for perfect alignment
        settings_frame = tk.Frame(stats_frame, bg='#1a4d2e')
        settings_frame.pack(pady=3, padx=10, fill=tk.X)

        row = 0

        # Simulations
        tk.Label(settings_frame, text="Simulations/Hand:", font=('Arial', 9, 'bold'),
                bg='#1a4d2e', fg='white', anchor='w').grid(row=row, column=0, sticky='w', padx=(0, 5), pady=2)

        sim_values = [0, 1000, 5000, 10000, 50000, 100000]
        self.sim_var = tk.IntVar(value=10000)
        sim_dropdown = ttk.Combobox(settings_frame, textvariable=self.sim_var,
                                   values=sim_values, state='readonly', width=10)
        sim_dropdown.grid(row=row, column=1, sticky='w', pady=2)
        sim_dropdown.bind('<<ComboboxSelected>>', self.update_simulations)
        row += 1

        # EV Deck Mode
        tk.Label(settings_frame, text="EV Calculation:", font=('Arial', 9, 'bold'),
                bg='#1a4d2e', fg='white', anchor='w').grid(row=row, column=0, sticky='w',
                                                            padx=(0, 5), pady=2)

        self.ev_deck_mode = tk.StringVar(value="Depleting Shoe")
        deck_mode_values = ["Fresh Deck", "Depleting Shoe"]
        deck_mode_dropdown = ttk.Combobox(settings_frame, textvariable=self.ev_deck_mode,
                                         values=deck_mode_values, state='readonly', width=10)
        deck_mode_dropdown.grid(row=row, column=1, sticky='w', pady=2)
        deck_mode_dropdown.bind('<<ComboboxSelected>>', self.update_deck_mode)
        row += 1

        # Hand category filters
        tk.Label(settings_frame, text="Hand Filters:", font=('Arial', 9, 'bold'),
                bg='#1a4d2e', fg='white', anchor='w').grid(row=row, column=0, columnspan=2, sticky='w', pady=(5, 2))
        row += 1

        hand_filter_row = tk.Frame(settings_frame, bg='#1a4d2e')
        hand_filter_row.grid(row=row, column=0, columnspan=2, sticky='w', pady=3)

        tk.Checkbutton(hand_filter_row, text="Pairs", variable=self.filter_pairs,
                      font=('Arial', 8), bg='#1a4d2e', fg='white',
                      selectcolor='#0B6623').pack(side=tk.LEFT, padx=2)

        tk.Checkbutton(hand_filter_row, text="Ace", variable=self.filter_ace,
                      font=('Arial', 8), bg='#1a4d2e', fg='white',
                      selectcolor='#0B6623').pack(side=tk.LEFT, padx=2)

        tk.Checkbutton(hand_filter_row, text="Soft", variable=self.filter_soft,
                      font=('Arial', 8), bg='#1a4d2e', fg='white',
                      selectcolor='#0B6623').pack(side=tk.LEFT, padx=2)

        tk.Checkbutton(hand_filter_row, text="Hard", variable=self.filter_hard,
                      font=('Arial', 8), bg='#1a4d2e', fg='white',
                      selectcolor='#0B6623').pack(side=tk.LEFT, padx=2)
        row += 1

        # Section headers and dropdowns
        tk.Label(settings_frame, text="Dealer Upcard:", font=('Arial', 9, 'bold'),
                bg='#1a4d2e', fg='white', anchor='w').grid(row=row, column=0, columnspan=2, sticky='w', pady=(5, 2))
        row += 1

        tk.Label(settings_frame, text="Dealer:", font=('Arial', 9, 'bold'),
                bg='#1a4d2e', fg='white', anchor='w').grid(row=row, column=0, sticky='w', padx=(0, 5), pady=2)

        dealer_upcard_values = ['Any', 'A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        dealer_dropdown = ttk.Combobox(settings_frame, textvariable=self.dealer_upcard_value,
                                      values=dealer_upcard_values, state='readonly', width=10)
        dealer_dropdown.grid(row=row, column=1, sticky='w', pady=2)
        row += 1

        # Player cards section
        tk.Label(settings_frame, text="Player Cards:", font=('Arial', 9, 'bold'),
                bg='#1a4d2e', fg='white', anchor='w').grid(row=row, column=0, columnspan=2, sticky='w', pady=(5, 2))
        row += 1

        tk.Label(settings_frame, text="1st:", font=('Arial', 9, 'bold'),
                bg='#1a4d2e', fg='white', anchor='w').grid(row=row, column=0, sticky='w', padx=(0, 5), pady=2)

        player_upcard_values = ['Any', 'A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        player_dropdown = ttk.Combobox(settings_frame, textvariable=self.player_upcard_value,
                                      values=player_upcard_values, state='readonly', width=10)
        player_dropdown.grid(row=row, column=1, sticky='w', pady=2)
        row += 1

        tk.Label(settings_frame, text="2nd:", font=('Arial', 9, 'bold'),
                bg='#1a4d2e', fg='white', anchor='w').grid(row=row, column=0, sticky='w', padx=(0, 5), pady=2)

        player_second_card_values = ['Any', 'A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        player_second_dropdown = ttk.Combobox(settings_frame, textvariable=self.player_second_card_value,
                                      values=player_second_card_values, state='readonly', width=10)
        player_second_dropdown.grid(row=row, column=1, sticky='w', pady=2)

        # Separator
        tk.Frame(stats_frame, bg='gold', height=2).pack(fill=tk.X, padx=10, pady=5)

        # Auto-Simulator section
        auto_sim_frame = tk.Frame(stats_frame, bg='#1a4d2e')
        auto_sim_frame.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)

        tk.Label(auto_sim_frame, text="Auto-Simulator", font=('Arial', 10, 'bold'),
                bg='#1a4d2e', fg='white').pack(pady=3)

        # View EV Results button at top
        self.view_ev_button = tk.Button(auto_sim_frame, text="View EV Results", font=('Arial', 9, 'bold'),
                                       command=self.show_ev_results, width=16, bg='#2196F3', fg='white',
                                       state=tk.DISABLED)
        self.view_ev_button.pack(pady=3)

        # Number of hands input
        hands_input_frame = tk.Frame(auto_sim_frame, bg='#1a4d2e')
        hands_input_frame.pack(pady=3)

        tk.Label(hands_input_frame, text="Hands:", font=('Arial', 9),
                bg='#1a4d2e', fg='white').pack(side=tk.LEFT, padx=(0, 5))

        self.auto_hands_entry = tk.Entry(hands_input_frame, font=('Arial', 9), width=8)
        self.auto_hands_entry.insert(0, "1000")
        self.auto_hands_entry.pack(side=tk.LEFT)

        # Exploration mode checkbox
        self.explore_all_actions = tk.BooleanVar(value=True)
        explore_frame = tk.Frame(auto_sim_frame, bg='#1a4d2e')
        explore_frame.pack(pady=3)

        tk.Checkbutton(explore_frame, text="Explore All Actions", variable=self.explore_all_actions,
                      font=('Arial', 8), bg='#1a4d2e', fg='white',
                      selectcolor='#0B6623').pack()

        tk.Label(explore_frame, text="(Slower but comprehensive EV data)", font=('Arial', 7),
                bg='#1a4d2e', fg='#888888').pack()

        # Control buttons
        btn_frame = tk.Frame(auto_sim_frame, bg='#1a4d2e')
        btn_frame.pack(pady=3)

        self.start_sim_button = tk.Button(btn_frame, text="Start", font=('Arial', 9, 'bold'),
                                         command=self.start_auto_sim, width=8, bg='#4CAF50', fg='white')
        self.start_sim_button.pack(side=tk.LEFT, padx=2)

        self.stop_sim_button = tk.Button(btn_frame, text="Stop", font=('Arial', 9, 'bold'),
                                        command=self.stop_auto_sim, width=8, bg='#F44336', fg='white',
                                        state=tk.DISABLED)
        self.stop_sim_button.pack(side=tk.LEFT, padx=2)

        # Statistics display
        stats_display_frame = tk.Frame(auto_sim_frame, bg='#1a4d2e')
        stats_display_frame.pack(pady=3, fill=tk.BOTH, expand=True)

        self.sim_progress_label = tk.Label(stats_display_frame, text="Ready",
                                          font=('Arial', 9, 'bold'), bg='#1a4d2e', fg='yellow')
        self.sim_progress_label.pack(pady=(2, 0))

        self.sim_stats_label = tk.Label(stats_display_frame, text="",
                                        font=('Arial', 8), bg='#1a4d2e', fg='white', justify=tk.LEFT,
                                        anchor='n', wraplength=410)
        self.sim_stats_label.pack(pady=0, fill=tk.X)

        self.sim_timer_label = tk.Label(stats_display_frame, text="",
                                        font=('Arial', 9), bg='#1a4d2e', fg='#00BFFF')
        self.sim_timer_label.pack(pady=(2, 0))

        # Left sidebar - Card Counting & Strategy
        tk.Label(left_stats_frame, text="Card Counting & Strategy", font=('Arial', 16, 'bold'),
                bg='#1a4d2e', fg='white').pack(pady=(5,3))

        # Deck Settings Frame
        deck_settings_frame = tk.Frame(left_stats_frame, bg='#1a4d2e')
        deck_settings_frame.pack(fill=tk.X, padx=10, pady=3)

        tk.Label(deck_settings_frame, text="Number of Decks:", font=('Arial', 9, 'bold'),
                bg='#1a4d2e', fg='white').grid(row=0, column=0, sticky='w', padx=5, pady=2)

        self.num_decks_var = tk.IntVar(value=4)
        deck_spinbox = tk.Spinbox(deck_settings_frame, from_=1, to=8, textvariable=self.num_decks_var,
                                 width=5, state='readonly', font=('Arial', 9))
        deck_spinbox.grid(row=0, column=1, sticky='w', padx=5, pady=2)

        apply_deck_btn = tk.Button(deck_settings_frame, text="Apply", command=self.apply_deck_count,
                                  font=('Arial', 8), bg='#0B6623', fg='white')
        apply_deck_btn.grid(row=0, column=2, sticky='w', padx=5, pady=2)

        # Separator
        tk.Frame(left_stats_frame, bg='gold', height=2).pack(fill=tk.X, padx=10, pady=5)

        # Card Count Display Frame
        count_display_frame = tk.Frame(left_stats_frame, bg='#1a4d2e')
        count_display_frame.pack(fill=tk.X, padx=10, pady=3)

        tk.Label(count_display_frame, text="Card Counting", font=('Arial', 10, 'bold'),
                bg='#1a4d2e', fg='gold').pack(pady=(2,0))

        self.cards_remaining_label = tk.Label(count_display_frame, text="Cards Remaining: 52 / 52",
                                             font=('Arial', 9), bg='#1a4d2e', fg='white')
        self.cards_remaining_label.pack(pady=1)

        # Running and True count on same line
        count_line_frame = tk.Frame(count_display_frame, bg='#1a4d2e')
        count_line_frame.pack(pady=1)

        self.running_count_label = tk.Label(count_line_frame, text="Running: 0",
                                           font=('Arial', 9), bg='#1a4d2e', fg='white')
        self.running_count_label.pack(side=tk.LEFT, padx=5)

        self.true_count_label = tk.Label(count_line_frame, text="True: 0.0",
                                        font=('Arial', 9), bg='#1a4d2e', fg='white')
        self.true_count_label.pack(side=tk.LEFT, padx=5)

        # Buttons frame for reshuffle and view cards
        buttons_frame = tk.Frame(count_display_frame, bg='#1a4d2e')
        buttons_frame.pack(pady=3)

        reshuffle_btn = tk.Button(buttons_frame, text="Reshuffle Shoe",
                                 command=self.manual_reshuffle,
                                 font=('Arial', 8), bg='#0B6623', fg='white')
        reshuffle_btn.pack(side=tk.LEFT, padx=2)

        view_cards_btn = tk.Button(buttons_frame, text="View Cards",
                                  command=self.show_remaining_cards,
                                  font=('Arial', 8), bg='#0B6623', fg='white')
        view_cards_btn.pack(side=tk.LEFT, padx=2)

        # Count adjustment controls
        count_adjust_frame = tk.Frame(count_display_frame, bg='#1a4d2e')
        count_adjust_frame.pack(pady=3)

        tk.Label(count_adjust_frame, text="Adjust True Count:",
                 font=('Arial', 9, 'bold'), bg='#1a4d2e', fg='gold').pack(pady=2)

        # Control row
        control_row = tk.Frame(count_adjust_frame, bg='#1a4d2e')
        control_row.pack(pady=2)

        # -1 button
        self.count_adjust_down_btn = tk.Button(control_row, text="-1",
                                                command=lambda: self.adjust_count_by_increment(-1),
                                                font=('Arial', 9, 'bold'), bg='#FF5722', fg='white',
                                                width=3, state=tk.DISABLED)
        self.count_adjust_down_btn.pack(side=tk.LEFT, padx=2)

        # Spinbox for custom increment (-10 to +10)
        self.count_adjust_var = tk.IntVar(value=1)
        count_spinbox = tk.Spinbox(control_row, from_=-10, to=10,
                                   textvariable=self.count_adjust_var,
                                   width=4, font=('Arial', 9), state='readonly')
        count_spinbox.pack(side=tk.LEFT, padx=2)

        # Apply button
        self.count_adjust_apply_btn = tk.Button(control_row, text="Apply",
                                                 command=lambda: self.adjust_count_by_increment(self.count_adjust_var.get()),
                                                 font=('Arial', 8), bg='#4CAF50', fg='white',
                                                 width=5, state=tk.DISABLED)
        self.count_adjust_apply_btn.pack(side=tk.LEFT, padx=2)

        # +1 button
        self.count_adjust_up_btn = tk.Button(control_row, text="+1",
                                              command=lambda: self.adjust_count_by_increment(1),
                                              font=('Arial', 9, 'bold'), bg='#4CAF50', fg='white',
                                              width=3, state=tk.DISABLED)
        self.count_adjust_up_btn.pack(side=tk.LEFT, padx=2)

        # Status label
        self.count_adjust_status_label = tk.Label(count_adjust_frame, text="(Depleting Shoe mode only)",
                                                  font=('Arial', 8, 'italic'), bg='#1a4d2e',
                                                  fg='#CCCCCC')
        self.count_adjust_status_label.pack(pady=1)

        # Separator
        tk.Frame(left_stats_frame, bg='gold', height=2).pack(fill=tk.X, padx=10, pady=5)

        # Card counting section
        card_count_frame = tk.Frame(left_stats_frame, bg='#1a4d2e')
        card_count_frame.pack(pady=3, padx=10, fill=tk.X)

        tk.Label(card_count_frame, text="Remaining Cards", font=('Arial', 11, 'bold'),
                bg='#1a4d2e', fg='white').pack(pady=(2,1))

        self.player_bust_label = tk.Label(card_count_frame, text="Player Bust: N/A",
                                          font=('Arial', 10, 'bold'), bg='#1a4d2e', fg='#FF5252', width=25, anchor='w')
        self.player_bust_label.pack(pady=1, padx=10, fill=tk.X)

        self.bust_ranks_label = tk.Label(card_count_frame, text="",
                                         font=('Arial', 9), bg='#1a4d2e', fg='#FF9999', justify=tk.LEFT,
                                         anchor='w', wraplength=200)
        self.bust_ranks_label.pack(pady=0, padx=15, fill=tk.X)

        self.player_safe_label = tk.Label(card_count_frame, text="Player Safe: N/A",
                                          font=('Arial', 10, 'bold'), bg='#1a4d2e', fg='#4CAF50', width=25, anchor='w')
        self.player_safe_label.pack(pady=1, padx=10, fill=tk.X)

        self.safe_ranks_label = tk.Label(card_count_frame, text="",
                                         font=('Arial', 9), bg='#1a4d2e', fg='#90EE90', justify=tk.LEFT,
                                         anchor='w', wraplength=200)
        self.safe_ranks_label.pack(pady=0, padx=15, fill=tk.X)

        # Separator
        tk.Frame(left_stats_frame, bg='gold', height=2).pack(fill=tk.X, padx=10, pady=5)

        # Expected Value Display
        ev_frame = tk.Frame(left_stats_frame, bg='#1a4d2e')
        ev_frame.pack(pady=3, padx=10, fill=tk.X)

        # EV header with Show EV checkbox
        ev_header_frame = tk.Frame(ev_frame, bg='#1a4d2e')
        ev_header_frame.pack(pady=(2,1), fill=tk.X)

        tk.Label(ev_header_frame, text="Expected Value ($)", font=('Arial', 13, 'bold'),
                bg='#1a4d2e', fg='white').pack(side=tk.LEFT, padx=(5, 10))

        # Add mode indicator label
        self.ev_mode_indicator = tk.Label(ev_header_frame, text="[Fresh]",
                                         font=('Arial', 8), bg='#1a4d2e', fg='#FFD700')
        self.ev_mode_indicator.pack(side=tk.LEFT, padx=5)

        # EV for each action
        self.ev_labels = {}
        actions = ['HIT', 'STAND', 'DOUBLE', 'SPLIT']
        colors = {'HIT': '#4CAF50', 'STAND': '#2196F3', 'DOUBLE': '#FF9800', 'SPLIT': '#9C27B0'}

        for action in actions:
            action_frame = tk.Frame(ev_frame, bg='#1a4d2e')
            action_frame.pack(fill=tk.X, pady=1, padx=5)

            tk.Label(action_frame, text=f"{action}:", font=('Arial', 10, 'bold'),
                    bg='#1a4d2e', fg=colors[action], width=7, anchor='w').pack(side=tk.LEFT)

            label = tk.Label(action_frame, text="N/A", font=('Arial', 9),
                           bg='#1a4d2e', fg='white', anchor='w')
            label.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.ev_labels[action] = label

        # Best action recommendation
        self.best_action_label = tk.Label(ev_frame, text="", font=('Arial', 12, 'bold'),
                                         bg='#1a4d2e', fg='yellow')
        self.best_action_label.pack()

        # Calculate EV button
        self.calc_ev_button = tk.Button(ev_frame, text="Calculate EV", font=('Arial', 11, 'bold'),
                                       command=self.calculate_all_ev, bg='#FF5722', fg='white',
                                       width=18, state=tk.DISABLED)
        self.calc_ev_button.pack(pady=5)

    def deal_hand_with_filters(self):
        """Deal a hand respecting the filter settings. Returns True if successful, False if failed."""
        max_attempts = 1000
        attempts = 0

        while attempts < max_attempts:
            # Reset hands
            self.dealer_hand = Hand()
            self.player_hands = [Hand()]

            # Deal player first card (with filter if enabled)
            if self.player_upcard_value.get() != "Any":
                # Find a card matching the specified rank
                target_rank = self.player_upcard_value.get()
                player_card = None
                for card in self.deck.cards:
                    if card.rank == target_rank:
                        player_card = card
                        self.deck.cards.remove(card)
                        break

                if player_card:
                    self.player_hands[0].add_card(player_card)
                else:
                    # No matching card found, reshuffle and try again
                    self.deck.shuffle()
                    attempts += 1
                    continue
            else:
                self.player_hands[0].add_card(self.deck.deal())

            # Deal dealer upcard (with filter if enabled)
            if self.dealer_upcard_value.get() != "Any":
                # Find a card matching the specified rank
                target_rank = self.dealer_upcard_value.get()
                dealer_card = None
                for card in self.deck.cards:
                    if card.rank == target_rank:
                        dealer_card = card
                        self.deck.cards.remove(card)
                        break

                if dealer_card:
                    self.dealer_hand.add_card(dealer_card)
                else:
                    # No matching card found, reshuffle and try again
                    self.deck.cards.extend(self.player_hands[0].cards)
                    self.deck.shuffle()
                    attempts += 1
                    continue
            else:
                self.dealer_hand.add_card(self.deck.deal())

            # Deal player second card (with filter if enabled)
            if self.player_second_card_value.get() != "Any":
                # Find a card matching the specified rank
                target_rank = self.player_second_card_value.get()
                player_card_2 = None
                for card in self.deck.cards:
                    if card.rank == target_rank:
                        player_card_2 = card
                        self.deck.cards.remove(card)
                        break

                if player_card_2:
                    self.player_hands[0].add_card(player_card_2)
                else:
                    # No matching card found, reshuffle and try again
                    self.deck.cards.extend(self.player_hands[0].cards)
                    self.deck.cards.extend(self.dealer_hand.cards)
                    self.deck.shuffle()
                    attempts += 1
                    continue
            else:
                self.player_hands[0].add_card(self.deck.deal())

            card = self.deck.deal()
            self.dealer_hand.add_card(card)

            # Check if hand matches filter
            if self.check_hand_category(self.player_hands[0]):
                # Hand matches! Track the count for visible cards only
                # Count player's 2 cards
                for player_card in self.player_hands[0].cards:
                    self.update_count(player_card)
                # Count only dealer's upcard (first card), NOT the hidden card
                self.update_count(self.dealer_hand.cards[0])
                self.update_count_display()
                return True

            # Return cards to deck and reshuffle
            self.deck.cards.extend(self.player_hands[0].cards)
            self.deck.cards.extend(self.dealer_hand.cards)
            self.deck.shuffle()

            attempts += 1

        return False

    def calculate_card_counts(self):
        """Calculate how many cards will bust vs help player"""
        if not self.game_in_progress:
            return

        current_hand = self.player_hands[self.current_hand_index]
        player_value = current_hand.value
        player_has_usable_ace = current_hand.aces > 0

        # Count remaining cards in deck by rank
        player_bust_count = 0
        player_safe_count = 0
        bust_ranks = {}  # rank -> count
        safe_ranks = {}  # rank -> count

        for card in self.deck.cards:
            # Player analysis - account for soft hands
            will_bust = False

            # Aces count as 1 (minimum value)
            if card.rank == 'A':
                # Even counting as 1, check if it busts
                if player_value + 1 > 21:
                    will_bust = True
                else:
                    will_bust = False
            else:
                new_value = player_value + card.value

                if new_value > 21:
                    # Check if we have a usable ace that can save us
                    if player_has_usable_ace:
                        # Ace can be counted as 1 instead of 11 (subtract 10)
                        adjusted_value = new_value - 10
                        if adjusted_value > 21:
                            will_bust = True
                    else:
                        will_bust = True

            if will_bust:
                player_bust_count += 1
                bust_ranks[card.rank] = bust_ranks.get(card.rank, 0) + 1
            else:
                player_safe_count += 1
                safe_ranks[card.rank] = safe_ranks.get(card.rank, 0) + 1

        total_cards = len(self.deck.cards)

        # Update summary labels
        self.player_bust_label.config(
            text=f"Player Bust: {player_bust_count}/{total_cards} ({player_bust_count/total_cards*100:.1f}%)")
        self.player_safe_label.config(
            text=f"Player Safe: {player_safe_count}/{total_cards} ({player_safe_count/total_cards*100:.1f}%)")

        # Build rank breakdown strings
        rank_order = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']

        bust_text = ""
        for rank in rank_order:
            if rank in bust_ranks:
                bust_text += f"{rank}: {bust_ranks[rank]}  "

        safe_text = ""
        for rank in rank_order:
            if rank in safe_ranks:
                safe_text += f"{rank}: {safe_ranks[rank]}  "

        self.bust_ranks_label.config(text=bust_text.strip() if bust_text else "None")
        self.safe_ranks_label.config(text=safe_text.strip() if safe_text else "None")

    def update_simulations(self, event=None):
        """Update number of simulations"""
        self.num_simulations = self.sim_var.get()
        self.simulator.num_simulations = self.num_simulations

        # Grey out EV section if 0 simulations
        if self.num_simulations == 0:
            # Disable and grey out EV labels
            for label in self.ev_labels.values():
                label.config(fg='#666666', text="Disabled")
            self.best_action_label.config(fg='#666666', text="EV Disabled (0 simulations)")
            self.calc_ev_button.config(state=tk.DISABLED)
        else:
            # Re-enable EV labels
            for label in self.ev_labels.values():
                label.config(fg='white', text="N/A")
            self.best_action_label.config(fg='yellow', text="")
            if self.game_in_progress:
                self.calc_ev_button.config(state=tk.NORMAL)

    def update_deck_mode(self, event=None):
        """Update EV calculation deck mode"""
        mode = self.ev_deck_mode.get()

        # Update simulator mode
        use_depleting = (mode == "Depleting Shoe")
        self.simulator.use_depleting_shoe = use_depleting

        # Clear current EV display to indicate recalculation needed
        for label in self.ev_labels.values():
            label.config(text="N/A")
        self.best_action_label.config(text="")

        # Update mode indicator if it exists
        if hasattr(self, 'ev_mode_indicator'):
            if use_depleting:
                self.ev_mode_indicator.config(text="[Shoe]", fg='#FF5722')
            else:
                self.ev_mode_indicator.config(text="[Fresh]", fg='#FFD700')

        # Update status message
        if use_depleting:
            self.status_label.config(text=f"EV mode: Depleting Shoe (uses {self.deck.num_decks}-deck shoe state)")
        else:
            self.status_label.config(text="EV mode: Fresh Deck (basic strategy)")

        # Enable/disable count adjustment controls
        if use_depleting and not self.game_in_progress:
            self.count_adjust_down_btn.config(state=tk.NORMAL)
            self.count_adjust_apply_btn.config(state=tk.NORMAL)
            self.count_adjust_up_btn.config(state=tk.NORMAL)
            self.count_adjust_status_label.config(text="Ready", fg='#4CAF50')
        else:
            self.count_adjust_down_btn.config(state=tk.DISABLED)
            self.count_adjust_apply_btn.config(state=tk.DISABLED)
            self.count_adjust_up_btn.config(state=tk.DISABLED)
            if not use_depleting:
                self.count_adjust_status_label.config(text="(Depleting Shoe mode only)", fg='#CCCCCC')
            else:
                self.count_adjust_status_label.config(text="(Not during game)", fg='#CCCCCC')

        # Auto-recalculate if game in progress
        if self.game_in_progress and self.show_ev.get() and self.num_simulations > 0:
            self.root.after(100, self.calculate_all_ev)

    def basic_strategy_decision(self, player_hand, dealer_upcard_value):
        """Make decision based on basic blackjack strategy"""
        player_value = player_hand.value
        has_usable_ace = player_hand.aces > 0
        can_split = player_hand.can_split()
        can_double = len(player_hand.cards) == 2

        # Pair splitting
        if can_split and self.chips >= self.current_bet:
            player_rank = player_hand.cards[0].rank
            if player_rank in ['A', '8']:
                return 'SPLIT'
            elif player_rank in ['2', '3', '7'] and dealer_upcard_value <= 7:
                return 'SPLIT'
            elif player_rank == '6' and dealer_upcard_value <= 6:
                return 'SPLIT'
            elif player_rank == '9' and dealer_upcard_value != 7 and dealer_upcard_value != 10 and dealer_upcard_value != 11:
                return 'SPLIT'

        # Soft totals (with usable ace)
        if has_usable_ace:
            if player_value >= 19:
                return 'STAND'
            elif player_value == 18:
                if dealer_upcard_value >= 9:
                    return 'HIT'
                elif dealer_upcard_value <= 6 and can_double and self.chips >= self.current_bet:
                    return 'DOUBLE'
                else:
                    return 'STAND'
            elif player_value >= 15 and player_value <= 17:
                if dealer_upcard_value <= 6 and can_double and self.chips >= self.current_bet:
                    return 'DOUBLE'
                else:
                    return 'HIT'
            else:
                return 'HIT'

        # Hard totals
        if player_value >= 17:
            return 'STAND'
        elif player_value >= 13:
            if dealer_upcard_value <= 6:
                return 'STAND'
            else:
                return 'HIT'
        elif player_value == 12:
            if 4 <= dealer_upcard_value <= 6:
                return 'STAND'
            else:
                return 'HIT'
        elif player_value == 11:
            if can_double and self.chips >= self.current_bet:
                return 'DOUBLE'
            else:
                return 'HIT'
        elif player_value == 10:
            if dealer_upcard_value <= 9 and can_double and self.chips >= self.current_bet:
                return 'DOUBLE'
            else:
                return 'HIT'
        elif player_value == 9:
            if 3 <= dealer_upcard_value <= 6 and can_double and self.chips >= self.current_bet:
                return 'DOUBLE'
            else:
                return 'HIT'
        else:
            return 'HIT'

    def start_auto_sim(self):
        """Start the auto-simulator"""
        try:
            hands_to_play = int(self.auto_hands_entry.get())
            if hands_to_play <= 0:
                messagebox.showerror("Invalid Input", "Number of hands must be greater than 0!")
                return
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number of hands!")
            return

        # Initialize simulator state
        self.auto_sim_running = True
        self.auto_sim_hands_to_play = hands_to_play
        self.auto_sim_hands_played = 0
        self.auto_sim_wins = 0
        self.auto_sim_losses = 0
        self.auto_sim_pushes = 0
        self.auto_sim_starting_chips = self.chips
        self.auto_sim_ev_data = {}  # Reset EV tracking
        self.auto_sim_start_time = datetime.now()

        # Update UI
        self.start_sim_button.config(state=tk.DISABLED)
        self.stop_sim_button.config(state=tk.NORMAL)
        self.deal_button.config(state=tk.DISABLED)

        # Start the timer display
        self.update_sim_timer()

        # Start the simulation loop
        self.play_auto_hand()

    def stop_auto_sim(self):
        """Stop the auto-simulator"""
        self.auto_sim_running = False
        self.start_sim_button.config(state=tk.NORMAL)
        self.stop_sim_button.config(state=tk.DISABLED)
        self.deal_button.config(state=tk.NORMAL)
        self.sim_progress_label.config(text="Stopped")

        # Stop the timer
        if self.auto_sim_timer_id:
            self.root.after_cancel(self.auto_sim_timer_id)
            self.auto_sim_timer_id = None

        # Display final elapsed time
        if self.auto_sim_start_time:
            elapsed = datetime.now() - self.auto_sim_start_time
            self.sim_timer_label.config(text=f"Time: {self.format_elapsed_time(elapsed)}")

    def update_sim_timer(self):
        """Update the timer display during auto-simulation"""
        if self.auto_sim_running and self.auto_sim_start_time:
            elapsed = datetime.now() - self.auto_sim_start_time
            self.sim_timer_label.config(text=f"Time: {self.format_elapsed_time(elapsed)}")
            # Schedule next update in 100ms for smooth display
            self.auto_sim_timer_id = self.root.after(100, self.update_sim_timer)

    def format_elapsed_time(self, elapsed):
        """Format timedelta as MM:SS.s or HH:MM:SS"""
        total_seconds = elapsed.total_seconds()
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = total_seconds % 60

        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:05.2f}"
        else:
            return f"{minutes}:{seconds:05.2f}"

    def play_auto_hand(self):
        """Play one hand automatically using basic strategy"""
        if not self.auto_sim_running or self.auto_sim_hands_played >= self.auto_sim_hands_to_play:
            # Simulation complete
            self.auto_sim_running = False
            self.start_sim_button.config(state=tk.NORMAL)
            self.stop_sim_button.config(state=tk.DISABLED)
            self.deal_button.config(state=tk.NORMAL)

            # Stop the timer
            if self.auto_sim_timer_id:
                self.root.after_cancel(self.auto_sim_timer_id)
                self.auto_sim_timer_id = None

            # Display final elapsed time
            if self.auto_sim_start_time:
                elapsed = datetime.now() - self.auto_sim_start_time
                self.sim_timer_label.config(text=f"Time: {self.format_elapsed_time(elapsed)}")

            chip_change = self.chips - self.auto_sim_starting_chips
            win_rate = (self.auto_sim_wins / self.auto_sim_hands_played * 100) if self.auto_sim_hands_played > 0 else 0

            self.sim_progress_label.config(text="Complete!")
            self.sim_stats_label.config(
                text=f"Final: {self.auto_sim_hands_played} hands | W: {self.auto_sim_wins} L: {self.auto_sim_losses} P: {self.auto_sim_pushes}\n"
                     f"Win Rate: {win_rate:.1f}% | Chips: {chip_change:+d}")

            # Enable View EV Results button if we have data
            if self.auto_sim_ev_data:
                self.view_ev_button.config(state=tk.NORMAL)

            return

        # Check if we have enough chips
        bet_amount = int(self.bet_entry.get()) if self.bet_entry.get() else 10
        if self.chips < bet_amount:
            messagebox.showwarning("Out of Chips", "Not enough chips to continue simulation!")
            self.stop_auto_sim()
            return

        # Update progress
        self.sim_progress_label.config(text=f"Playing: {self.auto_sim_hands_played + 1}/{self.auto_sim_hands_to_play}")

        # Deal a hand
        self.current_bet = bet_amount
        self.chips -= bet_amount
        self.current_bet_label.config(text=f"Current Bet: ${self.current_bet}")

        # Check if reshuffle needed
        # In Fresh Deck mode, reshuffle after every hand (simulate infinite deck)
        # In Depleting Shoe mode, only reshuffle when shoe is depleted
        if self.ev_deck_mode.get() == "Fresh Deck":
            self.reshuffle_shoe()
        elif self.deck.reshuffle_needed():
            self.reshuffle_shoe()

        # Reset game state (but NOT the deck!)
        self.dealer_hand = Hand()
        self.player_hands = [Hand()]
        self.current_hand_index = 0
        self.game_in_progress = True
        self.dealer_hidden = True
        self.has_split = False

        # Disable count adjustment buttons during game
        if hasattr(self, 'count_adjust_down_btn'):
            self.count_adjust_down_btn.config(state=tk.DISABLED)
            self.count_adjust_apply_btn.config(state=tk.DISABLED)
            self.count_adjust_up_btn.config(state=tk.DISABLED)
            self.count_adjust_status_label.config(text="(Not during game)", fg='#CCCCCC')

        # Deal cards with filter applied
        if not self.deal_hand_with_filters():
            # Could not deal matching hand, stop simulation
            messagebox.showwarning("Filter Too Restrictive",
                                 "Could not deal a hand matching the selected filters. Stopping simulation.")
            self.stop_auto_sim()
            self.chips += bet_amount
            return

        # Check for blackjacks
        if self.player_hands[0].is_blackjack():
            if self.dealer_hand.is_blackjack():
                # Push
                self.chips += self.current_bet
                self.auto_sim_pushes += 1
            else:
                # Player blackjack wins
                self.chips += self.current_bet + int(self.current_bet * 2.5)
                self.auto_sim_wins += 1
            self.auto_sim_hands_played += 1
            self.update_auto_stats()
            self.root.after(10, self.play_auto_hand)
            return
        elif self.dealer_hand.is_blackjack():
            # Dealer blackjack, player loses
            self.auto_sim_losses += 1
            self.auto_sim_hands_played += 1
            self.update_auto_stats()
            self.root.after(10, self.play_auto_hand)
            return

        # Initialize decision tracking for this hand
        self.current_decision_data = []

        # Play the hand using basic strategy
        self.auto_play_hand()

    def auto_play_hand(self):
        """Automatically play the current hand using basic strategy"""
        if self.current_hand_index >= len(self.player_hands):
            # All player hands complete, play dealer
            self.auto_dealer_turn()
            return

        current_hand = self.player_hands[self.current_hand_index]

        if current_hand.is_busted():
            self.current_hand_index += 1
            self.root.after(10, self.auto_play_hand)
            return

        # Check if this is a split ace hand (has 2 cards with first card being an ace)
        is_split_ace = (self.has_split and len(current_hand.cards) == 2 and
                       current_hand.cards[0].rank == 'A')

        # Split aces get one card only and automatically stand
        if is_split_ace:
            self.current_hand_index += 1
            self.root.after(10, self.auto_play_hand)
            return

        # Get basic strategy decision
        dealer_upcard_value = self.dealer_hand.cards[0].value
        # Normalize dealer upcard rank (J, Q, K -> 10)
        dealer_upcard_rank = self.dealer_hand.cards[0].rank
        if dealer_upcard_rank in ['J', 'Q', 'K']:
            dealer_upcard_rank = '10'
        player_total = current_hand.value
        decision = self.basic_strategy_decision(current_hand, dealer_upcard_value)

        # Run Monte Carlo simulations for all possible actions and store EV data
        # Only do this if "Explore All Actions" is enabled and for 2-card hands
        if self.explore_all_actions.get() and len(current_hand.cards) == 2 and self.num_simulations > 0:
            # Helper function to normalize card ranks (J, Q, K -> 10)
            def normalize_rank(rank):
                return '10' if rank in ['J', 'Q', 'K'] else rank

            # Identify hand type - pairs first, then soft, then hard
            # For pairs, all 10-value cards are treated as the same
            norm_rank1 = normalize_rank(current_hand.cards[0].rank)
            norm_rank2 = normalize_rank(current_hand.cards[1].rank)
            is_pair = (len(current_hand.cards) == 2 and norm_rank1 == norm_rank2)
            is_soft = current_hand.aces > 0

            if is_pair:
                hand_label = f"{norm_rank1}-{norm_rank2}"
            elif is_soft:
                hand_label = f"S{player_total}"
            else:
                hand_label = str(player_total)

            # Create dealer upcard hand for simulation
            dealer_upcard_hand = Hand()
            dealer_upcard_hand.add_card(self.dealer_hand.cards[0].copy())

            # Get all known cards (cards we can see)
            known_cards = []
            known_cards.extend(current_hand.cards)
            known_cards.append(self.dealer_hand.cards[0])

            # Try each possible action
            actions_to_try = ['HIT', 'STAND']

            # Can double on 2-card hands if we have enough chips
            if self.chips >= self.current_bet:
                actions_to_try.append('DOUBLE')

            # Can split if pair and have enough chips
            if (len(current_hand.cards) == 2 and
                current_hand.cards[0].rank == current_hand.cards[1].rank and
                self.chips >= self.current_bet):
                actions_to_try.append('SPLIT')

            # Run simulations for each action
            for action in actions_to_try:
                outcomes = []

                # Check if using depleting shoe mode
                use_depleting = (self.ev_deck_mode.get() == "Depleting Shoe")

                for _ in range(min(self.num_simulations, 1000)):  # Limit to 1000 per action for speed
                    # Create simulator
                    temp_simulator = MonteCarloSimulator(1)

                    # Get deck based on mode
                    if use_depleting:
                        sim_deck = temp_simulator.create_deck_from_shoe(self.deck, known_cards)
                    else:
                        sim_deck = temp_simulator.create_fresh_deck(known_cards)

                    # Simulate the action
                    if action == 'HIT':
                        outcome = temp_simulator.simulate_hit(current_hand.copy(), dealer_upcard_hand,
                                                             sim_deck, self.current_bet)
                    elif action == 'STAND':
                        outcome = temp_simulator.simulate_stand(current_hand.copy(), dealer_upcard_hand,
                                                               sim_deck, self.current_bet)
                    elif action == 'DOUBLE':
                        outcome = temp_simulator.simulate_double(current_hand.copy(), dealer_upcard_hand,
                                                                sim_deck, self.current_bet)
                    elif action == 'SPLIT':
                        outcome = temp_simulator.simulate_split(current_hand.copy(), dealer_upcard_hand,
                                                               sim_deck, self.current_bet)

                    outcomes.append(outcome)

                # Store in EV data
                key = (hand_label, dealer_upcard_rank, action)
                if key not in self.auto_sim_ev_data:
                    self.auto_sim_ev_data[key] = []
                self.auto_sim_ev_data[key].extend(outcomes)
        else:
            # If not exploring all actions, just track the decision for later outcome recording
            if len(current_hand.cards) == 2:
                if not hasattr(self, 'current_decision_data'):
                    self.current_decision_data = []

                # Helper function to normalize card ranks (J, Q, K -> 10)
                def normalize_rank(rank):
                    return '10' if rank in ['J', 'Q', 'K'] else rank

                # Identify hand type - pairs first, then soft, then hard
                # For pairs, all 10-value cards are treated as the same
                norm_rank1 = normalize_rank(current_hand.cards[0].rank)
                norm_rank2 = normalize_rank(current_hand.cards[1].rank)
                is_pair = (len(current_hand.cards) == 2 and norm_rank1 == norm_rank2)
                is_soft = current_hand.aces > 0

                if is_pair:
                    hand_label = f"{norm_rank1}-{norm_rank2}"
                elif is_soft:
                    hand_label = f"S{player_total}"
                else:
                    hand_label = str(player_total)

                self.current_decision_data.append({
                    'player_hand': hand_label,
                    'dealer_upcard': dealer_upcard_rank,
                    'action': decision,
                    'hand_index': self.current_hand_index
                })

        if decision == 'STAND':
            self.current_hand_index += 1
            self.root.after(10, self.auto_play_hand)
        elif decision == 'HIT':
            card = self.deck.deal()
            self.update_count(card)
            current_hand.add_card(card)
            self.root.after(10, self.auto_play_hand)
        elif decision == 'DOUBLE':
            if self.chips >= self.current_bet:
                self.chips -= self.current_bet
                self.current_bet *= 2
                self.current_bet_label.config(text=f"Current Bet: ${self.current_bet}")
            card = self.deck.deal()
            self.update_count(card)
            current_hand.add_card(card)
            self.current_hand_index += 1
            self.root.after(10, self.auto_play_hand)
        elif decision == 'SPLIT':
            if self.chips >= self.current_bet:
                self.chips -= self.current_bet
                self.has_split = True

                original_hand = self.player_hands[self.current_hand_index]
                new_hand = Hand()

                second_card = original_hand.cards.pop()

                # Recalculate original hand value from remaining cards
                original_hand.value = 0
                original_hand.aces = 0
                for card in original_hand.cards:
                    original_hand.value += card.value
                    if card.rank == 'A':
                        original_hand.aces += 1
                original_hand.adjust_for_ace()

                new_hand.add_card(second_card)

                card1 = self.deck.deal()
                self.update_count(card1)
                original_hand.add_card(card1)

                card2 = self.deck.deal()
                self.update_count(card2)
                new_hand.add_card(card2)

                self.player_hands.insert(self.current_hand_index + 1, new_hand)

            self.root.after(10, self.auto_play_hand)

    def auto_dealer_turn(self):
        """Automatically play dealer's turn"""
        self.dealer_hidden = False

        # Count the dealer's hidden card now that it's revealed
        if len(self.dealer_hand.cards) >= 2:
            self.update_count(self.dealer_hand.cards[1])

        # Check if all player hands busted
        all_busted = all(hand.is_busted() for hand in self.player_hands)

        if not all_busted:
            # Dealer plays
            while self.dealer_hand.value < 17:
                card = self.deck.deal()
                self.update_count(card)
                self.dealer_hand.add_card(card)

        # Determine outcome
        dealer_value = self.dealer_hand.value
        dealer_busted = self.dealer_hand.is_busted()

        won_hands = 0
        lost_hands = 0
        push_hands = 0
        hand_outcomes = []  # Track outcome for each hand

        for i, hand in enumerate(self.player_hands):
            if hand.is_busted():
                lost_hands += 1
                hand_outcomes.append(-self.current_bet)
            elif dealer_busted:
                won_hands += 1
                self.chips += self.current_bet * 2
                hand_outcomes.append(self.current_bet)
            elif hand.value > dealer_value:
                won_hands += 1
                self.chips += self.current_bet * 2
                hand_outcomes.append(self.current_bet)
            elif hand.value < dealer_value:
                lost_hands += 1
                hand_outcomes.append(-self.current_bet)
            else:
                push_hands += 1
                self.chips += self.current_bet
                hand_outcomes.append(0)

        # Track EV data for each decision
        if hasattr(self, 'current_decision_data'):
            for decision_info in self.current_decision_data:
                hand_idx = decision_info['hand_index']
                if hand_idx < len(hand_outcomes):
                    # Normalize dealer upcard (10/J/Q/K all become '10')
                    dealer_upcard = decision_info['dealer_upcard']
                    if dealer_upcard in ['J', 'Q', 'K']:
                        dealer_upcard = '10'

                    key = (decision_info['player_hand'], dealer_upcard, decision_info['action'])
                    if key not in self.auto_sim_ev_data:
                        self.auto_sim_ev_data[key] = []
                    self.auto_sim_ev_data[key].append(hand_outcomes[hand_idx])

        # Update stats - count each hand separately (important for splits)
        self.auto_sim_wins += won_hands
        self.auto_sim_losses += lost_hands
        self.auto_sim_pushes += push_hands

        self.auto_sim_hands_played += 1  # Count number of deals (not individual split hands)
        self.update_auto_stats()
        self.game_in_progress = False

        # Continue to next hand
        self.root.after(10, self.play_auto_hand)

    def update_auto_stats(self):
        """Update auto-simulator statistics display"""
        if self.auto_sim_hands_played > 0:
            win_rate = (self.auto_sim_wins / self.auto_sim_hands_played * 100)
            chip_change = self.chips - self.auto_sim_starting_chips

            self.sim_stats_label.config(
                text=f"W: {self.auto_sim_wins} L: {self.auto_sim_losses} P: {self.auto_sim_pushes}\n"
                     f"Win Rate: {win_rate:.1f}% | Chips: {chip_change:+d}")

    def show_ev_results(self):
        """Display EV results in a new window"""
        if not self.auto_sim_ev_data:
            messagebox.showinfo("No Data", "No EV data available. Run a simulation first.")
            return

        # Create new window
        results_window = tk.Toplevel(self.root)
        results_window.title("Auto-Simulator EV Results")
        results_window.geometry("930x750")
        results_window.configure(bg='#0B6623')

        # Title
        tk.Label(results_window, text="Expected Value Analysis", font=('Arial', 18, 'bold'),
                bg='#0B6623', fg='white').pack(pady=10)

        # Filter and Summary section
        filter_summary_frame = tk.Frame(results_window, bg='#1a4d2e', highlightbackground='gold', highlightthickness=2)
        filter_summary_frame.pack(pady=5, padx=10, fill=tk.X)

        # Filter row
        filter_row = tk.Frame(filter_summary_frame, bg='#1a4d2e', highlightthickness=0)
        filter_row.pack(pady=5, padx=10)

        tk.Label(filter_row, text="Filter by Dealer Card:", font=('Arial', 11, 'bold'),
                bg='#1a4d2e', fg='white').pack(side=tk.LEFT, padx=(0, 10))

        dealer_filter_var = tk.StringVar(value="All")
        dealer_filter_values = ['All', 'A', '2', '3', '4', '5', '6', '7', '8', '9', '10']
        dealer_filter_dropdown = ttk.Combobox(filter_row, textvariable=dealer_filter_var,
                                             values=dealer_filter_values, state='readonly', width=10)
        dealer_filter_dropdown.pack(side=tk.LEFT)

        # Summary stats
        total_decisions = len(self.auto_sim_ev_data)
        summary_label = tk.Label(filter_summary_frame, text=f"Total Unique Situations: {total_decisions}",
                                font=('Arial', 11, 'bold'), bg='#1a4d2e', fg='white')
        summary_label.pack(pady=5)

        # Create frame with scrollbar
        main_frame = tk.Frame(results_window, bg='#0B6623', highlightthickness=0)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Add canvas for scrolling
        canvas = tk.Canvas(main_frame, bg='#0B6623', highlightthickness=0)
        scrollbar = tk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#0B6623', highlightthickness=0)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)

        # Function to refresh the display based on filter
        def refresh_display(*args):
            # Clear existing content
            for widget in scrollable_frame.winfo_children():
                widget.destroy()

            # Process and sort data by dealer upcard then player hand
            sorted_data = {}
            for (player_hand, dealer_upcard, action), outcomes in self.auto_sim_ev_data.items():
                if dealer_upcard not in sorted_data:
                    sorted_data[dealer_upcard] = {}
                if player_hand not in sorted_data[dealer_upcard]:
                    sorted_data[dealer_upcard][player_hand] = {}

                avg_ev = sum(outcomes) / len(outcomes)
                wins = sum(1 for x in outcomes if x > 0)
                losses = sum(1 for x in outcomes if x < 0)
                pushes = sum(1 for x in outcomes if x == 0)

                sorted_data[dealer_upcard][player_hand][action] = {
                    'ev': avg_ev,
                    'count': len(outcomes),
                    'wins': wins,
                    'losses': losses,
                    'pushes': pushes
                }

            # Get selected filter
            selected_dealer = dealer_filter_var.get()

            # Display results grouped by dealer upcard
            dealer_order = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10']

            for dealer_upcard in dealer_order:
                # Skip if not in data or filtered out
                if dealer_upcard not in sorted_data:
                    continue
                if selected_dealer != "All" and dealer_upcard != selected_dealer:
                    continue

                # Dealer upcard section
                dealer_frame = tk.Frame(scrollable_frame, bg='#1a4d2e', highlightbackground='gold', highlightthickness=2)
                dealer_frame.pack(fill=tk.X, pady=8, padx=5)

                # Dealer header
                tk.Label(dealer_frame, text=f"━━━ Dealer Shows: {dealer_upcard} ━━━", font=('Arial', 15, 'bold'),
                        bg='#1a4d2e', fg='#FFD700').pack(pady=8)

                # Table header
                header_frame = tk.Frame(dealer_frame, bg='#0B6623', highlightthickness=0)
                header_frame.pack(fill=tk.X, padx=10, pady=(0, 5))

                tk.Label(header_frame, text="Hand", font=('Arial', 10, 'bold'),
                        bg='#0B6623', fg='white', width=8, anchor='w').grid(row=0, column=0, padx=2)
                tk.Label(header_frame, text="Hit EV", font=('Arial', 10, 'bold'),
                        bg='#0B6623', fg='#4CAF50', width=20, anchor='w').grid(row=0, column=1, padx=2)
                tk.Label(header_frame, text="Stand EV", font=('Arial', 10, 'bold'),
                        bg='#0B6623', fg='#2196F3', width=20, anchor='w').grid(row=0, column=2, padx=2)
                tk.Label(header_frame, text="Double EV", font=('Arial', 10, 'bold'),
                        bg='#0B6623', fg='#FF9800', width=20, anchor='w').grid(row=0, column=3, padx=2)
                tk.Label(header_frame, text="Split EV", font=('Arial', 10, 'bold'),
                        bg='#0B6623', fg='#E91E63', width=20, anchor='w').grid(row=0, column=4, padx=2)
                tk.Label(header_frame, text="Best", font=('Arial', 10, 'bold'),
                        bg='#0B6623', fg='yellow', width=8, anchor='w').grid(row=0, column=5, padx=2)

                # Sort player hands: pairs first, then hard hands, then soft hands
                def hand_sort_key(hand_str):
                    if '-' in hand_str:
                        # Pair - sort by card rank
                        rank = hand_str.split('-')[0]
                        # Convert rank to numeric value for sorting
                        rank_order = {'A': 14, 'K': 13, 'Q': 12, 'J': 11, '10': 10, '9': 9, '8': 8, '7': 7, '6': 6, '5': 5, '4': 4, '3': 3, '2': 2}
                        return (0, rank_order.get(rank, 0))
                    elif hand_str.startswith('S'):
                        # Soft hand - sort by numeric part
                        return (2, int(hand_str[1:]))
                    else:
                        # Hard hand - sort numerically
                        return (1, int(hand_str))

                player_hands = sorted(sorted_data[dealer_upcard].keys(), key=hand_sort_key)

                # Display each hand
                for player_hand in player_hands:
                    actions_data = sorted_data[dealer_upcard][player_hand]

                    # Create row
                    row_frame = tk.Frame(dealer_frame, bg='#1a4d2e', highlightthickness=0)
                    row_frame.pack(fill=tk.X, padx=10, pady=2)

                    # Player hand label
                    tk.Label(row_frame, text=player_hand, font=('Arial', 11, 'bold'),
                            bg='#1a4d2e', fg='white', width=8, anchor='w').grid(row=0, column=0, padx=2, sticky='w')

                    # Action columns
                    action_colors = {'HIT': '#4CAF50', 'STAND': '#2196F3', 'DOUBLE': '#FF9800', 'SPLIT': '#E91E63'}
                    evs = {}

                    for idx, action in enumerate(['HIT', 'STAND', 'DOUBLE', 'SPLIT'], start=1):
                        if action in actions_data:
                            ev = actions_data[action]['ev']
                            wins = actions_data[action]['wins']
                            losses = actions_data[action]['losses']
                            pushes = actions_data[action]['pushes']
                            evs[action] = ev

                            text = f"${ev:+.2f} ({wins}W-{losses}L-{pushes}P)"
                            tk.Label(row_frame, text=text, font=('Arial', 10),
                                    bg='#1a4d2e', fg=action_colors[action], width=20, anchor='w').grid(row=0, column=idx, padx=2, sticky='w')
                        else:
                            tk.Label(row_frame, text="—", font=('Arial', 10),
                                    bg='#1a4d2e', fg='#666666', width=20, anchor='w').grid(row=0, column=idx, padx=2, sticky='w')

                    # Best action
                    if evs:
                        best_action = max(evs, key=evs.get)
                        tk.Label(row_frame, text=best_action, font=('Arial', 11, 'bold'),
                                bg='#1a4d2e', fg='yellow', width=8, anchor='w').grid(row=0, column=5, padx=2, sticky='w')

        # Bind filter change to refresh function
        dealer_filter_dropdown.bind('<<ComboboxSelected>>', refresh_display)

        # Initial display
        refresh_display()

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Button frame
        button_frame = tk.Frame(results_window, bg='#0B6623', highlightthickness=0)
        button_frame.pack(pady=10)

        # Export button
        tk.Button(button_frame, text="Export to CSV", font=('Arial', 12, 'bold'),
                 command=self.export_ev_results, width=15, bg='#4CAF50', fg='white').pack(side=tk.LEFT, padx=5)

        # Close button
        tk.Button(button_frame, text="Close", font=('Arial', 12, 'bold'),
                 command=results_window.destroy, width=15, bg='#F44336', fg='white').pack(side=tk.LEFT, padx=5)

    def export_ev_results(self):
        """Export EV results to CSV file"""
        if not self.auto_sim_ev_data:
            messagebox.showinfo("No Data", "No EV data available to export.")
            return

        # Ask user where to save the file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"blackjack_ev_results_{timestamp}.csv"

        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=default_filename
        )

        if not filepath:
            return  # User cancelled

        try:
            with open(filepath, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)

                # Write header
                writer.writerow(['Player Hand', 'Dealer Upcard', 'Action', 'Average EV',
                               'Wins', 'Losses', 'Pushes', 'Total Simulations'])

                # Sort data by dealer upcard then player hand
                sorted_data = {}
                for (player_hand, dealer_upcard, action), outcomes in self.auto_sim_ev_data.items():
                    if dealer_upcard not in sorted_data:
                        sorted_data[dealer_upcard] = {}
                    if player_hand not in sorted_data[dealer_upcard]:
                        sorted_data[dealer_upcard][player_hand] = {}

                    avg_ev = sum(outcomes) / len(outcomes)
                    wins = sum(1 for x in outcomes if x > 0)
                    losses = sum(1 for x in outcomes if x < 0)
                    pushes = sum(1 for x in outcomes if x == 0)

                    sorted_data[dealer_upcard][player_hand][action] = {
                        'ev': avg_ev,
                        'wins': wins,
                        'losses': losses,
                        'pushes': pushes,
                        'total': len(outcomes)
                    }

                # Write data
                dealer_order = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10']

                for dealer_upcard in dealer_order:
                    if dealer_upcard not in sorted_data:
                        continue

                    # Sort player hands
                    def hand_sort_key(hand_str):
                        if '-' in hand_str:
                            rank = hand_str.split('-')[0]
                            rank_order = {'A': 14, 'K': 13, 'Q': 12, 'J': 11, '10': 10, '9': 9, '8': 8, '7': 7, '6': 6, '5': 5, '4': 4, '3': 3, '2': 2}
                            return (0, rank_order.get(rank, 0))
                        elif hand_str.startswith('S'):
                            return (2, int(hand_str[1:]))
                        else:
                            return (1, int(hand_str))

                    player_hands = sorted(sorted_data[dealer_upcard].keys(), key=hand_sort_key)

                    for player_hand in player_hands:
                        for action in ['HIT', 'STAND', 'DOUBLE', 'SPLIT']:
                            if action in sorted_data[dealer_upcard][player_hand]:
                                data = sorted_data[dealer_upcard][player_hand][action]
                                writer.writerow([
                                    player_hand,
                                    dealer_upcard,
                                    action,
                                    f"{data['ev']:.2f}",
                                    data['wins'],
                                    data['losses'],
                                    data['pushes'],
                                    data['total']
                                ])

            messagebox.showinfo("Export Successful", f"EV results exported to:\n{filepath}")

        except Exception as e:
            messagebox.showerror("Export Failed", f"Failed to export data:\n{str(e)}")

    def quick_bet(self, amount):
        """Quick bet button handler"""
        if not self.game_in_progress:
            self.bet_entry.delete(0, tk.END)
            self.bet_entry.insert(0, str(amount))

    def check_hand_category(self, hand):
        """Check if hand matches selected filters"""
        # If no filters selected, allow all hands
        if not any([self.filter_pairs.get(), self.filter_ace.get(),
                   self.filter_soft.get(), self.filter_hard.get()]):
            return True

        matches = True

        # Check pair filter
        if self.filter_pairs.get():
            if not (len(hand.cards) == 2 and hand.cards[0].rank == hand.cards[1].rank):
                matches = False

        # Check ace filter
        if self.filter_ace.get():
            has_ace = any(card.rank == 'A' for card in hand.cards)
            if not has_ace:
                matches = False

        # Check soft hand filter (has ace counted as 11)
        if self.filter_soft.get():
            if hand.aces == 0:  # No usable ace
                matches = False

        # Check hard hand filter (no ace or ace counted as 1)
        if self.filter_hard.get():
            if hand.aces > 0:  # Has usable ace
                matches = False

        return matches

    def cancel_ev_calculation_if_running(self):
        """Cancel any ongoing EV calculation"""
        if self.ev_calculation_in_progress:
            self.cancel_ev_calculation = True
            # Wait briefly for thread to finish
            if self.ev_calculation_thread and self.ev_calculation_thread.is_alive():
                self.ev_calculation_thread.join(timeout=0.1)

    def calculate_all_ev(self):
        """Calculate expected value for all possible actions asynchronously"""
        if not self.game_in_progress or not self.show_ev.get():
            return

        # Don't calculate if simulations set to 0
        if self.num_simulations == 0:
            return

        # Safety check for valid hand index
        if self.current_hand_index >= len(self.player_hands):
            return

        # Safety check for dealer hand
        if not self.dealer_hand or len(self.dealer_hand.cards) == 0:
            return

        # Cancel any ongoing calculation
        self.cancel_ev_calculation_if_running()

        # Mark as in progress
        self.ev_calculation_in_progress = True
        self.cancel_ev_calculation = False

        self.calc_ev_button.config(state=tk.DISABLED, text="Calculating...")

        current_hand = self.player_hands[self.current_hand_index]

        # Create a dealer hand with only visible card
        visible_dealer_hand = Hand()
        visible_dealer_hand.add_card(self.dealer_hand.cards[0].copy())

        # Gather all known cards (player's cards + dealer's visible card)
        known_cards = []
        for hand in self.player_hands:
            known_cards.extend(hand.cards)
        known_cards.append(self.dealer_hand.cards[0])

        # Determine which actions are possible
        can_double = self.chips >= self.current_bet and len(current_hand.cards) == 2
        can_split = current_hand.can_split() and self.chips >= self.current_bet

        # Run calculation in background thread
        def calculate_in_thread():
            results = {}

            # Calculate EV for Hit
            result_hit = self.simulator.calculate_expected_value(
                "HIT", current_hand, visible_dealer_hand, known_cards, self.current_bet,
                cancel_flag=lambda: self.cancel_ev_calculation,
                actual_deck=self.deck)
            if result_hit is not None:
                results['HIT'] = result_hit

            # Calculate EV for Stand
            if not self.cancel_ev_calculation:
                result_stand = self.simulator.calculate_expected_value(
                    "STAND", current_hand, visible_dealer_hand, known_cards, self.current_bet,
                    cancel_flag=lambda: self.cancel_ev_calculation,
                    actual_deck=self.deck)
                if result_stand is not None:
                    results['STAND'] = result_stand

            # Calculate EV for Double Down if possible
            if can_double and not self.cancel_ev_calculation:
                result_double = self.simulator.calculate_expected_value(
                    "DOUBLE", current_hand, visible_dealer_hand, known_cards, self.current_bet,
                    cancel_flag=lambda: self.cancel_ev_calculation,
                    actual_deck=self.deck)
                if result_double is not None:
                    results['DOUBLE'] = result_double

            # Calculate EV for Split if possible
            if can_split and not self.cancel_ev_calculation:
                result_split = self.simulator.calculate_expected_value(
                    "SPLIT", current_hand, visible_dealer_hand, known_cards, self.current_bet,
                    cancel_flag=lambda: self.cancel_ev_calculation,
                    actual_deck=self.deck)
                if result_split is not None:
                    results['SPLIT'] = result_split

            # Update UI in main thread
            self.root.after(0, lambda: self.update_ev_display(results, can_double, can_split))

        # Start thread
        self.ev_calculation_thread = threading.Thread(target=calculate_in_thread, daemon=True)
        self.ev_calculation_thread.start()

    def update_ev_display(self, results, can_double, can_split):
        """Update EV display with calculation results (runs in main thread)"""
        # Check if calculation was cancelled
        if self.cancel_ev_calculation:
            self.calc_ev_button.config(state=tk.NORMAL, text="Calculate EV")
            self.ev_calculation_in_progress = False
            return

        ev_results = {}

        # Update Hit
        if 'HIT' in results:
            result = results['HIT']
            ev_results['HIT'] = result['ev']
            self.ev_labels['HIT'].config(
                text=f"${result['ev']:+.2f} ({result['wins']}W-{result['losses']}L-{result['pushes']}P)")

        # Update Stand
        if 'STAND' in results:
            result = results['STAND']
            ev_results['STAND'] = result['ev']
            self.ev_labels['STAND'].config(
                text=f"${result['ev']:+.2f} ({result['wins']}W-{result['losses']}L-{result['pushes']}P)")

        # Update Double
        if can_double:
            if 'DOUBLE' in results:
                result = results['DOUBLE']
                ev_results['DOUBLE'] = result['ev']
                self.ev_labels['DOUBLE'].config(
                    text=f"${result['ev']:+.2f} ({result['wins']}W-{result['losses']}L-{result['pushes']}P)")
        else:
            self.ev_labels['DOUBLE'].config(text="N/A")

        # Update Split
        if can_split:
            if 'SPLIT' in results:
                result = results['SPLIT']
                ev_results['SPLIT'] = result['ev']
                self.ev_labels['SPLIT'].config(
                    text=f"${result['ev']:+.2f} ({result['wins']}W-{result['losses']}L-{result['pushes']}P)")
        else:
            self.ev_labels['SPLIT'].config(text="N/A")

        # Find best action
        valid_actions = {k: v for k, v in ev_results.items() if k in self.ev_labels and self.ev_labels[k].cget('text') != "N/A"}
        if valid_actions:
            best_action = max(valid_actions, key=valid_actions.get)
            best_ev = valid_actions[best_action]
            self.best_action_label.config(
                text=f"Best Action: {best_action} (EV: ${best_ev:.2f})")

        self.calc_ev_button.config(state=tk.NORMAL, text="Calculate EV")
        self.ev_calculation_in_progress = False

        # Update card counts
        self.calculate_card_counts()

    def deal_cards(self):
        """Deal initial cards to player and dealer"""
        try:
            bet = int(self.bet_entry.get())
            if bet <= 0:
                messagebox.showerror("Invalid Bet", "Bet must be greater than 0!")
                return
            if bet > self.chips:
                messagebox.showerror("Insufficient Chips", f"You only have ${self.chips}!")
                return
        except ValueError:
            messagebox.showerror("Invalid Bet", "Please enter a valid bet amount!")
            return

        self.current_bet = bet
        self.chips -= bet
        self.current_bet_label.config(text=f"Current Bet: ${self.current_bet}")

        # Check if reshuffle needed
        if self.deck.reshuffle_needed():
            self.reshuffle_shoe()

        # Reset game state (but NOT the deck!)
        self.dealer_hand = Hand()
        self.player_hands = [Hand()]
        self.current_hand_index = 0
        self.game_in_progress = True
        self.dealer_hidden = True
        self.stand_count = 0
        self.has_split = False

        # Disable count adjustment buttons during game
        if hasattr(self, 'count_adjust_down_btn'):
            self.count_adjust_down_btn.config(state=tk.DISABLED)
            self.count_adjust_apply_btn.config(state=tk.DISABLED)
            self.count_adjust_up_btn.config(state=tk.DISABLED)
            self.count_adjust_status_label.config(text="(Not during game)", fg='#CCCCCC')

        # Reset EV labels
        for label in self.ev_labels.values():
            label.config(text="N/A")
        self.best_action_label.config(text="")

        # Deal cards with filter applied
        if not self.deal_hand_with_filters():
            messagebox.showwarning("Filter Too Restrictive",
                                 "Could not deal a hand matching the selected filters after 1000 attempts. Try different filters.")
            self.chips += bet
            self.game_in_progress = False

            # Re-enable count adjustment buttons if in Depleting Shoe mode
            if self.ev_deck_mode.get() == "Depleting Shoe":
                if hasattr(self, 'count_adjust_down_btn'):
                    self.count_adjust_down_btn.config(state=tk.NORMAL)
                    self.count_adjust_apply_btn.config(state=tk.NORMAL)
                    self.count_adjust_up_btn.config(state=tk.NORMAL)
                    self.count_adjust_status_label.config(text="Ready", fg='#4CAF50')
            return

        self.update_display()

        # Check for blackjack
        if self.player_hands[0].is_blackjack() and self.dealer_hand.is_blackjack():
            self.dealer_hidden = False
            self.update_display()
            self.end_game("Both Blackjack! Push!", 0)
        elif self.player_hands[0].is_blackjack():
            self.dealer_hidden = False
            self.update_display()
            self.end_game("Blackjack! You win!", 2.5)
        elif self.dealer_hand.is_blackjack():
            self.dealer_hidden = False
            self.update_display()
            self.end_game("Dealer has Blackjack! You lose!", -1)
        else:
            # Enable buttons
            self.deal_button.config(state=tk.DISABLED)
            self.hit_button.config(state=tk.NORMAL)
            self.stand_button.config(state=tk.NORMAL)
            # Only enable calc_ev_button if simulations > 0
            if self.num_simulations > 0:
                self.calc_ev_button.config(state=tk.NORMAL)

            # Enable double down if player has enough chips
            if self.chips >= self.current_bet:
                self.double_button.config(state=tk.NORMAL)

            # Enable split if possible
            if self.player_hands[0].can_split() and self.chips >= self.current_bet:
                self.split_button.config(state=tk.NORMAL)

            # Check if player already has 21 (but not blackjack)
            if self.player_hands[0].value == 21:
                self.hit_button.config(state=tk.DISABLED)
                self.double_button.config(state=tk.DISABLED)
                self.status_label.config(text="You have 21! (Hit Stand to continue)")
            else:
                self.status_label.config(text="Your turn! Hit or Stand?")

            # Auto-calculate EV if enabled and simulations > 0
            if self.show_ev.get() and self.num_simulations > 0:
                self.root.after(100, self.calculate_all_ev)

    def hit(self):
        """Player hits (takes another card)"""
        # Cancel any ongoing EV calculation
        self.cancel_ev_calculation_if_running()

        current_hand = self.player_hands[self.current_hand_index]
        card = self.deck.deal()
        self.update_count(card)
        current_hand.add_card(card)
        self.update_display()
        self.update_count_display()

        # Disable double down and split after first hit
        self.double_button.config(state=tk.DISABLED)
        self.split_button.config(state=tk.DISABLED)

        if current_hand.is_busted():
            self.status_label.config(text=f"Hand {self.current_hand_index + 1} Busted!")
            self.next_hand_or_dealer()
        elif current_hand.value == 21:
            # Automatically stand on 21
            self.status_label.config(text=f"Hand {self.current_hand_index + 1} - 21! Auto-standing.")
            self.next_hand_or_dealer()
        else:
            # Recalculate EV if enabled and simulations > 0
            if self.show_ev.get() and self.num_simulations > 0:
                self.root.after(100, self.calculate_all_ev)

    def stand(self):
        """Player stands (keeps current hand)"""
        # Cancel any ongoing EV calculation
        self.cancel_ev_calculation_if_running()

        self.stand_count += 1
        self.status_label.config(text=f"Hand {self.current_hand_index + 1} stands at {self.player_hands[self.current_hand_index].value}")
        self.next_hand_or_dealer()

    def double_down(self):
        """Player doubles down (double bet, one card, then stand)"""
        # Cancel any ongoing EV calculation
        self.cancel_ev_calculation_if_running()

        if self.chips >= self.current_bet:
            self.chips -= self.current_bet
            self.current_bet *= 2
            self.current_bet_label.config(text=f"Current Bet: ${self.current_bet}")
            current_hand = self.player_hands[self.current_hand_index]
            card = self.deck.deal()
            self.update_count(card)
            current_hand.add_card(card)
            self.update_display()
            self.update_count_display()

            if current_hand.is_busted():
                self.status_label.config(text=f"Hand {self.current_hand_index + 1} Busted after Double Down!")
            else:
                self.status_label.config(text=f"Hand {self.current_hand_index + 1} doubled down!")

            self.next_hand_or_dealer()

    def split(self):
        """Player splits their hand into two hands"""
        # Cancel any ongoing EV calculation
        self.cancel_ev_calculation_if_running()

        if self.chips >= self.current_bet:
            self.chips -= self.current_bet
            self.has_split = True

            # Create new hand with second card
            original_hand = self.player_hands[self.current_hand_index]
            new_hand = Hand()

            # Move second card to new hand
            second_card = original_hand.cards.pop()

            # Recalculate original hand value from remaining cards
            original_hand.value = 0
            original_hand.aces = 0
            for card in original_hand.cards:
                original_hand.value += card.value
                if card.rank == 'A':
                    original_hand.aces += 1
            original_hand.adjust_for_ace()

            new_hand.add_card(second_card)

            # Check if splitting aces (before dealing new cards)
            splitting_aces = second_card.rank == 'A'

            # Deal new cards to both hands
            card1 = self.deck.deal()
            self.update_count(card1)
            original_hand.add_card(card1)

            card2 = self.deck.deal()
            self.update_count(card2)
            new_hand.add_card(card2)

            # Insert new hand after current hand
            self.player_hands.insert(self.current_hand_index + 1, new_hand)

            self.split_button.config(state=tk.DISABLED)

            self.update_display()
            self.update_count_display()

            # Special rule: Split aces get one card only and cannot hit
            if splitting_aces:
                self.hit_button.config(state=tk.DISABLED)
                self.double_button.config(state=tk.DISABLED)
                self.status_label.config(text=f"Aces split! Each hand gets one card. (Hit Stand to continue)")
                # Recalculate EV if enabled and simulations > 0
                if self.show_ev.get() and self.num_simulations > 0:
                    self.root.after(100, self.calculate_all_ev)
            else:
                # Enable double down if player has enough chips (allowing double after split)
                if self.chips >= self.current_bet:
                    self.double_button.config(state=tk.NORMAL)
                else:
                    self.double_button.config(state=tk.DISABLED)

                # Check if first hand after split has 21
                current_hand = self.player_hands[self.current_hand_index]
                if current_hand.value == 21:
                    self.hit_button.config(state=tk.DISABLED)
                    self.double_button.config(state=tk.DISABLED)
                    self.status_label.config(text=f"Hand split! Hand {self.current_hand_index + 1} has 21! (Hit Stand to continue)")
                else:
                    self.status_label.config(text=f"Hand split! Playing hand {self.current_hand_index + 1}")

                # Recalculate EV if enabled and simulations > 0
                if self.show_ev.get() and self.num_simulations > 0:
                    self.root.after(100, self.calculate_all_ev)

    def next_hand_or_dealer(self):
        """Move to next hand or dealer's turn"""
        self.current_hand_index += 1

        if self.current_hand_index < len(self.player_hands):
            # Play next hand
            current_hand = self.player_hands[self.current_hand_index]

            # Check if this is a split ace hand (has 2 cards with first card being an ace)
            is_split_ace = (self.has_split and len(current_hand.cards) == 2 and
                           current_hand.cards[0].rank == 'A')

            if is_split_ace:
                # Split aces cannot hit or double
                self.hit_button.config(state=tk.DISABLED)
                self.double_button.config(state=tk.DISABLED)
                self.status_label.config(text=f"Hand {self.current_hand_index + 1} (Split Ace): {current_hand.value} (Hit Stand to continue)")
            else:
                # Enable double down if player has enough chips and hand has exactly 2 cards
                if self.chips >= self.current_bet and len(current_hand.cards) == 2:
                    self.double_button.config(state=tk.NORMAL)
                else:
                    self.double_button.config(state=tk.DISABLED)

                # Check if this hand already has 21
                if current_hand.value == 21:
                    self.hit_button.config(state=tk.DISABLED)
                    self.double_button.config(state=tk.DISABLED)
                    self.status_label.config(text=f"Hand {self.current_hand_index + 1} has 21! (Hit Stand to continue)")
                else:
                    self.status_label.config(text=f"Playing hand {self.current_hand_index + 1}")

            self.split_button.config(state=tk.DISABLED)

            self.update_display()

            # Recalculate EV for new hand if enabled and simulations > 0
            if self.show_ev.get() and self.num_simulations > 0:
                self.root.after(100, self.calculate_all_ev)
        else:
            # All hands played, dealer's turn
            self.dealer_turn()

    def dealer_turn(self):
        """Dealer plays their hand"""
        self.dealer_hidden = False

        # Count the dealer's hidden card now that it's revealed
        if len(self.dealer_hand.cards) >= 2:
            self.update_count(self.dealer_hand.cards[1])
            self.update_count_display()

        self.hit_button.config(state=tk.DISABLED)
        self.stand_button.config(state=tk.DISABLED)
        self.double_button.config(state=tk.DISABLED)
        self.split_button.config(state=tk.DISABLED)
        self.calc_ev_button.config(state=tk.DISABLED)

        # Clear EV display
        for label in self.ev_labels.values():
            label.config(text="N/A")
        self.best_action_label.config(text="")

        self.update_display()

        # Check if all player hands are busted
        all_busted = all(hand.is_busted() for hand in self.player_hands)

        if not all_busted:
            # Dealer must hit on 16 or less, stand on 17 or more
            while self.dealer_hand.value < 17:
                card = self.deck.deal()
                self.update_count(card)
                self.dealer_hand.add_card(card)
                self.update_display()
                self.update_count_display()
                self.root.update()
                self.root.after(500)

        self.determine_winners()

    def determine_winners(self):
        """Determine winner and update chips"""
        dealer_value = self.dealer_hand.value
        dealer_busted = self.dealer_hand.is_busted()

        results = []
        total_winnings = 0

        for i, hand in enumerate(self.player_hands):
            if hand.is_busted():
                results.append(f"Hand {i+1}: Bust (Lost)")
            elif dealer_busted:
                results.append(f"Hand {i+1}: Dealer bust (Won)")
                total_winnings += self.current_bet * 2
            elif hand.value > dealer_value:
                results.append(f"Hand {i+1}: {hand.value} > {dealer_value} (Won)")
                total_winnings += self.current_bet * 2
            elif hand.value < dealer_value:
                results.append(f"Hand {i+1}: {hand.value} < {dealer_value} (Lost)")
            else:
                results.append(f"Hand {i+1}: Push (Tie)")
                total_winnings += self.current_bet

        # Calculate net result
        net_result = total_winnings - (self.current_bet * len(self.player_hands))

        self.chips += total_winnings

        result_message = "\n".join(results)
        if net_result > 0:
            result_message += f"\n\nYou won ${net_result}!"
        elif net_result < 0:
            result_message += f"\n\nYou lost ${-net_result}!"
        else:
            result_message += "\n\nPush!"

        self.status_label.config(text=result_message)
        self.update_chips_display()

        self.game_in_progress = False
        self.deal_button.config(state=tk.NORMAL)
        self.current_bet = 0
        self.current_bet_label.config(text="Current Bet: $0")

        # Re-enable count adjustment buttons if in Depleting Shoe mode
        if self.ev_deck_mode.get() == "Depleting Shoe":
            if hasattr(self, 'count_adjust_down_btn'):
                self.count_adjust_down_btn.config(state=tk.NORMAL)
                self.count_adjust_apply_btn.config(state=tk.NORMAL)
                self.count_adjust_up_btn.config(state=tk.NORMAL)
                self.count_adjust_status_label.config(text="Ready", fg='#4CAF50')

        if self.chips <= 0:
            messagebox.showinfo("Game Over", "You're out of chips! Resetting to $1000.")
            self.chips = 1000
            self.update_chips_display()

    def end_game(self, message, multiplier):
        """End game with a specific result"""
        self.status_label.config(text=message)

        if multiplier > 0:
            winnings = int(self.current_bet * multiplier)
            self.chips += self.current_bet + winnings
        elif multiplier == 0:
            self.chips += self.current_bet

        self.update_chips_display()

        self.game_in_progress = False
        self.deal_button.config(state=tk.NORMAL)
        self.hit_button.config(state=tk.DISABLED)
        self.stand_button.config(state=tk.DISABLED)
        self.double_button.config(state=tk.DISABLED)
        self.split_button.config(state=tk.DISABLED)
        self.calc_ev_button.config(state=tk.DISABLED)
        self.current_bet = 0
        self.current_bet_label.config(text="Current Bet: $0")

        # Re-enable count adjustment buttons if in Depleting Shoe mode
        if self.ev_deck_mode.get() == "Depleting Shoe":
            if hasattr(self, 'count_adjust_down_btn'):
                self.count_adjust_down_btn.config(state=tk.NORMAL)
                self.count_adjust_apply_btn.config(state=tk.NORMAL)
                self.count_adjust_up_btn.config(state=tk.NORMAL)
                self.count_adjust_status_label.config(text="Ready", fg='#4CAF50')

        # Clear EV display
        for label in self.ev_labels.values():
            label.config(text="N/A")
        self.best_action_label.config(text="")

    def update_display(self):
        """Update the display with current game state"""
        # Clear canvases
        self.dealer_canvas.delete("all")
        self.player_canvas.delete("all")
        self.card_images.clear()

        # Dealer display
        x_offset = 30
        for i, card in enumerate(self.dealer_hand.cards):
            if i == 1 and self.dealer_hidden:
                img = self.create_card_image(card, hidden=True)
            else:
                img = self.create_card_image(card)

            self.card_images[f'dealer_{i}'] = img
            self.dealer_canvas.create_image(x_offset + i * 72, 5, anchor=tk.NW, image=img)

        if self.dealer_hidden and len(self.dealer_hand.cards) > 0:
            dealer_value = self.dealer_hand.cards[0].value
            dealer_value_text = f"Value: {dealer_value}"
        else:
            dealer_value = self.dealer_hand.value
            # Show hard/soft for dealer
            if self.dealer_hand.aces > 0:
                hard_value = dealer_value - 10
                dealer_value_text = f"Value: {hard_value}/{dealer_value} (Soft {dealer_value})"
            else:
                dealer_value_text = f"Value: {dealer_value}"

        self.dealer_value_label.config(text=dealer_value_text)

        # Player display
        if len(self.player_hands) > 1:
            y_offset = 5
            for hand_idx, hand in enumerate(self.player_hands):
                x_offset = 30
                for i, card in enumerate(hand.cards):
                    img = self.create_card_image(card)
                    self.card_images[f'player_{hand_idx}_{i}'] = img
                    self.player_canvas.create_image(x_offset + i * 72, y_offset, anchor=tk.NW, image=img)

                # Show hard/soft values for split hands
                if hand.aces > 0:
                    hard_value = hand.value - 10
                    value_text = f"{hard_value}/{hand.value}"
                else:
                    value_text = str(hand.value)

                marker = " ← ACTIVE" if hand_idx == self.current_hand_index else ""
                self.player_canvas.create_text(x_offset + len(hand.cards) * 72 + 15, y_offset + 50,
                                             text=f"Hand {hand_idx+1}: {value_text}{marker}",
                                             fill='yellow' if hand_idx == self.current_hand_index else 'white',
                                             font=('Arial', 11, 'bold'), anchor=tk.W)
                y_offset += 60

            self.player_value_label.config(text="")
        else:
            x_offset = 30
            for i, card in enumerate(self.player_hands[0].cards):
                img = self.create_card_image(card)
                self.card_images[f'player_0_{i}'] = img
                self.player_canvas.create_image(x_offset + i * 72, 5, anchor=tk.NW, image=img)

            # Show hard/soft values for single hand
            if self.player_hands[0].aces > 0:
                hard_value = self.player_hands[0].value - 10
                player_value_text = f"Value: {hard_value}/{self.player_hands[0].value} (Soft {self.player_hands[0].value})"
            else:
                player_value_text = f"Value: {self.player_hands[0].value}"

            self.player_value_label.config(text=player_value_text)

        self.update_chips_display()

    def update_chips_display(self):
        """Update chips display"""
        self.chips_label.config(text=f"Chips: ${self.chips}")

    def update_count(self, card):
        """Update running count based on Hi-Lo system"""
        # Don't count cards in Fresh Deck mode (infinite deck simulation)
        if self.ev_deck_mode.get() == "Fresh Deck":
            return

        rank = card.rank
        if rank in ['2', '3', '4', '5', '6']:
            self.running_count += 1
        elif rank in ['10', 'J', 'Q', 'K', 'A']:
            self.running_count -= 1
        # 7, 8, 9 = 0 (no change)

    def get_true_count(self):
        """Calculate true count"""
        decks_remaining = self.deck.get_decks_remaining()
        if decks_remaining == 0:
            return 0
        return round(self.running_count / decks_remaining, 1)

    def reset_count(self):
        """Reset running count to 0"""
        self.running_count = 0

    def update_count_display(self):
        """Update all count-related UI labels"""
        # Cards remaining
        remaining = self.deck.get_cards_remaining()
        total = self.deck.initial_card_count
        self.cards_remaining_label.config(text=f"Cards Remaining: {remaining} / {total}")

        # Color code based on percentage
        pct = remaining / total if total > 0 else 0
        if pct > 0.5:
            color = '#00FF00'  # Green
        elif pct > 0.25:
            color = '#FFFF00'  # Yellow
        else:
            color = '#FF0000'  # Red
        self.cards_remaining_label.config(fg=color)

        # Running count
        rc = self.running_count
        self.running_count_label.config(text=f"Running: {rc:+d}")

        # True count
        tc = self.get_true_count()
        self.true_count_label.config(text=f"True: {tc:+.1f}")

        # Color code counts
        count_color = '#00FF00' if rc > 0 else '#FF0000' if rc < 0 else 'white'
        self.running_count_label.config(fg=count_color)
        self.true_count_label.config(fg=count_color)

    def adjust_count_by_increment(self, increment):
        """Adjust the deck composition to change true count by specified increment

        Args:
            increment: Desired change in true count (positive or negative)
        """
        # === VALIDATION PHASE ===

        # Check mode
        if self.ev_deck_mode.get() != "Depleting Shoe":
            messagebox.showwarning("Invalid Mode",
                                  "Count adjustment only available in Depleting Shoe mode.")
            return

        # Check game state
        if self.game_in_progress:
            messagebox.showwarning("Game in Progress",
                                  "Cannot adjust count during an active game.")
            return

        # Check for zero increment
        if increment == 0:
            self.count_adjust_status_label.config(text="No change requested", fg='yellow')
            return

        # Check if deck has cards
        if len(self.deck.cards) == 0:
            messagebox.showerror("Empty Deck", "Deck is empty. Reshuffle needed.")
            return

        # === CALCULATION PHASE ===

        # Calculate current and target counts
        current_true_count = self.get_true_count()
        target_true_count = current_true_count + increment

        # Calculate decks remaining
        decks_remaining = self.deck.get_decks_remaining()
        if decks_remaining < 0.1:  # Less than ~5 cards
            messagebox.showwarning("Too Few Cards",
                                  "Not enough cards remaining to adjust count reliably.")
            return

        # Calculate target running count
        current_running_count = self.running_count
        target_running_count = round(target_true_count * decks_remaining)
        running_count_change_needed = target_running_count - current_running_count

        # === CARD SELECTION STRATEGY ===

        # Count available cards by Hi-Lo category
        low_cards = []   # 2-6 (count value: +1 each)
        high_cards = []  # 10/J/Q/K/A (count value: -1 each)

        for card in self.deck.cards:
            if card.rank in ['2', '3', '4', '5', '6']:
                low_cards.append(card)
            elif card.rank in ['10', 'J', 'Q', 'K', 'A']:
                high_cards.append(card)

        # Determine action based on needed running count change
        cards_to_remove = []
        cards_to_add = []

        if running_count_change_needed > 0:
            # INCREASE count: Remove low cards first, then add high cards
            num_to_remove = min(abs(running_count_change_needed), len(low_cards))
            cards_to_remove = random.sample(low_cards, num_to_remove)

            # If not enough low cards to remove, add high cards
            remaining_change = running_count_change_needed - num_to_remove
            if remaining_change > 0:
                num_to_add = min(remaining_change, 10)  # Limit to prevent unrealistic decks
                for i in range(num_to_add):
                    # Add high cards with suit distribution
                    suit = Card.SUITS[i % 4]
                    rank = random.choice(['10', 'J', 'Q', 'K', 'A'])
                    cards_to_add.append(Card(suit, rank))

        elif running_count_change_needed < 0:
            # DECREASE count: Remove high cards first, then add low cards
            num_to_remove = min(abs(running_count_change_needed), len(high_cards))
            cards_to_remove = random.sample(high_cards, num_to_remove)

            # If not enough high cards to remove, add low cards
            remaining_change = abs(running_count_change_needed) - num_to_remove
            if remaining_change > 0:
                num_to_add = min(remaining_change, 10)  # Limit additions
                for i in range(num_to_add):
                    suit = Card.SUITS[i % 4]
                    rank = random.choice(['2', '3', '4', '5', '6'])
                    cards_to_add.append(Card(suit, rank))

        # === VALIDATION OF CHANGES ===

        # Check if adjustment is achievable
        if len(cards_to_remove) == 0 and len(cards_to_add) == 0:
            messagebox.showinfo("No Change", "Target count already achieved or not achievable.")
            return

        # Warn if adding too many cards (unrealistic)
        if len(cards_to_add) > 5:
            response = messagebox.askyesno("Unrealistic Adjustment",
                                           f"This will add {len(cards_to_add)} cards to the shoe.\n"
                                           f"This is unrealistic for actual card counting.\n"
                                           f"Continue anyway?")
            if not response:
                return

        # === APPLY CHANGES ===

        # Remove cards from deck
        for card in cards_to_remove:
            for i, deck_card in enumerate(self.deck.cards):
                if deck_card.suit == card.suit and deck_card.rank == card.rank:
                    self.deck.cards.pop(i)
                    break

        # Add cards to deck
        self.deck.cards.extend(cards_to_add)

        # Shuffle to integrate new cards
        if len(cards_to_add) > 0:
            self.deck.shuffle()

        # === UPDATE RUNNING COUNT ===

        # Adjust running count based on what was removed/added
        for card in cards_to_remove:
            # REMOVE card = simulate it was dealt, so update count as if we saw it
            if card.rank in ['2', '3', '4', '5', '6']:
                self.running_count += 1  # Low card dealt = count increases
            elif card.rank in ['10', 'J', 'Q', 'K', 'A']:
                self.running_count -= 1  # High card dealt = count decreases

        for card in cards_to_add:
            # ADD card = reverse a dealt card, so reverse the count effect
            if card.rank in ['2', '3', '4', '5', '6']:
                self.running_count -= 1  # Undo low card count
            elif card.rank in ['10', 'J', 'Q', 'K', 'A']:
                self.running_count += 1  # Undo high card count

        # === UPDATE UI ===

        # Update count display
        self.update_count_display()

        # Update card analysis if method exists
        if hasattr(self, 'calculate_card_counts'):
            self.calculate_card_counts()

        # Update status label
        new_true_count = self.get_true_count()
        actual_change = new_true_count - current_true_count

        status_msg = f"Count adjusted: {current_true_count:+.1f} → {new_true_count:+.1f} "
        status_msg += f"({len(cards_to_remove)} cards removed)"
        self.count_adjust_status_label.config(text=status_msg, fg='#4CAF50')

        # Show messagebox confirmation
        details = f"True Count: {current_true_count:+.1f} → {new_true_count:+.1f}\n"
        details += f"Running Count: {current_running_count:+d} → {self.running_count:+d}\n"
        details += f"Cards Removed: {len(cards_to_remove)}\n"
        details += f"Cards Remaining: {len(self.deck.cards)}"

        messagebox.showinfo("Count Adjusted", details)

    def reshuffle_shoe(self):
        """Reshuffle the shoe and reset count"""
        self.deck.build()
        self.reset_count()
        self.update_count_display()
        self.status_label.config(text="Shoe reshuffled!")

    def apply_deck_count(self):
        """Apply the selected number of decks"""
        if self.game_in_progress:
            messagebox.showwarning("Game in Progress", "Cannot change deck count during an active game.")
            return

        num_decks = self.num_decks_var.get()
        self.deck = Deck(num_decks=num_decks)
        self.reset_count()
        self.update_count_display()
        self.status_label.config(text=f"Deck reset to {num_decks} deck(s)!")

        # Reset count adjustment status
        if hasattr(self, 'count_adjust_status_label'):
            if self.ev_deck_mode.get() == "Depleting Shoe":
                self.count_adjust_status_label.config(text="Ready", fg='#4CAF50')
            else:
                self.count_adjust_status_label.config(text="(Depleting Shoe mode only)", fg='#CCCCCC')

    def manual_reshuffle(self):
        """Manually reshuffle the shoe"""
        if self.game_in_progress:
            messagebox.showwarning("Game in Progress", "Cannot reshuffle during an active game.")
            return

        self.reshuffle_shoe()

        # Reset count adjustment status
        if hasattr(self, 'count_adjust_status_label'):
            if self.ev_deck_mode.get() == "Depleting Shoe":
                self.count_adjust_status_label.config(text="Ready", fg='#4CAF50')
            else:
                self.count_adjust_status_label.config(text="(Depleting Shoe mode only)", fg='#CCCCCC')

    def show_remaining_cards(self):
        """Show all remaining cards in the deck in a new window"""
        # Create new window
        cards_window = tk.Toplevel(self.root)
        cards_window.title("Remaining Cards in Shoe")
        cards_window.geometry("600x500")
        cards_window.configure(bg='#0B6623')

        # Title
        title_label = tk.Label(cards_window, text="Remaining Cards",
                              font=('Arial', 16, 'bold'), bg='#0B6623', fg='white')
        title_label.pack(pady=10)

        # Info label
        remaining = self.deck.get_cards_remaining()
        total = self.deck.initial_card_count
        info_label = tk.Label(cards_window,
                             text=f"Cards Remaining: {remaining} / {total} ({remaining/total*100:.1f}%)",
                             font=('Arial', 12), bg='#0B6623', fg='gold')
        info_label.pack(pady=5)

        # Count high vs low cards for Hi-Lo counting
        low_cards = 0   # 2-6 (count as +1)
        neutral_cards = 0  # 7-9 (count as 0)
        high_cards = 0  # 10, J, Q, K, A (count as -1)

        for card in self.deck.cards:
            if card.rank in ['2', '3', '4', '5', '6']:
                low_cards += 1
            elif card.rank in ['7', '8', '9']:
                neutral_cards += 1
            else:  # 10, J, Q, K, A
                high_cards += 1

        # Calculate percentages
        if remaining > 0:
            low_pct = (low_cards / remaining) * 100
            neutral_pct = (neutral_cards / remaining) * 100
            high_pct = (high_cards / remaining) * 100
        else:
            low_pct = neutral_pct = high_pct = 0

        # Card counting composition info
        comp_frame = tk.Frame(cards_window, bg='#1a4d2e', relief=tk.RIDGE, borderwidth=2)
        comp_frame.pack(fill=tk.X, padx=20, pady=5)

        tk.Label(comp_frame, text="Card Composition (Hi-Lo)", font=('Arial', 11, 'bold'),
                bg='#1a4d2e', fg='gold').pack(pady=2)

        stats_frame = tk.Frame(comp_frame, bg='#1a4d2e')
        stats_frame.pack(fill=tk.X, padx=10, pady=5)

        # Low cards (favorable when dealt out)
        low_frame = tk.Frame(stats_frame, bg='#1a4d2e')
        low_frame.pack(side=tk.LEFT, expand=True, fill=tk.X)
        tk.Label(low_frame, text=f"Low (2-6): {low_cards}", font=('Arial', 10),
                bg='#1a4d2e', fg='#4CAF50').pack()
        tk.Label(low_frame, text=f"{low_pct:.1f}%", font=('Arial', 9),
                bg='#1a4d2e', fg='#90EE90').pack()

        # Neutral cards
        neutral_frame = tk.Frame(stats_frame, bg='#1a4d2e')
        neutral_frame.pack(side=tk.LEFT, expand=True, fill=tk.X)
        tk.Label(neutral_frame, text=f"Neutral (7-9): {neutral_cards}", font=('Arial', 10),
                bg='#1a4d2e', fg='white').pack()
        tk.Label(neutral_frame, text=f"{neutral_pct:.1f}%", font=('Arial', 9),
                bg='#1a4d2e', fg='#CCCCCC').pack()

        # High cards (favorable when remaining)
        high_frame = tk.Frame(stats_frame, bg='#1a4d2e')
        high_frame.pack(side=tk.LEFT, expand=True, fill=tk.X)
        tk.Label(high_frame, text=f"High (10-A): {high_cards}", font=('Arial', 10),
                bg='#1a4d2e', fg='#FF5252').pack()
        tk.Label(high_frame, text=f"{high_pct:.1f}%", font=('Arial', 9),
                bg='#1a4d2e', fg='#FF9999').pack()

        # Create scrollable frame
        canvas = tk.Canvas(cards_window, bg='#1a4d2e', highlightthickness=0)
        scrollbar = tk.Scrollbar(cards_window, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#1a4d2e')

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Count cards by rank and suit
        rank_counts = {}
        suits_in_order = ['♠', '♥', '♦', '♣']

        for card in self.deck.cards:
            rank = card.rank
            if rank not in rank_counts:
                rank_counts[rank] = {'♠': 0, '♥': 0, '♦': 0, '♣': 0}
            rank_counts[rank][card.suit] += 1

        # Display cards grouped by rank
        ranks_order = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']

        for rank in ranks_order:
            if rank in rank_counts:
                rank_frame = tk.Frame(scrollable_frame, bg='#1a4d2e', relief=tk.RIDGE, borderwidth=1)
                rank_frame.pack(fill=tk.X, padx=10, pady=2)

                # Rank label
                total_for_rank = sum(rank_counts[rank].values())
                rank_label = tk.Label(rank_frame, text=f"{rank}:", font=('Arial', 12, 'bold'),
                                     bg='#1a4d2e', fg='white', width=4)
                rank_label.pack(side=tk.LEFT, padx=5)

                # Count label
                count_label = tk.Label(rank_frame, text=f"({total_for_rank})",
                                      font=('Arial', 10, 'bold'), bg='#1a4d2e', fg='gold', width=4)
                count_label.pack(side=tk.LEFT, padx=5)

                # Suit counts
                suits_frame = tk.Frame(rank_frame, bg='#1a4d2e')
                suits_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

                for suit in suits_in_order:
                    count = rank_counts[rank][suit]
                    if count > 0:
                        color = 'red' if suit in ['♥', '♦'] else 'white'
                        suit_label = tk.Label(suits_frame,
                                            text=f"{suit}×{count}",
                                            font=('Arial', 11), bg='#1a4d2e', fg=color)
                        suit_label.pack(side=tk.LEFT, padx=8)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)

        # Close button
        close_btn = tk.Button(cards_window, text="Close", command=cards_window.destroy,
                             font=('Arial', 10, 'bold'), bg='#FF5722', fg='white', width=15)
        close_btn.pack(pady=10)


def main():
    root = tk.Tk()
    game = BlackjackMonteCarloGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
