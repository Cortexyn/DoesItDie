"""Runs French and Spanish spell tooltips through the addon's real parser (DoesItDie.lua with Locale.lua and every
language file the .toc loads before it) and the real name tables, and checks what the addon would track.

The French tooltips are WoW: Forever's own (Wowhead, data env Forever, locale fr), from PR #11. The Spanish ones are
assembled from the Forever wording quoted in PR #6 (wowhead.com/forever/es) and are less complete. Every English
parse runs first, as in game, so these also check that English patterns never misread French or Spanish text.

    pip install lupa
    python tools/test_locale_fr_es.py
"""
import os
import sys

from lupa import lua51

HERE = os.path.dirname(os.path.abspath(__file__))
ADDON = os.path.join(HERE, "..", "DoesItDie")
src = open(os.path.join(ADDON, "DoesItDie.lua"), encoding="utf-8").read()
TOC = [line.strip() for line in open(os.path.join(ADDON, "DoesItDie.toc"), encoding="utf-8")]
LOCALE_PRELUDE = "local ns = {}\n" + "".join(
    ";(function(...)\n" + open(os.path.join(ADDON, name), encoding="utf-8").read() + "\nend)(\"DoesItDie\", ns)\n"
    for name in TOC[:TOC.index("DoesItDie.lua")] if name.endswith(".lua"))


def chunk(start_marker, end_marker):
    start = src.index(start_marker)
    return src[start:src.index(end_marker, start)]


lua = lua51.LuaRuntime(unpack_returned_tuples=True)
track, locale = lua.execute("\n".join([
    LOCALE_PRELUDE,
    "local function isSecret(v) return false end",
    chunk("local DEFAULT_TICK_INTERVAL", "local TICK_MATCH_WINDOW"),
    chunk("-- Tick intervals that differ", "-- User options"),
    chunk("local function schoolFromWords",
          "---------------------------------------------------------------------------\n-- DoT tracking"),
    """
    -- onPlayerCast's decision: ignore list by the client's name, parse, interval and school by name.
    return function(name, desc, comboPoints)
        if IGNORED_SPELLS[name] then return "ignored (list)" end
        local total, school, duration, stated = parseDot(desc, comboPoints)
        if not total then return "not tracked" end
        local interval = stated or KNOWN_TICK_INTERVALS[name] or DEFAULT_TICK_INTERVAL
        school = SCHOOL_BY_NAME[name] or school
        local ticks = math.max(1, math.floor(duration / interval + 0.5))
        return string.format("%d dmg, school %d, %gs, every %gs -> %d ticks of %.1f",
            total, school, duration, interval, ticks, total / ticks)
    end, ns.locale
    """,
]))

# (French spell name, French tooltip text, combo points or None, expected tracking result)
FR_CASES = [
    # --- tracked DoTs, every school and clause shape ---
    ("Corruption", "Corrompt la cible et lui inflige 40 points de dégâts d'Ombre en 12 sec.",
     None, "40 dmg, school 32, 12s, every 3s -> 4 ticks of 10.0"),
    ("Éclat lunaire", "Brûle l'ennemi et lui inflige 10 à 12 points de dégâts des Arcanes, puis 12 points de dégâts des Arcanes supplémentaires en 9 sec.",
     None, "12 dmg, school 64, 9s, every 3s -> 3 ticks of 4.0"),
    ("Mot de l'ombre : Douleur", "Un mot des ténèbres qui inflige 30 points de dégâts d'Ombre en 18 sec.",
     None, "30 dmg, school 32, 18s, every 3s -> 6 ticks of 5.0"),
    ("Peste dévorante", "La cible contracte une maladie qui lui inflige 128 points de dégâts d'Ombre en 24 sec. Les dégâts infligés par la Peste dévorante soignent le lanceur de sorts.",
     None, "128 dmg, school 32, 24s, every 3s -> 8 ticks of 16.0"),
    ("Morsure de serpent", "Mord la cible et lui inflige 10 points de dégâts de Nature en 15 sec. Une seule technique de Morsure ou de Piqûre peut être active sur la cible par chasseur.",
     None, "10 dmg, school 8, 15s, every 3s -> 5 ticks of 2.0"),
    ("Sarments", "Immobilise la cible sur place et lui inflige 20 points de dégâts de nature en 12 sec. Si la cible subit des dégâts, l'effet peut être interrompu.",
     None, "20 dmg, school 8, 12s, every 3s -> 4 ticks of 5.0"),
    ("Boule de feu", "Projette une boule ardente qui inflige 15 à 23 points de dégâts de Feu et 2 points de dégâts de Feu supplémentaires en 4 sec.",
     None, "2 dmg, school 4, 4s, every 2s -> 2 ticks of 1.0"),
    ("Explosion pyrotechnique", "Lance un immense rocher enflammé qui inflige 101 à 131 points de dégâts de Feu et 44 points de dégâts de Feu supplémentaires en 12 sec.",
     None, "44 dmg, school 4, 12s, every 3s -> 4 ticks of 11.0"),
    ("Flammes sacrées", "Consume l'ennemi dans des flammes sacrées et lui inflige 53 à 65 points de dégâts du Sacré et 20 points de dégâts du Sacré supplémentaires en 10 sec.",
     None, "20 dmg, school 2, 10s, every 2s -> 5 ticks of 4.0"),
    ("Plaie d'agonie", "Afflige la cible d'une plaie d'agonie qui lui inflige 72 points de dégâts d'ombre en 24 sec. Les dégâts sont progressifs et sont plus importants avec le temps.",
     None, "72 dmg, school 32, 24s, every 2s -> 12 ticks of 6.0"),
    # --- Physical bleeds: "points de dégâts" with no school, and "perd ... points de vie" ---
    ("Garrot", "Garrotte l'ennemi et lui inflige 144 points de dégâts en 18 sec, augmentés par votre puissance d'attaque. Il faut être camouflé et derrière la cible. Vous gagnez 1 point de combo.",
     None, "144 dmg, school 1, 18s, every 3s -> 6 ticks of 24.0"),
    ("Griffure", "Lacère la cible, lui infligeant 23 points de dégâts et 48 points de dégâts supplémentaires sur la durée en 9 sec. Vous gagnez 1 point de combo.",
     None, "48 dmg, school 1, 9s, every 3s -> 3 ticks of 16.0"),
    ("Traquenard", "Attaque la cible par surprise et l'étourdit pendant 2 sec en lui infligeant 90 points de dégâts en 18 sec. Vous devez être camouflé et derrière la cible. Vous gagnez 1 point de combo.",
     None, "90 dmg, school 1, 18s, every 3s -> 6 ticks of 15.0"),
    ("Pourfendre", "Blesse la cible. Elle saigne et perd 15 points de vie en 9 sec.",
     None, "15 dmg, school 1, 9s, every 3s -> 3 ticks of 5.0"),
    # --- health-drain rate (Siphon Life): school comes from SCHOOL_BY_NAME, not the text ---
    ("Siphon de vie", "Transfère 11 points de vie de la cible vers le lanceur ou la lanceuse toutes les 3 s. Dure 30 sec.",
     None, "110 dmg, school 32, 30s, every 3s -> 10 ticks of 11.0"),
    # --- finishers (Coup de grâce): per-combo table, clamped to the points spent ---
    ("Déchirure", "Coup de grâce qui inflige des dégâts sur la durée. Les dégâts augmentent avec le nombre de points de combo et votre puissance d'attaque : 1 point : 44 points de dégâts en 12 sec. 2 points : 71 points de dégâts en 12 sec. 3 points : 97 points de dégâts en 12 sec. 4 points : 124 points de dégâts en 12 sec. 5 points : 150 points de dégâts en 12 sec.",
     5, "150 dmg, school 1, 12s, every 2s -> 6 ticks of 25.0"),
    ("Déchirure", "Coup de grâce qui inflige des dégâts sur la durée. Les dégâts augmentent avec le nombre de points de combo et votre puissance d'attaque : 1 point : 44 points de dégâts en 12 sec. 2 points : 71 points de dégâts en 12 sec. 3 points : 97 points de dégâts en 12 sec. 4 points : 124 points de dégâts en 12 sec. 5 points : 150 points de dégâts en 12 sec.",
     1, "44 dmg, school 1, 12s, every 2s -> 6 ticks of 7.3"),
    ("Rupture", "Coup de grâce qui inflige des dégâts sur la durée. Les dégâts augmentent avec votre puissance d'attaque et l'effet dure plus longtemps selon le nombre de points de combo : 1 point : 25 points de dégâts en 8 s 2 points : 37 points de dégâts en 10 s 3 points : 51 points de dégâts en 12 s 4 points : 68 points de dégâts en 14 s 5 points : 87 points de dégâts en 16 s",
     5, "87 dmg, school 1, 16s, every 2s -> 8 ticks of 10.9"),
    # --- heal over time: never a DoT ---
    ("Rénovation", "Rend 45 points de vie à la cible en 15 sec.", None, "not tracked"),
    # --- direct-damage poison proc: no "en N sec", so not a DoT ---
    ("Poison instantané", "13 à 17 points de dégâts de nature.", None, "not tracked"),
    # --- ignored by name: several of these WOULD parse as a DoT if the French name weren't mapped ---
    ("Pluie de feu", "Invoque une pluie de feu qui brûle les adversaires dans la zone d'effet.",
     None, "ignored (list)"),
    ("Flammes infernales", "Enflamme la zone qui entoure le lanceur de sorts.", None, "ignored (list)"),
    ("Choc de flammes", "Invoque un pilier de feu qui inflige 55 à 71 points de dégâts de feu et 44 points de dégâts de feu supplémentaires en 8 sec.",
     None, "ignored (list)"),
    ("Salve", "Tire une salve sur la zone ciblée. Inflige 70 points de dégâts des arcanes toutes les 1 s pendant 6 sec.",
     None, "ignored (list)"),
    ("Ouragan", "Crée une violente tempête qui inflige 69 points de dégâts de nature toutes les 1 s. Dure 10 sec.",
     None, "ignored (list)"),
    ("Consécration", "Consacre le sol et inflige 16 points de dégâts du sacré en 8 sec aux adversaires qui entrent dans la zone.",
     None, "ignored (list)"),
    ("Projectiles des arcanes", "Lance des projectiles des arcanes sur l'ennemi et inflige 25 points de dégâts des Arcanes toutes les secondes pendant 3 sec.",
     None, "ignored (list)"),
    ("Éclats stellaires", "Une pluie d'éclats lunaires s'abat sur la tête de l'ennemi et lui inflige 162 points de dégâts des Arcanes en 6 sec.",
     None, "ignored (list)"),
    ("Drain de vie", "Transfère 10 points de vie de la cible vers le personnage lanceur toutes les 1 s. Dure 5 sec.",
     None, "ignored (list)"),
    ("Siphon d'âme", "Draine l'âme de la cible et lui inflige 85 points de dégâts d'ombre en 15 sec.",
     None, "ignored (list)"),
    ("Fouet mental", "Attaque l'esprit de la cible avec l'énergie de l'ombre, ce qui lui inflige 63 points de dégâts d'ombre en 3 sec et réduit sa vitesse de déplacement de 50 %.",
     None, "ignored (list)"),
    ("Drain de mana", "Transfère 44 points de mana toutes les 1 s de la cible vers le personnage lanceur. Dure 5 sec.",
     None, "ignored (list)"),
    ("Captation de vie", "Rend 12 points de vie toutes les secondes au familier du personnage lanceur pendant 10 sec.",
     None, "ignored (list)"),
    # --- non-breaking space (U+00A0) between the number and "points", exactly as the French client sends it;
    #     lupa re-encodes " " to the UTF-8 bytes \194\160. Both were logged NOT READ in-game before the fix.
    ("Plaie d'agonie", "Afflige la cible d’une plaie d’agonie qui lui inflige 78 points de dégâts d’ombre en 24 sec. Les dégâts sont progressifs et sont plus importants avec le temps. La cible ne peut être victime que d’une plaie par démoniste à la fois.",
     None, "78 dmg, school 32, 24s, every 2s -> 12 ticks of 6.5"),
    # Immolation also reorders to "points supplémentaires de dégâts"; both NBSP and word order are handled.
    ("Immolation", "Brûle l’ennemi et lui inflige 22 points de dégâts de feu, puis 32 points supplémentaires de dégâts de feu en 15 sec.",
     None, "32 dmg, school 4, 15s, every 3s -> 5 ticks of 6.4"),
    # Finisher with NBSP in the per-combo table (tested, not re-verified in-game).
    ("Déchirure", "Coup de grâce qui inflige des dégâts sur la durée. Les dégâts augmentent avec le nombre de points de combo et votre puissance d'attaque : 1 point : 44 points de dégâts en 12 sec. 2 points : 71 points de dégâts en 12 sec. 3 points : 97 points de dégâts en 12 sec. 4 points : 124 points de dégâts en 12 sec. 5 points : 150 points de dégâts en 12 sec.",
     5, "150 dmg, school 1, 12s, every 2s -> 6 ticks of 25.0"),
]


# (Spanish spell name, tooltip text, combo points or None, expected tracking result)
ES_CASES = [
    ("Corrupción", "Corrompe al objetivo, causando 40 p. de daño de las Sombras durante 12 s.",
     None, "40 dmg, school 32, 12s, every 3s -> 4 ticks of 10.0"),
    ("Corrupción", "Corrompe al objetivo, causando 1.314 p. de daño de las Sombras durante 18 s.",
     None, "1314 dmg, school 32, 18s, every 3s -> 6 ticks of 219.0"),
    ("Inmolar", "Quema al enemigo y le inflige 11 p. de daño de Fuego y 20 p. de daño de Fuego más durante 15 s.",
     None, "20 dmg, school 4, 15s, every 3s -> 5 ticks of 4.0"),
    ("Bola de Fuego", "Lanza una bola de fuego que inflige 14 p. de daño de Fuego y 2 p. de daño de Fuego extra durante 4 s.",
     None, "2 dmg, school 4, 4s, every 2s -> 2 ticks of 1.0"),
    ("Arañazo", "Araña al objetivo y le inflige 19 p. de daño y un daño extra de 48 p. durante 9 s. Otorga 1 punto de combo.",
     None, "48 dmg, school 1, 9s, every 3s -> 3 ticks of 16.0"),
    ("Succionar vida", "Transfiere 11 p. de salud del objetivo al taumaturgo cada 3 s. Dura 30 s.",
     None, "110 dmg, school 32, 30s, every 3s -> 10 ticks of 11.0"),
    ("Destripar", "Remate que inflige daño en el tiempo. El daño aumenta con los puntos de combo: 1 punto: 44 de daño durante 12 s. 2 puntos: 71 de daño durante 12 s. 5 puntos: 150 de daño durante 12 s.",
     2, "71 dmg, school 1, 12s, every 2s -> 6 ticks of 11.8"),
    ("Ruptura", "Remate que causa daño en el tiempo. Dura más por punto de combo: 1 punto: 25 p. de daño durante 8 s 2 puntos: 37 p. de daño durante 10 s",
     1, "25 dmg, school 1, 8s, every 2s -> 4 ticks of 6.2"),
    ("Hacer trizas", "Remate que aumenta la velocidad de ataque un 40%. Dura más por punto de combo: 1 punto: 9 s 2 puntos: 12 s",
     None, "not tracked"),
    ("Rejuvenecimiento", "Cura el objetivo en 45 p. de daño durante 15 s.", None, "not tracked"),
    ("Veneno instantáneo", "Cubre un arma con veneno que dura 30 min. Cada golpe puede inflijir 13 p. de daño de Naturaleza durante 4 s.",
     None, "not tracked"),
    ("Lluvia de Fuego", "Invoca una lluvia de fuego que inflige 42 p. de daño de Fuego durante 8 s.", None, "ignored (list)"),
    ("Despelleje mental", "Asalta la mente del objetivo, causando 75 p. de daño de las Sombras durante 3 s.", None, "ignored (list)"),
]

# Combo points, finishers and name lookups the cases above don't cover.
EXTRA = [
    ("fr combo awarded (Garrot)", locale.comboPointsAwarded("... Vous gagnez 1 point de combo."), 1),
    ("fr no combo line", locale.comboPointsAwarded("Inflige 40 points de dégâts d'Ombre en 12 sec."), None),
    # combo line with a non-breaking space (tested, not re-verified in-game)
    ("fr combo awarded (NBSP)", locale.comboPointsAwarded("... Vous gagnez 1 point de combo."), 1),
    ("fr finisher (Déchirure)", locale.isFinisher("Coup de grâce qui inflige des dégâts sur la durée."), True),
    ("fr not a finisher", locale.isFinisher("Corrompt la cible et lui inflige 40 points de dégâts."), False),
    ("es combo awarded (punto)", locale.comboPointsAwarded("Otorga 1 punto de combo."), 1),
    ("es combo awarded (p.)", locale.comboPointsAwarded("Otorga 2 p. de combo."), 2),
    ("es finisher (Destripar)", locale.isFinisher("Remate que inflige daño en el tiempo."), True),
    ("es not a finisher", locale.isFinisher("Corrompe al objetivo."), False),
    ("en finisher still English", locale.isFinisher("Finishing move that causes damage over time."), False),
]

if __name__ == "__main__":
    failures = 0
    for lang, cases in (("fr", FR_CASES), ("es", ES_CASES)):
        width = max(len(c[0]) for c in cases)
        for name, desc, cp, expect in cases:
            got = track(name, desc, cp)
            ok = got == expect
            failures += not ok
            print(f"{'PASS' if ok else 'FAIL'}  {lang} {name:<{width}}  {got}" + ("" if ok else f"   (expected {expect})"))
        print()
    for label, got, expect in EXTRA:
        ok = got == expect
        failures += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {label:<30} {got}" + ("" if ok else f"   (expected {expect})"))
    print()
    print("all passed" if not failures else f"{failures} FAILED")
    sys.exit(1 if failures else 0)
