"""Strict v0.2.9-to-v0.2.10 diff and load-safety guard; not a runtime test."""
from pathlib import Path
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BASELINE = '75331685057bcdb676c72a1a622c93912ed2c096'
UNSAFE = 'May travel on Water tiles without embarking <when adjacent to a [Civilian] unit>'
ALLOWED = {
    'jsons/ModOptions.json', 'jsons/UnitPromotions.json', 'README.md', 'BUILD_STATUS.md',
    'ART_VERIFICATION.json', 'tools/v029/build_assets.py', 'tools/v029/test_verification.py',
    'tools/v029/test_results.json', '.github/workflows/v021-art-build.yml',
    'tools/v0210/verify_hotfix.py', 'tools/v0210/VeilfallSaveLoadTest.kt',
    'tools/v0210/VERIFICATION.md',
}

def old(path):
    return subprocess.check_output(['git', 'show', BASELINE + ':' + path], cwd=ROOT)

def main():
    baseline_files = subprocess.check_output(
        ['git', 'ls-tree', '-r', '--name-only', BASELINE], cwd=ROOT, text=True).splitlines()
    for rel in baseline_files:
        if rel not in ALLOWED:
            assert (ROOT / rel).read_bytes() == old(rel), 'Unexpected change: ' + rel
    added = subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard'], cwd=ROOT, text=True).splitlines()
    tracked = subprocess.check_output(['git', 'ls-files'], cwd=ROOT, text=True).splitlines()
    for rel in set(added + tracked) - set(baseline_files):
        if '__pycache__' in Path(rel).parts:
            continue
        assert rel in ALLOWED, 'Unexpected added file: ' + rel
    for file in (ROOT / 'jsons').glob('*.json'):
        json.loads(file.read_text())
    expected = json.loads(old('jsons/UnitPromotions.json'))
    marine = next(p for p in expected if p['name'] == 'Marine Naval Integration')
    assert marine['uniques'].count(UNSAFE) == 1
    marine['uniques'].remove(UNSAFE)
    actual = json.loads((ROOT / 'jsons/UnitPromotions.json').read_text())
    assert actual == expected, 'Only the unsafe unique may change in promotions'
    options = json.loads(old('jsons/ModOptions.json'))
    options.update(modVersion='0.2.10', lastUpdated='2026-09-30')
    assert json.loads((ROOT / 'jsons/ModOptions.json').read_text()) == options
    # Review all ruleset occurrences, not just Marine Naval Integration. In this
    # exact hotfix, adjacency is permitted only on existing combat Strength or
    # Worker construction bonuses, which MapUnitCache.updateUniques does not query.
    reviewed = []
    def walk(value, path):
        if isinstance(value, dict):
            for k, v in value.items(): walk(v, path + '/' + k)
        elif isinstance(value, list):
            for i, v in enumerate(value): walk(v, path + '/' + str(i))
        elif isinstance(value, str) and '<when adjacent to a [' in value:
            base = value.split(' <')[0]
            assert re.fullmatch(r'\[[+-]?\d+\]% (Strength|construction time for \[.*\] improvements)', base), (path, value)
            reviewed.append({'path': path, 'unique': value})
        if isinstance(value, str):
            assert value != UNSAFE, (path, value)
            if value.startswith('May travel on Water tiles without embarking'):
                assert '<' not in value, ('Conditional CanMoveOnWater requires load review', path, value)
    for file in (ROOT / 'jsons').glob('*.json'):
        walk(json.loads(file.read_text()), file.name)
    print(json.dumps({'release': 'v0.2.10', 'result': 'PASS',
        'actual_runtime_executed_by_this_script': False,
        'all_v029_art_bytes_unchanged': True,
        'only_gameplay_change': 'Remove unsafe Marine Naval Integration unique',
        'marine_upgrade_chain_and_stats_unchanged': True,
        'slave_raider_50_percent_rule_unchanged': True,
        'remaining_adjacency_uniques_reviewed': reviewed}, indent=2))

if __name__ == '__main__': main()
