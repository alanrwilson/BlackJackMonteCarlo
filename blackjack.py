
import tkinter as tk
from tkinter import messagebox
import random


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

    def __str__(self):
        return ' '.join(str(card) for card in self.cards)


class BlackjackGUI:
    """Main Blackjack game with Tkinter GUI"""
    def __init__(self, root):
        self.root = root
        self.root.title("Blackjack")
        self.root.geometry("900x700")
        self.root.configure(bg='#0B6623')

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

        self.setup_gui()

    def setup_gui(self):
        """Setup the GUI elements"""
        # Title
        title_label = tk.Label(self.root, text="BLACKJACK", font=('Arial', 36, 'bold'),
                               bg='#0B6623', fg='white')
        title_label.pack(pady=20)

        # Dealer section
        dealer_frame = tk.Frame(self.root, bg='#0B6623')
        dealer_frame.pack(pady=10)

        tk.Label(dealer_frame, text="Dealer's Hand", font=('Arial', 16, 'bold'),
                bg='#0B6623', fg='white').pack()
        self.dealer_cards_label = tk.Label(dealer_frame, text="", font=('Arial', 14),
                                           bg='#0B6623', fg='white')
        self.dealer_cards_label.pack()
        self.dealer_value_label = tk.Label(dealer_frame, text="Value: 0", font=('Arial', 14),
                                          bg='#0B6623', fg='white')
        self.dealer_value_label.pack()

        # Player section
        player_frame = tk.Frame(self.root, bg='#0B6623')
        player_frame.pack(pady=10)

        tk.Label(player_frame, text="Your Hand", font=('Arial', 16, 'bold'),
                bg='#0B6623', fg='white').pack()
        self.player_cards_label = tk.Label(player_frame, text="", font=('Arial', 14),
                                          bg='#0B6623', fg='white')
        self.player_cards_label.pack()
        self.player_value_label = tk.Label(player_frame, text="Value: 0", font=('Arial', 14),
                                          bg='#0B6623', fg='white')
        self.player_value_label.pack()

        # Status message
        self.status_label = tk.Label(self.root, text="Place your bet to start!",
                                    font=('Arial', 14, 'bold'), bg='#0B6623', fg='yellow')
        self.status_label.pack(pady=10)

        # Chips and betting section
        chips_frame = tk.Frame(self.root, bg='#0B6623')
        chips_frame.pack(pady=10)

        self.chips_label = tk.Label(chips_frame, text=f"Chips: ${self.chips}",
                                    font=('Arial', 14, 'bold'), bg='#0B6623', fg='gold')
        self.chips_label.pack()

        bet_frame = tk.Frame(self.root, bg='#0B6623')
        bet_frame.pack(pady=5)

        tk.Label(bet_frame, text="Bet: $", font=('Arial', 12), bg='#0B6623', fg='white').pack(side=tk.LEFT)
        self.bet_entry = tk.Entry(bet_frame, font=('Arial', 12), width=10)
        self.bet_entry.pack(side=tk.LEFT, padx=5)

        # Betting buttons
        bet_buttons_frame = tk.Frame(self.root, bg='#0B6623')
        bet_buttons_frame.pack(pady=5)

        for amount in [10, 25, 50, 100]:
            btn = tk.Button(bet_buttons_frame, text=f"${amount}", font=('Arial', 10),
                          command=lambda a=amount: self.quick_bet(a), width=6)
            btn.pack(side=tk.LEFT, padx=5)

        # Game action buttons
        buttons_frame = tk.Frame(self.root, bg='#0B6623')
        buttons_frame.pack(pady=20)

        self.deal_button = tk.Button(buttons_frame, text="Deal", font=('Arial', 14, 'bold'),
                                     command=self.deal_cards, width=10, bg='green', fg='white')
        self.deal_button.pack(side=tk.LEFT, padx=5)

        self.hit_button = tk.Button(buttons_frame, text="Hit", font=('Arial', 14, 'bold'),
                                    command=self.hit, width=10, state=tk.DISABLED)
        self.hit_button.pack(side=tk.LEFT, padx=5)

        self.stand_button = tk.Button(buttons_frame, text="Stand", font=('Arial', 14, 'bold'),
                                      command=self.stand, width=10, state=tk.DISABLED)
        self.stand_button.pack(side=tk.LEFT, padx=5)

        self.double_button = tk.Button(buttons_frame, text="Double Down", font=('Arial', 14, 'bold'),
                                       command=self.double_down, width=12, state=tk.DISABLED)
        self.double_button.pack(side=tk.LEFT, padx=5)

        self.split_button = tk.Button(buttons_frame, text="Split", font=('Arial', 14, 'bold'),
                                      command=self.split, width=10, state=tk.DISABLED)
        self.split_button.pack(side=tk.LEFT, padx=5)

    def quick_bet(self, amount):
        """Quick bet button handler"""
        if not self.game_in_progress:
            self.bet_entry.delete(0, tk.END)
            self.bet_entry.insert(0, str(amount))

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

        # Deal cards
        self.player_hands[0].add_card(self.deck.deal())
        self.dealer_hand.add_card(self.deck.deal())
        self.player_hands[0].add_card(self.deck.deal())
        self.dealer_hand.add_card(self.deck.deal())

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

            # Enable double down if player has enough chips
            if self.chips >= self.current_bet:
                self.double_button.config(state=tk.NORMAL)

            # Enable split if possible
            if self.player_hands[0].can_split() and self.chips >= self.current_bet:
                self.split_button.config(state=tk.NORMAL)

            self.status_label.config(text="Your turn! Hit or Stand?")

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
            self.double_button.config(state=tk.DISABLED)

            self.update_display()
            self.status_label.config(text=f"Hand split! Playing hand {self.current_hand_index + 1}")

    def next_hand_or_dealer(self):
        """Move to next hand or dealer's turn"""
        self.current_hand_index += 1

        if self.current_hand_index < len(self.player_hands):
            # Play next hand
            self.double_button.config(state=tk.DISABLED)
            self.split_button.config(state=tk.DISABLED)

            self.update_display()
            self.status_label.config(text=f"Playing hand {self.current_hand_index + 1}")
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
                # Bet already taken
            elif dealer_busted:
                results.append(f"Hand {i+1}: Dealer bust (Won)")
                total_winnings += self.current_bet * 2
            elif hand.value > dealer_value:
                results.append(f"Hand {i+1}: {hand.value} > {dealer_value} (Won)")
                total_winnings += self.current_bet * 2
            elif hand.value < dealer_value:
                results.append(f"Hand {i+1}: {hand.value} < {dealer_value} (Lost)")
                # Bet already taken
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

    def update_display(self):
        """Update the display with current game state"""
        # Dealer display
        if self.dealer_hidden and len(self.dealer_hand.cards) > 0:
            dealer_cards = str(self.dealer_hand.cards[0]) + " [Hidden]"
            dealer_value = self.dealer_hand.cards[0].value
        else:
            dealer_cards = str(self.dealer_hand)
            dealer_value = self.dealer_hand.value

        self.dealer_cards_label.config(text=dealer_cards)
        self.dealer_value_label.config(text=f"Value: {dealer_value}")

        # Player display
        if len(self.player_hands) > 1:
            # Multiple hands (split)
            player_cards = ""
            for i, hand in enumerate(self.player_hands):
                marker = " ←" if i == self.current_hand_index else ""
                player_cards += f"Hand {i+1}: {str(hand)} (Value: {hand.value}){marker}\n"
            self.player_cards_label.config(text=player_cards.strip())
            self.player_value_label.config(text="")
        else:
            # Single hand
            self.player_cards_label.config(text=str(self.player_hands[0]))
            self.player_value_label.config(text=f"Value: {self.player_hands[0].value}")

        self.update_chips_display()

    def update_chips_display(self):
        """Update chips display"""
        self.chips_label.config(text=f"Chips: ${self.chips}")


def main():
    root = tk.Tk()
    game = BlackjackGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
