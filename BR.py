from random import choices, randint, shuffle
from typing import Callable
from LogSetup import CreateLogger
from logging import Logger
from json import dumps, load, dump
from datetime import datetime as dt
from os import makedirs, path
from time import sleep


logger: Logger = CreateLogger("BRLogger")


# Types used within the program to help with keeping track
ModeData = dict[str, str]
PlayerData = dict[str, int]
RoundInfo = dict[str, int]
ItemData = dict[str, str]
ShotData = dict[str, str]
LoadData = dict[str, str | dict[str, str]]
RoundData =  dict[str, list[ItemData | LoadData | ShotData ] | RoundInfo]


class BR():
    def __init__(self) -> None:
        self.__name: str = ""
        self.__gameData: dict[str, dict[str, PlayerData | ModeData | list[RoundData]]] = {}
        self.__players: list[Player] = [Player("addrStr"),Player("addrStr")]
        self.__Items: list[Callable] = [
            self.__Knife, 
            self.__Glass, 
            self.__Drugs,
            self.__Cuffs, 
            self.__Voddy  # Demo Reference
        ]
        self.__currentRound: int = 0
        self.__gun: Gun = Gun()
        self.__rounds:list[RoundInfo] = []

    def Connect(self, addrStr):
        if self.__players != 2:
            self.__players.append(Player(addrStr))
            return True
        return False 
    
    def Connections(self):
        return len(self.__players)
    
    def GetPlayer(self, addrStr):
        if addrStr == str(self.__players[0]):
            return self.__players[0]
        return self.__players[1]
    
    def PlayGame(self) -> dict[str, dict[str, ModeData | list[RoundData]]]:
        self.__currentPlayer: Player = self.__players[0]
        self.__SetGameMode(2) # Auto sets the game to Double or Nothing
        self.__EnterNames()
        print(self.__name)
        self.__gameData.update({self.__name: {"Mode": {"GameMode": "Double or Nothing"}}})
        logger.info(self.__gameData)
        self.__gameData[self.__name].update({"Game": []})
        for index, roundInfo in enumerate(self.__rounds):
            round: RoundData = {
                "Info": roundInfo,
                "History": []
            }
            self.__currentRound = index
            print("---")
            self.__SetRound()
            print("-")
            loadInfo: LoadData | None = self.__NewLoad()
            round["History"].append(loadInfo) if loadInfo is not None else None
            for player in self.__players:
                self.__currentState = self.__GetState()
                self.__currentPlayer = self.__GetOpponent()
            while not self.__IsRoundOver():
                choice:int = -1
                loadInfo: LoadData | None = self.__NewLoad()
                round["History"].append(loadInfo) if loadInfo is not None else None
                self.__currentState = self.__GetState()
                self.__ShowInfo()
                print("-")
                choice = self.__ActionMenu()
                print("-")
                if choice in [str(item.__name__)[2] for item in self.__Items]:
                    actionData, reward = self.__UseItem(choice)
                else:
                    impact , actionData, reward = self.__ShootSomeone(int(choice))
                round["History"].append(actionData) if actionData is not None else None
                self.__currentState = self.__GetState()
                self.__currentState.update({"Action" : actionData})
                print(end = "-")
                self.__Sleep(2)

                # If player shoots themselves with a blank, they get a second turn
                if choice in ("1","0"):
                    if impact != 0 or choice != "1":
                        print("-")
                        self.__NextTurn()
                    else:
                        print(" ")
                
                # Uncuff players and Uncrit gun
                self.__EndTurn()
            self.__gameData[self.__name]["Game"].append(round)
        self.__gameData[self.__name].update({"Players": {}})
        for player in self.__players:
            self.__gameData[self.__name]["Players"].update({player._GetName() : player._GetWins()})
        logger.info("Game Saved under '" + self.__SaveGame() + "'")
        return self.__gameData

    def __Sleep(self,secs):
        pass
    
    def __SetGameMode(self, choice) -> None:
        self.__doubleOrNothing: bool = True if choice == 2 else False
        if not self.__doubleOrNothing:
            self.__rounds:list[RoundInfo] = [
                {
                    "MaxHealth": 2,
                    "ItemsPerLoad": 0
                },
                {
                    "MaxHealth": 4,
                    "ItemsPerLoad": 2
                }, 
                {
                    "MaxHealth": 6,
                    "ItemsPerLoad": 4
                }
            ]
        else:
            for _ in range(3):
                self.__rounds.append({
                    "MaxHealth": randint(2,4),
                    "ItemsPerLoad": randint(1,4)
                })
        if self.__doubleOrNothing:
            self.__Items += [
                self.__Twist,
                self.__Spike,
                self.__8Ball,
                self.__Pluck
            ]
    
    def __SaveGame(self) -> str:
        if not path.exists('log'):
            makedirs('log')
        filename: str = dt.now().strftime(f'log/{self.__name.replace(" ","_")}-%d_%b_%y_%Hh_%Mm_%Ss_%fms.json') 
        with open(filename, 'w') as json_file:
            dump(self.__gameData, json_file, indent=4)
        return filename
        
    def __ActionMenu(self, plucking=False) -> str:
        print(self.__currentPlayer._GetName() + "'s Turn") if not plucking else None
        player = self.__currentPlayer if not plucking else self.__GetOpponent()
        items = list(set(eval(str(player._GetGallery()))))
        options: list[str] = player._GetGallery()._Options() + (["0","1"] if not plucking else [])
        print("Select an Action:")
        print(f"(1) Shoot Yourself ({self.__currentPlayer._GetName()})") if not plucking else None
        for item in items:
            print(f"({item[0]}) {item}")
        print(f"(0) Shoot Opponent ({self.__GetOpponent()._GetName()})") if not plucking else None
        while True:
            try:
                choice:str = self.__currentPlayer._GetInput()
                if choice not in options:
                    raise ValueError
                if choice == "P":
                    if plucking:
                        raise IndexError
                    elif self.__GetOpponent()._GetGallery()._Options() == [] or all(option == "P" for option in self.__GetOpponent()._GetGallery()._Options()):
                        raise LookupError
                return choice
            except ValueError:
                logger.error(f"{choice} is not an option. Please select a valid option {str(options)}")
            except IndexError:
                logger.error(f"You cannot pluck a pluck when plucking. Please select another option")
            except LookupError:
                logger.error(f"There isn't enough items to Pluck. Please select another option")
            
    def __EnterNames(self) -> None:
        while True:
            for index, player in enumerate(self.__players):
                player._SetName(input(f"Enter Player {index+1}'s Name: "))
            if self.__players[0]._GetName() != self.__players[1]._GetName():
                self.__name: str = f"{self.__players[0]._GetName()} vs. {self.__players[1]._GetName()}"
                return
            logger.warning("Both players need different names")

    def __SetRound(self) -> None:
        print(f"Round {self.__currentRound + 1}")
        logger.info(self.__rounds[self.__currentRound])
        for player in self.__players:
            player._SetHeath(
                self.__rounds[self.__currentRound]["MaxHealth"]
            )
            player._GetGallery()._Clear()

    def __NewLoad(self) -> LoadData | None:
        if not self.__gun._IsEmpty():
            return
        self.__gun._Load()
        print("The gun holds: ")
        self.__gun._ShowBulletsGraphically()
        self.__gun._Shuffle() 
        loadInfo: dict[str, str | dict[str, str]] = {
            "Type": "NewLoad",
            "Chamber": str(self.__gun),
            "Items": {
                self.__players[0]._GetName() : "",
                self.__players[1]._GetName() : ""
            }
        }
        for player in self.__players:
            items: int = self.__rounds[self.__currentRound]["ItemsPerLoad"]
            while items != 0 and not player._GetGallery()._IsFull():
                player._GetGallery()._Add(
                    choices(self.__Items)[0]
                )
                items -= 1
            loadInfo["Items"][player._GetName()] = str(player._GetGallery())
        logger.info(loadInfo) if loadInfo is not None else None
        self.__Sleep(2)
        return loadInfo
    
    def __ShowInfo(self) -> None:
        for player in self.__players:
            print(f"{player._GetName()}: {str(player._GetHealth())}/{self.__rounds[self.__currentRound]['MaxHealth']} hearts, {str(player._GetWins())} {'Wins' if player._GetWins() != 1 else 'Win'}")
            print(player._GetName() + "'s Items: " + str(player._GetGallery()))
            print(f"{player._GetName()} is Cuffed") if player._IsCuffed() else None
            print()
        print(f"Gun is{'' if self.__gun._GetCrit() else ' NOT'} dealing double damage")

    def __GetState(self) -> dict[str, dict[str, bool | dict[str, int] ] | dict[str, bool | list[Callable] | int ]]:
        stateInfo = {}
        for player in self.__players:
            stateInfo.update({
                "Player" if player == self.__currentPlayer else "Opponent": {
                    "Hearts": player._GetHealth(),
                    "Items": eval(str(player._GetGallery())),
                    "Cuffed": player._IsCuffed()
                }
            })
        stateInfo.update({"Gun": {
            "Bullets" : self.__gun._CountBullets(),
            "Crit": self.__gun._GetCrit()
        }})
        return stateInfo
                
    def __IsRoundOver(self) -> bool:
        roundOver: bool = self.__GetOpponent()._GetHealth() == 0 or self.__currentPlayer._GetHealth() == 0
        if self.__GetOpponent()._GetHealth() == 0:
            self.__currentPlayer._AddWin()
        elif self.__currentPlayer._GetHealth() == 0:
            self.__GetOpponent()._AddWin()
        if roundOver:
            self.__gun._Empty()
        return roundOver
    
    def __NextTurn(self) -> None:
        if not self.__GetOpponent()._IsCuffed():
            self.__currentPlayer = self.__GetOpponent()
    
    def __EndTurn(self) -> None:
        self.__gun._SetCrit(False)
        if self.__GetOpponent()._IsCuffed():
            self.__GetOpponent()._SetCuffed(False)
    
    def __GetOpponent(self) -> "Player":
        return [player for player in self.__players if player != self.__currentPlayer][0]

    def __Knife(self) -> None:
        self.__gun._SetCrit(True)
        print("The Gun is Crit")

    def __Glass(self) -> None:
        print("This bullet is", end=": ")
        if self.__gun._Peek():
            print("LIVE")
        else:
            print("DEAD")

    def __Drugs(self) -> None:
        self.__currentPlayer._ModifyHealth(1, self.__rounds[self.__currentRound]['MaxHealth'])
        print(self.__currentPlayer._GetName() + "'s health = " + str(self.__currentPlayer._GetHealth()))

    def __Cuffs(self) -> None:
        self.__GetOpponent()._SetCuffed(True)
        print(self.__GetOpponent()._GetName() + " has been handcuffed")

    def __Voddy(self) -> None:
        print("The bullet was", end=": ")
        if self.__gun._Rack():
            print("LIVE")
        else:
            print("DEAD")
    
    def __Twist(self) -> None:
        print("The bullet has been Twisted")
        self.__gun._Twist()
    
    def __Spike(self) -> None:
        spike = 2 if randint(0, 99) < 40 else -1
        self.__currentPlayer._ModifyHealth(spike, self.__rounds[self.__currentRound]['MaxHealth'])
        print(self.__currentPlayer._GetName() + "'s health = " + str(self.__currentPlayer._GetHealth()))
    
    def __8Ball(self) -> None:
        bullet = self.__gun._RandPeek()
        print(f"Bullet {bullet[0]} is", end=": ")
        if bullet[1]:
            print("LIVE")
        else:
            print("DEAD")

    def __Pluck(self) -> tuple[ItemData | None, int]:
        choice = self.__ActionMenu(plucking=True)
        print("-")
        actionData, reward = self.__UseItem(choice, plucked=True)
        return (actionData, reward)
        
    def __UseItem(self, choice:str, plucked=False) -> tuple[ItemData | None, int]:
        player = self.__currentPlayer if not plucked else self.__GetOpponent()
        item: Callable | None = player._GetGallery()._Use(choice)
        data = {}
        reward = 0
        if item is not None:
            if item.__name__[2:] != "Pluck":
                data: dict[str, str] = {
                    "Type": f"{'Pluck:' if plucked else ''}{item.__name__[2:]}",
                    "Player": self.__currentPlayer._GetName()
                }
                logger.info(data)
            pluckData = item()
            reward = -1
            if pluckData != None:
                data = pluckData[0]
                reward += pluckData[1]
        return (data, reward)
    
    def __ShootSomeone(self, choice:int) -> tuple[int, ShotData | None, int]:
        impact:int = self.__gun._Shoot()
        player: Player = self.__currentPlayer if choice == 1 else self.__GetOpponent()
        player._ModifyHealth(
            -impact, 
            self.__rounds[self.__currentRound]["MaxHealth"]
        )
        data: dict[str, str] = {
            "Type": "Shot",
            "Shooter": self.__currentPlayer._GetName(),
            "Victim": player._GetName()
        }
        print(self.__currentPlayer._GetName() + " shot " + player._GetName())
        print("The bullet was:",end = " ")
        print("LIVE" if impact else "DEAD") 
        logger.info(data)
        reward: int =  2 if (choice == 1 and impact == 0) else ((-impact * 5) if choice == 1 else (impact * 5))
        return (impact, data, reward)
        

class Player:
    def __init__(self, addrStr) -> None:
        self._name: str = ""
        self._addrSr: str = addrStr
        self.__health: int = 0
        self.__gallery: Gallery = Gallery()
        self.__cuffed: bool = False
        self.__wins: int = 0
    
    def _SetName(self, name:str) -> None:
        self._name = name

    def _GetName(self) -> str:
        return self._name
    
    def _SetHeath(self, health: int) -> None:
        self.__health = health
    
    def _GetHealth(self) -> int:
        return self.__health
    
    def _ModifyHealth(self, health, maxHealth) -> None:
        self.__health += health
        if self.__health >  maxHealth:
            self.__health = maxHealth
        elif self.__health < 0:
            self.__health = 0
    
    def _GetGallery(self) -> "Gallery":
        return self.__gallery
    
    def _IsCuffed(self) -> bool:
        return self.__cuffed
    
    def _SetCuffed(self, cuffed:bool) -> None:
        self.__cuffed = cuffed
    
    def _AddWin(self) -> None:
        self.__wins += 1
    
    def _GetWins(self) -> int:
        return self.__wins

    def _GetInput(self) -> str:
        return input().upper()

    def __str__(self) -> str:
        return self._addrSr

class Gun:
    def __init__(self) -> None:
        self.__chamber:list[bool] = []
        self.__crit: bool = False
    
    def _Load(self) -> None:
        self.__chamber = [True, False]
        for bullet in range(randint(0,6)):
            self.__chamber.append(
                choices([True, False])[0]
            )
        
    def _Shuffle(self) -> None:
        for _ in range(randint(0,100)):
            shuffle(self.__chamber)
    
    def _Peek(self) -> bool:
        return self.__chamber[0]
    
    def _Rack(self) -> bool:
        return self.__chamber.pop(0)
    
    def _Shoot(self) -> int:
        impact: int = 2 if self.__crit else 1
        if self.__chamber.pop(0):
            return impact
        return 0
    
    def _IsEmpty(self) -> bool:
        if len(self.__chamber) == 0:
            return True
        return False
    
    def _ShowBulletsGraphically(self) -> None:
        m:str = "     ---- "
        for bullet in self.__chamber:
            m += "\n    |"
            if bullet:
                m += "LIVE"
            else:
                 m += "DEAD"
            m += "|\n     ---- "
        print(m)

    def __str__(self) -> str:
        return str(self.__chamber)
    
    def _SetCrit(self, crit:bool) -> None:
        self.__crit = crit
    
    def _GetCrit(self) -> bool:
        return self.__crit

    def _Empty(self) -> None:
        self.__chamber = []

    def _CountBullets(self) -> dict[str, int]:
        liveCount: int = len([bullet for bullet in self.__chamber if bullet])
        return {
            "Live": liveCount,
            "Dead": len(self.__chamber) - liveCount
        }
    
    def _Twist(self):
        self.__chamber[0] = not self.__chamber[0]
    
    def _RandPeek(self) -> tuple[int, bool]:
        bullet = randint(0, len(self.__chamber) - 1)
        return (bullet + 1, self.__chamber[bullet])

class Gallery:
    def __init__(self) -> None:
        self.__items: list[Callable] = []
    
    def __len__(self) -> int:
        return len(self.__items)

    def _Clear(self) -> None:
        self.__items = []

    def _Use(self, choice:str) -> Callable | None:
        try:
            index: int = self._Options().index(choice)
        except ValueError:
            return None
        return self.__items.pop(index)
    
    def _Add(self, item:Callable) -> None:
        self.__items.append(item)

    def _IsFull(self) -> bool:
        if len(self.__items) == 8:
            return True
        return False
    
    def __str__(self) -> str:
        return str([item.__name__[2:] for item in self.__items])
    
    def  __repr__(self) -> list:
        string: str = str(self.__items).strip('[]')
        items: list[str] = string.split(', ')
        return [item.strip('\'"') for item in items if item]

    def _Options(self) -> list[str]:
        return [item[0] for item in eval(str(self))]

if __name__ == "__main__":
    try:
        BR().PlayGame()
    except Exception as e:
        # Log the exception
        import traceback
        logger.fatal(traceback.format_exc())
        print("An unexpected error occurred. Please check the BR.log file for details.")
