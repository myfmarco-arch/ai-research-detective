#!/usr/bin/env bash
# skills/research-reviewer/scripts/tests/run_tests.sh —— lint_review 自检
set -u

cd "$(dirname "$0")/../../../.."

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

PASS=0
FAIL=0

assert_exit() {
    if [ "$2" = "$3" ]; then
        echo -e "${GREEN}✓${NC} $1 (exit $3)"
        PASS=$((PASS + 1))
    else
        echo -e "${RED}✗${NC} $1 (expected exit $2, got $3)"
        FAIL=$((FAIL + 1))
    fi
}

assert_contains() {
    if echo "$3" | grep -qF "$2"; then
        echo -e "${GREEN}✓${NC} $1 (contains '$2')"
        PASS=$((PASS + 1))
    else
        echo -e "${RED}✗${NC} $1 (missing '$2')"
        echo "$3" | head -20 | sed 's/^/    /'
        FAIL=$((FAIL + 1))
    fi
}

SCRIPT="skills/research-reviewer/scripts/lint_review.py"
GOOD="skills/research-reviewer/scripts/tests/fixture_review_good.md"
BAD="skills/research-reviewer/scripts/tests/fixture_review_bad.md"

echo "=== 1. fixture_review_good (期望 PASS) ==="
GOOD_OUT=$(python3 "$SCRIPT" "$GOOD" 2>&1)
assert_exit "good fixture exits 0" 0 $?
assert_contains "good fixture says PASS" "PASS" "$GOOD_OUT"

echo ""
echo "=== 2. fixture_review_bad (期望红线全中) ==="
BAD_OUT=$(python3 "$SCRIPT" "$BAD" 2>&1)
BAD_EXIT=$?
assert_exit "bad fixture exits 1" 1 "$BAD_EXIT"
for rule in V_NO_SEARCH V_THIN_SEARCH V_NO_COUNTER V_NO_RECHECK; do
    assert_contains "bad fixture hits $rule" "[$rule" "$BAD_OUT"
done

echo ""
echo "=== 3. 不存在的文件 (期望 exit 2) ==="
NOEXIST_OUT=$(python3 "$SCRIPT" /tmp/__no_such_review_8881.md 2>&1)
assert_exit "missing file exits 2" 2 $?

echo ""
echo "=== 4. --quiet 模式 ==="
QUIET_OUT=$(python3 "$SCRIPT" --quiet "$BAD" 2>&1)
QUIET_EXIT=$?
assert_exit "quiet exits 1" 1 "$QUIET_EXIT"
if [ -z "$QUIET_OUT" ]; then
    echo -e "${GREEN}✓${NC} quiet 无输出"
    PASS=$((PASS + 1))
else
    echo -e "${RED}✗${NC} quiet 意外输出"
    FAIL=$((FAIL + 1))
fi

# ---------- 5. 复核表缺「重标依据」列 ----------
echo ""
echo "=== 5. 复核表缺「重标依据」列 (V_RECHECK_THIN) ==="
TMP=$(mktemp -t review_thin.XXXX.md)
cat > "$TMP" <<'EOF'
# 对抗性审查

## 结论 1:测试

**判定: confirmed**

**搜索记录:**

- 第 1 轮: grep → #interview_01
- 第 2 轮: 读 wiki → #interview_02
- 第 3 轮: 检查 → #interview_03

**未找到反面证据:** 搜了 3 轮未发现

## 证据强度复核

| 结论 | detective 标 | reviewer 重标 | 差异原因 |
|---|---|---|---|
| 测试 | 强 | 强 | 无 |
EOF
THIN_OUT=$(python3 "$SCRIPT" "$TMP" 2>&1)
THIN_EXIT=$?
rm -f "$TMP"
assert_exit "缺「重标依据」列 exits 1" 1 "$THIN_EXIT"
assert_contains "hits V_RECHECK_THIN" "V_RECHECK_THIN" "$THIN_OUT"

# ---------- 6. 缺「核心结论筛选模式」声明 ----------
echo ""
echo "=== 6. 缺「核心结论筛选模式」声明 (V_NO_SAMPLING_MODE) ==="
TMP6=$(mktemp -t review_no_mode.XXXX.md)
cat > "$TMP6" <<'EOF'
# 对抗性审查
## 结论 1:测试
**判定: confirmed**
**搜索记录:**
- 第 1 轮: grep → #interview_01
- 第 2 轮: 读 → #interview_02
- 第 3 轮: 检查 → #interview_03
**未找到反面证据:** 搜了 3 轮未发现
## 证据强度复核
| 结论 | detective 标 | reviewer 重标 | 重标依据 | 差异 |
|---|---|---|---|---|
| 测试 | 强 | 强 | 三源验证 | 无 |
EOF
NMODE_OUT=$(python3 "$SCRIPT" "$TMP6" 2>&1)
NMODE_EXIT=$?
rm -f "$TMP6"
assert_exit "缺 sampling mode 声明 exits 1" 1 "$NMODE_EXIT"
assert_contains "hits V_NO_SAMPLING_MODE" "V_NO_SAMPLING_MODE" "$NMODE_OUT"

# ---------- 7. 声明 multi-agent 但缺采样表 ----------
echo ""
echo "=== 7. 声明 multi-agent 但缺采样表 (V_NO_SAMPLING_TABLE) ==="
TMP7=$(mktemp -t review_no_table.XXXX.md)
cat > "$TMP7" <<'EOF'
# 对抗性审查
**核心结论筛选模式**: multi-agent 采样取交集
## 结论 1:测试
**判定: confirmed**
**搜索记录:**
- 第 1 轮: grep → #interview_01
- 第 2 轮: 读 → #interview_02
- 第 3 轮: 检查 → #interview_03
**未找到反面证据:** 搜了 3 轮未发现
## 证据强度复核
| 结论 | detective 标 | reviewer 重标 | 重标依据 | 差异 |
|---|---|---|---|---|
| 测试 | 强 | 强 | 三源验证 | 无 |
EOF
NTBL_OUT=$(python3 "$SCRIPT" "$TMP7" 2>&1)
NTBL_EXIT=$?
rm -f "$TMP7"
assert_exit "声明 multi-agent 但缺采样表 exits 1" 1 "$NTBL_EXIT"
assert_contains "hits V_NO_SAMPLING_TABLE" "V_NO_SAMPLING_TABLE" "$NTBL_OUT"

# ---------- 8. 降级到单 LLM 时不需要采样表 ----------
echo ""
echo "=== 8. 降级单 LLM 模式不强制采样表 (期望 PASS) ==="
TMP8=$(mktemp -t review_degraded.XXXX.md)
cat > "$TMP8" <<'EOF'
# 对抗性审查
**核心结论筛选模式**: 降级单 LLM(原因:用户指定快速审)
## 结论 1:测试
**判定: confirmed**
**搜索记录:**
- 第 1 轮: grep → #interview_01
- 第 2 轮: 读 → #interview_02
- 第 3 轮: 检查 → #interview_03
**未找到反面证据:** 搜了 3 轮未发现
## 证据强度复核
| 结论 | detective 标 | reviewer 重标 | 重标依据 | 差异 |
|---|---|---|---|---|
| 测试 | 强 | 强 | 三源验证 | 无 |
EOF
DEG_OUT=$(python3 "$SCRIPT" "$TMP8" 2>&1)
DEG_EXIT=$?
rm -f "$TMP8"
assert_exit "降级模式不缺采样表 exits 0" 0 "$DEG_EXIT"

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
