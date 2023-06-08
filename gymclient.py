import gym
import asyncio

from stupidbot import GameClient

import gym
import asyncio
import torch
import torch.nn as nn
import torch.nn.functional as F


from stable_baselines3.common.policies import ActorCriticPolicy
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor


class CustomPolicy(ActorCriticPolicy):
    def __init__(self, *args, **kwargs):
        super(CustomPolicy, self).__init__(*args, **kwargs)
        self.features_extractor = CustomFeaturesExtractor(
            self.observation_space, features_dim=64
        )
        self.policy = nn.Linear(64, self.action_space.n)
        self.value = nn.Linear(64, 1)

    def forward(self, obs):
        features = self.features_extractor(obs)
        return self.policy(features), self.value(features)


class CustomFeaturesExtractor(BaseFeaturesExtractor):
    def __init__(self, observation_space, features_dim=64):
        super(CustomFeaturesExtractor, self).__init__(observation_space, features_dim)

        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, stride=1, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1)
        self.fc1 = nn.Linear(64 * 8 * 8, features_dim)

    def forward(self, observations):
        x = F.relu(self.conv1(observations))
        x = F.relu(self.conv2(x))
        x = x.view(x.size(0), -1)
        return F.relu(self.fc1(x))


class GameEnvironment(gym.Env):
    def __init__(self, host, port, username, password):
        self.host = host
        self.port = port
        self.client = GameClient(host, port)
        self.username = username
        self.password = password

        # Define the action space and observation space
        self.action_space = gym.spaces.Discrete(4)  # Four possible directions
        self.observation_space = gym.spaces.Box(
            low=0,
            high=1,
            shape=(self.client.map_height, self.client.map_width),
            dtype=int,
        )
        asyncio.run(self.client.play_game(self.username, self.password))

    def reset(self):
        # Reset the game environment
        self.client = GameClient(self.host, self.port)

        # Connect and join the game
        asyncio.run(self.client.play_game(self.username, self.password))

        # Return the initial game state as an observation
        return self._get_observation()

    def step(self, action):
        # Perform the specified action in the game
        direction = ["up", "right", "down", "left"][action]
        asyncio.run(self.client.move(direction))

        # Receive the next game state and reward from the server
        packet = asyncio.run(self.client.receive_packet())
        packet_type, *args = packet.split("|")
        if packet_type == "pos":
            player_id, x, y = map(int, args)
            self.client.update_game_state(player_id, x, y)
            observation = self.client.game_state
            reward = 1  # Customize the reward based on the game's rules
            done = False  # Set to True if the game is over
            info = {}  # Additional information (e.g., game statistics)
        else:
            observation = self.client.game_state
            reward = 0
            done = True
            info = {}

        return observation, reward, done, info

    def _get_observation(self):
        return torch.tensor([self.client.game_state], dtype=torch.float32).unsqueeze(0)
