/**
 * Auto-generated code below aims at helping you parse
 * the standard input according to the problem statement.
 **/

 enum Common {
    id = 0,
    type = 1,
    x = 2,
    y = 3,
    shieldLife = 4,
    isControlled = 5
};

enum Spider {
    health = 6,
    vx = 7,
    vy = 8,
    nearBase = 9,
    threatFor = 10,
    distHeroIdx = 11,
    distOppIdx = 14
};

enum AgressiveSpider {
    distWithBase = 17
};


// Game constants
const moveHeroDistance = 800; // Max distance done by a hero to a target point
const monsterBaseDetectionDistance = 5000; // Distance at which a monster detect a base
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
let safetyBasePositions: number[][] = [];
let myMana: number = 0;
let myHealth: number = 0;
let oppMana: number = 0;
let oppHealth: number = 0;

function distance(x1: number, y1: number, x2: number, y2: number): number {
    return Math.round(Math.sqrt(Math.pow((x2-x1),2) + Math.pow((y2-y1),2)));
}

function norm(vX: number, vY: number): number {
    return Math.sqrt(vX * vX + vY * vY);
}

function dotProduct(v1X: number, v1Y: number, v2X: number, v2Y: number): number {
    return v1X * v2X + v1Y * v2Y;
}

function closestHeroIdxFromSpider(spider: number[], ignoreHero: number[]): number {
    let closest = -1;
    let distance = Infinity;
    for (let i = 0; i < heroesPerPlayer; i++) {
        if (ignoreHero.indexOf(i) != -1) {
            continue;
        }

        if (spider[Spider.distHeroIdx + i] < distance) {
            closest = i;
            distance = spider[Spider.distHeroIdx + i];
        }
    }
    return closest;
}

function degreeToRadian(angle: number): number {
    return (angle * Math.PI) / 180.0;
}

function neutralPositions(xBase: number, yBase: number): number[][] {
    let positions: number[][] = [];
    const angleDeg = 90 / 4;
    const distanceForScouting = fogBaseVisibility; // + (fogHeroVisibility / 2);

    for (let i = 0; i < heroesPerPlayer; i++) {
        const anglePosRad = xBase === 0 ? degreeToRadian(angleDeg * (i + 1)) : degreeToRadian((angleDeg + 180) * (i + 1));
        let x = xBase + (Math.cos(anglePosRad) * distanceForScouting);
        let y = yBase + (Math.sin(anglePosRad) * distanceForScouting);
        positions.push([Math.round(x), Math.round(y)]);
    }
    return positions;
}

function moveAction(x: number, y: number, comment: string): string {
    return 'MOVE ' + Math.round(x) + " " + Math.round(y) + " " + comment;
}

function spellWindAction(destX: number, destY: number, comment: string): string {
    return 'SPELL WIND ' + destX + " " + destY + " " + comment;
}

function spellControlAction(id: number, destX: number, destY: number, comment: string): string {
    return 'SPELL CONTROL ' + id + " " + destX + " " + destY + " " + comment;
}

// Main
let inputs: string[] = readline().split(' ');
const baseX: number = parseInt(inputs[0]); // The corner of the map representing your base
const baseY: number = parseInt(inputs[1]);
const oppBaseX: number = 17630 - baseX;
const oppBaseY: number = 9000 - baseY;
const heroesPerPlayer: number = parseInt(readline()); // Always 3
let actions: string [] = [];
let defaultPositions = neutralPositions(baseX, baseY);

// game loop
while (true) {
    heroes = [];
    oppHeroes = [];
    spiders = [];
    agressiveSpiders = [];
    oppAgressiveSpiders = [];
    threateningSpiders = [];
    oppThreateningSpiders = [];
    inoffensiveSpiders = [];
    actions = [moveAction(defaultPositions[0][0], defaultPositions[0][1], "Neutral position"),
               moveAction(defaultPositions[1][0], defaultPositions[1][1], "Neutral position"),
               moveAction(defaultPositions[2][0], defaultPositions[2][1], "Neutral position")]

    for (let i = 0; i < 2; i++) {
        let inputs: string[] = readline().split(' ');
        if (i === 0) {
            myHealth = parseInt(inputs[0]); // Each player's base health
            myMana = parseInt(inputs[1]); // Ignore in the first league; Spend ten mana to cast a spell
        }
        else {
            oppHealth = parseInt(inputs[0]); // Each player's base health
            oppMana = parseInt(inputs[1]); // Ignore in the first league; Spend ten mana to cast a spell
        }
    }
    const entityCount: number = parseInt(readline()); // Amount of heros and monsters you can see
    for (let i = 0; i < entityCount; i++) {
        let inputs: string[] = readline().split(' ');
        const id: number = parseInt(inputs[0]); // Unique identifier
        const type: number = parseInt(inputs[1]); // 0=monster, 1=your hero, 2=opponent hero
        const x: number = parseInt(inputs[2]); // Position of this entity
        const y: number = parseInt(inputs[3]);
        const shieldLife: number = parseInt(inputs[4]); // Ignore for this league; Count down until shield spell fades
        const isControlled: number = parseInt(inputs[5]); // Ignore for this league; Equals 1 when this entity is under a control spell
        const health: number = parseInt(inputs[6]); // Remaining health of this monster
        const vx: number = parseInt(inputs[7]); // Trajectory of this monster
        const vy: number = parseInt(inputs[8]);
        const nearBase: number = parseInt(inputs[9]); // 0=monster with no target yet, 1=monster targeting a base
        const threatFor: number = parseInt(inputs[10]); // Given this monster's trajectory, is it a threat to 1=your base, 2=your opponent's base, 0=neither

        if (type === 0) {
            const distWithHero: number[] = [];
            const distWithOpp: number[] = [];
            for (let i = 0; i < heroesPerPlayer; i++) {
                let dist = distance(heroes[i][Common.x], heroes[i][Common.y], x, y);
                distWithHero.push(dist);

                if (i < oppHeroes.length) {
                    dist = distance(oppHeroes[i][Common.x], oppHeroes[i][Common.y], x, y);
                    distWithOpp.push(dist);
                }
                else {
                    distWithOpp.push(-1);
                }
            }
            const spider = [id, type, x, y, shieldLife, isControlled, health, vx, vy, nearBase, threatFor, ...distWithHero, ...distWithOpp];
            spiders.push(spider);

            if (threatFor === 0) {
                inoffensiveSpiders.push(spider);
            }
            else if (threatFor === 1) {
                if (nearBase) {
                    const distWithBase = distance(baseX, baseY, x, y);
                    agressiveSpiders.push([...spider, distWithBase]);
                }
                else {
                    threateningSpiders.push(spider);
                }
            }
            else if (threatFor === 2) {
                if (nearBase) {
                    const distWithBase = distance(oppBaseX, oppBaseY, x, y);
                    oppAgressiveSpiders.push([...spider, distWithBase]);
                }
                else {
                    oppThreateningSpiders.push(spider);
                }
            }
        }
        else if (type === 1) {
            const distanceFromBase = distance(x, y, baseX, baseY);
            const distanceFromOpponentBase = distance(x, y, oppBaseX, oppBaseY);
            const hero = [id, type, x, y, shieldLife, isControlled, distanceFromBase, distanceFromOpponentBase];
            heroes.push(hero);
        }
        else {
            const distanceFromBase = distance(x, y, oppBaseX, oppBaseY);
            const distanceFromOpponentBase = distance(x, y, baseX, baseY);
            const hero = [id, type, x, y, shieldLife, isControlled, distanceFromBase, distanceFromOpponentBase];
            oppHeroes.push(hero);
        }
    }

    const heroesWithAlreadyAnAction: number[] = [];
    if (agressiveSpiders.length > 0) {
        // Sort spiders by how close they are from exploding in the base
        agressiveSpiders.sort((a, b) => {
            if (a[AgressiveSpider.distWithBase] < b[AgressiveSpider.distWithBase]) {
                return -1;
            }
            else {
                return 1;
            }
        });

        const mostUrgentSpider = agressiveSpiders[0];
        const closestHeroIdx = closestHeroIdxFromSpider(mostUrgentSpider, []);
        const isSpiderTooCloseAndHealthy = mostUrgentSpider[AgressiveSpider.distWithBase] - moveSpiderDistance <= attackBaseMonsterDistance && mostUrgentSpider[Spider.health] > 1;
        const isSpiderInWindRadius = mostUrgentSpider[Spider.distHeroIdx + closestHeroIdx] <= windRadius;
        const isSpiderHasShied = mostUrgentSpider[Common.shieldLife] > 0;

        if (isSpiderTooCloseAndHealthy && isSpiderInWindRadius && !isSpiderHasShied && myMana >= manaCostPerHero) {
            // Push away the spider to gain some time
            const action = spellWindAction(oppBaseX, oppBaseY, "Push away MDS");
            actions[closestHeroIdx] = action;
            heroesWithAlreadyAnAction.push(closestHeroIdx);
        }
        else {
            // Try to hit the spider without moving too much
            let vectX = mostUrgentSpider[Common.x] - heroes[closestHeroIdx][Common.x];
            let vectY = mostUrgentSpider[Common.y] - heroes[closestHeroIdx][Common.y];
            const normVect = norm(vectX, vectY);
            vectX = vectX / normVect;
            vectY = vectY / normVect;
            const cosAngleSpiderHero = dotProduct(vectX, vectY, 1, 0);
            const angleSpiderHero = Math.acos(cosAngleSpiderHero);

            let distanceCoefficient = moveHeroDistance;
            if (mostUrgentSpider[Spider.distHeroIdx + closestHeroIdx] > moveHeroDistance) {
                distanceCoefficient +=  moveSpiderDistance;
            }
            const posHeroX = mostUrgentSpider[Common.x] + Math.cos(angleSpiderHero) * distanceCoefficient;
            const posHeroY = mostUrgentSpider[Common.y] + Math.sin(angleSpiderHero) * distanceCoefficient;

            const action = moveAction(posHeroX, posHeroY, "Hit MDS");
            actions[closestHeroIdx] = action;
            heroesWithAlreadyAnAction.push(closestHeroIdx);
        }
    }

    if (threateningSpiders.length > 0) {
        // Sort spiders by how close they are from heroes
        inoffensiveSpiders.sort((a, b) => {
            const aAvg = (a[Spider.distHeroIdx] + a[Spider.distHeroIdx + 1] + a[Spider.distHeroIdx + 2]) / 3;
            const bAvg = (a[Spider.distHeroIdx] + a[Spider.distHeroIdx + 1] + a[Spider.distHeroIdx + 2]) / 3;
            if (aAvg < bAvg) {
                return -1;
            }
            else {
                return 1;
            }
        });

        const closestSpider = inoffensiveSpiders[0];
        const closestHeroIdx = closestHeroIdxFromSpider(closestSpider, heroesWithAlreadyAnAction);

        const isSpiderInControlRadius = closestSpider[Spider.distHeroIdx + closestHeroIdx] <= controlRadius;
        const isSpiderHasShied = closestSpider[Common.shieldLife] > 0;

        if (isSpiderInControlRadius && !isSpiderHasShied && myMana >= manaCostPerHero) {
            // Push away the spider to gain some time
            const action = spellControlAction(closestSpider[Common.id], oppBaseX, oppBaseY, "Control spider");
            actions[closestHeroIdx] = action;
            heroesWithAlreadyAnAction.push(closestHeroIdx);
        }
        else {
            // Try to hit the spider without moving too much
            let vectX = closestSpider[Common.x] - heroes[closestHeroIdx][Common.x];
            let vectY = closestSpider[Common.y] - heroes[closestHeroIdx][Common.y];
            const normVect = norm(vectX, vectY);
            vectX = vectX / normVect;
            vectY = vectY / normVect;
            const cosAngleSpiderHero = dotProduct(vectX, vectY, 1, 0);
            const angleSpiderHero = Math.acos(cosAngleSpiderHero);

            let distanceCoefficient = moveHeroDistance;
            if (closestSpider[Spider.distHeroIdx + closestHeroIdx] > moveHeroDistance) {
                distanceCoefficient +=  moveSpiderDistance;
            }
            const posHeroX = closestSpider[Common.x] + Math.cos(angleSpiderHero) * distanceCoefficient;
            const posHeroY = closestSpider[Common.y] + Math.sin(angleSpiderHero) * distanceCoefficient;

            const action = moveAction(posHeroX, posHeroY, "Hit TS");
            actions[closestHeroIdx] = action;
            heroesWithAlreadyAnAction.push(closestHeroIdx);
        }
    }

    if (inoffensiveSpiders.length > 0) {
        // Sort spiders by how close they are from heroes
        inoffensiveSpiders.sort((a, b) => {
            const aAvg = (a[Spider.distHeroIdx] + a[Spider.distHeroIdx + 1] + a[Spider.distHeroIdx + 2]) / 3;
            const bAvg = (a[Spider.distHeroIdx] + a[Spider.distHeroIdx + 1] + a[Spider.distHeroIdx + 2]) / 3;
            if (aAvg < bAvg) {
                return -1;
            }
            else {
                return 1;
            }
        });

        const closestSpider = inoffensiveSpiders[0];
        const closestHeroIdx = closestHeroIdxFromSpider(closestSpider, heroesWithAlreadyAnAction);

        const isSpiderInControlRadius = closestSpider[Spider.distHeroIdx + closestHeroIdx] <= controlRadius;
        const isSpiderHasShied = closestSpider[Common.shieldLife] > 0;

        if (isSpiderInControlRadius && !isSpiderHasShied && myMana >= manaCostPerHero) {
            // Push away the spider to gain some time
            const action = spellControlAction(closestSpider[Common.id], oppBaseX, oppBaseY, "Control spider");
            actions[closestHeroIdx] = action;
            heroesWithAlreadyAnAction.push(closestHeroIdx);
        }
    }

    if (oppThreateningSpiders.length > 0 && heroesWithAlreadyAnAction.length < 3) {
        // Sort spiders by how close they are from heroes
        oppThreateningSpiders.sort((a, b) => {
            const aAvg = (a[Spider.distHeroIdx] + a[Spider.distHeroIdx + 1] + a[Spider.distHeroIdx + 2]) / 3;
            const bAvg = (a[Spider.distHeroIdx] + a[Spider.distHeroIdx + 1] + a[Spider.distHeroIdx + 2]) / 3;
            if (aAvg < bAvg) {
                return -1;
            }
            else {
                return 1;
            }
        });

        const closestSpider = inoffensiveSpiders[0];
        const closestHeroIdx = closestHeroIdxFromSpider(closestSpider, heroesWithAlreadyAnAction);

        const isSpiderInWindRadius = closestSpider[Spider.distHeroIdx + closestHeroIdx] <= windRadius;
        const isSpiderHasShied = closestSpider[Common.shieldLife] > 0;

        if (isSpiderInWindRadius && !isSpiderHasShied && myMana >= manaCostPerHero) {
            // Push away the spider to gain some time
            const action = spellWindAction(oppBaseX, oppBaseY, "Push further spiders");
            actions[closestHeroIdx] = action;
        }
    }

    if (oppAgressiveSpiders.length > 0 && heroesWithAlreadyAnAction.length < 3) {
        // Sort spiders by how far they are from exploding in the base
        oppAgressiveSpiders.sort((a, b) => {
            if (a[AgressiveSpider.distWithBase] > b[AgressiveSpider.distWithBase]) {
                return -1;
            }
            else {
                return 1;
            }
        });

        const mostUrgentSpider = oppAgressiveSpiders[0];
        const closestHeroIdx = closestHeroIdxFromSpider(mostUrgentSpider, []);
        const isSpiderInWindRadius = mostUrgentSpider[Spider.distHeroIdx + closestHeroIdx] <= windRadius;
        const isSpiderHasShied = mostUrgentSpider[Common.shieldLife] > 0;

        if (isSpiderInWindRadius && !isSpiderHasShied && myMana >= manaCostPerHero) {
            // Push away the spider to gain some time
            const action = spellWindAction(oppBaseX, oppBaseY, "Push further MDS");
            actions[closestHeroIdx] = action;
            heroesWithAlreadyAnAction.push(closestHeroIdx);
        }
    }

    // Publish actions to perform
    for (let i = 0; i < heroesPerPlayer; i++) {
        console.log(actions[i]);
    }
}
//TODO : handle truncated and round position values depending of the place on the map
// Write an action using console.log()
// To debug: console.error('Debug messages...');