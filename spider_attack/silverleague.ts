// Game constants
const moveHeroDistance = 800; // Max distance done by a hero to a target point
const spiderBaseDetectionDistance = 5000; // Distance at which a monster detect a base
const moveSpiderDistance = 400; // Distance on a straight line done by a monster
const damageDoneByHero = 2; // Damage done by one hero on monster
const heroAttackRadius = 800; // Attack radius of a hero
const fogHeroVisibility = 2200; // Hero visibility of other units in the fog
const fogBaseVisibility = 6000; // Base visibility of other units in the fog
const attackBaseMonsterDistance = 300; // Distance spider attacking base if not killed
const manaCostPerHero = 10; // Mana could be spent by 1 hero
const windRadius = 1280; // Radius of spell Wind
const windStrength = 2200; // Force of wind applied to opponents and spiders
const controlRadius = 2200; // radius of control spell
const shieldRadius = 2200; // radius of control shield
const xMax = 17630;
const yMax = 9000;

class Entity {
    TYPE_SPIDER = 0;
    TYPE_MY_HERO = 1;
    TYPE_ENEMY = 2;
    MY_BASE = 1;
    ENEMY_BASE = 2;
    distanceFromMyBase: number;
    distanceFromEnemyBase: number;
    controlledByMe: boolean;
    windedByMe: boolean;
    targetByMe: boolean;
    constructor(
      public id: number,
      public type: number,
      public x: number,
      public y: number,
      public shieldLife: number,
      public isControlled: number,
      public health: number,
      public vx: number,
      public vy: number,
      public nearBase: number,
      public threatFor: number,
      private me: Player,
      private enemy: Player
    ) {
        this.distanceFromMyBase = this.getDistanceFrom(
            this.me.basePosX,
            this.me.basePosY
        );

        this.distanceFromEnemyBase = this.getDistanceFrom(
            this.enemy.basePosX,
            this.enemy.basePosY
        );

        this.controlledByMe = false;
        this.windedByMe = false;
        this.targetByMe = false;
    }
    isDangerousForMyBase = (): boolean => {
      return this.threatFor === this.MY_BASE;
    };
    isCriticalForMyBase = (): boolean => {
        return this.threatFor === this.MY_BASE && this.nearBase === 1;
    };
    isDangerousForEnemyBase = (): boolean => {
        return this.threatFor === this.ENEMY_BASE;
    };
    isCriticalForEnemyBase = (): boolean => {
        return this.threatFor === this.ENEMY_BASE && this.nearBase === 1;
    };
    isMyHero = (): boolean => {
        return this.type === this.TYPE_MY_HERO;
    }
    isSpider = (): boolean => {
        return this.type === this.TYPE_SPIDER;
    }
    isEnemy = (): boolean => {
        return this.type === this.TYPE_ENEMY;
    }
    isShielded = (): boolean => {
        return this.shieldLife > 0;
    }
    isBeingControlled = (): boolean => {
        return this.isControlled === 1;
    }
    isControlledByMe = (): boolean => {
        return this.controlledByMe;
    }
    isWindedByMe = (): boolean => {
        return this.windedByMe;
    }
    isTargetedByMe = (): boolean => {
        return this.targetByMe;
    }
    getDistanceFrom = (x: number, y: number): number => {
      return Math.sqrt(Math.pow(x - this.x, 2) + Math.pow(y - this.y, 2));
    };
}

class Player {
    constructor(
        public basePosX: number,
        public basePosY: number,
        public baseHealth: number,
        public mana: number
    ) {}
    setHealth = (value: number) => {
        this.baseHealth = value;
    };
    setMana = (value: number) => {
        this.mana = value;
    };
    canCast = (coeff: number = 1): boolean => {
        return this.mana >= (10 * coeff);
    };
}

class Game {
    ACTION_WAIT = "WAIT";
    ACTION_MOVE = "MOVE";
    ACTION_SPELL = "SPELL";
    SPELL_WIND = "WIND";
    SPELL_CONTROL = "CONTROL";
    SPELL_SHIELD = "SHIELD";

    me: Player;
    enemy: Player;
    myHeroes: Entity[];
    enemies: Entity[];
    spiders: Entity[];

    constructor(baseX: number, baseY: number, private heroes: number) {
      this.me = new Player(baseX, baseY, 3, 0);
      this.enemy = new Player(
        baseX === 0 ? 17630 : 0,
        baseY === 0 ? 9000 : 0,
        3,
        0
      );
      this.myHeroes = [];
      this.enemies = [];
      this.spiders = [];
    }

    newTurn = (
      health: number,
      mana: number,
      enemyHealth: number,
      enemyMana: number
    ) => {
      this.me.setHealth(health);
      this.me.setMana(mana);
      this.enemy.setHealth(enemyHealth);
      this.enemy.setMana(enemyMana);
      this.myHeroes = [];
      this.enemies = [];
      this.spiders = [];
    };

    addEntity = (entity: Entity) => {
        if (entity.isSpider()) {
            this.spiders.push(entity);
        }
        else if (entity.isEnemy()) {
            this.enemies.push(entity);
        }
        else {
            this.myHeroes.push(entity);
        }
    };

    moveAction = (x: number, y: number, comment: string): string => {
        return this.ACTION_MOVE + " " + Math.round(x) + " " + Math.round(y) + " " + comment;
    }

     spellWindAction = (entity: Entity, destX: number, destY: number, comment: string): string => {
        entity.windedByMe = true;
        this.me.mana = this.me.mana - 10;
        return this.ACTION_SPELL + " " + this.SPELL_WIND + " " + destX + " " + destY + " " + comment;
    }

    spellControlAction = (entity: Entity, destX: number, destY: number, comment: string): string => {
        entity.controlledByMe = true;
        this.me.mana = this.me.mana - 10;
        return this.ACTION_SPELL + " " + this.SPELL_CONTROL + " " + entity.id + " " + destX + " " + destY + " " + comment;
    }

    spellShieldAction = (id: number, comment: string): string => {
        this.me.mana = this.me.mana - 10;
        return this.ACTION_SPELL + " " + this.SPELL_SHIELD + " " + id + " " + comment;
    }

    waitAction = (comment: string): string => {
        return this.ACTION_WAIT + " " + comment;
    }

    solveAgressiveBehavior = (heroIdx: number, actions: string[]): string => {
        const hero = this.myHeroes[heroIdx];

        // Handle enemies
        const enemiesNearMe = this.enemies.filter((enemy) => {
            return enemy.getDistanceFrom(game.enemy.basePosX, game.enemy.basePosY) <= fogBaseVisibility;
        }).sort((e1, e2): number =>  e1.getDistanceFrom(hero.x, hero.y) < e2.getDistanceFrom(hero.x, hero.y) ? -1 : 1);

        const spidersNearEnemy = this.spiders.filter((spider) => {
            return spider.distanceFromEnemyBase <= fogBaseVisibility;
        }).sort((s1, s2): number =>  s1.getDistanceFrom(hero.x, hero.y) < s2.getDistanceFrom(hero.x, hero.y) ? -1 : 1);

        const spidersFurtherEnemy = this.spiders.filter((spider) => {
            return fogBaseVisibility < spider.distanceFromEnemyBase && spider.distanceFromEnemyBase <= (fogBaseVisibility + fogHeroVisibility);
        }).sort((s1, s2): number =>  s1.distanceFromEnemyBase < s2.distanceFromEnemyBase ? -1 : 1);


        const spidersInEnemyBase = this.spiders.filter((spider) => {
            return spider.isCriticalForEnemyBase();
        }).sort((s1, s2): number =>  s1.getDistanceFrom(hero.x, hero.y) < s2.getDistanceFrom(hero.x, hero.y) ? -1 : 1);

        if (enemiesNearMe.length > 0) {
            const enemy = enemiesNearMe[0];
            if (game.me.canCast() && game.enemy.canCast() && !hero.isShielded()
                && enemy.getDistanceFrom(hero.x, hero.y) <= controlRadius && spidersInEnemyBase.length > 0) {
                return this.spellShieldAction(hero.id, "Protect");
            }
        }

        // Try to push further more spiders in enemy base
        if (spidersNearEnemy.length > 0) {
            const closestSpider = spidersNearEnemy[0];
            const distanceFromHero = closestSpider.getDistanceFrom(hero.x, hero.y);
            if (game.me.canCast() && !closestSpider.isShielded() && !closestSpider.isWindedByMe()
                && distanceFromHero <= windRadius && closestSpider.health > 12) {
                return this.spellWindAction(closestSpider, game.enemy.basePosX, game.enemy.basePosY, "Push " + closestSpider.id);
            }
            else if (game.me.canCast() && (hero.isShielded() || enemiesNearMe.length == 0 || !game.enemy.canCast())
                    && closestSpider.isCriticalForEnemyBase() && !closestSpider.isShielded()
                    && !closestSpider.isWindedByMe() && distanceFromHero <= windRadius) {
                return this.spellWindAction(closestSpider, game.enemy.basePosX, game.enemy.basePosY, "Push more " + closestSpider.id);
            }
            else if (game.me.canCast() && (closestSpider.isDangerousForEnemyBase() || closestSpider.isCriticalForEnemyBase())
                && !closestSpider.isShielded() && !closestSpider.isWindedByMe() && !closestSpider.isBeingControlled() && distanceFromHero <= shieldRadius && closestSpider.health >= 15) {
                return this.spellShieldAction(closestSpider.id, "Boost " + closestSpider.id);
            }
            /*
            else if (game.me.canCast() && distanceFromHero > windRadius) {
                return this.moveAction(closestSpider.x + closestSpider.vx, closestSpider.y + closestSpider.vy, "Move to " + closestSpider.id);
            }
            */
        }

        if (spidersFurtherEnemy.length > 0) {
            const closestSpider = spidersFurtherEnemy[0];
            const distanceFromHero = closestSpider.getDistanceFrom(hero.x, hero.y);
            const spiderIsInoffensiveForEnnemy = !closestSpider.isDangerousForEnemyBase() && !closestSpider.isCriticalForEnemyBase();
            if (!closestSpider.isWindedByMe() && !closestSpider.isControlledByMe()
                && (closestSpider.health < 15 || !game.me.canCast()) && closestSpider.distanceFromEnemyBase > spiderBaseDetectionDistance) {
                return this.moveAction(closestSpider.x, closestSpider.y, "Mana from " + closestSpider.id);
            }
            else if (game.me.canCast() && spiderIsInoffensiveForEnnemy && !closestSpider.isShielded()
                    && !closestSpider.isWindedByMe() && distanceFromHero <= windRadius
                    && closestSpider.distanceFromEnemyBase < (spiderBaseDetectionDistance + windStrength)
                    && enemiesNearMe.length == 0) {
                return this.spellWindAction(closestSpider, game.enemy.basePosX, game.enemy.basePosY, "Push " + closestSpider.id);
            }
            else if (game.me.canCast() && spiderIsInoffensiveForEnnemy
                    && !closestSpider.isShielded() && !closestSpider.isWindedByMe() && distanceFromHero <= controlRadius && closestSpider.health >= 15) {
                return this.spellControlAction(closestSpider, game.enemy.basePosX, game.enemy.basePosY, "Control " + closestSpider.id);
            }
            else if (spiderIsInoffensiveForEnnemy && closestSpider.distanceFromEnemyBase > spiderBaseDetectionDistance) {
                // Get some mana while waiting something better do
                return this.moveAction(closestSpider.x, closestSpider.y, "Move to " + closestSpider.id);
            }
        }

        // Try to take out enemies from base
        if (enemiesNearMe.length > 0) {
            console.error("mana: " + game.me.mana + ", enemies: " + enemiesNearMe.length + ", spiders: " + spidersNearEnemy.length);

            enemiesNearMe.sort((e1, e2): number =>  e1.getDistanceFrom(game.enemy.basePosX, game.enemy.basePosY) < e2.getDistanceFrom(game.enemy.basePosX, game.enemy.basePosY) ? -1 : 1);
            const enemy = enemiesNearMe[0];
            const distanceFromHero = enemy.getDistanceFrom(hero.x, hero.y);
            if (game.me.canCast() && !enemy.isShielded() && distanceFromHero <= controlRadius && spidersInEnemyBase.length > 0 && enemy.distanceFromEnemyBase < spiderBaseDetectionDistance) {
                return this.spellControlAction(enemy, game.me.basePosX, game.me.basePosY, "Take out " + enemy.id);
            }
            else if (game.me.canCast() && !enemy.isShielded() && spidersNearEnemy.length > 0) {
                return this.moveAction(enemy.x, enemy.y, "Move to " + enemy.id);
            }
        }

        if (spidersNearEnemy.length > 0) {
            const closestSpider = spidersNearEnemy[0];
            const distanceFromHero = closestSpider.getDistanceFrom(hero.x, hero.y);
            if (game.me.canCast() && distanceFromHero > windRadius) {
                return this.moveAction(closestSpider.x, closestSpider.y, "Move to " + closestSpider.id);
            }
        }

        // Otherwise back to default positions
        if (this.me.basePosX === 0) {
            return this.moveAction(neutralPositions[heroIdx][0], neutralPositions[heroIdx][1], "Neutral Position");
        }
        else {
            return this.moveAction(xMax - neutralPositions[heroIdx][0], yMax - neutralPositions[heroIdx][1], "Neutral Position");
        }
    }

    solveDefensiveBehavior = (heroIdx: number, actions: string[]): string => {
        const hero = this.myHeroes[heroIdx];
        const otherHeroIdx = 1 - heroIdx;
        const otherHero = this.myHeroes[otherHeroIdx];

        const enemiesNearMe = this.enemies.filter((enemy) => {
            return enemy.getDistanceFrom(game.me.basePosX, game.me.basePosY) <= (fogBaseVisibility + fogHeroVisibility);
        }).sort((e1, e2): number =>  e1.getDistanceFrom(hero.x, hero.y) < e2.getDistanceFrom(hero.x, hero.y) ? -1 : 1);

        const enemiesNearBase = this.enemies.filter((enemy) => {
            return enemy.getDistanceFrom(game.me.basePosX, game.me.basePosY) <= (fogBaseVisibility + 0.5 * fogHeroVisibility) && !enemy.isTargetedByMe();
        });

        const spidersNearBase = this.spiders.filter((spider) => {
            return spider.distanceFromMyBase <= (fogBaseVisibility + (1.0 * fogHeroVisibility)) && (!spider.isTargetedByMe() || enemiesNearBase.length > 0);
        }).sort((s1, s2): number =>  {
            if (s1.isCriticalForMyBase() && s2.isCriticalForMyBase()) {
                /*
                if ((s1.distanceFromMyBase < (4 * moveSpiderDistance) || s2.distanceFromMyBase < (4 * moveSpiderDistance))) {
                    // Spider is really close to hit the base. Should be priorized over closest spider
                    if (s1.distanceFromMyBase < s2.distanceFromMyBase) {
                        return -1;
                    }
                    else if (s2.distanceFromMyBase < s1.distanceFromMyBase) {
                        return 1;
                    }
                }
                return s1.getDistanceFrom(hero.x, hero.y) < s2.getDistanceFrom(hero.x, hero.y) ? -1 : 1;
                */
                return s1.distanceFromMyBase < s2.distanceFromMyBase ? -1 : 1;
            }
            else if (s1.isCriticalForMyBase() && !s2.isCriticalForMyBase()) {
                return -1;
            }
            else if (s2.isCriticalForMyBase() && !s1.isCriticalForMyBase()) {
                return 1;
            }
            else if (s1.isDangerousForMyBase() && s2.isDangerousForMyBase()) {
                return s1.getDistanceFrom(hero.x, hero.y) < s2.getDistanceFrom(hero.x, hero.y) ? -1 : 1;
            }
            else if (s1.isDangerousForMyBase() && !s2.isDangerousForMyBase()) {
                return -1;
            }
            else if (!s1.isDangerousForMyBase() && s2.isDangerousForMyBase()) {
                return 1;
            }
            return 0;
        });

        const spidersInBase = this.spiders.filter((spider) => {
            return spider.isCriticalForMyBase();
        })

        console.error("["+heroIdx+"] " + "spiders near base: " + spidersNearBase.map((s) => {return s.id + "-" + s.isTargetedByMe()}).join(", "));
        console.error("["+heroIdx+"] " + "enemies near me: " + enemiesNearMe.map((e) => e.id).join(", "));

        // Handle enemies
        if (enemiesNearBase.length > 0) {
            const enemy = enemiesNearBase[0];
            if (game.me.canCast() && game.enemy.canCast() && enemy.getDistanceFrom(hero.x, hero.y) <= 0.9 * windRadius
                    && !enemy.isShielded() && !enemy.isControlledByMe() && !enemy.isWindedByMe()) {
                return this.spellWindAction(enemy, game.enemy.basePosX, game.enemy.basePosY, "Repel " + enemy.id);
            }
            /*
            else if (game.me.canCast() && game.enemy.canCast() && !enemy.isControlledByMe() && !enemy.isWindedByMe() && !enemy.isTargetedByMe()) {
                enemy.targetByMe = true;
                return this.moveAction(enemy.x, enemy.y, "Move to " + enemy.id);
            }
            */
        }

        // Handle controlled otherHeros
        if (game.me.canCast() && otherHero.isBeingControlled() && !hero.isShielded() && hero.getDistanceFrom(otherHero.x, otherHero.y) <= shieldRadius) {
            return this.spellShieldAction(otherHero.id, "Protect " + otherHero.id);
        }
        /*
        else if (game.me.canCast() && otherHero.isBeingControlled()) {
            return this.moveAction(otherHero.x, otherHero.y, "Go protect " + hero.id);
        }
        */

        // Handle myself
        if (enemiesNearMe.length > 0) {
            const enemy = enemiesNearMe[0];
            if (game.me.canCast() && game.enemy.canCast() && !hero.isShielded()
            && enemy.getDistanceFrom(hero.x, hero.y) <= controlRadius && spidersNearBase.length > 0) {
                return this.spellShieldAction(hero.id, "Protect me");
            }
        }

        // Handle spiders
       if (spidersNearBase.length > 0) {
            const closestSpider = spidersNearBase[0];
            const distanceFromHero = closestSpider.getDistanceFrom(hero.x, hero.y);
            const distanceFromOtherHero = closestSpider.getDistanceFrom(otherHero.x, otherHero.y);
            const isClosestHero = (distanceFromHero <= distanceFromOtherHero) || (actions[otherHeroIdx] !== ""); //If other hero already doing an action, I am the closest hero
            const isSpiderHealthLowEnough = (closestSpider.health * 0.5) <= Math.floor((closestSpider.distanceFromMyBase - attackBaseMonsterDistance)/ moveSpiderDistance);

            let log = "["+ heroIdx + "]" + " Closest spider " + closestSpider.id + " targeted: " + closestSpider.isTargetedByMe();
            log += ", " + "I'm closest : " + isClosestHero;
            console.error(log);

            if (game.me.canCast() && !closestSpider.isShielded() && !closestSpider.isControlledByMe() && !closestSpider.isWindedByMe()
                    && distanceFromHero <= windRadius && !isSpiderHealthLowEnough && closestSpider.isCriticalForMyBase()) {
                return this.spellWindAction(closestSpider, game.enemy.basePosX, game.enemy.basePosY, "Repel " + closestSpider.id);
            }
            else if (game.me.canCast() && !closestSpider.isShielded() && !closestSpider.isControlledByMe() && !closestSpider.isWindedByMe()
                && distanceFromHero <= controlRadius && !isSpiderHealthLowEnough && closestSpider.isCriticalForMyBase()
                && closestSpider.distanceFromMyBase < (4 * moveSpiderDistance)) {
                return this.spellControlAction(closestSpider, game.enemy.basePosX, game.enemy.basePosY, "Urgent Repel " + closestSpider.id);
            }
            else if (game.me.canCast(2) && !closestSpider.isShielded()
                    && !closestSpider.isDangerousForEnemyBase() && !closestSpider.isCriticalForMyBase()
                    && !closestSpider.isWindedByMe() && closestSpider.health >= 14 && distanceFromHero <= controlRadius) {
                return this.spellControlAction(closestSpider, game.enemy.basePosX, game.enemy.basePosY, "Control " + closestSpider.id);
            }
            // Avoid putting several heroes on a spider than can be handled only by one
            else if (isClosestHero && isSpiderHealthLowEnough && closestSpider.isCriticalForMyBase() && distanceFromHero <= heroAttackRadius) {
                closestSpider.targetByMe = true;
                return this.moveAction(closestSpider.x, closestSpider.y, "Move #1 to " + closestSpider.id);
            }
            else if (isClosestHero && isSpiderHealthLowEnough && closestSpider.isDangerousForMyBase()) {
                closestSpider.targetByMe = true;
                return this.moveAction(closestSpider.x, closestSpider.y, "Move #2 to " + closestSpider.id);
            }
            else if (isClosestHero && !closestSpider.isDangerousForMyBase() && !closestSpider.isDangerousForEnemyBase()) {
                closestSpider.targetByMe = true;
                return this.moveAction(closestSpider.x, closestSpider.y, "Move #3 to " + closestSpider.id);
            }
            else if (!isSpiderHealthLowEnough && !closestSpider.isControlledByMe() && !closestSpider.isWindedByMe()) {
                // Need several heroes on it
                return this.moveAction(closestSpider.x, closestSpider.y, "Backup to " + closestSpider.id);
            }
        }

        // Otherwise back to default positions
        if (this.me.basePosX === 0) {
            return this.moveAction(neutralPositions[heroIdx][0], neutralPositions[heroIdx][1], "Neutral Position");
        }
        else {
            return this.moveAction(xMax - neutralPositions[heroIdx][0], yMax - neutralPositions[heroIdx][1], "Neutral Position");
        }
    }

    nextAction = (heroIdx: number, actions: string[]): string => {
        if (heroIdx == 2) {
            return this.solveAgressiveBehavior(heroIdx, actions);
        }
        else {
            return this.solveDefensiveBehavior(heroIdx, actions);
        }
    };

    debug = (message: string, ...rest) => {
      console.error(message, ...rest);
    };
}

// Game variables
let heroes: number[][] = [];
let prevTurnHeroes: number[][] = [];
let targetsId: Array<number|undefined> = [undefined, undefined, undefined];
let oppHeroes: number[][] = [];
let spiders: number[][] = [];
let agressiveSpiders: number[][] = []; // spiders in my base
let oppAgressiveSpiders: number[][] = []; // spiders in opponent base
let threateningSpiders: number[][] = []; // spiders going to my base
let oppThreateningSpiders: number[][] = []; // spiders going to opponent base
let inoffensiveSpiders: number[][] = []; // spiders not going to any base
let isFirstRound = true;
let neutralPositions: number[][] = [[5543, 2296], [2296, 5543], [12496, 5496]]; //[13698, 5947]];

function distance(x1: number, y1: number, x2: number, y2: number): number {
    return Math.round(Math.sqrt(Math.pow((x2-x1),2) + Math.pow((y2-y1),2)));
}

function norm(vX: number, vY: number): number {
    return Math.sqrt(vX * vX + vY * vY);
}

function dotProduct(v1X: number, v1Y: number, v2X: number, v2Y: number): number {
    return v1X * v2X + v1Y * v2Y;
}

function degreeToRadian(angle: number): number {
    return (angle * Math.PI) / 180.0;
}

// Main
const [baseX, baseY] = readline().split(" ").map(Number); // The corner of the map representing your base
const heroesPerPlayer: number = Number(readline()); // Always 3
const game = new Game(baseX, baseY, heroesPerPlayer);

// game loop
while (true) {
  const myBaseInput: number[] = readline().split(" ").map(Number);
  const enemyBaseInput: number[] = readline().split(" ").map(Number);
  game.newTurn(
    myBaseInput[0],
    myBaseInput[1],
    enemyBaseInput[0],
    enemyBaseInput[1]
  );

  const entityCount: number = Number(readline()); // Amount of heros and monsters you can see
  for (let i = 0; i < entityCount; i++) {
    const inputs: number[] = readline().split(" ").map(Number);
    game.addEntity(
      new Entity(
        inputs[0], // Unique identifier
        inputs[1], // 0=monster, 1=your hero, 2=opponent hero
        inputs[2], // Position of this entity
        inputs[3],
        inputs[4], // Ignore for this league; Count down until shield spell fades
        inputs[5], // Ignore for this league; Equals 1 when this entity is under a control spell
        inputs[6], // Remaining health of this monster
        inputs[7], // Trajectory of this monster
        inputs[8],
        inputs[9], // 0=monster with no target yet, 1=monster targeting a base
        inputs[10], // Given this monster's trajectory, is it a threat to 1=your base, 2=your opponent's base, 0=neither
        game.me,
        game.enemy
      )
    );
  }


  let actions: string[] = ["", "", ""];
  for (let i = 0; i < heroesPerPlayer; i++) {
    actions[i] = game.nextAction(i, actions);
    if (i == 1 && actions[0].indexOf("Neutral Position") != -1) {
        actions[0] = game.nextAction(0, actions);
    }
  }

  for (let i = 0; i < heroesPerPlayer; i++) {
    console.log(actions[i]);
  }

  /*
  for (let i = 0; i < heroesPerPlayer; i++) {
    console.log(game.nextAction(i));
  }
  */
}
