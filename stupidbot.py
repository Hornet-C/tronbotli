import asyncio
import random

class GameClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None
        self.map_width = 0
        self.map_height = 0
        self.player_id = 0
        self.game_state = None
        self.running = True

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)

    async def send_packet(self, packet):
        self.writer.write(packet.encode())
        await self.writer.drain()

    async def receive_packet(self):
        packet = await self.reader.readline()
        return packet.decode().strip()

    async def join(self, username, password):
        packet = f"join|{username}|{password}\n"
        await self.send_packet(packet)

    async def move(self, direction):
        packet = f"move|{direction}\n"
        await self.send_packet(packet)

    async def chat(self, message):
        packet = f"chat|{message}\n"
        await self.send_packet(packet)

    def initialize_game_state(self):
        # Create an empty game state with the map dimensions
        self.game_state = [[0] * self.map_width for _ in range(self.map_height)]

        # Place the player's initial position in the game state
        initial_position = (self.map_width // 2, self.map_height // 2)
        self.game_state[initial_position[1]][initial_position[0]] = self.player_id

    def update_game_state(self, player_id, x, y):
        self.game_state[y][x] = player_id

    def determine_next_move(self):
        # Generate a random direction (up, right, down, left)
        directions = ["up", "right", "down", "left"]
        return random.choice(directions)

    async def start_game(self):
        while True:
            packet = await self.receive_packet()
            packet_type, *args = packet.split("|")
            if packet_type == "motd":
                motd_message = args[0]
                print(f"Message of the day: {motd_message}")
            elif packet_type == "game":
                self.map_width, self.map_height, self.player_id = map(int, args)
                self.initialize_game_state()
                print(f"New game started! Map size: {self.map_width}x{self.map_height}, Your player ID: {self.player_id}")
            elif packet_type == "pos":
                player_id, x, y = map(int, args)
                self.update_game_state(player_id, x, y)
            elif packet_type == "tick":
                print("Turn completed. It's your move.")
                next_move = self.determine_next_move()
                print(f"Your move: {next_move}")
                await self.move(next_move)
            elif packet_type == "die":
                print(f"Player(s) {' '.join(args)} died.")
            elif packet_type == "win":
                wins, losses = map(int, args)
                print(f"You won! Wins: {wins}, Losses: {losses}")
            elif packet_type == "lose":
                wins, losses = map(int, args)
                print(f"You lost! Wins: {wins}, Losses: {losses}")
            elif packet_type == "error":
                error = args[0]
                print(f"Error: {error}")
            else:
                print(f"Unknown packet type: {packet_type}")

    async def play_game(self, username, password):
        await self.connect()
        await self.join(username, password)
        await self.start_game()

    def run(self, username, password):
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self.play_game(username, password))
        except KeyboardInterrupt:
            print("\nGame ended.")
        finally:
            loop.close()

# Usage
host = '2001:67c:20a1:232:753b:18:538d:6a34'
port = 4000
username = "MindMelt"
password = "cheese"

client = GameClient(host, port)
client.run(username, password)
