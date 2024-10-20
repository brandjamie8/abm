import streamlit as st
from mesa import Agent, Model
from mesa.time import SimultaneousActivation
from mesa.space import MultiGrid
import matplotlib.pyplot as plt
import numpy as np
import random
import time

# Define Agent class with strength and health
class BattleAgent(Agent):
    def __init__(self, unique_id, model, team, strength, health):
        super().__init__(unique_id, model)
        self.team = team
        self.strength = strength
        self.health = health
        self.x, self.y = self.random_pos()

    def random_pos(self):
        """Randomize agent's position within the grid"""
        return self.random.randrange(self.model.grid.width), self.random.randrange(self.model.grid.height)

    def step(self):
        """Move agent and check for battles"""
        possible_moves = self.model.grid.get_neighborhood(
            (self.x, self.y), moore=True, include_center=False
        )
        new_position = self.random.choice(possible_moves)
        self.model.grid.move_agent(self, new_position)

        # Check for other agents at the new location
        cellmates = self.model.grid.get_cell_list_contents([new_position])
        for other in cellmates:
            if other != self and other.team != self.team:
                # Battle occurs if agents are from different teams
                if self.strength > other.health:
                    # Self wins
                    self.strength += 1
                    self.model.grid.remove_agent(other)
                    self.model.schedule.remove(other)
                elif other.strength > self.health:
                    # Other wins
                    other.strength += 1
                    self.model.grid.remove_agent(self)
                    self.model.schedule.remove(self)
                    break

# Define Model class
class BattleModel(Model):
    def __init__(self, N, width, height, teams):
        self.num_agents = N
        self.grid = MultiGrid(width, height, True)
        self.schedule = SimultaneousActivation(self)
        self.teams = teams

        # Create agents with random strength and health
        for i in range(self.num_agents):
            team = random.choice(teams)
            strength = random.randint(1, 10)
            health = random.randint(5, 20)
            agent = BattleAgent(i, self, team, strength, health)
            self.grid.place_agent(agent, (agent.x, agent.y))
            self.schedule.add(agent)

    def step(self):
        """Advance the model by one step"""
        self.schedule.step()

    def count_teams(self):
        """Return the number of remaining teams"""
        remaining_teams = set([agent.team for agent in self.schedule.agents])
        return len(remaining_teams)

# Streamlit interface
st.title("Agent-Based Battle Game")

# Sidebar for setting parameters
st.sidebar.header("Simulation Parameters")
num_agents = st.sidebar.slider("Number of agents", 10, 100, 20)
grid_size = st.sidebar.slider("Grid size", 5, 50, 10)
steps = st.sidebar.slider("Number of steps", 1, 200, 20)
team_list = st.sidebar.multiselect("Teams", options=["Red", "Blue", "Green", "Yellow"], default=["Red", "Blue"])

# Run button
if st.sidebar.button("Run Simulation"):

    # Initialize model
    model = BattleModel(num_agents, grid_size, grid_size, team_list)
    st.write(f"Simulation started with {num_agents} agents from {len(team_list)} teams on a {grid_size}x{grid_size} grid.")

    # Create figure for plotting
    fig, ax = plt.subplots()

    team_colors = {"Red": "r", "Blue": "b", "Green": "g", "Yellow": "y"}

    # Run simulation and plot at each step
    for i in range(steps):
        if model.count_teams() <= 1:
            st.write("Game Over!")
            break

        model.step()

        # Create grid to track agent positions and teams
        grid = np.zeros((grid_size, grid_size, 3))
        for agent in model.schedule.agents:
            color = team_colors[agent.team]
            x, y = agent.x, agent.y
            if color == 'r':
                grid[x, y, 0] = 1  # Red
            elif color == 'b':
                grid[x, y, 2] = 1  # Blue
            elif color == 'g':
                grid[x, y, 1] = 1  # Green
            elif color == 'y':
                grid[x, y] = [1, 1, 0]  # Yellow

        ax.clear()
        ax.imshow(grid, interpolation="none")
        ax.set_xticks([])
        ax.set_yticks([])
        st.pyplot(fig)
        time.sleep(0.5)  # Slow down updates to visualize the steps

    if model.count_teams() == 1:
        remaining_team = next(iter(set(agent.team for agent in model.schedule.agents)))
        st.write(f"The {remaining_team} team wins!")

st.sidebar.write("Set parameters and press 'Run Simulation' to start.")