# Dragonbane fight simulator

Small simple simulator to check if your party have a chance or not vs monsters

## Tested with
Works on linux with python3

## Installation
* Make sure you have Python3 installed
* Clone the repository to your computer
`git clone https://github.com/mattiasr/dragonbane_fight_simulator.git`

## Running the simulation
1. Make sure you have weapons, players and monsters added to `simulate.py`
![Configuration](configuration.png)
2. Set the number of times you like to run the simulation by edit `total_samples`
3. Run the simulation by executing `python3 simulate.py`

![Simulation](simulation.png)


## Example of 10k fights with the same party members and monsters    
```
======================================
Party: ['Mage', 'Thieve', 'Bard', 'Hunter']
Monsters: ['Monster#1', 'Monster#2', 'Monster#3', 'Monster#4', 'Boss#1']
Totalt:
34855 monstes killed (3.4855 killed/fight)
6971 monster whipes (0.6971 monster whipes/fight)
19975 players killed (1.9975 killed/fight)
3029 party whipes (0.3029 party whipes/fight)
10000 fights (9.989 rounds/fight)
```