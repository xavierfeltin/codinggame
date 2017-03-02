import json
import numpy as np
import matplotlib.pyplot as plt

class Data:
    def __init__(self):
        self.turn = 0
        self.best_score = 0
        self.nb_generation = 0
        self.scores = []

class Game:
    def __init__(self):
        self.nb_ckpt = 0
        self.nb_moves = 0
        self.nb_population = 0
        self.nb_tournament = 0
        self.data = []

    def set_from_json(self, json):
        self.nb_ckpt = json['game']['configuration']['nb_ckpt']
        self.nb_moves = json['game']['configuration']['nb_moves']
        self.nb_population = json['game']['configuration']['nb_population']
        self.nb_tournament = json['game']['configuration']['nb_tournament']

        for turn in sorted(json['game']['data'].keys(), key=lambda x: float(x)):
            data = Data()
            data.turn = json['game']['data'][turn]['turn']
            data.best_score = json['game']['data'][turn]['best_score']
            data.nb_generation = json['game']['data'][turn]['nb_generation']

            for score in json['game']['data'][turn]['scores']:
                checked = (json['game']['data'][turn]['checked_pod1'] + json['game']['data'][turn]['checked_pod2']) * 50000
                #data.scores.append(score-checked)
                data.scores.append(score)

            self.add_data(data)

    def add_data(self, new_data):
        self.data.append(new_data)

def parse_json(path):
    with open(path) as data_file:
        parsed_json = json.load(data_file)

    game = Game()
    game.set_from_json(parsed_json)
    return game

def visualize(game, turn):
    data_1 = game.data[turn]

    plt.title('Evolution of highest score at each new generation (turn '+ str(turn+1) + ')')
    plt.xlabel('Generation')
    plt.ylabel('Score')
    plt.plot(list(range(1,data_1.nb_generation+2)), data_1.scores)
    plt.show()

def visualize_improvement_by_turn(game):

    improvements = []
    turns = []
    for data in game.data:
        improvements.append(((data.best_score - data.scores[0])/abs(data.best_score))*100.0)
        turns.append(data.turn)

    plt.title('Improvement between first and last score at each turn')
    plt.xlabel('Turns')
    plt.ylabel('Improvement')

    plt.bar(turns,improvements)
    plt.show()

def visualize_best_scores(game):

    improvements = []
    turns = []
    for data in game.data:
        improvements.append(((data.best_score - data.scores[0])/abs(data.best_score))*100.0)
        turns.append(data.turn)

    plt.title('Improvement between first and last score at each turn')
    plt.xlabel('Turns')
    plt.ylabel('Improvement')

    plt.bar(turns,improvements)
    plt.show()

def print_best_scores(game):
    improvements = []
    turns = []
    for data in game.data:
        improvements.append(((data.best_score - data.scores[0]) / abs(data.best_score)) * 100.0)
        turns.append(data.turn)

    for i in range(len(improvements)):
        print('turn ' + str(turns[i]) + ', improvements rate ' + str(improvements[i]))

def visualize_min_max_by_turn(game):

    max_scores = []
    min_scores = []
    turns = []
    for data in game.data:
        min_scores.append(min(data.scores))
        max_scores.append(max(data.scores))
        turns.append(data.turn)

    plt.title('Min / Max scores function of game turns')
    plt.xlabel('Turns')
    plt.ylabel('Scores')
    plt.xlim(0, len(turns))
    plt.scatter(turns, min_scores)
    plt.scatter(turns, max_scores)
    plt.show()

def visualize_convergence(game):

    indexes = []
    nb_generations = []
    turns = []
    for data in game.data:
        try:
            indexes.append(data.scores.index(data.best_score))
        except(ValueError):
            indexes.append(-5)
        nb_generations.append(data.nb_generation)
        turns.append(data.turn)

    plt.title('Number of generations to reach the best score')
    plt.xlabel('Turns')
    plt.ylabel('Generation')

    plt.plot(turns,indexes)
    plt.plot(turns, nb_generations)
    plt.show()

if __name__ == '__main__':
    game = parse_json('resources/json_coder_strike_back_2.json')
    game2 = parse_json('resources/json_coder_strike_back_3.json')
    game3 = parse_json('resources/json_coder_strike_back_4.json')
    visualize_convergence(game)
    visualize_convergence(game2)
    visualize_convergence(game3)