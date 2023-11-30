# coding: utf-8

import subprocess
import itertools
import re
import time

NUM_RUNS = 500
# Define the hyperparameter grid to search over
# hyperparameter_grid = {
#     'FOOD_REWARD': [20],
#     'EMTPY_REWARD': [-0.03, -0.05],
#     'GHOST_REWARD': [-1000, -1250],
#     'GAMMA': [0.90, 0.95],
#     # 'ITERATIONS': [50, 75, 100],
#     'ISSMALL': [False],
#     'PREDICTION_THRESHOLD': [0.1, 0.25, 0.3]
# }

# Generate all combinations of hyperparameters
# all_combinations = list(itertools.product(*hyperparameter_grid.values()))

combinations_to_test = [
    {'FOOD_REWARD': 20, 'ISSMALL': False, 'GHOST_REWARD': -1000, 'PREDICTION_THRESHOLD': 0.1, 'EMTPY_REWARD': -0.05, 'GAMMA': 0.95},
    {'FOOD_REWARD': 20, 'ISSMALL': False, 'GHOST_REWARD': -1000, 'PREDICTION_THRESHOLD': 0.25, 'EMTPY_REWARD': -0.05, 'GAMMA': 0.9},
    {'FOOD_REWARD': 20, 'ISSMALL': False, 'GHOST_REWARD': -1000, 'PREDICTION_THRESHOLD': 0.3, 'EMTPY_REWARD': -0.05, 'GAMMA': 0.95},
    {'FOOD_REWARD': 20, 'ISSMALL': False, 'GHOST_REWARD': -1250, 'PREDICTION_THRESHOLD': 0.1, 'EMTPY_REWARD': -0.05, 'GAMMA': 0.95},
    {'FOOD_REWARD': 20, 'ISSMALL': False, 'GHOST_REWARD': -1250, 'PREDICTION_THRESHOLD': 0.25, 'EMTPY_REWARD': -0.03, 'GAMMA': 0.9}
]

# combinations_to_test = [{'PREDICTION_THRESHOLD': 0.1},
#                         {'PREDICTION_THRESHOLD': 0.2},
#                         {'PREDICTION_THRESHOLD': 0.25},
#                         {'PREDICTION_THRESHOLD': 0.3}]

# Function to modify agent code with new hyperparameters
def modify_agent_code(params):
    with open('GhostPredictionMapAgents.py', 'r') as file:
        code = file.readlines()

    # Update the lines in the code where hyperparameters are set
    for i, line in enumerate(code):
        if line.strip().startswith('PREDICTION_THRESHOLD'):
            code[i] = 'PREDICTION_THRESHOLD = {}\n'.format(params["PREDICTION_THRESHOLD"])
        elif line.strip().startswith('FOOD_REWARD'):
            code[i] = 'FOOD_REWARD = {}\n'.format(params["FOOD_REWARD"])
        elif line.strip().startswith('EMTPY_REWARD'):
            code[i] = 'EMTPY_REWARD = {}\n'.format(params["EMTPY_REWARD"])
        elif line.strip().startswith('GHOST_REWARD'):
            code[i] = 'GHOST_REWARD = {}\n'.format(params["GHOST_REWARD"])
        # elif line.strip().startswith('GHOST_DANGER_ZONE'):
        #     code[i] = 'GHOST_DANGER_ZONE = {}\n'.format(params["GHOST_DANGER_ZONE"])
        elif line.strip().startswith('GAMMA'):
            code[i] = 'GAMMA = {}\n'.format(params["GAMMA"])
        # elif line.strip().startswith('ITERATIONS'):
        #     code[i] = 'ITERATIONS = {}\n'.format(params["ITERATIONS"])
        # elif line.strip().startswith('ISSMALL'):
        #     code[i] = 'ISSMALL = {}\n'.format(params["ISSMALL"])

    with open('GhostPredictionMapAgents.py', 'w') as file:
        file.writelines(code)

# Function to parse the output and extract the performance metrics
def parse_output(output):
    average_score = re.search(r'Average Score:\s+([\d\.\-]+)', output).group(1)
    win_rate = re.search(r'Win Rate:\s+(\d+)/\d+\s+\(([\d\.]+)\)', output).group(2)
    excellence_score = re.search(r'Excellence Score:\s+([\d\.\-]+)', output).group(1)
    return float(average_score), float(win_rate), float(excellence_score)

# Run the hyperparameter tuning
best_score = float('-inf')
best_params = None
best_win_rate = 0
total_combinations = len(combinations_to_test)  # Get the total number of combinations

# for index, combo in enumerate(all_combinations, start=1):

#     # Create a dictionary of the current set of hyperparameters
#     params = dict(zip(hyperparameter_grid.keys(), combo))
    
#     # Print the current hyperparameter set and progress
#     print("Testing combination {} of {}: {}".format(index, total_combinations, params))
    
#     # Modify the agent code with the current set of hyperparameters
#     modify_agent_code(params)
    
#     start_time = time.time()
#     # Run the Pac-Man game with the current hyperparameters
#     process = subprocess.Popen(['python', 'pacman.py', '-q', '--pacman', 'GhostPredictionAgent', '--layout', 'mediumClassic', '-n', str(NUM_RUNS)],
#                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
#     output, errors = process.communicate()
#     end_time = time.time()

#     # Parse the output for performance metrics
#     average_score, win_rate, excellence_score = parse_output(output)
    
#     # Print the performance metrics for the current hyperparameter set
#     print("Combination {}\naverage score of {}\nwin rate of {}\naverage time of {}s per match \nexcellence score {}".format(index, average_score, win_rate, round((end_time - start_time) / NUM_RUNS, 2), excellence_score))
    
#     # Update the best hyperparameters based on the performance metric
#     if average_score > best_score or (average_score == best_score and win_rate > best_win_rate):
#         best_score = average_score
#         best_win_rate = win_rate
#         best_params = params

#     # Print a separator for readability
#     print('-' * 60)


for index, combo in enumerate(combinations_to_test, start=1):

    # Create a dictionary of the current set of hyperparameters
    # params = dict(zip(combinations_to_test[0].keys(), combo))
    
    # Print the current hyperparameter set and progress
    print("Testing combination {} of {}: {}".format(index, total_combinations, combo))
    
    # Modify the agent code with the current set of hyperparameters
    modify_agent_code(combo)
    
    start_time = time.time()
    # Run the Pac-Man game with the current hyperparameters
    process = subprocess.Popen(['python', 'pacman.py', '-q', '--pacman', 'GhostPredictionAgent', '--layout', 'mediumClassic', '-n', str(NUM_RUNS)],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    output, errors = process.communicate()
    end_time = time.time()

    # Parse the output for performance metrics
    average_score, win_rate, excellence_score = parse_output(output)
    
    # Print the performance metrics for the current hyperparameter set
    print("Combination {}\naverage score of {}\nwin rate of {}\naverage time of {}s per match \nexcellence score {}".format(index, average_score, win_rate, round((end_time - start_time) / NUM_RUNS, 2), excellence_score))
    
    # Update the best hyperparameters based on the performance metric
    if average_score > best_score or (average_score == best_score and win_rate > best_win_rate):
        best_score = average_score
        best_win_rate = win_rate
        best_params = combo

    # Print a separator for readability
    print('-' * 60)


# Function to run a single combination of hyperparameters
# def run_simulation(params):
#     pass
#     # modify_agent_code(params)
#     # process = subprocess.Popen(['python', 'pacman.py', '-q', '--pacman', 'GhostPredictionAgent', '--layout', 'smallGrid', '-n', '5'],
#     #                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
#     # output, errors = process.communicate()
#     # average_score, win_rate = parse_output(output)
#     # return params, average_score, win_rate

# # Function to initialize the multiprocessing pool and run the simulations
# def run_parallel_simulations(all_combinations):
#     pool = multiprocessing.Pool(multiprocessing.cpu_count())  # Creates a Pool with cpu_count processes
#     results = pool.map(run_simulation, all_combinations)  # Maps the run_simulation function to all combinations
#     pool.close()  # Close the pool
#     pool.join()  # Wait for all processes to finish
#     return results

# Function to find the best parameters from the results
# def find_best_parameters(results):
#     best_score = float('-inf')
#     best_params = None
#     best_win_rate = 0

#     for params, average_score, win_rate in results:
#         if average_score > best_score or (average_score == best_score and win_rate > best_win_rate):
#             best_score = average_score
#             best_win_rate = win_rate
#             best_params = params

#     return best_params, best_score, best_win_rate

# Main function to run the hyperparameter tuning
# if __name__ == '__main__':
#     all_combinations = list(itertools.product(*hyperparameter_grid.values()))
#     results = run_parallel_simulations(all_combinations)
#     best_params, best_score, best_win_rate = find_best_parameters(results)
    
#     print('Best Hyperparameters: ', best_params)
#     print('Best Average Score:', best_score)
#     print('Best Win Rate: ', best_win_rate)

