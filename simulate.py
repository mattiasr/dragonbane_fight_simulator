#!/usr/bin/env python3
import copy
import random
import time
from typing import Tuple, Union

ATTACK_SPELL = "\U00002728"
ATTACK_SWORD = "\u2694"
BIG_SKULL = "\U0001F480"
BLUE_HEART = "\U0001F499"
CRIT = "\U0001F4A5"
DEAMON = "\U0001F479"
DICE = "\U0001F3B2"
EXPLOSION = "\U0001F4A5"
EYES = "\U0001F440"
FAILED = "\u274C"
GREEN_HEART = "\U0001F49A"
HEAL = "\U0001F33F"
INFO = "\U0001F6C8"
OK = "\u2705"
RAINBOW = "\U0001F308"
SMALL_SKULL = "\u2620"
WARNING = "\U000026A0\U0000FE0F"


class Weapon:
    def __init__(self, name, damage, skill):
        self.name = name
        self.damage = damage
        self.skill = skill

    def roll_damage(self, is_crit=False) -> Tuple[int, list]:
        total_dmg = 0
        total_rolls = []
        if is_crit:
            damage, rolls = roll_dice(self.damage)
            total_rolls.append(rolls)
            total_dmg += damage

        damage, rolls = roll_dice(self.damage)
        total_rolls.append(rolls)
        total_dmg += damage

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

    def take_damage(self, amount: int) -> None:
        self.hp -= amount

    def heal_damage(self, amount: int) -> None:
        self.hp += amount

    def recover(self, amount: int) -> None:
        self.hp = 0
        self.successful_death_saves = 0
        self.failed_death_saves = 0
        self.hp += amount

    def attack(
        self, skill=None, fv=None, skadebonus=None, magic=False
    ) -> Tuple[int, int, list]:
        total_damage = 0
        damage = 0

        # Determine FV and Skadebonus based on character type
        if fv is None:
            fv = get_grundchans(getattr(self, skill, 0)) * 2
        if skadebonus is None:
            skadebonus = get_skadebonus(getattr(self, skill, 0))

        total_rolls = []

        fv_roll, fv_rolls = roll_dice("1T20")

        if fv_roll == 1:
            # Crit hit
            print(
                f"\t{CRIT}\t{self.name} rolls FV: {fv_roll} against FV: {fv} ({fv_rolls})"
            )
            if magic:
                damage, rolls = self.magic_spell.roll_damage(is_crit=True)
            else:
                damage, rolls = self.melee_weapon.roll_damage(is_crit=True)
            total_rolls.append(rolls)
            total_damage += damage
        elif fv_roll == 20:
            print(
                f"\t{DEAMON}\t{self.name} rolls FV: {fv_roll} against FV: {fv} ({fv_rolls})"
            )
            return fv_roll, 0, []
        elif fv_roll > fv:
            # Failed roll
            print(
                f"\t{FAILED}\t{self.name} rolls FV: {fv_roll} against FV: {fv} ({fv_rolls})"
            )
            return fv_roll, 0, []
        else:
            # Normal hit
            print(
                f"\t{OK}\t{self.name} rolls FV: {fv_roll} against FV: {fv} ({fv_rolls})"
            )
            if magic:
                damage, rolls = self.magic_spell.roll_damage()
            else:
                damage, rolls = self.melee_weapon.roll_damage()
            total_rolls.append(rolls)
            total_damage += damage

        # Do we have Skadebonus?
        if skadebonus and not magic:
            damage, rolls = roll_dice(skadebonus)
            total_rolls.append(rolls)
            total_damage += damage

        return fv_roll, total_damage, total_rolls


class Character(BaseStats):
    def __init__(
        self,
        name,
        sty,
        fys,
        smi,
        int_,
        psy,
        kar,
        ac=0,
        melee_weapon=None,
        range_weapon=None,
        magic_spell=None,
        is_mage=False,
        can_heal=True,
    ):
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
        return super().attack(
            skill=skill, skadebonus=get_skadebonus(getattr(self, skill, 0)), magic=magic
        )


class NPC(BaseStats):
    def __init__(self, name, hp, ac, fv, melee_weapon, magic_spell=None, sb=0):
        super().__init__(
            name, ac, hp=hp, melee_weapon=melee_weapon, magic_spell=magic_spell
        )
        self.fv = fv
        self.sb = sb
        self.targets = []
        self.is_player = False
        self.magic_spell = magic_spell

    def attack(self, skill=None, magic=None):
        return super().attack(fv=self.fv, skadebonus=self.sb)


class Boss(NPC):
    def __init__(self, name, hp, ac, fv, melee_weapon, magic_spell=None, sb=0):
        super().__init__(name, hp, ac, fv, melee_weapon, magic_spell=magic_spell, sb=sb)


def opponent_alive(fighters: list) -> int:
    max_count = sum([1 for f in fighters if isinstance(f, (NPC, Boss))])
    kill_count = sum([1 for f in fighters if isinstance(f, (NPC, Boss)) and f.hp <= 0])
    if kill_count == max_count:
        return 0
    else:
        return 1


def party_alive(fighters: list) -> int:
    max_count = sum([1 for f in fighters if isinstance(f, Character)])
    kill_count = sum([1 for f in fighters if isinstance(f, Character) and f.hp <= 0])
    if kill_count == max_count:
        return 0
    else:
        return 1


def roll_dice(dice_roll: str) -> Tuple[int, list]:
    rolls, max_roll = dice_roll.split("T")
    dice_type = f"T{max_roll}"
    total_sum = 0
    total_rolls = {}
    total_rolls[dice_type] = []
    i = 1

    while i <= int(rolls):
        roll = random.randint(1, int(max_roll))
        total_rolls[dice_type].append(roll)
        total_sum += roll
        i += 1

    return total_sum, total_rolls


def flatten(nested_list: list) -> list:
    flat_list = []
    for item in nested_list:
        if isinstance(item, list):
            flat_list.extend(flatten(item))  # Recursively flatten sublists
        else:
            flat_list.append(item)
    return flat_list


def get_skadebonus(value: int) -> Union[int, str]:
    if value <= 11:
        return 0
    elif value > 11 and value <= 16:
        return "1T4"
    elif value > 16:
        return "1T6"


def get_grundchans(value: int) -> int:
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


def decorate_initiative(fighters: list) -> list:
    live_dead = []
    for p in fighters:
        if isinstance(p, list):
            inner_list = []
            for m in p:
                if m.hp <= 0:
                    inner_list.append(f"{BIG_SKULL} {m.name}")
                else:
                    inner_list.append(f"{GREEN_HEART} {m.name}")
            live_dead.append(inner_list)
        elif isinstance(p, (NPC, Boss)):
            if p.hp <= 0:
                live_dead.append(f"{BIG_SKULL} {p.name}")
            else:
                live_dead.append(f"{GREEN_HEART} {p.name}")
        else:
            if p.hp <= 0 and p.perma_death:
                live_dead.append(f"{BIG_SKULL} {p.name}")
            elif p.hp <= 0:
                live_dead.append(f"{SMALL_SKULL} {p.name}")
            else:
                live_dead.append(f"{BLUE_HEART} {p.name}")
    return live_dead


def make_death_roll(player: Character) -> int:
    death_save, rolls = roll_dice("1T20")
    if death_save == 1:
        p.successful_death_saves += 2
        print(
            f"\t{CRIT}{DICE}{GREEN_HEART}\t{p.name} manage to survive perma death this time {p.successful_death_saves}/3 ({rolls})"
        )
    elif death_save <= p.FYS:
        p.successful_death_saves += 1
        print(
            f"\t{DICE}{GREEN_HEART}\t{p.name} manage to survive perma death this time {p.successful_death_saves}/3 ({rolls})"
        )
    elif death_save == 20:
        p.failed_death_saves += 2
        print(
            f"\t{DEAMON}{DICE}{SMALL_SKULL}\t{p.name} rolled deamon roll on perma death {p.failed_death_saves}/3 ({rolls})"
        )
    else:
        p.failed_death_saves += 1
        print(
            f"\t{DICE}{SMALL_SKULL}\t{p.name} failed roll on perma death {p.failed_death_saves}/3 ({rolls})"
        )

    if p.successful_death_saves >= 3:
        heal, rolls = roll_dice("1T6")
        print(
            f"\t{HEAL}\t{p.name} successfully manage to save himself and getup again with {heal}/{p.max_hp}"
        )
        p.recover(heal)
        return 1
    elif p.failed_death_saves >= 3:
        print(f"\t{BIG_SKULL}\t{p.name} has failed 3 death saves, the hero has fallen")
        p.perma_death = True
    return 0


def make_attack(attacker: BaseStats, opponents: list) -> None:
    # Remove dead ppl from your target list
    for t in attacker.targets:
        if t.hp <= 0:
            attacker.targets.remove(t)

    if attacker.targets == []:
        opponents = flatten(opponents)
        filter_opponents = []
        if isinstance(attacker, Character):
            filter_opponents = [
                o for o in opponents if isinstance(o, (NPC, Boss)) and o.hp > 0
            ]
        else:
            filter_opponents = [
                o for o in opponents if isinstance(o, Character) and o.hp > 0
            ]

        if filter_opponents == []:
            return 1

        give_wizard_a_chance = 0
        while True:
            pick_target = random.choice(filter_opponents)

            if pick_target.is_mage and give_wizard_a_chance == 0:
                print(
                    f"\t{EYES}\t{attacker.name} looks at {pick_target.name}, i will deal with you later..."
                )
                give_wizard_a_chance += 1
                continue
            else:
                attacker.targets.append(pick_target)
                break

    target = random.choice(attacker.targets)
    sb = 0
    if hasattr(attacker, "sb"):
        sb = attacker.sb
    else:
        sb = get_skadebonus(getattr(attacker, attacker.melee_weapon.skill, 0))

    damage = 0
    rolls = []

    if attacker.is_mage:
        if attacker.vp < 2:
            # Out of juice, should catch breath one round.
            gain_vp, rolls = roll_dice("1T6")
            attacker.vp += gain_vp
            print(
                f"\t{HEAL}\t{attacker.name} rest to be able to cast more, gain {gain_vp} VP ({rolls})"
            )
            return

    if attacker.is_mage and attacker.can_heal:
        # Check if someone down
        for p in opponents:
            if isinstance(p, list):
                continue
            if (
                p.hp <= 0
                and not p.perma_death
                and (p.failed_death_saves or p.successful_death_saves)
            ):
                # Heal one down member
                attacker.vp -= 2
                heal, rolls = roll_dice("2T6")
                p.recover(heal)
                print(
                    f"\t{HEAL}\t{attacker.name} runs and heal {p.name} for {heal} HP ({rolls})"
                )
                print(f"\t{BLUE_HEART}\t{p.name}: {p.hp}/{p.max_hp}")
                return

    if attacker.is_mage:
        fv_roll, damage, rolls = attacker.attack(attacker.magic_spell.skill, magic=True)
        attacker.vp -= 2
        print(
            f"\t{ATTACK_SPELL}\t{attacker.name} attacks {target.name} with {attacker.magic_spell.name} ({attacker.magic_spell.damage})",
            end=" ",
        )
    else:
        fv_roll, damage, rolls = attacker.attack(attacker.melee_weapon.skill)
        print(
            f"\t{ATTACK_SWORD}\t{attacker.name} attacks {target.name} with {attacker.melee_weapon.name} ({attacker.melee_weapon.damage} + {sb})",
            end=" ",
        )

    if damage > 0:
        print(f"hits for {damage}-{target.ac} damage ({flatten(rolls)})")
        if target.ac:
            damage -= target.ac

        if damage < 0:
            # Mitigate healing player with negative damage due to AC
            damage = 0

        target.take_damage(damage)
        heart_color = GREEN_HEART
        if isinstance(target, Character):
            heart_color = BLUE_HEART

        print(f"\t{heart_color}\t{target.name}: {target.hp}/{target.max_hp}")

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
    else:
        print("misses...")


# Weapons
unarmed = Weapon("Unarmed", "1T6", "STY")
dagger = Weapon("Dagger", "1T8", "SMI")
knife = Weapon("Knife", "1T8", "SMI")
shortspear = Weapon("ShortSpear", "1T10", "SMI")
shortsword = Weapon("ShortSword", "1T10", "STY")
ljungeld = Weapon("Ljungeld", "2T6", "PSY")
tentakel = Weapon("Tentacle", "1T8", "STY")
battleaxe = Weapon("BattleAxe", "2T8", "STY")
trident = Weapon("Trident", "2T6", "STY")

# Statistics metrics
total_samples = 1
total_rounds = []
players_killed = []
monsters_killed = []
party_whipes = []
monster_whipes = []

start_time = time.time()

# Let the fights begin
# ===========================================================================
for _ in range(total_samples):
    party = [
        Character(
            "Mage",
            sty=11,
            fys=12,
            smi=10,
            int_=12,
            psy=13,
            kar=5,
            ac=0,
            melee_weapon=dagger,
            magic_spell=ljungeld,
            is_mage=True,
        ),
        Character(
            "Thieve",
            sty=14,
            fys=16,
            smi=18,
            int_=15,
            psy=12,
            kar=8,
            ac=0,
            melee_weapon=dagger,
            range_weapon=knife,
        ),
        Character(
            "Bard",
            sty=14,
            fys=15,
            smi=15,
            int_=12,
            psy=13,
            kar=18,
            ac=0,
            melee_weapon=knife,
            range_weapon=knife,
        ),
        Character(
            "Hunter",
            sty=12,
            fys=13,
            smi=11,
            int_=13,
            psy=15,
            kar=11,
            ac=1,
            melee_weapon=knife,
            range_weapon=knife,
        ),
    ]
    npc = [
        NPC("Thug#1", hp=10, ac=2, fv=10, melee_weapon=shortspear, sb="1T4"),
        NPC("Thug#2", hp=10, ac=2, fv=10, melee_weapon=shortspear, sb="1T4"),
    ]

    bosses = [
        Boss("Boss#1", hp=30, ac=2, fv=14, melee_weapon=trident, sb="1T6"),
    ]
    fighters = copy.deepcopy(party)
    #    fighters.append(npc)
    fighters.append(
        Boss("WrongBoss#1", hp=30, ac=2, fv=14, melee_weapon=trident, sb="1T6")
    )

    if bosses:
        for boss in bosses:
            # Bosses will have own initiative
            fighters.append(boss)

    rounds = 0
    while True:
        flat_fighters = flatten(fighters)
        max_player_kill_count = sum(
            [1 for f in flat_fighters if isinstance(f, Character)]
        )
        max_monster_kill_count = sum(
            [1 for f in flat_fighters if isinstance(f, (NPC, Boss))]
        )
        player_kill_count = sum(
            [1 for f in flat_fighters if isinstance(f, Character) and f.hp <= 0]
        )
        monster_kill_count = sum(
            [1 for f in flat_fighters if isinstance(f, (NPC, Boss)) and f.hp <= 0]
        )

        random.shuffle(fighters)

        if not opponent_alive(flat_fighters):
            monsters_killed.append(monster_kill_count)
            players_killed.append(player_kill_count)
            monster_whipes.append(1)
            total_rounds.append(rounds)
            print(f"\t{RAINBOW}\tMonster whipe...")
            break

        if not party_alive(flat_fighters):
            monsters_killed.append(monster_kill_count)
            players_killed.append(player_kill_count)
            party_whipes.append(1)
            total_rounds.append(rounds)
            print(f"\t{WARNING}\tParty whipe...")
            break

        rounds += 1

        print(f"Round {rounds}", end=": ")
        print(
            f"Initiative {monster_kill_count}, {player_kill_count} - {decorate_initiative(fighters)}"
        )
        for p in fighters:
            if isinstance(p, list):
                # This is a monster phase
                if party_alive(flat_fighters) and opponent_alive(flat_fighters):
                    for m in p:
                        if isinstance(m, (NPC, Boss)):
                            make_attack(m, fighters)
                            if not party_alive(flat_fighters):
                                break
            else:
                # This is a player phase
                if isinstance(p, Character):
                    if party_alive(flat_fighters) and opponent_alive(flat_fighters):
                        if (
                            p.hp <= 0
                            and p.successful_death_saves < 3
                            and p.failed_death_saves < 3
                            and p.perma_death is not True
                        ):
                            make_death_roll(p)
                        else:
                            make_attack(p, fighters)

                        if not opponent_alive(flat_fighters):
                            break

                # If someone put a NPC/Boss without an list
                else:
                    if party_alive(flat_fighters) and opponent_alive(flat_fighters):
                        make_attack(p, fighters)
                        if not party_alive(flat_fighters):
                            break

end_time = time.time()
elapsed_time = end_time - start_time
percentage_of_success = (sum(monster_whipes) / total_samples) * 100

print("======================================")
print("Summary:")
print(
    f"{sum(monsters_killed)} monstes killed ({sum(monsters_killed)/total_samples} killed/fight)"
)
print(
    f"{sum(monster_whipes)} monster whipes ({sum(monster_whipes)/total_samples} monster whipes/fight)"
)
print(
    f"{sum(players_killed)} players killed ({sum(players_killed)/total_samples} killed/fight)"
)
print(
    f"{sum(party_whipes)} party whipes ({sum(party_whipes)/total_samples} party whipes/fight)"
)
print(f"{total_samples} fights ({sum(total_rounds)/total_samples} rounds/fight)")
print(f"Theres a {percentage_of_success:.2f}% Chance of success for the party")
print(f"Execution took {elapsed_time:.2f} seconds")
