"""Unit test: /api/fetch-models candidate URL order.

The user-supplied base_url must always be tried verbatim first (base/models);
/v1 and compat-suffix derivations are fallback probes only.

Usage: python tests/test_fetch_candidates.py
"""
import os
import sys
import tempfile
from pathlib import Path

# server.py initializes its database at import time — point it at a
# throwaway home before importing (same trick smoke.py uses).
_tmp = tempfile.mkdtemp(prefix="ccsw-cand-")
os.environ["CC_SWITCH_TEST_HOME"] = _tmp
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from server import _build_models_url_candidates, _plan_gateway_hint  # noqa: E402

failures = 0


def ok(cond, label):
    global failures
    if cond:
        print(f"  ok - {label}")
    else:
        failures += 1
        print(f"  FAIL - {label}")


# 火山方舟 coding-plan 地址：原样拼 /models 必须排第一，不能先拼 /v1/models
ark = _build_models_url_candidates("https://ark.cn-beijing.volces.com/api/plan/v3")
ok(ark[0] == "https://ark.cn-beijing.volces.com/api/plan/v3/models",
   "plain base_url tried verbatim first")
ok("/api/plan/v3/v1/models" in ark[1], "v1 fallback kept after exact URL")

# 已带 /v1 的地址：不再出现 v1/v1 这类拼接
v1 = _build_models_url_candidates("https://api.example.com/v1")
ok(v1 == ["https://api.example.com/v1/models"], "trailing /v1 yields single exact candidate")

# 中转后缀（生数云 /anthropic）：原样优先，兼容推导保留
ssy = _build_models_url_candidates("https://router.shengsuanyun.com/anthropic")
ok(ssy[0] == "https://router.shengsuanyun.com/anthropic/models",
   "compat-suffix base_url tried verbatim first")
ok("https://router.shengsuanyun.com/v1/models" in ssy and
   "https://router.shengsuanyun.com/models" in ssy,
   "compat root derivations kept as fallbacks")

# 尾斜杠只影响探测地址拼接，不产生重复候选
slash = _build_models_url_candidates("https://api.example.com/")
ok(slash == ["https://api.example.com/models", "https://api.example.com/v1/models"],
   "trailing slash stripped for probing, deduped")

# 火山套餐网关无 /models 接口：给出可操作提示而不是干巴巴的 404
hint = _plan_gateway_hint("https://ark.cn-beijing.volces.com/api/plan/v3")
ok(hint is not None and "ark-code-latest" in hint, "agent plan gateway gets actionable hint")
ok(_plan_gateway_hint("https://ark.cn-beijing.volces.com/api/coding/v3") is not None,
   "coding plan gateway gets hint too")
ok(_plan_gateway_hint("https://api.deepseek.com") is None, "non-ark gateway gets no hint")

if failures:
    print(f"FETCH CANDIDATE TESTS FAILED ({failures})")
    sys.exit(1)
print("FETCH CANDIDATE TESTS PASSED")
