"""Runs WoW: Forever's own Brazilian Portuguese (ptBR) tooltips through the addon's real parser (DoesItDie.lua
with Locale.lua and every language file the .toc loads before it) and the real name tables, and checks what the
addon would track. The tooltips are Wowhead's (tooltip API, data env Forever, locale pt; issue #19), with the
three amounts Wowhead shows as unresolved formulas replaced by numbers, as the game shows them. English patterns
run first, as in game, so this also checks that they (and Spanish's) never misread Portuguese text.

    pip install lupa
    python tools/test_locale_pt.py
"""
import os
import sys

import locale  # noqa: E402
locale.setlocale(locale.LC_CTYPE, "C")  # as in WoW: Lua's %d and %s follow the C library's locale
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


# (spell id, name, tooltip, combo points or None, expected tracking result)
CASES = [
    (172, 'Corrupção',
     'Corrompe o alvo, causando 40 de dano de Sombra ao longo de 12 s.',
     None, '40 dmg, school 32, 12s, every 3s -> 4 ticks of 10.0'),
    (348, 'Imolação',
     'Queima o inimigo, causando 11 de dano de Fogo e mais 15 de dano de Fogo ao longo de 15 s.',
     None, '15 dmg, school 4, 15s, every 3s -> 5 ticks of 3.0'),
    (589, 'Palavra Sombria: Dor',
     'Palavra de trevas que causa 30 de dano de Sombra ao longo de 18 s.',
     None, '30 dmg, school 32, 18s, every 3s -> 6 ticks of 5.0'),
    (2944, 'Peste Devoradora',
     'Causa uma doença no alvo que causa 128 de dano de Sombra ao longo de 24 s. O dano causado pela Peste Devoradora cura o lançador.',
     None, '128 dmg, school 32, 24s, every 3s -> 8 ticks of 16.0'),
    (8921, 'Fogo Lunar',
     'Queima o inimigo causando 10 para 12 de dano Arcano e mais 12 de dano Arcano ao longo de 9 s.',
     None, '12 dmg, school 64, 9s, every 3s -> 3 ticks of 4.0'),
    (5570, 'Nuvem de Insetos',
     'O alvo inimigo é atacado por uma nuvem de insetos, reduzindo em 2% a chance de acerto com ataques e causando 48 de dano de Natureza ao longo de 12 s.',
     None, '48 dmg, school 8, 12s, every 2s -> 6 ticks of 8.0'),
    (980, 'Ruína da Agonia',
     'Aflige o alvo com uma agonia, causando 72 de dano de Sombra ao longo de 24 s. De início, esse dano é causado lentamente, mas vai se intensificando conforme a Ruína se aproxima do fim da duração. Cada alvo só pode ter uma Ruína ativa por Bruxo ao mesmo tempo.',
     None, '72 dmg, school 32, 24s, every 2s -> 12 ticks of 6.0'),
    (14914, 'Fogo Sagrado',
     'Consome o inimigo em chamas Sagradas, que causam 53 para 65 de dano Sagrado e mais 20 de dano Sagrado ao longo de 10 s.',
     None, '20 dmg, school 2, 10s, every 2s -> 5 ticks of 4.0'),
    (133, 'Bola de Fogo',
     'Lança uma bola flamejante que causa 15 para 23 de dano de Fogo e mais 2 de dano de Fogo ao longo de 4 s.',
     None, '2 dmg, school 4, 4s, every 2s -> 2 ticks of 1.0'),
    (11366, 'Ignimpacto',
     'Lança um pedregulho flamejante imenso que causa 101 para 131 de dano de Fogo e mais 44 de dano de Fogo ao longo de 12 s.',
     None, '44 dmg, school 4, 12s, every 3s -> 4 ticks of 11.0'),
    (8050, 'Choque Flamejante',
     'Calcina instantaneamente o alvo, causando 24 de dano de Fogo imediatamente e mais 28 de dano de Fogo ao longo de 12 s.',
     None, '28 dmg, school 4, 12s, every 3s -> 4 ticks of 7.0'),
    (8052, 'Choque Flamejante',
     'Calcina o alvo, causando 38 de dano de Fogo imediatamente e mais 32 de dano de Fogo ao longo de 12 s.',
     None, '32 dmg, school 4, 12s, every 3s -> 4 ticks of 8.0'),
    (339, 'Raízes Enredantes',
     'Enraíza o alvo e causa 20 de dano de Natureza ao longo de 12 s. O dano causado ao alvo tem chance de interromper este efeito. Você [Exuberância',
     None, '20 dmg, school 8, 12s, every 3s -> 4 ticks of 5.0'),
    (1978, 'Picada de Serpente',
     'Envenena o alvo, causando 10 de dano de Natureza ao longo de 15 s. Os inimigos só podem ter uma Picada de cada Caçador por vez.',
     None, '10 dmg, school 8, 15s, every 3s -> 5 ticks of 2.0'),
    (13795, 'Armadilha Imolante',
     'Coloca uma armadilha de Fogo que queima o primeiro inimigo que se aproximar, causando 105 de dano de Fogo ao longo de 15 s. A armadilha persiste por 1 min. Só pode haver uma armadilha de Fogo ativa de cada vez.',
     None, '105 dmg, school 4, 15s, every 3s -> 5 ticks of 21.0'),
    (1822, 'Estraçalhar',
     'Estraçalha o alvo, causando 23 de dano e mais 48 de dano ao longo de 9 s. Concede 1 ponto de combo.',
     None, '48 dmg, school 1, 9s, every 3s -> 3 ticks of 16.0'),
    (703, 'Garrote',
     'Garroteia o inimigo, causando 144 de dano ao longo de 18 s. O dano aumenta de acordo com o seu Poder de Ataque. É preciso estar furtivo e atrás do alvo. Concede 1 ponto de combo.',
     None, '144 dmg, school 1, 18s, every 3s -> 6 ticks of 24.0'),
    (772, 'Dilacerar',
     'Fere o alvo, fazendo-o sangrar. O sangramento causa 15 de dano ao longo de 9 s.',
     None, '15 dmg, school 1, 9s, every 3s -> 3 ticks of 5.0'),
    (9005, 'Pulo do Gato',
     'Salta contra o alvo, atordoando-o por 2 s e causando 90 de dano ao longo de 18 s. É preciso estar furtivo e atrás do alvo. Concede 1 ponto de combo.',
     None, '90 dmg, school 1, 18s, every 3s -> 6 ticks of 15.0'),
    (18265, 'Sifão de Vida',
     'Transfere 11 pontos de vida do alvo para o lançador a cada 3 s. Dura 30 s.',
     None, '110 dmg, school 32, 30s, every 3s -> 10 ticks of 11.0'),
    (1079, 'Rasgar',
     'Golpe final que causa dano ao longo do tempo. O dano aumenta em função dos pontos de combo e do seu Poder de Ataque:\n \xa0 1 ponto: 44 de dano ao longo de 12 s.\n \xa0 2 pontos: 71 de dano ao longo de 12 s.\n \xa0 3 pontos: 97 de dano ao longo de 12 s.\n \xa0 4 pontos: 124 de dano ao longo de 12 s.\n \xa0 5 pontos: 150 de dano ao longo de 12 s.',
     5, '150 dmg, school 1, 12s, every 2s -> 6 ticks of 25.0'),
    (1079, 'Rasgar',
     'Golpe final que causa dano ao longo do tempo. O dano aumenta em função dos pontos de combo e do seu Poder de Ataque:\n \xa0 1 ponto: 44 de dano ao longo de 12 s.\n \xa0 2 pontos: 71 de dano ao longo de 12 s.\n \xa0 3 pontos: 97 de dano ao longo de 12 s.\n \xa0 4 pontos: 124 de dano ao longo de 12 s.\n \xa0 5 pontos: 150 de dano ao longo de 12 s.',
     1, '44 dmg, school 1, 12s, every 2s -> 6 ticks of 7.3'),
    (1943, 'Ruptura',
     'Golpe final que causa dano ao longo do tempo. O dano aumenta em função do seu Poder de Ataque. A duração aumenta em função dos pontos de combo:\n \xa0 1 ponto: 25 de dano ao longo de 8 s.\n \xa0 2 pontos: 37 de dano ao longo de 10 s.\n \xa0 3 pontos: 51 de dano ao longo de 12 s.\n \xa0 4 pontos: 68 de dano ao longo de 14 s.\n \xa0 5 pontos: 87 de dano ao longo de 16 s.',
     5, '87 dmg, school 1, 16s, every 2s -> 8 ticks of 10.9'),
    (1943, 'Ruptura',
     'Golpe final que causa dano ao longo do tempo. O dano aumenta em função do seu Poder de Ataque. A duração aumenta em função dos pontos de combo:\n \xa0 1 ponto: 25 de dano ao longo de 8 s.\n \xa0 2 pontos: 37 de dano ao longo de 10 s.\n \xa0 3 pontos: 51 de dano ao longo de 12 s.\n \xa0 4 pontos: 68 de dano ao longo de 14 s.\n \xa0 5 pontos: 87 de dano ao longo de 16 s.',
     1, '25 dmg, school 1, 8s, every 2s -> 4 ticks of 6.2'),
    (139, 'Renovar',
     'Cura 45 pontos de vida do alvo ao longo de 15 s.',
     None, 'not tracked'),
    (774, 'Rejuvenescer',
     'Cura 32 pontos de vida do alvo ao longo de 12 s.',
     None, 'not tracked'),
    (2823, 'Veneno Mortal',
     'Cobre a arma com um veneno que dura 30 min.\nCada acerto tem 30% de chance de envenenar o inimigo, causando 24 de dano de Natureza ao longo de 12 s. Acumula até 5 vezes em um único alvo. 90 cargas.',
     None, 'not tracked'),
    (8679, 'Veneno Instantâneo',
     'Cobre a arma com um veneno que dura 30 min.\nCada acerto tem 20% de chance de envenenar o inimigo, causando instantaneamente 13 para 17 de dano de Natureza. 60 cargas.',
     None, 'not tracked'),
    (1752, 'Golpe Sinistro',
     'Um golpe instantâneo que causa 3 de dano somado ao dano normal da arma. Concede 1 ponto de combo.',
     None, 'not tracked'),
    (1082, 'Garra',
     'Arranha o inimigo, causando 110% do dano normal mais 27. Concede 1 ponto de combo.',
     None, 'not tracked'),
    (10, 'Nevasca',
     'Fragmentos de gelo castigam a área selecionada, causando 196 de dano de Gelo ao longo de 8 s.',
     None, 'ignored (list)'),
    (5740, 'Chuva de Fogo',
     'Evoca uma chuva ígnea para queimar os inimigos na área do efeito, causando 166 de dano de Fogo ao longo de 8 s.',
     None, 'ignored (list)'),
    (1949, 'Fogo do Inferno',
     'Ateia fogo na área ao redor do lançador, causando 86 de dano de Fogo a si próprio e 86 de dano de Fogo a todos os inimigos próximos a cada 1 s. Dura 15 s.',
     None, 'ignored (list)'),
    (2120, 'Golpe Flamejante',
     'Convoca um pilar de fogo que queima todos os inimigos dentro da área, causando 55 para 71 de dano de Fogo e mais 44 de dano de Fogo ao longo de 8 s. O Mago só pode ter um Golpe Flamejante ativo por vez.',
     None, 'ignored (list)'),
    (26573, 'Consagração',
     'Consagra a terra sob o Paladino, causando 16 de dano Sagrado ao longo de 8 s aos inimigos que entrarem na área. Os 4 primeiros inimigos que entrarem na área receberão 32 a mais de dano ao longo de 8 s.',
     None, 'ignored (list)'),
    (16914, 'Furacão',
     'Cria uma tempestade violenta na área selecionada, causando 69 de dano de Natureza aos inimigos a cada 1 s e aumentando em 20% o intervalo entre os ataques dos inimigos. Dura 10 s. O Druida precisa canalizar para manter o feitiço.',
     None, 'ignored (list)'),
    (1510, 'Salva',
     'Dispara uma saraivada contínua de munições na área selecionada, causando 70 de dano Arcano aos alvos inimigo em um raio de 8 m a cada 1 s por 6 s.',
     None, 'ignored (list)'),
    (689, 'Drenar Vida',
     'Transfere 10 pontos de vida a cada 1 s do alvo para o lançador. Dura 5 s.',
     None, 'ignored (list)'),
    (1120, 'Drenar Alma',
     'Drena a alma do alvo, causando 85 de dano de Sombra ao longo de 15 s. Alvos não triviais que recebem dano de Drenar Alma têm chance de conceder a você um Estilhaço de Alma. Alvos não triviais abatidos por Drenar Alma sempre concedem a você um Estilhaço de Alma. Estilhaços de Alma são usados em outros feitiços.',
     None, 'ignored (list)'),
    (5138, 'Drenar Mana',
     'Transfere 44 pontos de mana a cada 1 s do alvo para o lançador. Dura 5 s.',
     None, 'ignored (list)'),
    (755, 'Funil de Vida',
     'Dá 12 pontos de vida ao ajudante do lançador a cada segundo por 10 s enquanto o lançador estiver canalizando. Geração de ameaça reduzida.',
     None, 'ignored (list)'),
    (15407, 'Açoite Mental',
     'Ataca a mente do alvo com energia Sombria, causando 63 de dano de Sombra ao longo de 3 s e reduzindo em 50% a velocidade de movimento.',
     None, 'ignored (list)'),
    (5143, 'Mísseis Arcanos',
     'Dispara Mísseis Arcanos contra o inimigo, causando 25 de dano Arcano a cada segundo por 3 s.',
     None, 'ignored (list)'),
    (10797, 'Fragmentos Estelares',
     'Faz chover fragmentos estelares sobre a cabeça do alvo inimigo, causando 162 de dano Arcano ao longo de 6 s.',
     None, 'ignored (list)'),
    (13813, 'Armadilha Explosiva',
     'Coloca uma armadilha de Fogo que explode quando um inimigo se aproxima, causando 105 para 135 de dano de Fogo e mais 150 de dano de Fogo ao longo de 20 s a todos em um raio de 10 m. A armadilha persiste por 1 min. Só pode haver uma armadilha de Fogo ativa de cada vez.',
     None, 'ignored (list)'),
]

# Combo points and finishers the cases above don't cover.
EXTRA = [
    ('combo awarded (Rake)', locale.comboPointsAwarded('Estraçalha o alvo, causando 23 de dano e mais 48 de dano ao longo de 9 s. Concede 1 ponto de combo.'), 1),
    ('combo awarded (Claw)', locale.comboPointsAwarded('Arranha o inimigo, causando 110% do dano normal mais 27. Concede 1 ponto de combo.'), 1),
    ('no combo line (Corruption)', locale.comboPointsAwarded('Corrompe o alvo, causando 40 de dano de Sombra ao longo de 12 s.'), None),
    ('finisher (Rip)', locale.isFinisher('Golpe final que causa dano ao longo do tempo. O dano aumenta em função dos pontos de combo e do seu Poder de Ataque:\n \xa0 1 ponto: 44 de dano ao longo de 12 s.\n \xa0 2 pontos: 71 de dano ao longo de 12 s.\n \xa0 3 pontos: 97 de dano ao longo de 12 s.\n \xa0 4 pontos: 124 de dano ao longo de 12 s.\n \xa0 5 pontos: 150 de dano ao longo de 12 s.'), True),
    ('not a finisher (Rake)', locale.isFinisher('Estraçalha o alvo, causando 23 de dano e mais 48 de dano ao longo de 9 s. Concede 1 ponto de combo.'), False),
]

if __name__ == "__main__":
    failures = 0
    sys.stdout.reconfigure(encoding="utf-8")
    width = max(len(c[1]) for c in CASES)
    for spell_id, name, desc, cp, expect in CASES:
        got = track(name, desc, cp)
        ok = got == expect
        failures += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {spell_id:>6} {name:<{width}}  {got}" + ("" if ok else f"   (expected {expect})"))
    print()
    for label, got, expect in EXTRA:
        ok = got == expect
        failures += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {label:<30} {got}" + ("" if ok else f"   (expected {expect})"))
    print()
    print("all passed" if not failures else f"{failures} FAILED")
    sys.exit(1 if failures else 0)
