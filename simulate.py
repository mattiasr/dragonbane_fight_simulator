#!/usr/bin/env python3
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
WARNING = "\U000026A0\U0000FE0F"
DICE = "\U0001F3B2"

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
        self.can_heal = False
        self.perma_death = False
        self.successful_death_saves = 0
        self.failed_death_saves = 0
        self.vp = 0
        self.melee_weapon = melee_weapon
        self.magic_spell = magic_spell

    def take_damage(self, amount):
        self.hp -= amount

    def heal_damage(self, amount):
        self.hp += amount

    def recover(self, amount):
        self.hp = 0
        self.successful_death_saves = 0
        self.failed_death_saves = 0
        self.hp += amount

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
            print(f"\t{FAILED}\t{self.name} rolls FV: {fv_roll} against FV: {fv} ({fv_rolls})")
            return 0, []
        elif fv_roll == 1:
            # Crit hit
            print(f"\t{EXPLOSION}\t{self.name} rolls FV: {fv_roll} against FV: {fv} ({fv_rolls})")
            if magic:
                damage, rolls = self.magic_spell.roll_damage(is_crit=True)
            else:
                damage, rolls = self.melee_weapon.roll_damage(is_crit=True)
            total_rolls.append(rolls)
            total_damage+=damage
        else:
            # Normal hit
            print(f"\t{INFO}\t{self.name} rolls FV: {fv_roll} against FV: {fv} ({fv_rolls})")
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
    def __init__(self, name, sty, fys, smi, int_, psy, kar, ac=0, melee_weapon=None, range_weapon=None, magic_spell=None, is_mage=False, can_heal=True):
        super().__init__(name, ac, melee_weapon=melee_weapon, magic_spell=magic_spell)
        self.STY = sty
        self.SMI = smi
        self.FYS = fys
        self.PSY = psy
        self.INT = int_
        self.KAR = kar
        self.is_mage = is_mage
        self.can_heal = can_heal
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

def make_attack(attacker, opponents):
    #print(f"{attacker.name}, {attacker.hp}")
    if attacker.hp <= 0:
        return 1

    # Remove dead ppl
    for t in attacker.targets:
        if t.hp <= 0:
            attacker.targets.remove(t)

    if attacker.targets == []:
        give_wizard_a_chance = 0
        while True:
            pick_target = random.choice(opponents)
            if attacker.is_player:
                if not isinstance(pick_target, list):
                    # Player try to target player? not today
                    continue
                pick_target = random.choice(pick_target)
            else:
                if isinstance(pick_target, list):
                    # Monster try to target monster? nah, skip and retry
                    continue

            if pick_target.is_player and pick_target.hp > 0:
                if pick_target.is_mage and give_wizard_a_chance == 0:
                    print(f"\t{EYES}\t{attacker.name} looks at {pick_target.name}, i will deal with you later...")
                    give_wizard_a_chance+=1
                    continue
                else:
                    attacker.targets.append(pick_target)
                    break
            elif pick_target.hp > 0:
                attacker.targets.append(pick_target)
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
            print(f"\t{HEAL}\t{attacker.name} rest to be able to cast more, gain {gain_vp} VP ({rolls})")
            return 1

    if attacker.is_mage and attacker.can_heal:
        # Check if someone down
        for p in opponents:
            if isinstance(p, list):
                continue
            if p.hp <= 0 and not p.perma_death and (p.failed_death_saves or p.successful_death_saves):
                # Heal one down member
                attacker.vp-=2
                heal, rolls = roll_dice("2T6")
                p.recover(heal)
                print(f"\t{HEAL}\t{attacker.name} runs and heal {p.name} for {heal} HP ({rolls})")
                print(f"\t{BLUE_HEART}\t{p.name}: {p.hp}/{p.max_hp}")
                return 1

    if attacker.is_mage:
        damage, rolls = attacker.attack(attacker.magic_spell.skill, magic=True)
        attacker.vp-=2
        print(f"\t{ATTACK_SPELL}\t{attacker.name} attacks {target.name} with {attacker.magic_spell.name} ({attacker.magic_spell.damage})", end=" ")
    else:
        damage, rolls = attacker.attack(attacker.melee_weapon.skill)
        print(f"\t{ATTACK_SWORD}\t{attacker.name} attacks {target.name} with {attacker.melee_weapon.name} ({attacker.melee_weapon.damage} + {sb})", end=" ")

    if damage > 0:
        print(f"hits for {damage}-{target.ac} damage ({flatten(rolls)})")
        if target.ac:
            damage-=target.ac

        if damage < 0:
            # Mitigate healing player with negative damage due to AC
            damage = 0

        target.take_damage(damage)
        if target.is_player:
            print(f"\t{BLUE_HEART}\t{target.name}: {target.hp}/{target.max_hp}")
        else:
            print(f"\t{GREEN_HEART}\t{target.name}: {target.hp}/{target.max_hp}")
        if target.hp <= 0:
            if target.is_player:
                if target.hp < (target.max_hp * -1):
                    print(f"\t{BIG_SKULL}\t{target.name} is perma dead...")
                    target.perma_death = True
                else:
                    print(f"\t{SMALL_SKULL}\t{target.name} is down")
            else:
                print(f"\t{BIG_SKULL}\t{target.name} is dead")
            attacker.targets.remove(target)

        if target.is_player:
            for o in opponents:
                if isinstance(o, list):
                    continue
                if o.hp > 0:
                    return 1
        else:
            for o in opponents:
                if isinstance(o, list):
                    for m in o:
                        if m.hp > 0:
                            return 1
        return 0
    else:
        print("misses...")
        return 1

# Weapons
unarmed = Weapon("Unarmed", "1T6", "STY")
dagger = Weapon("Dagger", "1T8", "SMI")
knife = Weapon("Knife", "1T8", "SMI")
shortsword = Weapon("ShortSword", "1T10", "STY")
ljungeld = Weapon("Ljungeld", "3T6", "PSY")
tentakel = Weapon("Tentacle", "1T8", "STY")
battleaxe = Weapon("BattleAxe", "1T8", "STY")

# Statistics metrics
total_samples = 100
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
        PartyMember("Hunter", sty=12, fys=13, smi=11, int_=13, psy=15, kar=11, ac=1, melee_weapon=knife, range_weapon=knife),
    ]
    monsters = [
        Monster("Monster#1", hp=9, ac=0, fv=9, melee_weapon=unarmed, sb="1T4"),
        Monster("Monster#2", hp=9, ac=0, fv=9, melee_weapon=unarmed, sb="1T4"),
        Monster("Monster#3", hp=9, ac=0, fv=9, melee_weapon=unarmed, sb="1T4"),
        Monster("Monster#4", hp=9, ac=0, fv=9, melee_weapon=unarmed, sb="1T4"),
        Monster("Boss#1", hp=30, ac=6, fv=15, melee_weapon=battleaxe, sb="1T6"),
#        Monster("Boss#2", hp=30, ac=6, fv=15, melee_weapon=battleaxe, sb="1T6"),
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
            print(f"\t{WARNING}\tMonster whipe...")
            break

        if not party_alive:
            pk_count = 0
            for p in party:
                if p.hp <= 0 and p.is_player:
                    pk_count+=1

            players_killed.append(pk_count)
            party_whipes.append(1)
            total_rounds.append(rounds)
            print(f"\t{WARNING}\tParty whipe...")
            break

        rounds+=1
        print(f"Round {rounds}", end=": ")
        #print(f"Initiative {[(p.name, p.hp) if hasattr(p, 'name') else [(sub_p.name, sub_p.hp) for sub_p in p] for p in fighters]}")
        print(f"Initiative {[p.name if hasattr(p, 'name') else [sub_p.name for sub_p in p] for p in fighters]}")
#        print(fighters)
        for p in fighters:
            if isinstance(p, list):
                # This is a monster phase
                if monster_party_alive:
                    for m in p:
                        party_alive = make_attack(m, fighters)
                        if not party_alive:
                            break 
            else:
                if party_alive:
                    # This is a player phase
                    if p.hp <= 0:
                        if p.successful_death_saves < 3 and p.failed_death_saves < 3:
                            death_save, rolls = roll_dice("1T20")
                            if death_save == 1:
                                p.successful_death_saves+=2
                                print(f"\t{EXPLOSION}{DICE}{GREEN_HEART}\t{p.name} manage to survive perma death this time {p.successful_death_saves}/3 ({rolls})")
                            elif death_save <= p.FYS:
                                p.successful_death_saves+=1
                                print(f"\t{DICE}{GREEN_HEART}\t{p.name} manage to survive perma death this time {p.successful_death_saves}/3 ({rolls})")
                            elif death_save == 20:
                                p.failed_death_saves+=2
                                print(f"\t{EXPLOSION}{DICE}{SMALL_SKULL}\t{p.name} rolled deamon roll on perma death {p.failed_death_saves}/3 ({rolls})")
                            else:
                                p.failed_death_saves+=1
                                print(f"\t{DICE}{SMALL_SKULL}\t{p.name} failed roll on perma death {p.failed_death_saves}/3 ({rolls})")

                            if p.successful_death_saves >= 3:
                                heal, rolls = roll_dice("1T6")
                                print(f"\t{HEAL}\t{p.name} successfully manage to save himself and getup again with {heal}/{p.max_hp}")
                                p.recover(heal)
                                party_alive = 1
                            elif p.failed_death_saves >= 3:
                                print(f"\t{BIG_SKULL}\t{p.name} has failed 3 death saves, the hero has fallen") 
                                p.perma_death = True
                    else:
                        monster_party_alive = make_attack(p, fighters)
                    if not monster_party_alive:
                        break

print("======================================")
#player_info = [(player.name, f"{player.hp}/{player.max_hp}") for player in party]
#monster_info = [(monster.name, f"{monster.hp}/{monster.max_hp}") for monster in monsters]
#print(f"Party: {player_info}")
#print(f"Monsters: {monster_info}")
print("Totalt:")
print(f"{sum(monsters_killed)} monstes killed ({sum(monsters_killed)/total_samples} killed/fight)")
print(f"{sum(monster_whipes)} monster whipes ({sum(monster_whipes)/total_samples} monster whipes/fight)")
print(f"{sum(players_killed)} players killed ({sum(players_killed)/total_samples} killed/fight)")
print(f"{sum(party_whipes)} party whipes ({sum(party_whipes)/total_samples} party whipes/fight)")
print(f"{total_samples} fights ({sum(total_rounds)/total_samples} rounds/fight)")