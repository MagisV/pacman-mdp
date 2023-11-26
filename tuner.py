# coding: utf-8

import subprocess
import itertools
import re
import multiprocessing

# Define the hyperparameter grid to search over
hyperparameter_grid = {
    'FOOD_REWARD': [20],
    'EMTPY_REWARD': [-0.01, -0.02],
    'GHOST_REWARD': [-100],
    'GHOST_DANGER_ZONE': [1],
    'GAMMA': [0.95],
    'ITERATIONS': [100],
    'ISSMALL': [True, False]
}

# FOOD_REWARD = 20
#             EMTPY_REWARD = -0.01
#             GHOST_REWARD = -100
#             GHOST_DANGER_ZONE = 1 # fields around ghost that are given a negative reward as well
#             GHOST_DANGER_ZONE_REWARD = GHOST_REWARD * 0.2 # fields around ghost that are given a negative reward as well
#             GAMMA = 0.99
#             ITERATIONS = 100

# Generate all combinations of hyperparameters
all_combinations = list(itertools.product(*hyperparameter_grid.values()))

# Function to modify agent code with new hyperparameters
def modify_agent_code(params):
    with open('NewMapAgents.py', 'r') as file:
        code = file.readlines()

    # Update the lines in the code where hyperparameters are set
    for i, line in enumerate(code):
        if line.strip().startswith('FOOD_REWARD'):
            code[i] = 'FOOD_REWARD = {}\n'.format(params["FOOD_REWARD"])
        elif line.strip().startswith('EMTPY_REWARD'):
            code[i] = 'EMTPY_REWARD = {}\n'.format(params["EMTPY_REWARD"])
        elif line.strip().startswith('GHOST_REWARD'):
            code[i] = 'GHOST_REWARD = {}\n'.format(params["GHOST_REWARD"])
        elif line.strip().startswith('GHOST_DANGER_ZONE'):
            code[i] = 'GHOST_DANGER_ZONE = {}\n'.format(params["GHOST_DANGER_ZONE"])
        elif line.strip().startswith('GAMMA'):
            code[i] = 'GAMMA = {}\n'.format(params["GAMMA"])
        elif line.strip().startswith('ITERATIONS'):
            code[i] = 'ITERATIONS = {}\n'.format(params["ITERATIONS"])
        elif line.strip().startswith('ISSMALL'):
            code[i] = 'ISSMALL = {}\n'.format(params["ISSMALL"])

    with open('SimpleMDPAgent.py', 'w') as file:
        file.writelines(code)

# Function to parse the output and extract the performance metrics
def parse_output(output):
    average_score = re.search(r'Average Score:\s+([\d\.\-]+)', output).group(1)
    win_rate = re.search(r'Win Rate:\s+(\d+)/\d+\s+\(([\d\.]+)\)', output).group(2)
    return float(average_score), float(win_rate)

# Run the hyperparameter tuning
best_score = float('-inf')
best_params = None
best_win_rate = 0
total_combinations = len(all_combinations)  # Get the total number of combinations

for index, combo in enumerate(all_combinations, start=1):
    # Create a dictionary of the current set of hyperparameters
    params = dict(zip(hyperparameter_grid.keys(), combo))
    
    # Print the current hyperparameter set and progress
    print("Testing combination {} of {}: {}".format(index, total_combinations, params))
    
    # Modify the agent code with the current set of hyperparameters
    modify_agent_code(params)
    
    # Run the Pac-Man game with the current hyperparameters
    process = subprocess.Popen(['python', 'pacman.py', '-q', '--pacman', 'NewMDPAgent', '--layout', 'smallGrid', '-n', '1000'],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    output, errors = process.communicate()

    # Parse the output for performance metrics
    average_score, win_rate = parse_output(output)
    
    # Print the performance metrics for the current hyperparameter set
    print("Combination {} resulted in an average score of {} and a win rate of {}.".format(index, average_score, win_rate))
    
    # Update the best hyperparameters based on the performance metric
    if average_score > best_score or (average_score == best_score and win_rate > best_win_rate):
        best_score = average_score
        best_win_rate = win_rate
        best_params = params

    # Print a separator for readability
    print('-' * 60)

# Function to run a single combination of hyperparameters
def run_simulation(params):
    modify_agent_code(params)
    process = subprocess.Popen(['python', 'pacman.py', '-q', '--pacman', 'NewMDPAgent', '--layout', 'smallGrid', '-n', '500'],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    output, errors = process.communicate()
    average_score, win_rate = parse_output(output)
    return params, average_score, win_rate

# Function to initialize the multiprocessing pool and run the simulations
def run_parallel_simulations(all_combinations):
    pool = multiprocessing.Pool(multiprocessing.cpu_count())  # Creates a Pool with cpu_count processes
    results = pool.map(run_simulation, all_combinations)  # Maps the run_simulation function to all combinations
    pool.close()  # Close the pool
    pool.join()  # Wait for all processes to finish
    return results

# Function to find the best parameters from the results
def find_best_parameters(results):
    best_score = float('-inf')
    best_params = None
    best_win_rate = 0

    for params, average_score, win_rate in results:
        if average_score > best_score or (average_score == best_score and win_rate > best_win_rate):
            best_score = average_score
            best_win_rate = win_rate
            best_params = params

    return best_params, best_score, best_win_rate

# Main function to run the hyperparameter tuning
if __name__ == '__main__':
    all_combinations = list(itertools.product(*hyperparameter_grid.values()))
    results = run_parallel_simulations(all_combinations)
    best_params, best_score, best_win_rate = find_best_parameters(results)
    
    print('Best Hyperparameters: ', best_params)
    print('Best Average Score:', best_score)
    print('Best Win Rate: ', best_win_rate)

