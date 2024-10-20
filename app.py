import streamlit as st
from mesa import Agent, Model
from mesa.time import SimultaneousActivation
from mesa.space import MultiGrid
import matplotlib.pyplot as plt
import numpy as np
import random

class BattleAgent(Agent):
    def __init__(self, unique_id, model, team, strength, health, move_distance):
        super().__init__(unique_id, model)
        self.team = team
        self.strength = strength
        self.health = health
        self.move_distance = move_distance
        self.x, self.y = self.random_pos()
        self.model.grid.place_agent(self, (self.x, self.y))  # Ensure agent is placed on the grid

    def step(self):
        """Move agent within the allowed move distance and check for battles"""
        possible_moves = self.model.grid.get_neighborhood(
            (self.x, self.y), moore=True, include_center=False, radius=self.move_distance
        )
        if possible_moves:
            new_position = self.random.choice(possible_moves)
            self.model.grid.move_agent(self, new_position)  # Move only if valid moves exist

            # Check for other agents at the new location
            cellmates = self.model.grid.get_cell_list_contents([new_position])
            for other in cellmates:
                if other != self and other.team != self.team:
                    # Battle logic
                    if self.strength > other.health:
                        if other.pos:
                            self.model.grid.remove_agent(other)
                            self.model.schedule.remove(other)
                        self.strength += 1
                    elif other.strength > self.health:
                        if self.pos:
                            self.model.grid.remove_agent(self)
                            self.model.schedule.remove(self)
                        other.strength += 1
                        break


# Define Model class
class BattleModel(Model):
    def __init__(self, N, width, height, teams, move_distance):
        self.num_agents = N
        self.grid = MultiGrid(width, height, True)
        self.schedule = SimultaneousActivation(self)
        self.teams = teams
        self.move_distance = move_distance

        # Create agents with random strength and health
        for i in range(self.num_agents):
            team = random.choice(teams)
            strength = random.randint(1, 10)
            health = random.randint(5, 20)
            agent = BattleAgent(i, self, team, strength, health, move_distance)
            self.grid.place_agent(agent, (agent.x, agent.y))
            self.schedule.add(agent)

    def step(self):
        """Advance the model by one step"""
        self.schedule.step()

    def count_teams(self):
        """Return the number of remaining teams"""
        remaining_teams = set([agent.team for agent in self.schedule.agents])
        return len(remaining_teams)

    def get_agents_positions(self):
        """Get a list of current positions of all agents"""
        positions = []
        for agent in self.schedule.agents:
            positions.append((agent.x, agent.y, agent.team))
        return positions

# Streamlit interface
st.title("Agent-Based Battle Game with Scrollable Timeline")

# Sidebar for setting parameters
st.sidebar.header("Simulation Parameters")
num_agents = st.sidebar.slider("Number of agents", 10, 100, 20)
grid_size = st.sidebar.slider("Grid size", 5, 50, 10)
steps = st.sidebar.slider("Number of steps", 1, 200, 50)
team_list = st.sidebar.multiselect("Teams", options=["Red", "Blue", "Green", "Yellow"], default=["Red", "Blue"])
move_distance = st.sidebar.slider("Move distance per step", 1, 5, 1)

# Run button
if st.sidebar.button("Run Simulation"):

    # Initialize model
    model = BattleModel(num_agents, grid_size, grid_size, team_list, move_distance)
    st.write(f"Simulation started with {num_agents} agents from {len(team_list)} teams on a {grid_size}x{grid_size} grid.")

    # Create list to store positions over all steps
    all_positions = []

    # Run the simulation for the specified number of steps and save positions
    for i in range(steps):
        if model.count_teams() <= 1:
            st.write("Game Over!")
            break
        model.step()
        all_positions.append(model.get_agents_positions())

    # Define team colors
    team_colors = {"Red": "r", "Blue": "b", "Green": "g", "Yellow": "y"}

    # Create a slider for selecting which step to display
    step_to_show = st.slider("Select Step", 0, len(all_positions) - 1, 0)

    # Get agent positions for the selected step
    selected_positions = all_positions[step_to_show]

    # Create grid to track agent positions and teams
    grid = np.zeros((grid_size, grid_size, 3))
    for pos in selected_positions:
        x, y, team = pos
        color = team_colors[team]
        if color == 'r':
            grid[x, y, 0] = 1  # Red
        elif color == 'b':
            grid[x, y, 2] = 1  # Blue
        elif color == 'g':
            grid[x, y, 1] = 1  # Green
        elif color == 'y':
            grid[x, y] = [1, 1, 0]  # Yellow

    # Plot the grid for the selected step
    fig, ax = plt.subplots()
    ax.imshow(grid, interpolation="none")
    ax.set_xticks([])
    ax.set_yticks([])
    st.pyplot(fig)

st.sidebar.write("Set parameters and press 'Run Simulation' to start.")

