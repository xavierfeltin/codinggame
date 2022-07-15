/**
 * Auto-generated code below aims at helping you parse
 * the standard input according to the problem statement.
 **/

// Game constants
const moveHeroDistance = 800; // Max distance done by a hero to a target point
const monsterBaseDetectionDistance = 5000; // Distance at which a monster detect a base
const moveMonsterDistance = 400; // Distance on a straight line done by a monster
const damageDoneByHero = 2; // Damage done by one hero on monster
const heroAttackRadius = 800; // Attack radius of a hero
const fogHeroVisibility = 2200; // Hero visibility of other units in the fog
const fogBaseVisibility = 6000; // Base visibility of other units in the fog
const attackBaseMonsterDistance = 300; // Distance spider attacking base if not killed
const manaCostPerHero = 10; // Mana could be spent by 1 hero
const windRadius = 1280; // Radius of spell Wind
const windStrength = 2200; // Force of wind applied to opponents and spiders

// Utilities
enum Common {
    id = 0,
    type = 1,
    x = 2,
    y = 3,
    shieldLife = 4,
    isControlled = 5
};

enum Monster {
    health = 6,
    vx = 7,
    vy = 8,
    nearBase = 9,
    threatFor = 10,
    targetedBy = 11
};

enum FilterSpider {
    distHeroSpider = 12,
    distBaseSpider = 13
}

function degreeToRadian(angle: number): number {
    return (angle * Math.PI) / 180.0;
}

function distance(x1: number, y1: number, x2: number, y2: number): number {
    return Math.round(Math.sqrt(Math.pow((x2-x1),2) + Math.pow((y2-y1),2)));
}

function searchEntityById(id: number|undefined, entities: number[][]): number[] | undefined {
    let i = 0;
    let nbEntities = entities.length;
    let found = false;

    while(!found && i < nbEntities) {
        found = entities[i][Common.id] === id;
        if (!found) {
            i++;
        }
    }

    return found ? entities[i] : undefined;
}

function closest(x: number, y: number, entities: number[][]): number[] |  undefined{
    if (entities.length === 0) {
        return undefined;
    }

    /*
    let closest: number = 0;
    let minDist = Infinity;
    let nbEntities = entities.length;
    for (let i = 0; i < nbEntities; i++) {
        const dist = distance(x, y, entities[i][Common.x], entities[i][Common.y]);
        if (dist < minDist) {
            minDist = dist;
            closest = i;
        }
    }
    return entities[closest];
    */
   return entities[0];
}

function generateSafetyBasePositions(nbHeroes: number, xBase: number, yBase: number, idxHeroInBase: number): number[][] {
    let safetyBasePositions: number[][] = [];
    const angleDeg = 90 / 4;
    const distanceFromBase = fogBaseVisibility + (fogHeroVisibility / 2);
    const distanceInBase = monsterBaseDetectionDistance / 2;

    for (let i = 0; i < nbHeroes; i++) {
        let x = 0;
        let y = 0;
        if (xBase === 0) {
            const anglePosRad = degreeToRadian(angleDeg * (i + 1));
            if (i === idxHeroInBase) {
                x = Math.cos(anglePosRad) * distanceInBase;
                y = Math.sin(anglePosRad) * distanceInBase;
            }
            else {
                x = Math.cos(anglePosRad) * distanceFromBase;
                y = Math.sin(anglePosRad) * distanceFromBase;
            }
        }
        else {
            const anglePosRad = degreeToRadian((angleDeg * (i + 1)) + 180);
            if (i === idxHeroInBase) {
                x = xBase + (Math.cos(anglePosRad) * distanceInBase);
                y = yBase + (Math.sin(anglePosRad) * distanceInBase);
            }
            else {
                x = xBase + (Math.cos(anglePosRad) * distanceFromBase);
                y = yBase + (Math.sin(anglePosRad) * distanceFromBase);
            }
        }
        safetyBasePositions.push([Math.round(x), Math.round(y)]);
    }
    return safetyBasePositions;
}

function distancePointLine(x: number, y: number, mLine: number, pLine: number): number {
    return Math.abs(mLine * x - y + pLine) / Math.sqrt(mLine * mLine + 1);
}

// line equation ax + by + c =0
// reduced equation y = -ax/b -c/b
function getEquationLineCoefficients(x: number, y: number, vx: number, vy: number): number[] {
    const b = -vx;
    const a = vy;
    const c = -a * x + -b * y;
    const m =  -a / b
    const p = -c / b;
    return [m, p];
}

function filterDangerousMonsters(xBase: number, yBase: number, monsters: number[][], idxHero: number, isHeroInBase: boolean): number[][] {
    let dangerousMonsters: number[][] = [];
    let nbMonsters = monsters.length;
    for (let i = 0; i < nbMonsters; i++) {
        const monster = monsters[i];

        if (monster[Monster.targetedBy] === idxHero || monster[Monster.targetedBy] === -1) {
            const trajectoryLineCoeff = getEquationLineCoefficients(monster[Common.x], monster[Common.y], monster[Monster.vx], monster[Monster.vy]);
            const distBaseMonsterTrajectory = distancePointLine(xBase, yBase, trajectoryLineCoeff[0], trajectoryLineCoeff[1]);

            const distBaseSpiderBeforeMoving = distance(xBase, yBase, monster[Common.x], monster[Common.y]);
            const distHeroSpider = distance(myHeroes[idxHero][Common.x], myHeroes[idxHero][Common.y], monster[Common.x], monster[Common.y]);

            const isSpiderCanReachBase = distBaseMonsterTrajectory <= monsterBaseDetectionDistance;
            const isSpiderCloseEnoughFromBase = distBaseSpiderBeforeMoving <= 2 * monsterBaseDetectionDistance;
            const isSpiderCloseEnoughFromHero = isHeroInBase ? distHeroSpider <= monsterBaseDetectionDistance : distHeroSpider <= fogHeroVisibility;
            const isSpiderInTrackingArea = isHeroInBase ? distBaseSpiderBeforeMoving <= monsterBaseDetectionDistance : distBaseSpiderBeforeMoving >= monsterBaseDetectionDistance;

            console.error(monster[Common.id] + ": " + isSpiderCanReachBase + ", " + isSpiderCloseEnoughFromBase + "(" + distBaseSpiderBeforeMoving + ")" + ", " + isSpiderCloseEnoughFromHero + "(" + distHeroSpider + ")" + ", " + isSpiderInTrackingArea);

            if (isSpiderCanReachBase && isSpiderCloseEnoughFromBase && isSpiderCloseEnoughFromHero && isSpiderInTrackingArea) {
                dangerousMonsters.push([...monster, distHeroSpider, distBaseSpiderBeforeMoving]);
            }
        }
    }

    if (isHeroInBase) {
        dangerousMonsters = dangerousMonsters.sort((mA: number[], mB: number[]) => {
            if (mA[FilterSpider.distBaseSpider] <= mB[FilterSpider.distBaseSpider])
                return -1;
            else
                return 1;
        });
    }
    else {
        dangerousMonsters = dangerousMonsters.sort((mA: number[], mB: number[]) => {
            if (mA[FilterSpider.distHeroSpider] <= mB[FilterSpider.distHeroSpider])
                return -1;
            else
                return 1;
        });
    }

    //log
    const ids = dangerousMonsters.map((monster) => monster[Common.id])
    console.error(ids.join(', '));

    return dangerousMonsters;
}

// Game variables
const heroLeftInBase = 1;
let myHeroes: number[][] = [];
let targetsId: Array<number|undefined> = [undefined, undefined, undefined];
let oppHeroes: number[][] = [];
let allMonsters: number[][] = [];
let isFirstRound = true;
let safetyBasePositions: number[][] = [];
let myMana: number = 0;
let myHealth: number = 0;
let oppMana: number = 0;
let oppHealth: number = 0;

// Main
let inputs: string[] = readline().split(' ');
const baseX: number = parseInt(inputs[0]); // The corner of the map representing your base
const baseY: number = parseInt(inputs[1]);
const oppBaseX: number = 17630 - baseX;
const oppBaseY: number = 9000 - baseY;
const heroesPerPlayer: number = parseInt(readline()); // Always 3
let actions: string [] = [];

safetyBasePositions = generateSafetyBasePositions(heroesPerPlayer, baseX, baseY, heroLeftInBase);

// game loop
while (true) {
    myHeroes = [];
    oppHeroes = [];
    allMonsters = [];
    actions = [];

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
        const targetedBy: number = targetsId.indexOf(id);

        if (type === 0) {
            const monster = [id, type, x, y, shieldLife, isControlled, health, vx, vy, nearBase, threatFor, targetedBy];
            allMonsters.push(monster);
        }
        else if (type === 1) {
            const hero= [id, type, x, y, shieldLife, isControlled];
            myHeroes.push(hero);
        }
        else {
            const hero= [id, type, x, y, shieldLife, isControlled];
            oppHeroes.push(hero);
        }
    }
    // Consider only the spiders than can enter the base


    // Update the previous targets with the new monsters list
    for (let i = 0; i < heroesPerPlayer; i++) {
        const monster = searchEntityById(targetsId[i], allMonsters);
        targetsId[i] = monster === undefined ? undefined : monster[Common.id];
    }

    // TODO: do not focus same spider with different heroes
    for (let i = 0; i < heroesPerPlayer; i++) {
        const myHero = myHeroes[i];

        let monsters = filterDangerousMonsters(baseX, baseY, allMonsters, i, i === heroLeftInBase);
        console.error("[Hero " + i + "] Prev. target: " + targetsId[i]);

        let target: number[] | undefined = undefined;
        if (targetsId[i] === undefined) {
            const target = closest(myHero[Common.x], myHero[Common.y], monsters);
            targetsId[i] = target === undefined ? undefined : target[Common.id];
            console.error("[Hero " + i + "] New target: " + targetsId[i]);
        }
        else {
            const previousTarget = searchEntityById(targetsId[i], monsters); // TODO: save before the monster to avoid searching twice
            if (previousTarget === undefined) {
                target = closest(myHero[Common.x], myHero[Common.y], monsters);
                targetsId[i] = target === undefined ? undefined : target[Common.id];
                console.error("[Hero " + i + "] New target: " + targetsId[i]);
            }
            else {
                target = previousTarget;
            }
        }

        // In the first league: MOVE <x> <y> | WAIT; In later leagues: | SPELL <spellParams>;
        if (target === undefined) {
            actions.push('MOVE ' + safetyBasePositions[i][0] + " " + safetyBasePositions[i][1] + " Back to safety");
        }
        else {
            const xTargetAfterMovement = target[Common.x] + target[Monster.vx];
            const yTargetAfterMovement = target[Common.y] + target[Monster.vy];
            const xWindSpellOppositionToSpider = myHero[Common.x] - target[Monster.vx];
            const yWindSpellOppositionToSpider = myHero[Common.y] - target[Monster.vy];

            if (i === heroLeftInBase) {
                const action = myMana >= manaCostPerHero && target[FilterSpider.distHeroSpider] <= windRadius ?
                    'SPELL WIND ' + xWindSpellOppositionToSpider + " " + yWindSpellOppositionToSpider + " Cast Wind"
                :
                    'MOVE ' +xTargetAfterMovement + " " + yTargetAfterMovement + " Target:" + targetsId[i];
                actions.push(action);
            }
            else {
                const action = myMana >= 3 * manaCostPerHero && target[FilterSpider.distHeroSpider] <= windRadius ?
                    'SPELL WIND ' + oppBaseX + " " + oppBaseY + " Cast Wind"
                :
                    'MOVE ' +xTargetAfterMovement + " " + yTargetAfterMovement + " Target:" + targetsId[i];
                actions.push(action);
            }
        }
    }

    for (let i = 0; i < heroesPerPlayer; i++) {
        console.log(actions[i]);
    }

    isFirstRound = false;
}
// Write an action using console.log()
// To debug: console.error('Debug messages...');