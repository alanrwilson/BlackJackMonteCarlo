import tkinter as tk
from tkinter import messagebox, ttk
import random
import copy
from PIL import Image, ImageDraw, ImageFont, ImageTk


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
    """Represents a deck of 52 cards"""
    def __init__(self):
        self.cards = []
        self.build()

    def build(self):
        """Build a standard 52-card deck"""
        self.cards = [Card(suit, rank) for suit in Card.SUITS for rank in Card.RANKS]
        self.shuffle()

    def shuffle(self):
        """Shuffle the deck"""
        random.shuffle(self.cards)

    def deal(self):
        """Deal a card from the deck"""
        if len(self.cards) == 0:
            self.build()
        return self.cards.pop()

    def copy(self):
        """Create a deep copy of the deck"""
        new_deck = Deck.__new__(Deck)
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

    def __init__(self, num_simulations=10000):
        self.num_simulations = num_simulations

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

        # Create deck object
        deck = Deck.__new__(Deck)
        deck.cards = all_cards
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

        hand1.add_card(deck.deal())
        hand2.add_card(deck.deal())

        # Play out both hands with basic strategy
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

    def calculate_expected_value(self, action, player_hand, dealer_upcard, known_cards, bet):
        """Calculate expected value for a specific action and return EV with W-L-P stats"""
        total = 0
        wins = 0
        losses = 0
        pushes = 0

        for _ in range(self.num_simulations):
            # Create fresh deck for each simulation
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
        self.deck = Deck()
        self.dealer_hand = Hand()
        self.player_hands = [Hand()]
        self.current_hand_index = 0
        self.chips = 1000
        self.current_bet = 0
        self.game_in_progress = False
        self.dealer_hidden = True
        self.stand_count = 0
        self.has_split = False

        # Simulation settings
        self.num_simulations = 10000
        self.simulator = MonteCarloSimulator(self.num_simulations)
        self.show_ev = tk.BooleanVar(value=True)

        # Hand category filters
        self.filter_pairs = tk.BooleanVar(value=False)
        self.filter_ace = tk.BooleanVar(value=False)
        self.filter_soft = tk.BooleanVar(value=False)
        self.filter_hard = tk.BooleanVar(value=False)

        # Dealer upcard filter
        self.filter_dealer_upcard = tk.BooleanVar(value=False)
        self.dealer_upcard_value = tk.StringVar(value="Any")

        # Player upcard filter
        self.filter_player_upcard = tk.BooleanVar(value=False)
        self.player_upcard_value = tk.StringVar(value="Any")

        # Player second card filter
        self.filter_player_second_card = tk.BooleanVar(value=False)
        self.player_second_card_value = tk.StringVar(value="Any")

        # Auto-simulator state
        self.auto_sim_running = False
        self.auto_sim_hands_to_play = 0
        self.auto_sim_hands_played = 0
        self.auto_sim_wins = 0
        self.auto_sim_losses = 0
        self.auto_sim_pushes = 0
        self.auto_sim_starting_chips = 0

        # EV tracking: {(player_total, dealer_upcard, action): [outcomes]}
        self.auto_sim_ev_data = {}

        # Card image cache
        self.card_images = {}

        self.setup_gui()

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
        stats_frame = tk.Frame(main_frame, bg='#1a4d2e', highlightbackground='gold', highlightthickness=2, width=450, height=635)
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
        tk.Label(stats_frame, text="Monte Carlo Analysis", font=('Arial', 16, 'bold'),
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
                          command=lambda a=amount: self.quick_bet(a), width=4)
            btn.pack(side=tk.LEFT, padx=1)

        # Simulation settings
        settings_frame = tk.Frame(stats_frame, bg='#1a4d2e')
        settings_frame.pack(pady=3, padx=10, fill=tk.X)

        sim_row = tk.Frame(settings_frame, bg='#1a4d2e')
        sim_row.pack(fill=tk.X)

        tk.Label(sim_row, text="Sims:", font=('Arial', 9, 'bold'),
                bg='#1a4d2e', fg='white').pack(side=tk.LEFT, padx=(0, 5))

        sim_values = [1000, 5000, 10000, 50000]
        self.sim_var = tk.IntVar(value=10000)
        sim_dropdown = ttk.Combobox(sim_row, textvariable=self.sim_var,
                                   values=sim_values, state='readonly', width=10)
        sim_dropdown.pack(side=tk.LEFT)
        sim_dropdown.bind('<<ComboboxSelected>>', self.update_simulations)

        # Hand category filters
        tk.Label(settings_frame, text="Hand Filters:", font=('Arial', 9, 'bold'),
                bg='#1a4d2e', fg='white').pack(pady=(3, 2))

        hand_filter_row = tk.Frame(settings_frame, bg='#1a4d2e')
        hand_filter_row.pack(pady=3)

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

        # Dealer upcard filter - compact layout
        tk.Label(settings_frame, text="Dealer Upcard:", font=('Arial', 9, 'bold'),
                bg='#1a4d2e', fg='white').pack(pady=(5, 2))

        dealer_frame = tk.Frame(settings_frame, bg='#1a4d2e')
        dealer_frame.pack(pady=2, padx=10, fill=tk.X)

        tk.Checkbutton(dealer_frame, text="Dealer:", variable=self.filter_dealer_upcard,
                      font=('Arial', 9, 'bold'), bg='#1a4d2e', fg='white',
                      selectcolor='#0B6623').pack(side=tk.LEFT, padx=(0, 5))

        dealer_upcard_values = ['Any', 'A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        dealer_dropdown = ttk.Combobox(dealer_frame, textvariable=self.dealer_upcard_value,
                                      values=dealer_upcard_values, state='readonly', width=8)
        dealer_dropdown.pack(side=tk.LEFT)

        # Player cards section header
        tk.Label(settings_frame, text="Player Cards:", font=('Arial', 9, 'bold'),
                bg='#1a4d2e', fg='white').pack(pady=(5, 2))

        # Player first card - compact layout
        player_first_frame = tk.Frame(settings_frame, bg='#1a4d2e')
        player_first_frame.pack(pady=2, padx=10, fill=tk.X)

        tk.Checkbutton(player_first_frame, text="1st:", variable=self.filter_player_upcard,
                      font=('Arial', 9, 'bold'), bg='#1a4d2e', fg='white',
                      selectcolor='#0B6623').pack(side=tk.LEFT, padx=(0, 5))

        player_upcard_values = ['Any', 'A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        player_dropdown = ttk.Combobox(player_first_frame, textvariable=self.player_upcard_value,
                                      values=player_upcard_values, state='readonly', width=8)
        player_dropdown.pack(side=tk.LEFT)

        # Player second card - compact layout
        player_second_frame = tk.Frame(settings_frame, bg='#1a4d2e')
        player_second_frame.pack(pady=2, padx=10, fill=tk.X)

        tk.Checkbutton(player_second_frame, text="2nd:", variable=self.filter_player_second_card,
                      font=('Arial', 9, 'bold'), bg='#1a4d2e', fg='white',
                      selectcolor='#0B6623').pack(side=tk.LEFT, padx=(0, 5))

        player_second_card_values = ['Any', 'A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        player_second_dropdown = ttk.Combobox(player_second_frame, textvariable=self.player_second_card_value,
                                      values=player_second_card_values, state='readonly', width=8)
        player_second_dropdown.pack(side=tk.LEFT)

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
        self.sim_progress_label.pack(pady=2)

        self.sim_stats_label = tk.Label(stats_display_frame, text="",
                                        font=('Arial', 8), bg='#1a4d2e', fg='white', justify=tk.LEFT,
                                        wraplength=410)
        self.sim_stats_label.pack(pady=2, fill=tk.BOTH, expand=True)

        # Left sidebar - Card Analysis
        tk.Label(left_stats_frame, text="Card Analysis", font=('Arial', 18, 'bold'),
                bg='#1a4d2e', fg='white').pack(pady=10)

        # Card counting section
        card_count_frame = tk.Frame(left_stats_frame, bg='#1a4d2e')
        card_count_frame.pack(pady=10, padx=10, fill=tk.X)

        tk.Label(card_count_frame, text="Remaining Cards", font=('Arial', 11, 'bold'),
                bg='#1a4d2e', fg='white').pack(pady=5)

        self.player_bust_label = tk.Label(card_count_frame, text="Player Bust: N/A",
                                          font=('Arial', 10, 'bold'), bg='#1a4d2e', fg='#FF5252', width=25, anchor='w')
        self.player_bust_label.pack(pady=3, padx=10, fill=tk.X)

        self.bust_ranks_label = tk.Label(card_count_frame, text="",
                                         font=('Arial', 9), bg='#1a4d2e', fg='#FF9999', justify=tk.LEFT,
                                         anchor='w', wraplength=200)
        self.bust_ranks_label.pack(pady=2, padx=15, fill=tk.X)

        self.player_safe_label = tk.Label(card_count_frame, text="Player Safe: N/A",
                                          font=('Arial', 10, 'bold'), bg='#1a4d2e', fg='#4CAF50', width=25, anchor='w')
        self.player_safe_label.pack(pady=3, padx=10, fill=tk.X)

        self.safe_ranks_label = tk.Label(card_count_frame, text="",
                                         font=('Arial', 9), bg='#1a4d2e', fg='#90EE90', justify=tk.LEFT,
                                         anchor='w', wraplength=200)
        self.safe_ranks_label.pack(pady=2, padx=15, fill=tk.X)

        # Expected Value Display
        ev_frame = tk.Frame(left_stats_frame, bg='#1a4d2e')
        ev_frame.pack(pady=10, padx=10, fill=tk.X)

        # EV header with Show EV checkbox
        ev_header_frame = tk.Frame(ev_frame, bg='#1a4d2e')
        ev_header_frame.pack(pady=5, fill=tk.X)

        tk.Label(ev_header_frame, text="Expected Value ($)", font=('Arial', 13, 'bold'),
                bg='#1a4d2e', fg='white').pack(side=tk.LEFT, padx=(5, 10))

        tk.Checkbutton(ev_header_frame, text="Show", variable=self.show_ev,
                      font=('Arial', 9), bg='#1a4d2e', fg='white',
                      selectcolor='#0B6623', command=self.update_ev_display).pack(side=tk.LEFT)

        # EV for each action
        self.ev_labels = {}
        actions = ['HIT', 'STAND', 'DOUBLE', 'SPLIT']
        colors = {'HIT': '#4CAF50', 'STAND': '#2196F3', 'DOUBLE': '#FF9800', 'SPLIT': '#9C27B0'}

        for action in actions:
            action_frame = tk.Frame(ev_frame, bg='#1a4d2e')
            action_frame.pack(fill=tk.X, pady=3, padx=5)

            tk.Label(action_frame, text=f"{action}:", font=('Arial', 10, 'bold'),
                    bg='#1a4d2e', fg=colors[action], width=7, anchor='w').pack(side=tk.LEFT)

            label = tk.Label(action_frame, text="N/A", font=('Arial', 9),
                           bg='#1a4d2e', fg='white', anchor='w')
            label.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.ev_labels[action] = label

        # Best action recommendation
        self.best_action_label = tk.Label(ev_frame, text="", font=('Arial', 12, 'bold'),
                                         bg='#1a4d2e', fg='yellow', wraplength=220)
        self.best_action_label.pack(pady=10)

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
            if self.filter_player_upcard.get() and self.player_upcard_value.get() != "Any":
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
            if self.filter_dealer_upcard.get() and self.dealer_upcard_value.get() != "Any":
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
            if self.filter_player_second_card.get() and self.player_second_card_value.get() != "Any":
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

            self.dealer_hand.add_card(self.deck.deal())

            # Check if hand matches filter
            if self.check_hand_category(self.player_hands[0]):
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

    def update_ev_display(self):
        """Toggle EV display"""
        if not self.show_ev.get():
            for label in self.ev_labels.values():
                label.config(text="N/A")
            self.best_action_label.config(text="")

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

        # Update UI
        self.start_sim_button.config(state=tk.DISABLED)
        self.stop_sim_button.config(state=tk.NORMAL)
        self.deal_button.config(state=tk.DISABLED)

        # Start the simulation loop
        self.play_auto_hand()

    def stop_auto_sim(self):
        """Stop the auto-simulator"""
        self.auto_sim_running = False
        self.start_sim_button.config(state=tk.NORMAL)
        self.stop_sim_button.config(state=tk.DISABLED)
        self.deal_button.config(state=tk.NORMAL)
        self.sim_progress_label.config(text="Stopped")

    def play_auto_hand(self):
        """Play one hand automatically using basic strategy"""
        if not self.auto_sim_running or self.auto_sim_hands_played >= self.auto_sim_hands_to_play:
            # Simulation complete
            self.auto_sim_running = False
            self.start_sim_button.config(state=tk.NORMAL)
            self.stop_sim_button.config(state=tk.DISABLED)
            self.deal_button.config(state=tk.NORMAL)

            chip_change = self.chips - self.auto_sim_starting_chips
            win_rate = (self.auto_sim_wins / self.auto_sim_hands_played * 100) if self.auto_sim_hands_played > 0 else 0

            self.sim_progress_label.config(text="Complete!")
            self.sim_stats_label.config(
                text=f"Final: {self.auto_sim_hands_played} hands\n"
                     f"W: {self.auto_sim_wins} L: {self.auto_sim_losses} P: {self.auto_sim_pushes}\n"
                     f"Win Rate: {win_rate:.1f}%\n"
                     f"Chips: {chip_change:+d}")

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

        self.deck = Deck()
        self.dealer_hand = Hand()
        self.player_hands = [Hand()]
        self.current_hand_index = 0
        self.game_in_progress = True
        self.dealer_hidden = True
        self.has_split = False

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

        # Get basic strategy decision
        dealer_upcard_value = self.dealer_hand.cards[0].value
        dealer_upcard_rank = self.dealer_hand.cards[0].rank
        player_total = current_hand.value
        decision = self.basic_strategy_decision(current_hand, dealer_upcard_value)

        # Store the decision for later tracking (before outcome is known)
        if not hasattr(self, 'current_decision_data'):
            self.current_decision_data = []

        # Only track initial decisions (2-card hands)
        if len(current_hand.cards) == 2:
            # Identify if this is a soft hand
            is_soft = current_hand.aces > 0
            hand_label = f"S{player_total}" if is_soft else str(player_total)

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
            current_hand.add_card(self.deck.deal())
            self.root.after(10, self.auto_play_hand)
        elif decision == 'DOUBLE':
            if self.chips >= self.current_bet:
                self.chips -= self.current_bet
                self.current_bet *= 2
            current_hand.add_card(self.deck.deal())
            self.current_hand_index += 1
            self.root.after(10, self.auto_play_hand)
        elif decision == 'SPLIT':
            if self.chips >= self.current_bet:
                self.chips -= self.current_bet
                self.has_split = True

                original_hand = self.player_hands[self.current_hand_index]
                new_hand = Hand()

                second_card = original_hand.cards.pop()
                original_hand.value -= second_card.value
                if second_card.rank == 'A':
                    original_hand.aces -= 1
                new_hand.add_card(second_card)

                original_hand.add_card(self.deck.deal())
                new_hand.add_card(self.deck.deal())

                self.player_hands.insert(self.current_hand_index + 1, new_hand)

            self.root.after(10, self.auto_play_hand)

    def auto_dealer_turn(self):
        """Automatically play dealer's turn"""
        self.dealer_hidden = False

        # Check if all player hands busted
        all_busted = all(hand.is_busted() for hand in self.player_hands)

        if not all_busted:
            # Dealer plays
            while self.dealer_hand.value < 17:
                self.dealer_hand.add_card(self.deck.deal())

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

        # Update stats based on overall hand result
        if won_hands > lost_hands:
            self.auto_sim_wins += 1
        elif lost_hands > won_hands:
            self.auto_sim_losses += 1
        else:
            self.auto_sim_pushes += 1

        self.auto_sim_hands_played += 1
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
                     f"Win Rate: {win_rate:.1f}%\n"
                     f"Chips: {chip_change:+d}")

    def show_ev_results(self):
        """Display EV results in a new window"""
        if not self.auto_sim_ev_data:
            messagebox.showinfo("No Data", "No EV data available. Run a simulation first.")
            return

        # Create new window
        results_window = tk.Toplevel(self.root)
        results_window.title("Auto-Simulator EV Results")
        results_window.geometry("1200x700")
        results_window.configure(bg='#0B6623')

        # Title
        tk.Label(results_window, text="Expected Value Analysis", font=('Arial', 18, 'bold'),
                bg='#0B6623', fg='white').pack(pady=10)

        # Create frame with scrollbar
        main_frame = tk.Frame(results_window, bg='#0B6623')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Add canvas for scrolling
        canvas = tk.Canvas(main_frame, bg='#0B6623')
        scrollbar = tk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#0B6623')

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)

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

        # Display results grouped by dealer upcard
        dealer_order = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10']

        for dealer_upcard in dealer_order:
            if dealer_upcard not in sorted_data:
                continue

            # Dealer upcard header
            dealer_frame = tk.Frame(scrollable_frame, bg='#1a4d2e')
            dealer_frame.pack(fill=tk.X, pady=5, padx=5)

            tk.Label(dealer_frame, text=f"Dealer Upcard: {dealer_upcard}", font=('Arial', 14, 'bold'),
                    bg='#1a4d2e', fg='yellow').pack(pady=5)

            # Sort player hands: hard hands (numeric) first, then soft hands (S prefix)
            def hand_sort_key(hand_str):
                if hand_str.startswith('S'):
                    # Soft hand - sort by numeric part, put after hard hands
                    return (1, int(hand_str[1:]))
                else:
                    # Hard hand - sort numerically, put before soft hands
                    return (0, int(hand_str))

            player_hands = sorted(sorted_data[dealer_upcard].keys(), key=hand_sort_key)

            for player_hand in player_hands:
                actions_data = sorted_data[dealer_upcard][player_hand]

                # Create row for this player hand - using Text widget for better visibility
                row_frame = tk.Frame(dealer_frame, bg='#1a4d2e')
                row_frame.pack(fill=tk.X, padx=10, pady=3)

                # Player hand label
                tk.Label(row_frame, text=f"Player {player_hand}:", font=('Arial', 12, 'bold'),
                        bg='#1a4d2e', fg='white').pack(side=tk.LEFT, padx=5, pady=5)

                # Action EVs - display each on same row
                action_colors = {'HIT': '#4CAF50', 'STAND': '#2196F3', 'DOUBLE': '#FF9800', 'SPLIT': '#FF00FF'}

                action_container = tk.Frame(row_frame, bg='#1a4d2e')
                action_container.pack(side=tk.LEFT, fill=tk.X, expand=True)

                for action in ['HIT', 'STAND', 'DOUBLE', 'SPLIT']:
                    if action in actions_data:
                        ev = actions_data[action]['ev']
                        count = actions_data[action]['count']
                        wins = actions_data[action]['wins']
                        losses = actions_data[action]['losses']
                        pushes = actions_data[action]['pushes']

                        text = f"{action}: ${ev:+.2f} ({wins}W-{losses}L-{pushes}P)"

                        action_label = tk.Label(action_container,
                                              text=text,
                                              font=('Arial', 11, 'bold'), bg='#1a4d2e',
                                              fg=action_colors.get(action, 'white'),
                                              anchor='w', padx=10)
                        action_label.pack(side=tk.LEFT, pady=5)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Close button
        tk.Button(results_window, text="Close", font=('Arial', 12, 'bold'),
                 command=results_window.destroy, width=15, bg='#F44336', fg='white').pack(pady=10)

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

    def calculate_all_ev(self):
        """Calculate expected value for all possible actions"""
        if not self.game_in_progress or not self.show_ev.get():
            return

        # Safety check for valid hand index
        if self.current_hand_index >= len(self.player_hands):
            return

        self.calc_ev_button.config(state=tk.DISABLED, text="Calculating...")
        self.root.update()

        current_hand = self.player_hands[self.current_hand_index]

        # Create a dealer hand with only visible card
        visible_dealer_hand = Hand()
        visible_dealer_hand.add_card(self.dealer_hand.cards[0].copy())

        # Gather all known cards (player's cards + dealer's visible card)
        known_cards = []
        for hand in self.player_hands:
            known_cards.extend(hand.cards)
        known_cards.append(self.dealer_hand.cards[0])

        ev_results = {}

        # Calculate EV for Hit
        result_hit = self.simulator.calculate_expected_value(
            "HIT", current_hand, visible_dealer_hand, known_cards, self.current_bet)
        ev_results['HIT'] = result_hit['ev']
        self.ev_labels['HIT'].config(text=f"${result_hit['ev']:+.2f} ({result_hit['wins']}W-{result_hit['losses']}L-{result_hit['pushes']}P)")

        # Calculate EV for Stand
        result_stand = self.simulator.calculate_expected_value(
            "STAND", current_hand, visible_dealer_hand, known_cards, self.current_bet)
        ev_results['STAND'] = result_stand['ev']
        self.ev_labels['STAND'].config(text=f"${result_stand['ev']:+.2f} ({result_stand['wins']}W-{result_stand['losses']}L-{result_stand['pushes']}P)")

        # Calculate EV for Double Down if possible
        if self.chips >= self.current_bet and len(current_hand.cards) == 2:
            result_double = self.simulator.calculate_expected_value(
                "DOUBLE", current_hand, visible_dealer_hand, known_cards, self.current_bet)
            ev_results['DOUBLE'] = result_double['ev']
            self.ev_labels['DOUBLE'].config(text=f"${result_double['ev']:+.2f} ({result_double['wins']}W-{result_double['losses']}L-{result_double['pushes']}P)")
        else:
            self.ev_labels['DOUBLE'].config(text="N/A")

        # Calculate EV for Split if possible
        if current_hand.can_split() and self.chips >= self.current_bet:
            result_split = self.simulator.calculate_expected_value(
                "SPLIT", current_hand, visible_dealer_hand, known_cards, self.current_bet)
            ev_results['SPLIT'] = result_split['ev']
            self.ev_labels['SPLIT'].config(text=f"${result_split['ev']:+.2f} ({result_split['wins']}W-{result_split['losses']}L-{result_split['pushes']}P)")
        else:
            self.ev_labels['SPLIT'].config(text="N/A")

        # Find best action
        valid_actions = {k: v for k, v in ev_results.items() if k in self.ev_labels and self.ev_labels[k].cget('text') != "N/A"}
        if valid_actions:
            best_action = max(valid_actions, key=valid_actions.get)
            best_ev = valid_actions[best_action]
            self.best_action_label.config(
                text=f"Best Action:\n{best_action}\n(EV: ${best_ev:.2f})")

        self.calc_ev_button.config(state=tk.NORMAL, text="Calculate EV")

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

        # Reset game state
        self.deck = Deck()
        self.dealer_hand = Hand()
        self.player_hands = [Hand()]
        self.current_hand_index = 0
        self.game_in_progress = True
        self.dealer_hidden = True
        self.stand_count = 0
        self.has_split = False

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

            # Auto-calculate EV if enabled
            if self.show_ev.get():
                self.root.after(100, self.calculate_all_ev)

    def hit(self):
        """Player hits (takes another card)"""
        current_hand = self.player_hands[self.current_hand_index]
        current_hand.add_card(self.deck.deal())
        self.update_display()

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
            # Recalculate EV
            if self.show_ev.get():
                self.root.after(100, self.calculate_all_ev)

    def stand(self):
        """Player stands (keeps current hand)"""
        self.stand_count += 1
        self.status_label.config(text=f"Hand {self.current_hand_index + 1} stands at {self.player_hands[self.current_hand_index].value}")
        self.next_hand_or_dealer()

    def double_down(self):
        """Player doubles down (double bet, one card, then stand)"""
        if self.chips >= self.current_bet:
            self.chips -= self.current_bet
            self.current_bet *= 2
            current_hand = self.player_hands[self.current_hand_index]
            current_hand.add_card(self.deck.deal())
            self.update_display()

            if current_hand.is_busted():
                self.status_label.config(text=f"Hand {self.current_hand_index + 1} Busted after Double Down!")
            else:
                self.status_label.config(text=f"Hand {self.current_hand_index + 1} doubled down!")

            self.next_hand_or_dealer()

    def split(self):
        """Player splits their hand into two hands"""
        if self.chips >= self.current_bet:
            self.chips -= self.current_bet
            self.has_split = True

            # Create new hand with second card
            original_hand = self.player_hands[self.current_hand_index]
            new_hand = Hand()

            # Move second card to new hand
            second_card = original_hand.cards.pop()
            original_hand.value -= second_card.value
            if second_card.rank == 'A':
                original_hand.aces -= 1
            new_hand.add_card(second_card)

            # Deal new cards to both hands
            original_hand.add_card(self.deck.deal())
            new_hand.add_card(self.deck.deal())

            # Insert new hand after current hand
            self.player_hands.insert(self.current_hand_index + 1, new_hand)

            self.split_button.config(state=tk.DISABLED)

            # Enable double down if player has enough chips (allowing double after split)
            if self.chips >= self.current_bet:
                self.double_button.config(state=tk.NORMAL)
            else:
                self.double_button.config(state=tk.DISABLED)

            self.update_display()

            # Check if first hand after split has 21
            current_hand = self.player_hands[self.current_hand_index]
            if current_hand.value == 21:
                self.hit_button.config(state=tk.DISABLED)
                self.double_button.config(state=tk.DISABLED)
                self.status_label.config(text=f"Hand split! Hand {self.current_hand_index + 1} has 21! (Hit Stand to continue)")
            else:
                self.status_label.config(text=f"Hand split! Playing hand {self.current_hand_index + 1}")

            # Recalculate EV
            if self.show_ev.get():
                self.root.after(100, self.calculate_all_ev)

    def next_hand_or_dealer(self):
        """Move to next hand or dealer's turn"""
        self.current_hand_index += 1

        if self.current_hand_index < len(self.player_hands):
            # Play next hand
            current_hand = self.player_hands[self.current_hand_index]

            # Enable double down if player has enough chips and hand has exactly 2 cards
            if self.chips >= self.current_bet and len(current_hand.cards) == 2:
                self.double_button.config(state=tk.NORMAL)
            else:
                self.double_button.config(state=tk.DISABLED)

            self.split_button.config(state=tk.DISABLED)

            self.update_display()

            # Check if this hand already has 21
            if current_hand.value == 21:
                self.hit_button.config(state=tk.DISABLED)
                self.double_button.config(state=tk.DISABLED)
                self.status_label.config(text=f"Hand {self.current_hand_index + 1} has 21! (Hit Stand to continue)")
            else:
                self.status_label.config(text=f"Playing hand {self.current_hand_index + 1}")

            # Recalculate EV for new hand
            if self.show_ev.get():
                self.root.after(100, self.calculate_all_ev)
        else:
            # All hands played, dealer's turn
            self.dealer_turn()

    def dealer_turn(self):
        """Dealer plays their hand"""
        self.dealer_hidden = False
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
                self.dealer_hand.add_card(self.deck.deal())
                self.update_display()
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


def main():
    root = tk.Tk()
    game = BlackjackMonteCarloGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
