# codinggame

This project is here to capitalize my code from the CodinGame challenges (https://www.codingame.com, Xavier_F.).

The code is developped in Python 3.

## Coders Strike Back (gold league, genetic algorithms)
*Reference : https://www.codingame.com/ide/puzzle/coders-strike-back*

This game is a course between pods (as the one in Star Wars). The pod is piloted with an optimization routine that the developper has to write. The routine is then called by the main game. The routine has to respect criteria set by the challenge (*see the challenge page for further information*).
 
The code for the first leagues (..., bronze and silver) is lost since the same code has evolved through each league. (I will try to do better for the others challenges).

Specific bibliography and readings:
  - Global approach: https://www.analyticsvidhya.com/blog/2017/07/introduction-to-genetic-algorithm/ 
  - A fast and elitist multiobjective genetic algorithm NSGA-II: https://www.iitk.ac.in/kangal/Deb_NSGA-II.pdf
  - Revisiting the NSGA-II Crowding-Distance computation: https://www.lri.fr/~hansen/proceedings/2013/GECCO/proceedings/p623.pdf

## Ghost in the cell (legend league, heuristics)
*Reference : https://www.codingame.com/multiplayer/bot-programming/ghost-in-the-cell*

This Galcon-inspired multiplayer puzzle takes place on a graph, in which you move your units (cyborg) and must capture some nodes (factories) to increase your production. You must strike a balance between your decision on long and short term .

E.g. Capture a close factory which produces only 1 cyborg OR capture a distant factory which produces 3 cyborgs.

## Hypersonic (legend league, decision tree, BFS, A*)
*Reference : https://www.codingame.com/multiplayer/bot-programming/hypersonic*

This multiplayer programming game plays out on a grid, where you have to destroy as many boxes as possible without dying. Try to simulate the upcoming turns to find out the best solution to play, and avoid explosions.

Specific bibliography and readings:
  - Integrating Backtracking with Beam Search: https://www.aaai.org/Papers/ICAPS/2005/ICAPS05-010.pdf

## Tron battle (legend league, Voronoi diagram, Articulation points, Tree of chambers, A*, Monte Carlo Tree Seach, Minimax)
*Reference : https://www.codingame.com/multiplayer/bot-programming/tron-battle*

*Repository for the local version : https://github.com/xavierfeltin/tron_battle*

Specific bibliography and readings:
  - Global approach: https://project.dke.maastrichtuniversity.nl/games/files/bsc/Denteuling-paper.pdf
  - Global approach: https://www.a1k0n.net/2010/03/04/google-ai-postmortem.html
  - Monte Carlo Tree Search: https://en.wikipedia.org/wiki/MCTS
  - Minimax: https://en.wikipedia.org/wiki/Minimax
  - Articulation points: https://en.wikipedia.org/wiki/Biconnected_component
  - Articulation points: http://www.geeksforgeeks.org/articulation-points-or-cut-vertices-in-a-graph/
  - Tree of chambers principle: https://github.com/ikhramts/TronBot (the readme only)
  - Voronoi diagram generation algorithm based on Delaunay Triangulation: https://pdfs.semanticscholar.org/7815/f5b005465d84f5af8534b4b8bea661131891.pdf 
  - End game detection in Tron: https://project.dke.maastrichtuniversity.nl/games/files/bsc/Kang_Bsc-paper.pdf
  
  
In this game your are a program driving the legendary tron light cycle. The light cycle moves in straight lines and only turns in 90° angles while leaving a solid light ribbon in its wake. Each cycle and associated ribbon features a different color.

Should a light cycle stop, hit a light ribbon or go off the game grid, it will be instantly deactivated. The last cycle in play wins the game.
