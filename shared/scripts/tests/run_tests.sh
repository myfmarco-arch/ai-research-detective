#!/usr/bin/env bash
# shared/scripts/tests/run_tests.sh —— lint_context 自检
set -u

# 上溯到仓库根(tests/ → scripts/ → shared/ → repo root)
cd "$(dirname "$0")/../../.."

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
        echo "$haystack" | head -30 | sed 's/^/    /'
        FAIL=$((FAIL + 1))
    fi
}

SCRIPT="shared/scripts/lint_context.py"

# ---------- 1. fixture_context_good.md ----------
echo "=== 1. fixture_context_good.md (期望干净通过) ==="
GOOD_OUT=$(python3 "$SCRIPT" shared/scripts/tests/fixture_context_good.md 2>&1)
GOOD_EXIT=$?
assert_exit "good fixture exits 0" 0 "$GOOD_EXIT"
assert_contains "good fixture says PASS" "PASS" "$GOOD_OUT"

# ---------- 2. fixture_context_bad.md ----------
echo ""
echo "=== 2. fixture_context_bad.md (期望红线全中) ==="
BAD_OUT=$(python3 "$SCRIPT" shared/scripts/tests/fixture_context_bad.md 2>&1)
BAD_EXIT=$?
assert_exit "bad fixture exits 1" 1 "$BAD_EXIT"
for rule in R_EMPTY R_PLACEHOLDER R_RESEARCH_Q_THIN Y_FILLER_BOTTOMLINE; do
    assert_contains "bad fixture hits $rule" "[$rule" "$BAD_OUT"
done
# 具体场景
assert_contains "bad fixture catches 「了解用户对智能音箱」12 字过短" "了解用户对智能音箱" "$BAD_OUT"
assert_contains "bad fixture catches 「请谨慎使用」填充式底线" "请谨慎使用" "$BAD_OUT"
assert_contains "bad fixture catches 「我的身份」空段" "「我的身份」" "$BAD_OUT"

# ---------- 3. 空模板自检(模板里所有字段都空 + 模板说明块在) ----------
echo ""
echo "=== 3. 空模板 CONTEXT (期望 fail,模板说明块 + 占位符 + 空字段都中) ==="
TEMPL_OUT=$(python3 "$SCRIPT" shared/templates/CONTEXT.md 2>&1)
TEMPL_EXIT=$?
assert_exit "template exits 1" 1 "$TEMPL_EXIT"
assert_contains "template hits R_TEMPLATE_BLOCK" "R_TEMPLATE_BLOCK" "$TEMPL_OUT"
assert_contains "template hits R_PLACEHOLDER" "R_PLACEHOLDER" "$TEMPL_OUT"
assert_contains "template hits R_EMPTY 要回答" "要回答" "$TEMPL_OUT"

# ---------- 4. 不存在的文件 ----------
echo ""
echo "=== 4. 不存在的文件 (期望 exit 2) ==="
NOEXIST_OUT=$(python3 "$SCRIPT" /tmp/__no_such_context_8881.md 2>&1)
NOEXIST_EXIT=$?
assert_exit "missing file exits 2" 2 "$NOEXIST_EXIT"

# ---------- 5. --quiet 模式 ----------
echo ""
echo "=== 5. --quiet 模式 (期望无 stdout) ==="
QUIET_OUT=$(python3 "$SCRIPT" --quiet shared/scripts/tests/fixture_context_bad.md 2>&1)
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

# ---------- 6. --no-warn 模式 ----------
echo ""
echo "=== 6. --no-warn 模式 (good fixture 完全干净) ==="
NW_OUT=$(python3 "$SCRIPT" --no-warn shared/scripts/tests/fixture_context_good.md 2>&1)
NW_EXIT=$?
assert_exit "no-warn good exits 0" 0 "$NW_EXIT"

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
