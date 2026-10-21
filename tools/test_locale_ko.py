"""Runs WoW: Forever's own Korean (koKR) tooltips through the addon's real parser (DoesItDie.lua with Locale.lua
and every language file the .toc loads before it) and the real name tables, and checks what the addon would
track. The tooltips are Wowhead's (tooltip API, data env Forever, locale ko; issue #18), with the three amounts
Wowhead shows as unresolved formulas replaced by numbers, as the game shows them. English patterns run first,
as in game, so this also checks that they never misread Korean text.

    pip install lupa
    python tools/test_locale_ko.py
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


# (spell id, Korean name, tooltip, combo points or None, expected tracking result)
CASES = [
    (172, '부패',
     '대상을 부패시켜 12초에 걸쳐 총 40의 암흑 피해를 입힙니다.',
     None, '40 dmg, school 32, 12s, every 3s -> 4 ticks of 10.0'),
    (348, '제물',
     '적을 불태워 11의 화염 피해를 입히고 추가로 15초에 걸쳐 총 15의 화염 피해를 입힙니다.',
     None, '15 dmg, school 4, 15s, every 3s -> 5 ticks of 3.0'),
    (589, '어둠의 권능: 고통',
     '어둠의 힘으로 18초에 걸쳐 총 30의 암흑 피해를 입힙니다.',
     None, '30 dmg, school 32, 18s, every 3s -> 6 ticks of 5.0'),
    (2944, '파멸의 역병',
     '적을 질병에 감염시켜 24초에 걸쳐 총 128의 암흑 피해를 입힙니다. 파멸의 역병으로 인해 입히는 피해만큼 시전자의 생명력이 회복됩니다.',
     None, '128 dmg, school 32, 24s, every 3s -> 8 ticks of 16.0'),
    (8921, '달빛섬광',
     '적을 불태워 10 에서 12의 비전 피해를 입히고 9초에 걸쳐 총 12의 비전 피해를 입힙니다.',
     None, '12 dmg, school 64, 9s, every 3s -> 3 ticks of 4.0'),
    (5570, '곤충 떼',
     '적이 곤충 떼에게 둘러싸여 공격 적중률이 2%만큼 감소되고 12초에 걸쳐 총 48의 자연 피해를 입습니다.',
     None, '48 dmg, school 8, 12s, every 2s -> 6 ticks of 8.0'),
    (980, '고통의 파멸',
     '고통의 저주를 걸어 24초에 걸쳐 72의 암흑 피해를 입힙니다. 처음엔 피해를 천천히 입히다가 갈수록 피해를 주는 속도가 빨라집니다. 흑마법사마다 대상에 동시에 하나의 파멸만 걸 수 있습니다.',
     None, '72 dmg, school 32, 24s, every 2s -> 12 ticks of 6.0'),
    (14914, '신성한 불꽃',
     '신성한 불길이 적을 집어삼켜 53 에서 65의 신성 피해를 입히고 추가로 10초에 걸쳐 20의 신성 피해를 입힙니다.',
     None, '20 dmg, school 2, 10s, every 2s -> 5 ticks of 4.0'),
    (133, '화염구',
     '적에게 불타는 구체를 날려 15 에서 23의 화염 피해를 입히고 4초에 걸쳐 총 2의 추가 화염 피해를 입힙니다.',
     None, '2 dmg, school 4, 4s, every 2s -> 2 ticks of 1.0'),
    (11366, '불덩이 작렬',
     '엄청난 크기의 불덩이를 던져 101 에서 131의 화염 피해를 입히고 추가로 12초에 걸쳐 총 44의 화염 피해를 입힙니다.',
     None, '44 dmg, school 4, 12s, every 3s -> 4 ticks of 11.0'),
    (8050, '화염 충격',
     '시전 즉시 대상을 불로 그을려 24의 화염 피해를 입히고 12초에 걸쳐 추가로 총 28의 화염 피해를 입힙니다.',
     None, '28 dmg, school 4, 12s, every 3s -> 4 ticks of 7.0'),
    (339, '휘감는 뿌리',
     '대상을 제자리에 묶어 12초에 걸쳐 총 20의 자연 피해를 입힙니다. 대상이 피해를 입으면 효과가 해제될 수 있습니다. 동시에 [과성장',
     None, '20 dmg, school 8, 12s, every 3s -> 4 ticks of 5.0'),
    (1978, '독사 쐐기',
     '쐐기를 대상에게 발사하여 15초에 걸쳐 총 10의 자연 피해를 입힙니다. 사냥꾼마다 한 대상에 동시에 하나의 쐐기만 사용할 수 있습니다.',
     None, '10 dmg, school 8, 15s, every 3s -> 5 ticks of 2.0'),
    (13795, '제물의 덫',
     '덫을 설치합니다. 적이 다가오면 불태워 15초에 걸쳐 총 105의 화염 피해를 입힙니다. 덫은 1분 동안 지속되며, 한 개만 놓아둘 수 있습니다.',
     None, '105 dmg, school 4, 15s, every 3s -> 5 ticks of 21.0'),
    (1822, '갈퀴 발톱',
     '대상을 발톱으로 할퀴어 23의 피해를 입히고 추가로 9초에 걸쳐 총 48의 피해를 입힙니다. 1의 연계 포인트가 주어집니다.',
     None, '48 dmg, school 1, 9s, every 3s -> 3 ticks of 16.0'),
    (703, '목조르기',
     '적의 목을 졸라 18초에 걸쳐 총 144의 피해를 입힙니다. 총 피해는 전투력에 따라 증가합니다. 적의 배후에서 은신 상태로 사용해야 합니다. 1의 연계 포인트가 주어집니다.',
     None, '144 dmg, school 1, 18s, every 3s -> 6 ticks of 24.0'),
    (772, '분쇄',
     '적에게 깊은 상처를 입혀 출혈을 일으킵니다. 9초에 걸쳐 총 15의 피해를 입힙니다.',
     None, '15 dmg, school 1, 9s, every 3s -> 3 ticks of 5.0'),
    (9005, '암습',
     '적을 암습하여 2초 동안 기절시키고 18초에 걸쳐 총 90의 피해를 입힙니다. 숨은 상태로 적의 배후에서 공격해야 합니다. 1의 연계 포인트가 주어집니다.',
     None, '90 dmg, school 1, 18s, every 3s -> 6 ticks of 15.0'),
    (18265, '생명력 착취',
     '대상으로부터 3초마다 11의 생명력을 흡수합니다. 30초 동안 지속됩니다.',
     None, '110 dmg, school 32, 30s, every 3s -> 10 ticks of 11.0'),
    (1079, '도려내기',
     '마무리 일격을 시도하여 적에게 지속적인 피해를 입힙니다. 연계 점수와 전투력에 따라 피해가 증가합니다:\n \xa0 연계 점수 1점: 12초에 걸쳐 44의 피해\n \xa0 연계 점수 2점: 12초에 걸쳐 71의 피해\n \xa0 연계 점수 3점: 12초에 걸쳐 97의 피해\n \xa0 연계 점수 4점: 12초에 걸쳐 124의 피해\n \xa0 연계 점수 5점: 12초에 걸쳐 150의 피해',
     5, '150 dmg, school 1, 12s, every 2s -> 6 ticks of 25.0'),
    (1079, '도려내기',
     '마무리 일격을 시도하여 적에게 지속적인 피해를 입힙니다. 연계 점수와 전투력에 따라 피해가 증가합니다:\n \xa0 연계 점수 1점: 12초에 걸쳐 44의 피해\n \xa0 연계 점수 2점: 12초에 걸쳐 71의 피해\n \xa0 연계 점수 3점: 12초에 걸쳐 97의 피해\n \xa0 연계 점수 4점: 12초에 걸쳐 124의 피해\n \xa0 연계 점수 5점: 12초에 걸쳐 150의 피해',
     1, '44 dmg, school 1, 12s, every 2s -> 6 ticks of 7.3'),
    (1943, '파열',
     '마무리 일격을 시도하여 적에게 지속 피해를 입힙니다. 입히는 피해는 전투력에 비례합니다. 연계 점수에 따라 지속시간이 증가합니다.\n \xa0 연계 점수 1점: 8초에 걸쳐 25의 피해\n \xa0 연계 점수 2점: 10초에 걸쳐 37의 피해\n \xa0 연계 점수 3점: 12초에 걸쳐 51의 피해\n \xa0 연계 점수 4점: 14초에 걸쳐 68의 피해\n \xa0 연계 점수 5점: 16초에 걸쳐 87의 피해',
     5, '87 dmg, school 1, 16s, every 2s -> 8 ticks of 10.9'),
    (1943, '파열',
     '마무리 일격을 시도하여 적에게 지속 피해를 입힙니다. 입히는 피해는 전투력에 비례합니다. 연계 점수에 따라 지속시간이 증가합니다.\n \xa0 연계 점수 1점: 8초에 걸쳐 25의 피해\n \xa0 연계 점수 2점: 10초에 걸쳐 37의 피해\n \xa0 연계 점수 3점: 12초에 걸쳐 51의 피해\n \xa0 연계 점수 4점: 14초에 걸쳐 68의 피해\n \xa0 연계 점수 5점: 16초에 걸쳐 87의 피해',
     1, '25 dmg, school 1, 8s, every 2s -> 4 ticks of 6.2'),
    (139, '소생',
     '15초에 걸쳐 대상의 생명력을 총 45만큼 회복시킵니다.',
     None, 'not tracked'),
    (774, '회복',
     '12초에 걸쳐 32의 생명력을 회복시킵니다.',
     None, 'not tracked'),
    (2823, '맹독',
     '무기에 30분 동안 유지되는 독을 바릅니다.\n매 공격 시 30%의 확률로 적을 중독시켜 12초에 걸쳐 24의 자연 피해를 입힙니다. 효과는 대상마다 5번까지 중첩될 수 있습니다. 90회 사용 가능.',
     None, 'not tracked'),
    (8679, '순간 효과 독',
     '무기에 30분 동안 유지되는 독을 바릅니다.\n매 공격 시 20%의 확률로 적을 중독시켜 즉시 13 에서 17의 자연 피해를 입힙니다. 60회 사용 가능합니다.',
     None, 'not tracked'),
    (1752, '사악한 일격',
     '대상을 순간적으로 공격하여 3의 추가 피해를 입힙니다. 1의 연계 포인트가 주어집니다.',
     None, 'not tracked'),
    (1082, '할퀴기',
     '적을 발톱으로 할퀴어 일반 공격력의 110%에 해당하는 피해와 27의 추가 피해를 입힙니다. 연계 점수 1점을 생성합니다.',
     None, 'not tracked'),
    (10, '눈보라',
     '대상 지역에 얼음 파편을 퍼부어, 8초에 걸쳐 총 196의 냉기 피해를 입힙니다.',
     None, 'ignored (list)'),
    (5740, '불의 비',
     '8초에 걸쳐 불의 비를 내려 대상 지역의 모든 적에게 총 166의 화염 피해를 입힙니다.',
     None, 'ignored (list)'),
    (1949, '지옥의 불길',
     '시전자 주위를 불길로 감싸 매 1초마다 시전자에게 86의 화염 피해를 입히고 주변의 적에게 86의 화염 피해를 입힙니다. 15초 동안 지속됩니다.',
     None, 'ignored (list)'),
    (2120, '불기둥',
     '불기둥을 불러일으켜 그 지역 안의 모든 적에게 55 에서 71의 화염 피해를 입히고 추가로 8초에 걸쳐 총 44의 화염 피해를 입힙니다. 마법사마다 한 번에 하나의 불기둥만 활성화할 수 있습니다.',
     None, 'ignored (list)'),
    (26573, '신성화',
     '성기사가 서 있는 땅을 신성화하여 해당 지역에 들어서는 적에게 8초에 걸쳐 16의 신성 피해를 입힙니다. 가장 먼저 해당 지역에 들어서는 적 4명은 8초에 걸쳐 32의 추가 피해를 받습니다.',
     None, 'ignored (list)'),
    (16914, '허리케인',
     '대상 지역에 맹렬한 폭풍을 생성하여 1초마다 적에게 69의 자연 피해를 입히고 적의 공격 간격을 20%만큼 늘입니다. 10초 동안 지속됩니다. 주문을 유지하려면 계속 정신을 집중해야 합니다.',
     None, 'ignored (list)'),
    (1510, '연발 사격',
     '8미터 반경의 지역에 연발 사격을 가하여 대상 지역 내의 적에게 6초에 걸쳐 1초마다 70의 비전 피해를 입힙니다.',
     None, 'ignored (list)'),
    (689, '생명력 흡수',
     '대상으로부터 1초마다 10의 생명력을 흡수합니다. 5초 동안 지속됩니다.',
     None, 'ignored (list)'),
    (1120, '영혼 흡수',
     '적의 영혼을 소진시켜 15초에 걸쳐 85의 암흑 피해를 입힙니다. 영혼 흡수로 사소하지 않은 대상에게 피해를 입히면 일정 확률로 영혼의 조각을 얻습니다. 영혼 흡수로 사소하지 않은 대상을 처치하면 항상 영혼의 조각을 얻습니다. 영혼의 조각은 다른 흑마법에 사용됩니다.',
     None, 'ignored (list)'),
    (5138, '마나 흡수',
     '대상으로부터 1초마다 44의 마나를 흡수합니다. 5초 동안 지속됩니다.',
     None, 'ignored (list)'),
    (755, '생명력 집중',
     '시전자가 정신을 집중하는 동안 10초 동안 1초마다 12의 생명력을 시전자의 소환수에게 이전합니다. 위협 수준 생성량이 감소합니다.',
     None, 'ignored (list)'),
    (15407, '정신의 채찍',
     '대상의 정신을 암흑의 기운으로 공격하여, 3초에 걸쳐 63의 암흑 피해를 입히고 이동 속도를 50%만큼 감소시킵니다.',
     None, 'ignored (list)'),
    (5143, '신비한 화살',
     '3초에 걸쳐 적에게 마법 화살을 날려 매초마다 각각 25의 비전 피해를 입힙니다.',
     None, 'ignored (list)'),
    (10797, '별조각',
     '적의 머리 위로 별조각을 내려 6초에 걸쳐 총 162의 비전 피해를 입힙니다.',
     None, 'ignored (list)'),
    (13813, '폭발의 덫',
     '덫을 설치합니다. 적이 다가오면 폭발하여 적에게 105 에서 135의 화염 피해를 입히고 주위 10미터 반경에 있는 모든 대상에게 20초에 걸쳐 150의 추가 화염 피해를 입힙니다. 덫은 1분 동안 지속되며, 한 개만 놓아둘 수 있습니다.',
     None, 'ignored (list)'),
]

# Combo points and finishers the cases above don't cover.
EXTRA = [
    ("combo awarded (Rake)", locale.comboPointsAwarded('대상을 발톱으로 할퀴어 23의 피해를 입히고 추가로 9초에 걸쳐 총 48의 피해를 입힙니다. 1의 연계 포인트가 주어집니다.'), 1),
    ("combo awarded (Claw)", locale.comboPointsAwarded('적을 발톱으로 할퀴어 일반 공격력의 110%에 해당하는 피해와 27의 추가 피해를 입힙니다. 연계 점수 1점을 생성합니다.'), 1),
    ("no combo line (Corruption)", locale.comboPointsAwarded('대상을 부패시켜 12초에 걸쳐 총 40의 암흑 피해를 입힙니다.'), None),
    ("finisher (Rip)", locale.isFinisher('마무리 일격을 시도하여 적에게 지속적인 피해를 입힙니다. 연계 점수와 전투력에 따라 피해가 증가합니다:\n \xa0 연계 점수 1점: 12초에 걸쳐 44의 피해\n \xa0 연계 점수 2점: 12초에 걸쳐 71의 피해\n \xa0 연계 점수 3점: 12초에 걸쳐 97의 피해\n \xa0 연계 점수 4점: 12초에 걸쳐 124의 피해\n \xa0 연계 점수 5점: 12초에 걸쳐 150의 피해'), True),
    ("not a finisher (Rake)", locale.isFinisher('대상을 발톱으로 할퀴어 23의 피해를 입히고 추가로 9초에 걸쳐 총 48의 피해를 입힙니다. 1의 연계 포인트가 주어집니다.'), False),
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
