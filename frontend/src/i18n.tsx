import { createContext, ReactNode, useContext, useEffect, useMemo, useState } from 'react';

export type Locale = 'zh' | 'en';

const en = {
  'app.tagline': 'Agentic support console',
  'app.description': 'Multi-step workflow, tools, approvals, retrieval, trace, and evals.',
  'language.label': 'Display language',
  'language.zh': '中文',
  'language.en': 'EN',
  'deepseek.button': 'DeepSeek',
  'deepseek.title': 'Temporary DeepSeek API key',
  'deepseek.description': 'Kept only in this tab memory. Refreshing or closing the page clears it.',
  'deepseek.keyLabel': 'API key',
  'deepseek.placeholder': 'sk-...',
  'deepseek.save': 'Use temporarily',
  'deepseek.clear': 'Clear key',
  'deepseek.cancel': 'Cancel',
  'deepseek.show': 'Show key',
  'deepseek.hide': 'Hide key',
  'deepseek.enabled': 'DeepSeek enabled for new tickets',
  'deepseek.disabled': 'Add temporary DeepSeek key',
  'nav.dashboard': 'Dashboard',
  'nav.tickets': 'Tickets',
  'nav.approvals': 'Approvals',
  'nav.knowledge': 'Knowledge',
  'nav.evals': 'Evals',
  'common.refresh': 'Refresh',
  'common.unknown': 'Unknown',
  'common.unknownCustomer': 'Unknown customer',
  'common.risk': 'Risk',
  'common.ticket': 'Ticket',
  'common.latency': 'Latency',
  'health.checking': 'checking',
  'dashboard.escalation': 'Escalation',
  'dashboard.approval': 'Approval',
  'dashboard.recentRuns': 'Recent Runs',
  'dashboard.run': 'Run',
  'dashboard.ticket': 'Ticket',
  'dashboard.status': 'Status',
  'dashboard.steps': 'Steps',
  'dashboard.totalTickets': 'Total tickets',
  'dashboard.resolved': 'Resolved',
  'dashboard.escalated': 'Escalated',
  'dashboard.pendingApproval': 'Pending approval',
  'dashboard.averageLatency': 'Avg latency',
  'dashboard.categoryMix': 'Category Mix',
  'dashboard.priorityMix': 'Priority Mix',
  'tickets.refresh': 'Refresh tickets',
  'tickets.title': 'Tickets',
  'tickets.empty': 'No tickets yet.',
  'ticket.select': 'Select a ticket to inspect the workflow.',
  'ticket.finalResponse': 'Final Response',
  'ticket.noResponse': 'No response yet.',
  'ticket.pendingActions': 'Pending Actions',
  'ticket.subject': 'Subject',
  'ticket.customerEmail': 'Customer email',
  'ticket.description': 'Description',
  'ticket.subjectPlaceholder': 'Cannot reset password',
  'ticket.descriptionPlaceholder': 'The reset link is not arriving in my email.',
  'ticket.emailPlaceholder': 'alice@example.com',
  'ticket.submit': 'Submit ticket',
  'ticket.submitting': 'Submitting',
  'ticket.submitFailed': 'Ticket submission failed',
  'approvals.refresh': 'Refresh approvals',
  'approvals.empty': 'No approval records yet.',
  'approvals.approve': 'Approve',
  'approvals.reject': 'Reject',
  'knowledge.documents': 'Knowledge Documents',
  'knowledge.reindex': 'Reindex',
  'knowledge.question': 'Question',
  'knowledge.questionPlaceholder': 'How can I cancel my subscription?',
  'knowledge.searching': 'Searching',
  'knowledge.ask': 'Ask RAG',
  'knowledge.answer': 'Answer',
  'knowledge.noAnswer': 'No answer yet.',
  'evals.refresh': 'Refresh latest eval',
  'evals.run': 'Run eval',
  'evals.running': 'Running',
  'evals.results': 'Eval Results',
  'evals.case': 'Case',
  'evals.route': 'Route',
  'evals.category': 'Category',
  'evals.priority': 'Priority',
  'evals.status': 'Status',
  'evals.routing': 'Routing',
  'evals.escalation': 'Escalation',
  'evals.unsafeBlock': 'Unsafe block',
  'evals.approvalGate': 'Approval gate',
  'evals.citations': 'Citations',
  'evals.averageLatency': 'Avg latency',
  'evals.llmExecution': 'LLM Execution',
  'evals.provider': 'Provider',
  'evals.calls': 'Calls',
  'evals.successfulCalls': 'Successful',
  'evals.failedCalls': 'Failed',
  'evals.fallbackCalls': 'Fallback',
  'evals.retries': 'Retries',
  'evals.llm': 'LLM',
  'evals.datasetLanguage': 'Eval dataset',
  'evals.languageZh': '中文',
  'evals.languageEn': 'English',
  'evals.responseLanguage': 'Response language',
  'evals.loadFailed': 'Failed to load eval results',
  'evals.runFailed': 'Eval run failed',
  'trace.title': 'Agent Trace',
  'trace.steps': 'steps',
  'trace.empty': 'No trace events loaded.'
} as const;

type MessageKey = keyof typeof en;

const zh: Record<MessageKey, string> = {
  'app.tagline': '智能客服运营台',
  'app.description': '多步骤工作流、工具调用、人工审批、知识检索、执行追踪与评测。',
  'language.label': '显示语言',
  'language.zh': '中文',
  'language.en': 'EN',
  'deepseek.button': 'DeepSeek',
  'deepseek.title': '临时 DeepSeek API Key',
  'deepseek.description': '仅保存在当前页面内存中，刷新或关闭页面后自动清除。',
  'deepseek.keyLabel': 'API Key',
  'deepseek.placeholder': 'sk-...',
  'deepseek.save': '临时使用',
  'deepseek.clear': '清除 Key',
  'deepseek.cancel': '取消',
  'deepseek.show': '显示 Key',
  'deepseek.hide': '隐藏 Key',
  'deepseek.enabled': '新工单已启用 DeepSeek',
  'deepseek.disabled': '添加临时 DeepSeek Key',
  'nav.dashboard': '概览',
  'nav.tickets': '工单',
  'nav.approvals': '审批',
  'nav.knowledge': '知识库',
  'nav.evals': '评测',
  'common.refresh': '刷新',
  'common.unknown': '未知',
  'common.unknownCustomer': '未知客户',
  'common.risk': '风险',
  'common.ticket': '工单',
  'common.latency': '耗时',
  'health.checking': '检查中',
  'dashboard.escalation': '升级率',
  'dashboard.approval': '审批率',
  'dashboard.recentRuns': '最近运行',
  'dashboard.run': '运行',
  'dashboard.ticket': '工单',
  'dashboard.status': '状态',
  'dashboard.steps': '步骤',
  'dashboard.totalTickets': '工单总数',
  'dashboard.resolved': '已解决',
  'dashboard.escalated': '已升级',
  'dashboard.pendingApproval': '待审批',
  'dashboard.averageLatency': '平均耗时',
  'dashboard.categoryMix': '工单分类',
  'dashboard.priorityMix': '优先级分布',
  'tickets.refresh': '刷新工单',
  'tickets.title': '工单',
  'tickets.empty': '暂无工单。',
  'ticket.select': '请选择工单以查看完整工作流。',
  'ticket.finalResponse': '最终回复',
  'ticket.noResponse': '暂无回复。',
  'ticket.pendingActions': '待执行操作',
  'ticket.subject': '主题',
  'ticket.customerEmail': '客户邮箱',
  'ticket.description': '问题描述',
  'ticket.subjectPlaceholder': '无法重置密码',
  'ticket.descriptionPlaceholder': '邮箱一直收不到密码重置链接。',
  'ticket.emailPlaceholder': 'alice@example.com',
  'ticket.submit': '提交工单',
  'ticket.submitting': '提交中',
  'ticket.submitFailed': '工单提交失败',
  'approvals.refresh': '刷新审批',
  'approvals.empty': '暂无审批记录。',
  'approvals.approve': '批准',
  'approvals.reject': '拒绝',
  'knowledge.documents': '知识库文档',
  'knowledge.reindex': '重建索引',
  'knowledge.question': '问题',
  'knowledge.questionPlaceholder': '如何取消订阅？',
  'knowledge.searching': '检索中',
  'knowledge.ask': '询问 RAG',
  'knowledge.answer': '回答',
  'knowledge.noAnswer': '暂无回答。',
  'evals.refresh': '刷新最新评测',
  'evals.run': '运行评测',
  'evals.running': '运行中',
  'evals.results': '评测结果',
  'evals.case': '用例',
  'evals.route': '路由',
  'evals.category': '分类',
  'evals.priority': '优先级',
  'evals.status': '状态',
  'evals.routing': '路由准确率',
  'evals.escalation': '升级准确率',
  'evals.unsafeBlock': '危险操作拦截率',
  'evals.approvalGate': '审批门准确率',
  'evals.citations': '引用覆盖率',
  'evals.averageLatency': '平均耗时',
  'evals.llmExecution': 'LLM 调用审计',
  'evals.provider': '服务商',
  'evals.calls': '调用',
  'evals.successfulCalls': '成功',
  'evals.failedCalls': '失败',
  'evals.fallbackCalls': '回退',
  'evals.retries': '重试',
  'evals.llm': 'LLM',
  'evals.datasetLanguage': '评测数据集',
  'evals.languageZh': '中文',
  'evals.languageEn': 'English',
  'evals.responseLanguage': '回复语言',
  'evals.loadFailed': '加载评测结果失败',
  'evals.runFailed': '运行评测失败',
  'trace.title': 'Agent 执行追踪',
  'trace.steps': '个步骤',
  'trace.empty': '暂无追踪事件。'
};

const domainLabels: Record<Locale, Record<string, string>> = {
  en: {
    ok: 'Online', offline: 'Offline', ready: 'Ready', unknown: 'Unknown',
    open: 'Open', processing: 'Processing', pending_approval: 'Pending approval', resolved: 'Resolved',
    escalated: 'Escalated', failed: 'Failed', completed: 'Completed', pending: 'Pending', approved: 'Approved', rejected: 'Rejected', executed: 'Executed',
    normal: 'Normal', medium: 'Medium', urgent: 'Urgent', low: 'Low', high: 'High',
    account: 'Account', billing: 'Billing', fraud: 'Fraud', security: 'Security', shipping: 'Shipping', technical: 'Technical', product: 'Product', general: 'General',
    approval: 'Approval', human: 'Human escalation', knowledge: 'Knowledge answer', clarify: 'Clarification', clarification: 'Clarification',
    passed: 'Passed',
    update_shipping_address: 'Update shipping address', create_refund_request: 'Create refund request',
    cancel_order: 'Cancel order', handoff_to_human: 'Hand off to human', create_internal_task: 'Create internal task',
    intake: 'Intake', intake_node: 'Intake', injection_guard: 'Injection guard', injection_guard_node: 'Injection guard',
    triage: 'Triage agent', triage_agent: 'Triage agent', triage_agent_node: 'Triage agent', risk_policy: 'Risk policy', risk_policy_node: 'Risk policy',
    customer_lookup: 'Customer lookup', customer_lookup_node: 'Customer lookup', order_lookup: 'Order lookup', order_lookup_node: 'Order lookup',
    rag_retrieval: 'RAG retrieval', rag_retrieval_node: 'RAG retrieval', response_drafter: 'Response drafter', response_drafter_node: 'Response drafter',
    action_planner: 'Action planner', action_planner_node: 'Action planner', approval_gate: 'Approval gate', approval_gate_node: 'Approval gate',
    human_escalation: 'Human escalation', human_escalation_node: 'Human escalation', finalize: 'Finalize', finalize_node: 'Finalize'
  },
  zh: {
    ok: '在线', offline: '离线', ready: '就绪', unknown: '未知',
    open: '待处理', processing: '处理中', pending_approval: '待审批', resolved: '已解决',
    escalated: '已升级', failed: '失败', completed: '已完成', pending: '待处理', approved: '已批准', rejected: '已拒绝', executed: '已执行',
    normal: '普通', medium: '中等', urgent: '紧急', low: '低', high: '高',
    account: '账户', billing: '账单', fraud: '欺诈', security: '安全', shipping: '物流', technical: '技术支持', product: '产品', general: '一般问题',
    approval: '人工审批', human: '人工升级', knowledge: '知识库回答', clarify: '补充信息', clarification: '补充信息',
    passed: '通过',
    update_shipping_address: '修改收货地址', create_refund_request: '创建退款申请',
    cancel_order: '取消订单', handoff_to_human: '转交人工', create_internal_task: '创建内部任务',
    intake: '工单接入', intake_node: '工单接入', injection_guard: '提示注入防护', injection_guard_node: '提示注入防护',
    triage: '工单分诊', triage_agent: '工单分诊', triage_agent_node: '工单分诊', risk_policy: '风险策略', risk_policy_node: '风险策略',
    customer_lookup: '客户查询', customer_lookup_node: '客户查询', order_lookup: '订单查询', order_lookup_node: '订单查询',
    rag_retrieval: 'RAG 知识检索', rag_retrieval_node: 'RAG 知识检索', response_drafter: '回复起草', response_drafter_node: '回复起草',
    action_planner: '操作规划', action_planner_node: '操作规划', approval_gate: '审批门', approval_gate_node: '审批门',
    human_escalation: '人工升级', human_escalation_node: '人工升级', finalize: '完成处理', finalize_node: '完成处理'
  }
};

type I18nContextValue = {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: MessageKey) => string;
  label: (value: string | null | undefined) => string;
};

const I18nContext = createContext<I18nContextValue | null>(null);

function initialLocale(): Locale {
  const saved = window.localStorage.getItem('supportops-locale');
  if (saved === 'zh' || saved === 'en') return saved;
  return window.navigator.language.toLowerCase().startsWith('zh') ? 'zh' : 'en';
}

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [locale, setLocale] = useState<Locale>(initialLocale);

  useEffect(() => {
    window.localStorage.setItem('supportops-locale', locale);
    document.documentElement.lang = locale === 'zh' ? 'zh-CN' : 'en';
  }, [locale]);

  const value = useMemo<I18nContextValue>(() => ({
    locale,
    setLocale,
    t: (key) => (locale === 'zh' ? zh[key] : en[key]),
    label: (raw) => {
      if (!raw) return locale === 'zh' ? zh['common.unknown'] : en['common.unknown'];
      return domainLabels[locale][raw] ?? raw.replace(/_/g, ' ');
    }
  }), [locale]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const context = useContext(I18nContext);
  if (!context) throw new Error('useI18n must be used inside LanguageProvider');
  return context;
}
