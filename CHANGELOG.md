# DoesItDie

## v0.8.1

- **Plater and other nameplate addons:** the nameplate marker finds their health bars automatically. If yours still doesn't show it, Advanced > Nameplate health bar takes the path to its bar.

## v0.8.0

**Restart the game fully after updating** (not just /reload): this version adds new files.

- **Focus frame:** the marker and kill icon also show on your focus's health bar (Blizzard's, EllesmereUI's, or a custom one under Advanced), with its own tab (Focus) for its look and a focus frame in the options preview. `/cast [@focus]` macros put the DoT on your focus. Thanks to toughnuts99 for the patch.
- **Dungeons:** where mobs can't be told apart by ID, DoTs are tracked per mob through its nameplate, so tab-dotting a pack works (needs enemy nameplates on). Thanks to Staypuft.
- **Window language** setting (Advanced): the options window can now be translated. No translations yet; see issue #10 on GitHub if you'd like to help.
- The options window is a little wider, so all tabs fit.

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
