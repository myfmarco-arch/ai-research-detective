#!/usr/bin/env bash
# skills/research-detective/scripts/tests/run_tests.sh —— lint 自检
set -u

# 上溯到仓库根(tests/ → scripts/ → research-detective/ → skills/ → repo root)
cd "$(dirname "$0")/../../../.."

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m'

PASS=0
FAIL=0

assert_exit() {
    local desc="$1"
    local expected="$2"
    local actual="$3"
    if [ "$expected" = "$actual" ]; then
        echo -e "${GREEN}✓${NC} $desc (exit $actual)"
        PASS=$((PASS + 1))
    else
        echo -e "${RED}✗${NC} $desc (expected exit $expected, got $actual)"
        FAIL=$((FAIL + 1))
    fi
}

assert_contains() {
    local desc="$1"
    local needle="$2"
    local haystack="$3"
    if echo "$haystack" | grep -qF "$needle"; then
        echo -e "${GREEN}✓${NC} $desc (contains '$needle')"
        PASS=$((PASS + 1))
    else
        echo -e "${RED}✗${NC} $desc (missing '$needle')"
        echo "  --- output ---"
        echo "$haystack" | head -20 | sed 's/^/    /'
        echo "  --- end ---"
        FAIL=$((FAIL + 1))
    fi
}

# ---------- 1. fixture_bad.md ----------
echo "=== 1. fixture_bad.md (期望红线全中) ==="
BAD_OUT=$(python3 skills/research-detective/scripts/lint_report.py skills/research-detective/scripts/tests/fixture_bad.md 2>&1)
BAD_EXIT=$?
assert_exit "bad fixture exits 1" 1 "$BAD_EXIT"
for rule in R_VOCAB R_ABSTRACT R_PARALLEL R_FILLER_NUM R_SMALL_N R_FOOTNOTE R_DASH_TAIL R_BUREAU R_HEDGE_BUFFER R_HEDGE_TIME R_HEDGE_SIGNPOST Y_GENERIC Y_CLOSING Y_BOLD Y_DASH_DENSITY Y_HEDGE_PASSIVE; do
    assert_contains "bad fixture hits $rule" "[$rule" "$BAD_OUT"
done

# humanizer 互补补丁：新加的具体词必须命中
assert_contains "R_VOCAB hits 彰显 (humanizer #7 vocab)" "彰显" "$BAD_OUT"
assert_contains "R_VOCAB hits 铸就 (humanizer #7 vocab)" "铸就" "$BAD_OUT"
assert_contains "R_HEDGE_SIGNPOST hits 综上所述 (humanizer #28 signposting)" "综上所述" "$BAD_OUT"
assert_contains "R_HEDGE_SIGNPOST hits 值得注意的是 (humanizer #27 authority trope)" "值得注意的是" "$BAD_OUT"
assert_contains "Y_BOLD hits 单行加粗滥用 (humanizer #15)" "Y_BOLD" "$BAD_OUT"

# 春秋笔法：让步缓冲词 + 时间副词定语 + 假被动密度
assert_contains "R_HEDGE_BUFFER hits 诚然 (让步缓冲)" "诚然" "$BAD_OUT"
assert_contains "R_HEDGE_BUFFER hits 不可否认 (让步缓冲)" "不可否认" "$BAD_OUT"
assert_contains "R_HEDGE_TIME hits 长期被X (时间副词)" "长期被X" "$BAD_OUT"
assert_contains "R_HEDGE_TIME hits 迟迟未X (时间副词)" "迟迟未X" "$BAD_OUT"
assert_contains "Y_HEDGE_PASSIVE hits 假被动密度" "Y_HEDGE_PASSIVE" "$BAD_OUT"

# ---------- 2. fixture_good.md ----------
echo ""
echo "=== 2. fixture_good.md (期望干净通过) ==="
GOOD_OUT=$(python3 skills/research-detective/scripts/lint_report.py skills/research-detective/scripts/tests/fixture_good.md 2>&1)
GOOD_EXIT=$?
assert_exit "good fixture exits 0" 0 "$GOOD_EXIT"
assert_contains "good fixture says PASS" "PASS" "$GOOD_OUT"
# 豁免回归保护：fixture_good 末尾故意在引号/blockquote 里塞了 R_HEDGE 词，
# 必须不触发——若触发说明豁免逻辑被破坏
if echo "$GOOD_OUT" | grep -qF "R_HEDGE"; then
    echo -e "${RED}✗${NC} good fixture must NOT trigger R_HEDGE inside quotes/blockquote"
    FAIL=$((FAIL + 1))
else
    echo -e "${GREEN}✓${NC} R_HEDGE quote/blockquote exemption holds"
    PASS=$((PASS + 1))
fi

# ---------- 3. 不存在的文件 ----------
echo ""
echo "=== 3. 不存在的文件 (期望 exit 2) ==="
NOEXIST_OUT=$(python3 skills/research-detective/scripts/lint_report.py /tmp/__no_such_file_8881.md 2>&1)
NOEXIST_EXIT=$?
assert_exit "missing file exits 2" 2 "$NOEXIST_EXIT"

# ---------- 4. 空文件 ----------
echo ""
echo "=== 4. 空文件 (期望 exit 0) ==="
TMP=$(mktemp -t lint_empty.XXXX.md)
EMPTY_OUT=$(python3 skills/research-detective/scripts/lint_report.py "$TMP" 2>&1)
EMPTY_EXIT=$?
rm -f "$TMP"
assert_exit "empty file exits 0" 0 "$EMPTY_EXIT"

# ---------- 5. dogfood: report_principles.md（plugin 自身文档）----------
echo ""
echo "=== 5. dogfood report_principles.md (期望干净) ==="
RP_OUT=$(python3 skills/research-detective/scripts/lint_report.py skills/research-detective/guides/report_principles.md 2>&1)
RP_EXIT=$?
assert_exit "report_principles.md exits 0" 0 "$RP_EXIT"

# ---------- 6. --quiet 模式 ----------
echo ""
echo "=== 6. --quiet 模式 (期望无 stdout) ==="
QUIET_OUT=$(python3 skills/research-detective/scripts/lint_report.py --quiet skills/research-detective/scripts/tests/fixture_bad.md 2>&1)
QUIET_EXIT=$?
assert_exit "quiet mode exits 1" 1 "$QUIET_EXIT"
if [ -z "$QUIET_OUT" ]; then
    echo -e "${GREEN}✓${NC} quiet mode produces no output"
    PASS=$((PASS + 1))
else
    echo -e "${RED}✗${NC} quiet mode unexpectedly printed:"
    echo "$QUIET_OUT" | head -3 | sed 's/^/    /'
    FAIL=$((FAIL + 1))
fi

# ---------- 7. --format=md 模式 ----------
echo ""
echo "=== 7. --format=md 模式 (期望 markdown 输出) ==="
MD_OUT=$(python3 skills/research-detective/scripts/lint_report.py --format=md skills/research-detective/scripts/tests/fixture_bad.md 2>&1)
assert_contains "md format has heading" "# Lint:" "$MD_OUT"
assert_contains "md format has FAIL" "**FAIL**" "$MD_OUT"

# ---------- 8. B1 lint: fixture_pack_good.md ----------
echo ""
echo "=== 8. lint_information_pack.py · fixture_pack_good.md (期望干净通过) ==="
PACK_GOOD_OUT=$(python3 skills/research-detective/scripts/lint_information_pack.py skills/research-detective/scripts/tests/fixture_pack_good.md 2>&1)
PACK_GOOD_EXIT=$?
assert_exit "pack good fixture exits 0" 0 "$PACK_GOOD_EXIT"
assert_contains "pack good fixture says OK" "[OK]" "$PACK_GOOD_OUT"

# ---------- 9. B1 lint: fixture_pack_bad.md ----------
echo ""
echo "=== 9. lint_information_pack.py · fixture_pack_bad.md (期望红线全中) ==="
PACK_BAD_OUT=$(python3 skills/research-detective/scripts/lint_information_pack.py skills/research-detective/scripts/tests/fixture_pack_bad.md 2>&1)
PACK_BAD_EXIT=$?
assert_exit "pack bad fixture exits 1" 1 "$PACK_BAD_EXIT"
for rule in C1 C2 C4 C6 I1 S2 S3 S4 S5; do
    assert_contains "pack bad fixture hits $rule" "[$rule" "$PACK_BAD_OUT"
done

# ---------- 10. B1 lint: 不存在的文件 ----------
echo ""
echo "=== 10. lint_information_pack.py · 不存在的文件 (期望 exit 2) ==="
PACK_NOEXIST_OUT=$(python3 skills/research-detective/scripts/lint_information_pack.py /tmp/__no_such_pack_8881.md 2>&1)
PACK_NOEXIST_EXIT=$?
assert_exit "missing pack file exits 2" 2 "$PACK_NOEXIST_EXIT"

# ---------- 11. B1 lint: 缺 frontmatter (期望 exit 2) ----------
echo ""
echo "=== 11. lint_information_pack.py · 缺 frontmatter (期望 exit 2) ==="
TMP_NO_FM=$(mktemp -t pack_no_fm.XXXX.md)
echo "# 没有 frontmatter 的文件" > "$TMP_NO_FM"
PACK_NOFM_OUT=$(python3 skills/research-detective/scripts/lint_information_pack.py "$TMP_NO_FM" 2>&1)
PACK_NOFM_EXIT=$?
rm -f "$TMP_NO_FM"
assert_exit "missing frontmatter exits 2" 2 "$PACK_NOFM_EXIT"

# ---------- 12. lint_process.py: fixture_process_good ----------
echo ""
echo "=== 12. lint_process.py · fixture_process_good (期望 PASS) ==="
PROC_GOOD_OUT=$(python3 skills/research-detective/scripts/lint_process.py skills/research-detective/scripts/tests/fixture_process_good 2>&1)
PROC_GOOD_EXIT=$?
assert_exit "process good fixture exits 0" 0 "$PROC_GOOD_EXIT"
assert_contains "process good fixture says PASS" "PASS" "$PROC_GOOD_OUT"

# ---------- 13. lint_process.py: fixture_process_bad ----------
echo ""
echo "=== 13. lint_process.py · fixture_process_bad (期望红线全中) ==="
PROC_BAD_OUT=$(python3 skills/research-detective/scripts/lint_process.py skills/research-detective/scripts/tests/fixture_process_bad 2>&1)
PROC_BAD_EXIT=$?
assert_exit "process bad fixture exits 1" 1 "$PROC_BAD_EXIT"
for rule in P_THIN_3A P_THIN_3B P_MISSING_3D P_MISSING_3E; do
    assert_contains "process bad fixture hits $rule" "[$rule" "$PROC_BAD_OUT"
done

# ---------- 14. lint_process.py: --wiki-mode 仍抓 3b/3d/3e ----------
echo ""
echo "=== 14. lint_process.py · bad --wiki-mode (3a 放宽,其他必抓) ==="
PROC_WIKI_OUT=$(python3 skills/research-detective/scripts/lint_process.py --wiki-mode skills/research-detective/scripts/tests/fixture_process_bad 2>&1)
PROC_WIKI_EXIT=$?
assert_exit "wiki-mode bad exits 1 (3b/3d/3e 仍 fail)" 1 "$PROC_WIKI_EXIT"
assert_contains "wiki-mode 仍抓 3d 缺失" "P_MISSING_3D" "$PROC_WIKI_OUT"

# ---------- 15. lint_process.py: 不存在的目录 ----------
echo ""
echo "=== 15. lint_process.py · 不存在的目录 (期望 exit 2) ==="
PROC_NOEXIST_OUT=$(python3 skills/research-detective/scripts/lint_process.py /tmp/__no_such_process_8881 2>&1)
PROC_NOEXIST_EXIT=$?
assert_exit "missing process dir exits 2" 2 "$PROC_NOEXIST_EXIT"

# ---------- 总结 ----------
echo ""
echo "=== 总结 ==="
TOTAL=$((PASS + FAIL))
if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}全部通过：$PASS / $TOTAL${NC}"
    exit 0
else
    echo -e "${RED}失败：$FAIL / $TOTAL${NC}"
    exit 1
fi
