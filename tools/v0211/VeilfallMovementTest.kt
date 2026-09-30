package com.unciv.logic

import com.badlogic.gdx.Gdx
import com.badlogic.gdx.files.FileHandle
import com.unciv.UncivGame
import com.unciv.json.json
import com.unciv.logic.files.UncivFiles
import com.unciv.logic.map.mapunit.MapUnit
import com.unciv.models.ruleset.Ruleset
import com.unciv.models.ruleset.RulesetCache
import com.unciv.testing.BaseTestRunner
import com.unciv.testing.TestGame
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File

@RunWith(BaseTestRunner::class)
class VeilfallMovementTest {
    private val marines = linkedMapOf(
        "Continental Marines" to 2, "Marine Riflemen" to 2,
        "Expeditionary Marines" to 2, "Fleet Marine Force" to 2,
        "Marine Expeditionary Unit" to 3, "Exo-Marine" to 4)

    private fun mod(previous: Boolean): Ruleset {
        val folder = System.getenv(if (previous) "VEILFALL_V0210" else "VEILFALL_CANDIDATE")
            ?: error("Missing mod fixture path")
        return Ruleset().apply { name = "Veilfall"; load(FileHandle(File(folder, "jsons"))) }
    }
    private fun install(previous: Boolean) {
        RulesetCache.loadRulesets(noMods = true)
        RulesetCache["Veilfall"] = mod(previous)
    }
    private fun fixture(name: String, terrain: String, previous: Boolean): Pair<TestGame, MapUnit> {
        install(previous)
        val game = TestGame()
        game.ruleset.add(mod(previous))
        game.gameInfo.gameParameters.mods.add("Veilfall")
        game.gameInfo.setGlobalTransients()
        game.makeHexagonalMap(2)
        val civ = game.addCiv(game.ruleset.nations["Ashton"]!!, isPlayer = true)
        civ.tech.addTechnology("Optics") // Embarkation, without Astronomy's movement bonus.
        game.gameInfo.currentPlayer = civ.civID
        game.gameInfo.currentPlayerCiv = civ
        val tile = game.tileMap.tileList.first()
        tile.baseTerrain = terrain
        tile.setTerrainTransients()
        val unit = game.addUnit(name, civ, tile)
        for (promotion in unit.baseUnit.promotions)
            unit.promotions.addPromotion(promotion, isFree = true)
        unit.currentMovement = unit.getMaxMovement().toFloat()
        return game to unit
    }
    private fun current(terrain: String, water: Boolean) {
        for ((name, base) in marines) {
            val (_, unit) = fixture(name, terrain, false)
            assertEquals("Base movement changed: $name", base, unit.baseUnit.movement)
            assertEquals("Embarkation: $name on $terrain", water, unit.isEmbarked())
            assertEquals("Calculated movement: $name on $terrain", if (water) 3 else base + 1, unit.getMaxMovement())
            assertFalse(unit.cache.canMoveOnWater)
        }
    }
    private fun saved(terrain: String, water: Boolean) {
        for ((name, base) in marines) {
            val (game, original) = fixture(name, terrain, true)
            val previousMax = if (water) 2 else base
            assertEquals(previousMax, original.getMaxMovement())
            assertTrue(original.promotions.promotions.contains("Marine Naval Integration"))
            val bytes = json().toJson(game.gameInfo)
            val file = File.createTempFile("veilfall-v0210-marine-", ".json")
            try {
                file.writeText(bytes)
                val files = UncivFiles(Gdx.files)
                UncivGame.Current.files = files
                install(false)
                val loaded = files.loadGameFromFile(FileHandle(file))
                val restored = loaded.tileMap.values.flatMap { it.getUnits().toList() }.single()
                assertEquals(name, restored.name)
                assertEquals(original.id, restored.id)
                assertEquals(original.owner, restored.owner)
                assertEquals(original.promotions.promotions, restored.promotions.promotions)
                assertEquals(water, restored.isEmbarked())
                assertEquals(previousMax + 1, restored.getMaxMovement())
                // A mid-turn load must not refill already-spent movement points.
                assertEquals(original.currentMovement, restored.currentMovement, 0f)
                assertEquals(bytes, file.readText())
            } finally { file.delete() }
        }
    }
    @Test fun allSixOnLand() = current("Grassland", false)
    @Test fun allSixEmbarkedOnCoast() = current("Coast", true)
    @Test fun allSixEmbarkedOnOcean() = current("Ocean", true)
    @Test fun allSixExistingLandMarinesInheritBonus() = saved("Grassland", false)
    @Test fun allSixExistingEmbarkedMarinesInheritBonus() = saved("Coast", true)

    @Test fun bonusStacksNormallyWithExistingEmbarkedTechnologyBonus() {
        val (_, unit) = fixture("Continental Marines", "Coast", false)
        unit.civ.tech.addTechnology("Astronomy")
        assertEquals(4, unit.getMaxMovement())
    }
}
