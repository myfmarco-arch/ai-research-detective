#!/usr/bin/env bash
# skills/research-archivist/scripts/tests/run_tests.sh —— verify_quotes 自检
set -u

# 上溯到仓库根(tests/ → scripts/ → research-archivist/ → skills/ → repo root)
cd "$(dirname "$0")/../../../.."

GREEN='\033[0;32m'
RED='\033[0;31m'
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

assert_not_contains() {
    local desc="$1"
    local needle="$2"
    local haystack="$3"
    if ! echo "$haystack" | grep -qF "$needle"; then
        echo -e "${GREEN}✓${NC} $desc (does not contain '$needle')"
        PASS=$((PASS + 1))
    else
        echo -e "${RED}✗${NC} $desc (unexpectedly contains '$needle')"
        FAIL=$((FAIL + 1))
    fi
}

SCRIPT="skills/research-archivist/scripts/verify_quotes.py"
GOOD="skills/research-archivist/scripts/tests/fixture_wiki_good/wiki"
BAD="skills/research-archivist/scripts/tests/fixture_wiki_bad/wiki"

# ---------- 1. fixture_wiki_good ----------
echo "=== 1. fixture_wiki_good (期望全部命中,exit 0) ==="
GOOD_OUT=$(python3 "$SCRIPT" "$GOOD" 2>&1)
GOOD_EXIT=$?
assert_exit "good fixture exits 0" 0 "$GOOD_EXIT"
assert_contains "good fixture says PASS" "PASS" "$GOOD_OUT"

# ---------- 2. fixture_wiki_bad ----------
echo ""
echo "=== 2. fixture_wiki_bad (期望多条 fail,exit 1) ==="
BAD_OUT=$(python3 "$SCRIPT" "$BAD" 2>&1)
BAD_EXIT=$?
assert_exit "bad fixture exits 1" 1 "$BAD_EXIT"
assert_contains "bad fixture says FAIL" "FAIL" "$BAD_OUT"
# 三类失败必须都出现
assert_contains "bad fixture catches 改写引用 (12 点 vs 11 点)" "晚上 12 点" "$BAD_OUT"
assert_contains "bad fixture catches 不存在的资料文件 (interview_99)" "interview_99" "$BAD_OUT"
assert_contains "bad fixture catches 添加内容到原文 (卖给第三方)" "卖给第三方" "$BAD_OUT"
# 关键豁免:分析增量栏的内容不该被校验
assert_not_contains "bad fixture exempts 分析增量栏 (#analysis_20260601 不报)" "#analysis_20260601" "$BAD_OUT"

# ---------- 3. 不存在的 wiki 目录 ----------
echo ""
echo "=== 3. 不存在的 wiki 目录 (期望 exit 2) ==="
NOEXIST_OUT=$(python3 "$SCRIPT" /tmp/__no_such_wiki_8881 2>&1)
NOEXIST_EXIT=$?
assert_exit "missing wiki dir exits 2" 2 "$NOEXIST_EXIT"

# ---------- 4. 空 wiki(没有 themes/ 也没有 quotes.md)----------
echo ""
echo "=== 4. 空 wiki + 空 data (期望 exit 0,无引用 = 全部命中) ==="
TMP=$(mktemp -d -t verify_empty.XXXX)
mkdir -p "$TMP/wiki" "$TMP/data"
EMPTY_OUT=$(python3 "$SCRIPT" "$TMP/wiki" 2>&1)
EMPTY_EXIT=$?
rm -rf "$TMP"
assert_exit "empty wiki exits 0" 0 "$EMPTY_EXIT"

# ---------- 5. --quiet 模式 ----------
echo ""
echo "=== 5. --quiet 模式 (期望无 stdout,exit 1) ==="
QUIET_OUT=$(python3 "$SCRIPT" --quiet "$BAD" 2>&1)
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

# ---------- 总结 ----------
echo ""
echo "=== 总结 ==="
TOTAL=$((PASS + FAIL))
if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}全部通过:$PASS / $TOTAL${NC}"
    exit 0
else
    echo -e "${RED}失败:$FAIL / $TOTAL${NC}"
    exit 1
fi
