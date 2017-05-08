
game = Game()
simu = Game()

# game loop
while True:
    game.reset()
    simu.reset()

    for i in range(NB_SIMU_TURN):
        simu.simulate_turn()

    game.solve_turn(simu)