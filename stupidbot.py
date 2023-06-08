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

        # Place the player's initial position in the game state if it's within the map boundaries
        initial_position = (self.map_width // 2, self.map_height // 2)
        if 0 <= initial_position[0] < self.map_width and 0 <= initial_position[1] < self.map_height:
            self.game_state[initial_position[1]][initial_position[0]] = self.player_id
            
    def update_game_state(self, player_id, x, y):
        self.game_state[y][x] = player_id

    def determine_next_move(self):
        current_x, current_y = self.get_player_position(self.player_id)
        if current_x is None or current_y is None:
            # Player's position is unknown
            choice = random.choice(["up", "right", "down", "left"])
            print(f"Player's position is unknown, moving random {choice}")
            return choice

        # Generate a list of valid directions to move
        valid_directions = []
        if current_y > 0 and self.game_state[current_y - 1][current_x] == 0:
            valid_directions.append("up")
        if current_y < self.map_height - 1 and self.game_state[current_y + 1][
            current_x] == 0:
            valid_directions.append("down")
        if current_x > 0 and self.game_state[current_y][current_x - 1] == 0:
            valid_directions.append("left")
        if current_x < self.map_width - 1 and self.game_state[current_y][
            current_x + 1] == 0:
            valid_directions.append("right")

        if valid_directions:
            # Choose a random valid direction to move
            return random.choice(valid_directions)
        else:
            # No valid directions available, stay in place
            return "stay"

    def get_player_position(self, player_id):
        for y in range(self.map_height):
            for x in range(self.map_width):
                if self.game_state[y][x] == player_id:
                    return x, y
        return None, None

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
                print(
                    f"New game started! Map size: {self.map_width}x{self.map_height}, Your player ID: {self.player_id}")
                break  # Exit the loop and proceed with the other steps
            elif packet_type == "message":
                sender_id, message = int(args[0]), args[1]
                print(f"Player {sender_id} says: {message}")

        while True:
            packet = await self.receive_packet()
            packet_type, *args = packet.split("|")
            if packet_type == "pos":
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
                break  # Exit the loop and wait for the next "game" packet
            elif packet_type == "lose":
                wins, losses = map(int, args)
                print(f"You lost! Wins: {wins}, Losses: {losses}")
                break  # Exit the loop and wait for the next "game" packet
            elif packet_type == "error":
                error = args[0]
                print(f"Error: {error}")
            elif packet_type == "message":
                sender_id, message = int(args[0]), args[1]
                print(f"Player {sender_id} says: {message}")
            else:
                print(f"Unknown packet type: {packet_type}")

        # Wait for the next "game" packet before starting the next game
        await self.start_game()

    async def play_game(self, username, password):
        await self.connect()
        await self.join(username, password)
        await self.start_game()


# Usage
if __name__ == "__main__":
    host = "2001:67c:20a1:232:753b:18:538d:6a34"
    port = 4000
    username = "stupidbot_2"
    password = "cheese"

    client = GameClient(host, port)
    asyncio.run(client.play_game(username, password))
