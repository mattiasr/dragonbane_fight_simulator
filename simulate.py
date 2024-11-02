import random
import copy

INFO = "\U0001F6C8"
HEAL = "\U0001F33F"
EYES = "\U0001F440"
ATTACK_SPELL = "\U00002728"
ATTACK_SWORD = "\u2694"
GREEN_HEART = "\U0001F49A"
BLUE_HEART = "\U0001F499"
SMALL_SKULL = "\u2620"
BIG_SKULL = "\U0001F480"
EXPLOSION = "\U0001F4A5"
FAILED = "\u274C"

def make_attack(attacker, opponent):
    if attacker.hp <= 0:
        #print(f"{attacker.name} is down, skip his actions")
        return 1

    # Remove dead ppl
    for t in attacker.targets:
        if t.hp <= 0:
            attacker.targets.remove(t)

    if attacker.targets == []:
        give_wizard_a_chance = 0
        while True:
            targets = random.choice(opponent)
            if targets.is_player and targets.hp > 0:
                if targets.is_mage and give_wizard_a_chance == 0:
                    print(f"\t{EYES} {attacker.name} looks at {targets.name}, i will deal with you later...")
                    give_wizard_a_chance+=1
                    continue
                else:
                    attacker.targets.append(targets)
                    break
            elif targets.hp > 0:
                attacker.targets.append(targets)
                break

    target = random.choice(attacker.targets)
    sb = 0
    if hasattr(attacker, 'sb'):
        sb = attacker.sb
    else:
        sb = get_skadebonus(getattr(attacker, attacker.melee_weapon.skill, 0))

    damage = 0
    rolls = []

    if attacker.is_mage:
        if attacker.vp < 2:
            # Out of juice, should catch breath one round.
            gain_vp, rolls = roll_dice("1T6")
            attacker.vp+=gain_vp
            print(f"\t{HEAL} {attacker.name} rest to be able to cast more, gain {gain_vp} {rolls}")
            return 1

    if attacker.is_mage:
        # Check if someone down
        heal = 0
        for p in party:
            if p.hp <= 0:
                # Heal one down member
                p.hp = 0
                attacker.vp-=2
                heal, rolls = roll_dice("2T6")
                p.hp+= heal
                print(f"\t{HEAL} {attacker.name} runs and heal {p.name} for {heal} HP ({rolls})")
                print(f"\t{BLUE_HEART} {p.name}: {p.hp}/{p.max_hp}")
                break
        if heal:
            return 1

    if attacker.is_mage:
        damage, rolls = attacker.attack(attacker.magic_spell.skill, magic=True)
        attacker.vp-=2
        print(f"\t{ATTACK_SPELL} {attacker.name} attacks {target.name} with {attacker.magic_spell.name} ({attacker.magic_spell.damage})", end=" ")
    else:
        damage, rolls = attacker.attack(attacker.melee_weapon.skill)
        print(f"\t{ATTACK_SWORD} {attacker.name} attacks {target.name} with {attacker.melee_weapon.name} ({attacker.melee_weapon.damage} + {sb})", end=" ")

    if damage > 0:
        print(f"hits for {damage}-{target.ac} damage ({flatten(rolls)})")
        if target.ac:
            damage-=target.ac
        target.hp-=damage
        if target.is_player:
            print(f"\t{BLUE_HEART} {target.name}: {target.hp}/{target.max_hp}")
        else:
            print(f"\t{GREEN_HEART} {target.name}: {target.hp}/{target.max_hp}")
        if target.hp <= 0:
            if target.is_player:
                print(f"\t{SMALL_SKULL} {target.name} is down")
            else:
                print(f"\t{BIG_SKULL} {target.name} is dead")
            attacker.targets.remove(target)
        
        for o in opponent:
            if o.hp > 0:
                return 1
        return 0
    else:
        print("misses...")
        return 1

def roll_dice(dice_roll):
    rolls, max_roll = dice_roll.split("T")
    total_sum = 0
    total_rolls = []
    i = 1

    while i <= int(rolls):
        roll = random.randint(1, int(max_roll))
        total_rolls.append(roll)
        total_sum+= roll
        i+=1

    return total_sum, total_rolls

def flatten(nested_list):
    flat_list = []
    for item in nested_list:
        if isinstance(item, list):
            flat_list.extend(flatten(item))  # Recursively flatten sublists
        else:
            flat_list.append(item)
    return flat_list

def get_skadebonus(value):
    if value <= 11:
        return 0
    elif value > 11 and value <= 16:
        return "1T4"
    elif value > 16:
        return "1T6"

def get_grundchans(value):
    if value <= 5:
        return 3
    elif value > 5 and value <= 8:
        return 4
    elif value > 8 and value <= 12:
        return 5
    elif value > 12 and value <= 15:
        return 6
    elif value > 15 and value <= 18:
        return 7

class Weapon:
    def __init__(self, name, damage, skill):
        self.name = name
        self.damage = damage
        self.skill = skill

    def roll_damage(self, is_crit=False):
        total_dmg = 0
        total_rolls = []
        if is_crit:
            _, dice = self.damage.split("T")
            damage, rolls = roll_dice(f"1T{dice}")
            total_rolls.append(rolls)
            total_dmg+= damage

        damage, rolls = roll_dice(self.damage)
        total_rolls.append(rolls)
        total_dmg+= damage

        return total_dmg, total_rolls

class BaseStats:
    def __init__(self, name, ac, hp=None, melee_weapon=None, magic_spell=None):
        self.name = name
        self.ac = ac
        self.hp = hp
        self.max_hp = self.hp
        self.targets = []
        self.is_player = True
        self.is_mage = False
        self.vp = 0
        self.melee_weapon = melee_weapon
        self.magic_spell = magic_spell

    def attack(self, skill=None, fv=None, skadebonus=None, magic=False):
        total_damage = 0
        damage = 0

        # Determine FV and Skadebonus based on character type
        if fv is None:
            fv = get_grundchans(getattr(self, skill, 0)) * 2
        if skadebonus is None:
            skadebonus = get_skadebonus(getattr(self, skill, 0))

        total_rolls = []

        fv_roll, fv_rolls = roll_dice("1T20")

        if fv_roll > fv:
            # Failed roll
            print(f"\t{FAILED} {self.name} rolls FV: {fv_roll} against FV: {fv} ({fv_rolls})")
            return 0, []
        elif fv_roll == 1:
            # Crit hit
            print(f"\t{EXPLOSION} {self.name} rolls FV: {fv_roll} against FV: {fv} ({fv_rolls})")
            if magic:
                damage, rolls = self.magic_spell.roll_damage(is_crit=True)
            else:
                damage, rolls = self.melee_weapon.roll_damage(is_crit=True)
            total_rolls.append(rolls)
            total_damage+=damage
        else:
            # Normal hit
            print(f"\t{INFO} {self.name} rolls FV: {fv_roll} against FV: {fv} ({fv_rolls})")
            if magic:
                damage, rolls = self.magic_spell.roll_damage()
            else:
                damage, rolls = self.melee_weapon.roll_damage()
            total_rolls.append(rolls)
            total_damage+= damage
        
        # Do we have Skadebonus?
        if skadebonus and not magic:
            damage, rolls = roll_dice(skadebonus)
            total_rolls.append(rolls)
            total_damage+= damage

        return total_damage, total_rolls

class PartyMember (BaseStats):
    def __init__(self, name, sty, fys, smi, int_, psy, kar, ac=0, melee_weapon=None, range_weapon=None, magic_spell=None, is_mage=False):
        super().__init__(name, ac, melee_weapon=melee_weapon, magic_spell=magic_spell)
        self.STY = sty
        self.SMI = smi
        self.FYS = fys
        self.PSY = psy
        self.INT = int_
        self.KAR = kar
        self.is_mage = is_mage
        self.ac = ac  # Armor class
        self.range_weapon = range_weapon
        self.hp = self.FYS  # Default hp
        self.max_hp = self.FYS
        self.vp = self.PSY
    
    def attack(self, skill=None, magic=None):
        return super().attack(skill=skill, skadebonus=get_skadebonus(getattr(self, skill, 0)), magic=magic)

class Monster (BaseStats):
    def __init__(self, name, hp, ac, fv, melee_weapon, magic_spell=None, sb=0):
        super().__init__(name, ac, hp=hp, melee_weapon=melee_weapon, magic_spell=magic_spell)
        self.fv = fv
        self.sb = sb
        self.targets = []
        self.is_player = False
        self.magic_spell = magic_spell

    def attack(self, skill=None, magic=None):
        return super().attack(fv=self.fv, skadebonus=self.sb)


# Weapons
unarmed = Weapon("Unarmed", "1T6", "STY")
dagger = Weapon("Dagger", "1T8", "SMI")
knife = Weapon("Knife", "1T8", "SMI")
shortsword = Weapon("ShortSword", "1T10", "STY")
ljungeld = Weapon("Ljungeld", "3T6", "PSY")
tentakel = Weapon("Tentacle", "1T8", "STY")
battleaxe = Weapon("BattleAxe", "2T8", "STY")

# Statistics metrics
total_samples = 1
total_rounds = []
players_killed = []
monsters_killed = []
party_whipes = []
monster_whipes = []

# Let the fights begin
for _ in range(total_samples):
    party = [
        PartyMember("Mage", sty=11, fys=12, smi=10, int_=12, psy=13, kar=5, ac=0, melee_weapon=dagger, magic_spell=ljungeld, is_mage=True),
        PartyMember("Thieve", sty=14, fys=16, smi=18, int_=15, psy=12, kar=8, ac=0, melee_weapon=dagger, range_weapon=knife),
        PartyMember("Bard", sty=14, fys=15, smi=15, int_=12, psy=13, kar=18, ac=0, melee_weapon=knife, range_weapon=knife),
        PartyMember("Hunter", sty=14, fys=15, smi=15, int_=12, psy=13, kar=18, ac=0, melee_weapon=knife, range_weapon=knife),
    ]
    monsters = [
        Monster("Monster#1", hp=9, ac=0, fv=9, melee_weapon=unarmed, sb="1T4"),
        Monster("Monster#2", hp=9, ac=0, fv=9, melee_weapon=unarmed, sb="1T4"),
        Monster("Monster#3", hp=9, ac=0, fv=9, melee_weapon=unarmed, sb="1T4"),
        Monster("Monster#4", hp=9, ac=0, fv=9, melee_weapon=unarmed, sb="1T4"),
        Monster("Boss#1", hp=30, ac=6, fv=15, melee_weapon=battleaxe, sb="1T6"),
    ]
    fighters = copy.deepcopy(party)
    fighters.append(monsters)
    rounds = 0
    party_alive = 1
    monster_party_alive = 1
    while True:
        random.shuffle(fighters)
        if not monster_party_alive:
            mpk_count = 0
            for m in monsters:
                if m.hp <= 0:
                    mpk_count+=1
            monsters_killed.append(mpk_count)
            monster_whipes.append(1)

            pk_count = 0
            for p in party:
                if p.hp <= 0 and p.is_player:
                    pk_count+=1

            players_killed.append(pk_count)
            total_rounds.append(rounds)
            print(f"\t\U000026A0\U0000FE0F  Monster whipe...")
            break

        if not party_alive:
            pk_count = 0
            for p in party:
                if p.hp <= 0 and p.is_player:
                    pk_count+=1

            players_killed.append(pk_count)
            party_whipes.append(1)
            total_rounds.append(rounds)
            print(f"\t\U000026A0\U0000FE0F  Party whipe...")
            break

        rounds+=1
        print(f"Round {rounds}", end=": ")
        print(f"Initiative {[p.name if hasattr(p, 'name') else [sub_p.name for sub_p in p] for p in fighters]}")
        for p in fighters:
            if isinstance(p, list):
                # This is a monster phase
                if monster_party_alive:
                    for m in p:
                        party_alive = make_attack(m, party)
                        if not party_alive:
                            break 
            else:
                if party_alive:
                    # This is a player phase
                    monster_party_alive = make_attack(p, monsters)
                    if not monster_party_alive:
                        break

print("======================================")
player_info = [(player.name, f"{player.hp}/{player.max_hp}") for player in party]
monster_info = [(monster.name, f"{monster.hp}/{monster.max_hp}") for monster in monsters]
print(f"Party: {player_info}")
print(f"Monsters: {monster_info}")
print("Totalt:")
print(f"{sum(monsters_killed)} monstes killed ({sum(monsters_killed)/total_samples} killed/fight)")
print(f"{sum(monster_whipes)} monster whipes ({sum(monster_whipes)/total_samples} monster whipes/fight)")
print(f"{sum(players_killed)} players killed ({sum(players_killed)/total_samples} killed/fight)")
print(f"{sum(party_whipes)} party whipes ({sum(party_whipes)/total_samples} party whipes/fight)")
print(f"{total_samples} fights ({sum(total_rounds)/total_samples} rounds/fight)")