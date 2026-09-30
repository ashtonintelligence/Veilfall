package com.unciv.logic

import com.badlogic.gdx.files.FileHandle
import com.badlogic.gdx.graphics.g2d.TextureAtlas
import com.unciv.models.ruleset.Ruleset
import com.unciv.testing.GdxTestRunner
import com.unciv.testing.TestGame
import com.unciv.ui.components.tilegroups.TileSetStrings
import com.unciv.ui.images.ImageGetter
import com.unciv.view.GameView
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith

/** Real Unciv atlas loader and unit-name resolver with mock GL, not graphical acceptance. */
@RunWith(GdxTestRunner::class)
class VeilfallSpriteAtlasTest {
    @Test fun packedSpritesWinAtlasResolutionInAllThreeTilesets() {
        val root = FileHandle(System.getenv("VEILFALL_CANDIDATE") ?: error("Missing candidate"))
        val test = TestGame()
        val mod = Ruleset().apply { name = "Veilfall"; load(root.child("jsons")) }
        test.ruleset.add(mod)
        test.gameInfo.setGlobalTransients()
        test.makeHexagonalMap(3)
        val civ = test.addCiv(test.ruleset.nations["Ashton"]!!, isPlayer = true)
        val names = listOf("Slave", "Slave Raider", "Mounted Slave Raider", "Slave Hunter",
            "Industrial Slaver", "Continental Marines", "Marine Riflemen", "Expeditionary Marines",
            "Fleet Marine Force", "Marine Expeditionary Unit", "Exo-Marine")
        val units = names.mapIndexed { i, name -> test.addUnit(name, civ, test.tileMap.tileList[i]) }
        val view = GameView(test.gameInfo, civ)
        ImageGetter.resetAtlases()
        // Invoke the production loader directly: no independent approximation of
        // Atlases.json iteration order, TextureAtlas parsing or drawable overrides.
        val loader = ImageGetter.javaClass.getDeclaredMethod("loadModAtlases", String::class.java, FileHandle::class.java)
        loader.isAccessible = true
        loader.invoke(ImageGetter, "VeilfallSpriteCandidate", root)
        val overlay = ImageGetter.getSpecificAtlas("VeilfallSpriteCandidate/sprite-detail")!!
        assertEquals(33, overlay.regions.size)
        val legacy = ImageGetter.getSpecificAtlas("VeilfallSpriteCandidate/v021")!!
        for (ts in listOf("Minimal", "HexaRealm", "FantasyHex")) {
            val strings = TileSetStrings(ts, ts)
            for (unit in units) {
                val expected = "TileSets/$ts/Units/${unit.name}"
                val selected = strings.getUnitImageLocation(view.getForeignMapUnitView(unit))
                assertEquals("Wrong runtime asset for $ts / ${unit.name}", expected, selected)
                val region = ImageGetter.getDrawable(selected).region as TextureAtlas.AtlasRegion
                val packed = overlay.findRegion(expected)
                assertSame("Old atlas still selected", packed.texture, region.texture)
                assertEquals(packed.regionX, region.regionX)
                assertEquals(packed.regionY, region.regionY)
                assertEquals(256, region.regionWidth)
                assertEquals(region.regionWidth, region.originalWidth)
                assertEquals(region.regionHeight, region.originalHeight)
                assertEquals(0f, region.offsetX, 0f)
                assertEquals(0f, region.offsetY, 0f)
                val prior = legacy.findRegion(expected)
                assertEquals(prior.regionHeight.toFloat()/prior.regionWidth,
                    region.regionHeight.toFloat()/region.regionWidth, .00001f)
            }
        }
        // Preserved portraits/icons/religion must still resolve to the original page.
        for (key in listOf("UnitPortraits/Continental Marines", "UnitIcons/Slave",
            "ReligionIcons/Rationalism")) {
            assertSame(legacy.findRegion(key).texture, ImageGetter.getDrawable(key).region.texture)
        }
        ImageGetter.resetAtlases()
    }
}
