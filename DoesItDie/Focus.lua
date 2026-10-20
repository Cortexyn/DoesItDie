-- DoesItDie focus frame: the damage marker (and the kill icon, as on nameplates) on the focus frame's health bar,
-- for your DoTs on the focused mob. Based on toughnuts99's patch (issue #12).
--
-- Tracking is per mob already (ns.dotBreakdownForUnit) and UNIT_COMBAT reports hits on the focus, so this is only
-- display: it reuses the nameplate widgets (ns.barMarker) in a look of its own (Focus tab, focus* settings, read
-- through a view that maps the widgets' plate* keys to them), drawn on a custom focus bar (Advanced tab, a frame
-- path like the target's), else EllesmereUI's focus frame, else Blizzard's. The options window's preview has a
-- mock focus frame drawn the same way with its plain numbers (ns.setFocusPreview).
--
-- The widgets hang off a frame of our own rather than the bar's parent: unit frame addons may put the bar in a
-- clipping frame, which would cut off a kill icon beside the bar. So they're hidden by hand whenever there's no
-- focus, the bar isn't visible or there are no DoTs, and pinned so the nameplate refresh leaves them alone.

local _, ns = ...

local UPDATE_INTERVAL = 0.1

local function isSecret(v)
    if type(issecretvalue) ~= "function" then return false end
    local ok, r = pcall(issecretvalue, v)
    return ok and r or false
end

-- Blizzard's focus frame is built from the target frame's template, so its bar sits at the same paths.
local function blizzardFocusBar()
    local ff = FocusFrame
    local content = ff and ff.TargetFrameContent
    local main = content and content.TargetFrameContentMain
    return (main and main.HealthBarsContainer and main.HealthBarsContainer.HealthBar)
        or (main and main.HealthBar)
        or FocusFrameHealthBar
        or (ff and ff.healthbar)
end

-- The bar to draw on, and a description of it for the options window.
local function focusBar(db)
    local path = strtrim(db.customFocusHealthBar or "")
    local custom = path ~= "" and ns.resolveFramePath(path)
    if custom then return custom, "|cff66ff66" .. path .. "|r" end
    local known, owner = ns.knownFocusFrame()
    local fallback = (known and (owner .. " focus frame")) or (blizzardFocusBar() and "Blizzard's focus frame")
    local note = path ~= "" and ("|cffff6666" .. path .. " not found|r, using ") or ""
    if known then return known, note .. fallback end
    local blizzard = blizzardFocusBar()
    if blizzard then return blizzard, note .. fallback end
    return nil, note .. "|cffff6666no focus frame found|r"
end

-- What the focus marker is attached to (options window).
function ns.focusStatus()
    if not ns.db then return "" end
    return select(2, focusBar(ns.db))
end

-- The focus look: the nameplate widgets read plate* (and nameplateMode, nameplateIcon*) settings; this view
-- answers those keys with the focus* ones, and everything else (showMarkers) straight from the settings.
local FOCUS_KEYS = {
    nameplateMode = "focusMode", plateIcon = "focusIcon", nameplateIconSize = "focusIconSize",
    nameplateIconPosition = "focusIconPosition", plateIconOffsetX = "focusIconOffsetX",
    plateIconOffsetY = "focusIconOffsetY", plateDotColors = "focusDotColors", plateFillTexture = "focusFillTexture",
    plateFillColor = "focusFillColor", plateFillOpacity = "focusFillOpacity", plateOutlineStyle = "focusOutlineStyle",
    plateDashLength = "focusDashLength", plateOutlineThickness = "focusOutlineThickness",
    plateOutlineColor = "focusOutlineColor", plateOutlineOpacity = "focusOutlineOpacity",
}
local focusLook = setmetatable({}, { __index = function(_, key) return ns.db[FOCUS_KEYS[key] or key] end })
ns.focusKeys = FOCUS_KEYS -- (Options.lua's "Copy from Nameplates tab")

local host = CreateFrame("Frame", nil, UIParent)
host:SetAllPoints(UIParent)
local widgets

local function hide()
    if widgets then ns.barMarker.hide(widgets) end
end

-- The options window's mock focus frame: { frame, healthBar } and the preview state ({ health, dots } in % of max
-- health), or nil.
local previewHost, previewState, previewWidgets

function ns.setFocusPreview(mock, state)
    previewHost, previewState = mock, state
    if not mock and previewWidgets then ns.barMarker.hide(previewWidgets) end
end

local function refreshPreview(db)
    if not previewHost or not previewState then return end
    ns.barMarker.pin(previewHost.frame)
    previewWidgets = ns.barMarker.widgetsFor(previewHost.frame, previewHost.healthBar)
    local entries, total = {}, 0
    for _, dot in ipairs(previewState.dots) do
        if dot.damage > 0 then
            table.insert(entries, dot)
            total = total + dot.damage
        end
    end
    if total <= 0 or db.focusMode == "off" then return ns.barMarker.hide(previewWidgets) end
    ns.barMarker.draw(previewWidgets, entries, total, 100, math.max(previewState.health, 0.01), focusLook)
end

local function shown(bar)
    local ok, visible = pcall(bar.IsVisible, bar)
    return not ok or isSecret(visible) or visible ~= false
end

local function dead()
    local ok, isDead = pcall(UnitIsDead, "focus")
    return ok and not isSecret(isDead) and isDead
end

local function refresh()
    local db = ns.db
    if not db or not ns.barMarker then return end
    refreshPreview(db)
    if db.focusMode == "off" or not UnitExists("focus") or dead() then return hide() end
    local bar = focusBar(db)
    if not bar or not shown(bar) then return hide() end
    local entries, total = ns.dotBreakdownForUnit("focus")
    if total <= 0 then return hide() end
    ns.barMarker.pin(host)
    -- The bar isn't the host's child: take its strata so the marker draws above it.
    widgets = ns.barMarker.widgetsFor(host, bar, false, true)
    ns.barMarker.draw(widgets, entries, total, UnitHealthMax("focus"), UnitHealth("focus"), focusLook)
end

local driver = CreateFrame("Frame")
local sinceUpdate = 0
local reportedError = false
driver:SetScript("OnUpdate", function(_, elapsed)
    sinceUpdate = sinceUpdate + elapsed
    if sinceUpdate < UPDATE_INTERVAL then return end
    sinceUpdate = 0
    local ok, err = pcall(refresh)
    if not ok then
        pcall(hide)
        if not reportedError and ns.trace then
            reportedError = true
            ns.trace("ERROR in focus update: " .. tostring(err))
            ns.print("Focus display error (logged): " .. tostring(err))
        end
    end
end)
