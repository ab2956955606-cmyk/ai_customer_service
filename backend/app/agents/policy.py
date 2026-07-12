from __future__ import annotations

import re
from typing import Literal


Locale = Literal["en", "zh"]

CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
MARKDOWN_SOURCE_RE = re.compile(r"\b[a-zA-Z0-9_-]+\.md\b", re.IGNORECASE)

FRAUD_TERMS = {
    "fraud",
    "unauthorized charge",
    "chargeback",
    "欺诈",
    "盗刷",
    "未经授权扣款",
    "未经授权的扣款",
    "拒付",
}

SECURITY_TERMS = {
    "hacked",
    "account takeover",
    "legal",
    "lawsuit",
    "police",
    "emergency",
    "账号被盗",
    "账户被盗",
    "账号被黑",
    "账户被黑",
    "账号接管",
    "账户接管",
    "法律",
    "起诉",
    "诉讼",
    "律师函",
    "警察",
    "警方",
    "报警",
    "紧急",
}

URGENT_TERMS = FRAUD_TERMS | SECURITY_TERMS

REFUND_TERMS = {
    "refund",
    "money back",
    "duplicate charge",
    "退款",
    "退钱",
    "重复扣款",
    "重复收费",
}

CANCEL_ORDER_TERMS = {"cancel order", "取消订单"}

ADDRESS_CHANGE_TERMS = {
    "change address",
    "update address",
    "shipping address",
    "修改收货地址",
    "更改收货地址",
    "更新收货地址",
    "修改地址",
    "更改地址",
}

SHIPPING_TERMS = {
    "address",
    "shipping",
    "shipment",
    "delivery",
    "tracking",
    "package",
    "物流",
    "配送",
    "快递",
    "包裹",
    "发货",
    "到货",
    "送达",
    "追踪",
    "跟踪",
    "运单",
    "收货地址",
}

DOWNGRADE_TERMS = {"downgrade", "套餐降级", "降级套餐", "降级方案", "降级"}

SUBSCRIPTION_TERMS = {
    "cancel subscription",
    "subscription",
    "renewal",
    "取消订阅",
    "订阅",
    "续订",
    "续费",
}

ACCOUNT_DELETION_TERMS = {
    "account deletion",
    "delete my account",
    "删除账户",
    "删除账号",
    "注销账户",
    "注销账号",
}

PASSWORD_TERMS = {
    "password",
    "reset",
    "login",
    "sign in",
    "密码",
    "重置",
    "登录",
    "登陆",
}

INVOICE_TERMS = {
    "invoice",
    "receipt",
    "tax",
    "vat",
    "发票",
    "收据",
    "税务",
    "增值税",
}

SETUP_TERMS = {
    "setup",
    "install",
    "configure",
    "onboarding",
    "配置产品",
    "产品配置",
    "安装产品",
    "安装",
    "配置",
    "设置产品",
}

COMPLAINT_TERMS = {
    "angry",
    "terrible",
    "unacceptable",
    "complaint",
    "生气",
    "糟糕",
    "不可接受",
    "投诉",
    "差劲",
}

PROMPT_INJECTION_TERMS = {
    "ignore previous instructions",
    "reveal system prompt",
    "bypass approval",
    "execute refund without approval",
    "delete all data",
    "忽略之前的指令",
    "忽略先前指令",
    "无视之前的指令",
    "泄露系统提示词",
    "显示系统提示词",
    "绕过审批",
    "未经审批执行退款",
    "不经审批执行退款",
    "删除所有数据",
}

SEVERE_PROMPT_INJECTION_TERMS = PROMPT_INJECTION_TERMS - {
    "ignore previous instructions",
    "忽略之前的指令",
    "忽略先前指令",
    "无视之前的指令",
}

APPROVAL_TERMS = REFUND_TERMS | CANCEL_ORDER_TERMS | ADDRESS_CHANGE_TERMS | DOWNGRADE_TERMS | ACCOUNT_DELETION_TERMS


def normalize_text(subject: str, description: str = "") -> str:
    return f"{subject} {description}".lower()


def contains_any(text: str, terms: set[str]) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in terms)


def matching_terms(text: str, terms: set[str]) -> list[str]:
    lowered = text.lower()
    return sorted(term for term in terms if term in lowered)


def detect_locale(subject: str, description: str = "") -> Locale:
    return "zh" if CJK_RE.search(f"{subject} {description}") else "en"


def response_matches_locale(response: str | None, locale: Locale) -> bool:
    if not response or not response.strip():
        return False
    if locale == "en":
        return True

    customer_text = MARKDOWN_SOURCE_RE.sub("", response)
    chinese_count = len(CJK_RE.findall(customer_text))
    latin_count = len(re.findall(r"[a-zA-Z]", customer_text))
    return chinese_count >= 8 and chinese_count >= latin_count


def deterministic_classification(subject: str, description: str) -> dict[str, object]:
    text = normalize_text(subject, description)
    if contains_any(text, URGENT_TERMS):
        category = "fraud" if contains_any(text, FRAUD_TERMS) else "security"
        return _result(category, "urgent", "high", human=True, confidence=0.96)
    if contains_any(text, REFUND_TERMS):
        return _result("billing", "medium", "medium", approval=True, confidence=0.9)
    if contains_any(text, CANCEL_ORDER_TERMS):
        return _result("shipping", "medium", "medium", approval=True, confidence=0.9)
    if contains_any(text, ADDRESS_CHANGE_TERMS):
        return _result("shipping", "medium", "medium", approval=True, confidence=0.9)
    if contains_any(text, SHIPPING_TERMS):
        return _result("shipping", "normal", "low", confidence=0.88)
    if contains_any(text, DOWNGRADE_TERMS):
        return _result("account", "normal", "medium", approval=True, confidence=0.86)
    if contains_any(text, ACCOUNT_DELETION_TERMS):
        return _result("account", "medium", "medium", approval=True, confidence=0.9)
    if contains_any(text, SUBSCRIPTION_TERMS):
        return _result("account", "normal", "low", confidence=0.86)
    if contains_any(text, PASSWORD_TERMS):
        return _result("account", "normal", "low", confidence=0.92)
    if contains_any(text, INVOICE_TERMS):
        return _result("billing", "normal", "low", confidence=0.9)
    if contains_any(text, SETUP_TERMS):
        return _result("technical", "normal", "low", confidence=0.84)
    if contains_any(text, COMPLAINT_TERMS):
        return _result("general", "medium", "low", confidence=0.7)
    return _result("unknown", "normal", "low", confidence=0.35)


def _result(
    category: str,
    priority: str,
    risk_level: str,
    *,
    approval: bool = False,
    human: bool = False,
    confidence: float,
) -> dict[str, object]:
    return {
        "category": category,
        "priority": priority,
        "risk_level": risk_level,
        "requires_human": human,
        "requires_approval": approval,
        "confidence": confidence,
    }
