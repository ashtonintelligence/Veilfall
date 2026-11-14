# Veilfall Earth 300 x 150 - November 14, 2026

This release adds two selectable 300 x 150 Earth maps, **Historical Starts** and **Free Start**, without removing the 240 x 120 maps.

## User-requested corrections
- Expand the map from 28,800 to 45,000 tiles (56.25% more).
- Preserve the original geographic coastline, rivers, lakes, and resource locations by resampling the 240 x 120 Natural Earth-derived source.
- Reclassify much of western North America, including the Southwest, Great Basin, Great Plains and Canadian interior, from broad Desert/Tundra swaths into passable Plains, Grassland, Hills, and Forest. Arid and semiarid does not mean uniformly sandy desert.
- Reserve Desert terrain for Mojave, Sonoran, Chihuahuan and parts of the Great Basin.
- Make most Rocky Mountain and Appalachian tiles traversable Hills or forested hills, retaining selected impassable peaks.
- Increase useful resources in the settled West, while retaining resampled legacy deposits.
- Preplace 265 ancient ruins and 95 barbarian encampments, spaced away from historical starting positions.
- Maintain 35 named historical starting locations, including Ashton in Arkansas. Free Start has no fixed start markers.

## Static validation
- Exactly 45,000 unique hex tile positions in both maps.
- Historical map: 35 start markers on passable land; Free Start: no markers.
- 265 ruins and 95 camps per variant.
- Historical Ashton start at hex (68, -10).
- Southwest sampled region (approx. 125–101 W, 27–38 N): 139 land tiles, 40 Desert tiles (28.8%). 
- Rockies sampled region (approx. 125–103 W, 37–60 N): 366 land tiles, 6 Mountain tiles.
- Appalachian sampled region (approx. 89–66 W, 32–48 N): 169 land tiles, 2 Mountain tiles.
- More than 2,600 mapped resource deposits per variant.

## Notes
The worldwide water and shoreline geometry is inherited by nearest-tile resampling of the prior 240 x 120 map. River flags are likewise inherited, so fine river continuity and coast geometry merit in-game/map-editor review. No Android/Unciv 5.0 load or performance benchmark has been run through this release. A 45k-tile map may run slowly on mobile. Existing 240 x 120 games remain unaffected.

## Unciv selection
Update **Veilfall** through Mods. Start a new game > Map Type: Custom > Map Mod: Veilfall > Map file: Veilfall Earth 300x150 - Historical Starts (or Free Start).
