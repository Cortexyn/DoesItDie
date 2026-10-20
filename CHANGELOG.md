# DoesItDie

## v0.7.1

- **Immolation Trap** is tracked. The DoT starts on whichever mob springs the trap.

## v0.7.0

**Other UIs**

- **EllesmereUI:** the marker sits on EllesmereUI's nameplates and target frame health bars, and the kill icon on
  its portrait.
- **Platynator:** the nameplate marker and kill icon anchor to Platynator's plates.
- Nameplate addons that hide Blizzard's bar no longer get a stray box above the plate.

**Languages:** German, Spanish and French clients read your DoTs. If something isn't picked up on your client, a
`/did debug` log helps a lot.

**New**

- **Estimate while casting:** DoTs with a cast time (Immolate) show as soon as you start casting, and disappear if
  the cast is interrupted. Can be turned off under Advanced.
- **Learned tick sizes viewer** (Advanced > View, or `/did ticks`): what each of your DoTs really ticks for next to
  its tooltip, with spell icons and tooltips. Shift-click a spell to link it.
- Kill icon size up to 128, on the target frame and on nameplates.
- New default nameplate look: school colors, stripes and a dashed gold outline. Saved settings are kept.
- An icon in the AddOns list.

**Fixes**

- A bleed on a mob immune to it no longer shows on the health bar.
- The kill icon and marker no longer stay on a dead mob's nameplate.

Thanks to Merryfett, cdhawke, Ironship, 13Karl, gou-gouze, toughnuts99 and Zephancode on GitHub.
