package com.unciv.logic

import com.badlogic.gdx.Gdx
import com.badlogic.gdx.files.FileHandle
import com.unciv.UncivGame
import com.unciv.json.json
import com.unciv.logic.files.UncivFiles
import com.unciv.models.metadata.BaseRuleset
import com.unciv.models.ruleset.Ruleset
import com.unciv.models.ruleset.RulesetCache
import com.unciv.models.ruleset.validation.RulesetErrorSeverity
import com.unciv.testing.BaseTestRunner
import com.unciv.testing.TestGame
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File

/** Runs inside the unmodified, pinned Unciv 4.22.4 test project. */
@RunWith(BaseTestRunner::class)
class VeilfallSaveLoadTest {
    private val unsafe = "May travel on Water tiles without embarking <when adjacent to a [Civilian] unit>"

    private fun mod(baseline: Boolean): Ruleset {
        val folder = System.getenv(if (baseline) "VEILFALL_BASELINE" else "VEILFALL_CANDIDATE")
            ?: error("Missing fixture path")
        return Ruleset().apply { name = "Veilfall"; load(FileHandle(File(folder, "jsons"))) }
    }

    private fun install(baseline: Boolean) {
        RulesetCache.loadRulesets(noMods = true)
        RulesetCache["Veilfall"] = mod(baseline)
    }

    @Test fun candidateRulesetHasNoSemanticErrors() {
        TestGame()
        install(false)
        val combined = RulesetCache.getComplexRuleset(linkedSetOf("Veilfall"), BaseRuleset.Civ_V_GnK.fullName)
        val diagnostics = combined.getErrorList()
        val errors = diagnostics.filter { it.errorSeverityToReport == RulesetErrorSeverity.Error }
        println("Veilfall ruleset diagnostics: " + diagnostics.joinToString("\n") { it.text })
        assertTrue(errors.joinToString("\n") { it.text }, errors.isEmpty())
        assertFalse(combined.unitPromotions["Marine Naval Integration"]!!.uniques.contains(unsafe))
    }

    private fun exercise(water: Boolean, foreignNeighbor: Boolean) {
        // Construct a valid, fully initialized game. The fault must occur on reload,
        // not during fixture creation. Both versions load exactly the same save bytes.
        install(false)
        val test = TestGame()
        test.ruleset.add(mod(false))
        test.gameInfo.gameParameters.mods.add("Veilfall")
        test.gameInfo.setGlobalTransients()
        test.makeHexagonalMap(2)
        val civ = test.addCiv(test.ruleset.nations["Ashton"]!!, isPlayer = true)
        val other = test.addCiv(test.ruleset.nations["Rome"]!!)
        civ.tech.addTechnology("Optics")
        other.tech.addTechnology("Optics")
        test.gameInfo.currentPlayer = civ.civID
        test.gameInfo.currentPlayerCiv = civ
        val first = test.tileMap.tileList.first()
        val neighbor = first.neighbors.first()
        assertTrue(test.tileMap.tileList.indexOf(first) < test.tileMap.tileList.indexOf(neighbor))
        if (water) {
            first.baseTerrain = "Coast"; first.setTerrainTransients()
            neighbor.baseTerrain = "Coast"; neighbor.setTerrainTransients()
        }
        val marine = test.addUnit("Continental Marines", civ, first)
        for (promotion in marine.baseUnit.promotions)
            marine.promotions.addPromotion(promotion, isFree = true)
        test.addUnit("Worker", if (foreignNeighbor) other else civ, neighbor)
        assertTrue(marine.promotions.promotions.contains("Marine Naval Integration"))
        val serialized = json().toJson(test.gameInfo)
        val file = File.createTempFile("veilfall-load-order-", ".json")
        try {
            file.writeText(serialized)
            val files = UncivFiles(Gdx.files)
            UncivGame.Current.files = files
            install(true)
            val failure = assertThrows(UninitializedPropertyAccessException::class.java) {
                files.loadGameFromFile(FileHandle(file))
            }
            assertTrue(failure.message.orEmpty().contains("civ"))
            assertTrue(failure.stackTrace.any { it.className.endsWith("MapUnitCache") && it.methodName == "updateUniques" })
            assertTrue(failure.stackTrace.any { it.className.endsWith("Conditionals") })
            install(false)
            val loaded = files.loadGameFromFile(FileHandle(file))
            val units = loaded.tileMap.values.flatMap { it.getUnits().toList() }
            assertEquals(2, units.size)
            val restored = units.single { it.name == "Continental Marines" }
            assertEquals(marine.owner, restored.owner)
            assertEquals(marine.promotions.promotions, restored.promotions.promotions)
            assertEquals(water, restored.isEmbarked())
            assertFalse(restored.cache.canMoveOnWater)
            assertEquals(serialized, file.readText())
        } finally { file.delete() }
    }

    @Test fun landWithFriendlyNeighbor() = exercise(false, false)
    @Test fun waterWithFriendlyNeighbor() = exercise(true, false)
    @Test fun landWithForeignNeighbor() = exercise(false, true)
    @Test fun waterWithForeignNeighbor() = exercise(true, true)
}
