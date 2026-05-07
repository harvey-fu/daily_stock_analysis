# 本地代码修改记录

> 本文件记录所有本地代码修改项，方便与上游合并时对比。
> 最后更新：2026-05-07

---

## 修改一：支持 Tushare API 代理地址

**修改时间**：2026-05-04

**修改目的**：通过 `TUSHARE_API_URL` 环境变量支持自定义 Tushare 代理地址，使用中转服务替代官方 API

**涉及文件**：

### 1. `src/config.py` — 数据模型字段（第 598-600 行）

```diff
     # === 数据源 API Token ===
     tushare_token: Optional[str] = None
+    # [新增] 支持自定义 Tushare API 代理地址，使用中转服务时填写，留空则用官方 api.tushare.pro | 2026-05-04
+    tushare_api_url: Optional[str] = None
     tickflow_api_key: Optional[str] = None
```

### 2. `src/config.py` — 环境变量读取（第 1319-1321 行）

```diff
             feishu_folder_token=os.getenv('FEISHU_FOLDER_TOKEN'),
             tushare_token=os.getenv('TUSHARE_TOKEN'),
+            # [新增] 读取 TUSHARE_API_URL 环境变量，支持 Tushare 中转代理 | 2026-05-04
+            tushare_api_url=os.getenv('TUSHARE_API_URL'),
             tickflow_api_key=os.getenv('TICKFLOW_API_KEY'),
```

### 3. `data_provider/tushare_fetcher.py` — API 客户端构建（第 174-188 行）

```diff
     def _build_api_client(self, token: str) -> _TushareHttpClient:
         """
         Build a lightweight Tushare Pro client over direct HTTP requests.

         The project already normalizes all Pro calls through the same request
         contract, so we do not need the official tushare SDK during runtime.
         """
-        client = _TushareHttpClient(token=token)
-        logger.debug("Tushare API client configured for direct HTTP calls")
+        # client = _TushareHttpClient(token=token)  # 原始代码：使用官方默认地址
+        # logger.debug("Tushare API client configured for direct HTTP calls")
+        # [修改] 支持通过 TUSHARE_API_URL 环境变量自定义 Tushare API 代理地址 | 2026-05-04
+        config = get_config()
+        api_url = getattr(config, 'tushare_api_url', None) or "http://api.tushare.pro"
+        client = _TushareHttpClient(token=token, api_url=api_url)
+        logger.debug(f"Tushare API client configured for direct HTTP calls (url={api_url})")
         return client
```

### 4. `.env.example` — 配置模板（第 24-26 行）

```diff
 TUSHARE_TOKEN=
+ # [新增] Tushare API 代理地址，使用中转服务时填写，留空则用官方 api.tushare.pro | 2026-05-04
+ # TUSHARE_API_URL=https://your-proxy.example.com
```

---

## 修改二：指定 LLM 主模型为 deepseek-v4-pro

**修改时间**：2026-05-04

**修改目的**：解决 `config.py` 中 `DEEPSEEK_API_KEY` 存在时默认使用 `deepseek-chat` 而非 `deepseek-v4-pro` 的问题

**问题根因**：`src/config.py` 第 1131 行先读取 `LITELLM_MODEL` 环境变量；若为空，第 1145 行检测到 `DEEPSEEK_API_KEY` 后直接赋值 `deepseek/deepseek-chat`，导致第 1211 行的多渠道自动推断逻辑（`LLM_DEEPSEEK_MODELS`）被跳过。

**涉及文件**：

### 1. `.env` — 添加 LITELLM_MODEL（第 69-71 行）

```diff
 LLM_DEEPSEEK_MODELS=deepseek-v4-pro
+ # [新增] 显式指定主模型，避免 config.py 中 deepseek_api_keys 默认为 deepseek-chat | 2026-05-04
+ LITELLM_MODEL=deepseek/deepseek-v4-pro
```

**config.py 相关代码参考**（未修改，仅供理解）：

```python
# 第 1131 行：LITELLM_MODEL 优先级最高
litellm_model = os.getenv('LITELLM_MODEL', '').strip()

# 第 1145 行：当 LITELLM_MODEL 为空且 DEEPSEEK_API_KEY 存在时，回退到 deepseek-chat
if not litellm_model:
    ...
    elif deepseek_api_keys:
        litellm_model = 'deepseek/deepseek-chat'

# 第 1211 行：从多渠道推断，但此时 litellm_model 已有值，不会执行
if not litellm_model and llm_channels:
    for _ch in llm_channels:
        if _ch.get('models'):
            litellm_model = _ch['models'][0]
            break
```

---

## 修改汇总

| 序号 | 文件 | 修改类型 | 日期 |
|------|------|----------|------|
| 1 | `src/config.py:599-600` | 新增字段 | 2026-05-04 |
| 2 | `src/config.py:1320-1321` | 新增环境变量读取 | 2026-05-04 |
| 3 | `data_provider/tushare_fetcher.py:181-188` | 修改逻辑 | 2026-05-04 |
| 4 | `.env.example:25-26` | 新增配置模板 | 2026-05-04 |
| 5 | `.env:70-71` | 新增配置项 | 2026-05-04 |

> `.env` 文件不纳入 git 跟踪，拉取上游更新时不会冲突。
> `src/config.py` 和 `data_provider/tushare_fetcher.py` 的修改需在 git pull 后检查是否有冲突。

---

## 修改三：融资融券功能（Margin Trading）

**修改时间**：2026-05-06

**修改目的**：为持仓管理系统添加融资融券功能，支持独立的融资融券账户、融资买入/融券卖出交易、利息计算、担保品管理和风险监控

**功能概述**：
- 独立融资融券账户（与普通现金账户分开）
- 支持四种交易类型：融资买入、融券卖出、卖券还款、买券还券
- 按日计算利息，支持年利率配置
- 维持担保比例计算和风险告警
- CSV 导入支持（华泰/中信/招商融资融券格式）

**涉及文件**：

### 1. `src/storage.py` — 数据库层扩展

**PortfolioAccount 表新增字段**：
```diff
     # === Portfolio P0 fields ===
     name = Column(String(64), nullable=False)
     broker = Column(String(64), nullable=True)
     market = Column(String(8), nullable=False, default='cn')
     base_currency = Column(String(8), nullable=False, default='CNY')
     owner_id = Column(String(64), nullable=True)
+    # [新增] 融资融券账户支持 | 2026-05-06
+    account_type = Column(String(16), nullable=False, default='cash')  # cash/margin
+    margin_interest_rate = Column(Float, nullable=True)  # 融资年利率
+    securities_interest_rate = Column(Float, nullable=True)  # 融券年利率
+    margin_ratio = Column(Float, nullable=True)  # 保证金比例
```

**新增 PortfolioMarginDetail 表**：
```python
# [新增] 融资融券明细表 | 2026-05-06
class PortfolioMarginDetail(Base):
    __tablename__ = 'portfolio_margin_details'

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('portfolio_accounts.id'), nullable=False)
    trade_id = Column(Integer, ForeignKey('portfolio_trades.id'), nullable=True)
    symbol = Column(String(16), nullable=False)
    market = Column(String(8), nullable=False, default='cn')
    margin_type = Column(String(16), nullable=False)  # margin (融资) / securities (融券)
    principal = Column(Float, nullable=False)  # 融资/融券本金
    quantity = Column(Float, nullable=True)  # 融券数量
    interest_rate = Column(Float, nullable=False)  # 年利率
    accrued_interest = Column(Float, default=0.0)  # 已计利息
    total_interest_paid = Column(Float, default=0.0)  # 已付利息
    open_date = Column(Date, nullable=False)  # 开仓日期
    close_date = Column(Date, nullable=True)  # 平仓日期
    is_open = Column(Boolean, default=True)  # 是否未平仓
    collateral_value = Column(Float, nullable=True)  # 担保品价值
    maintenance_ratio = Column(Float, nullable=True)  # 维持担保比例
    note = Column(String(255))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
```

### 2. `src/repositories/portfolio_repo.py` — 数据访问层

**新增方法**：
- `create_account_with_type()` - 创建支持账户类型的账户
- `insert_margin_detail()` - 插入融资融券明细
- `get_open_margin_details()` - 获取未平仓融资融券明细
- `get_all_margin_details()` - 获取所有融资融券明细
- `update_margin_interest()` - 更新融资融券利息
- `close_margin_detail()` - 平仓融资融券
- `get_margin_summary()` - 获取融资融券汇总
- `calculate_margin_interest()` - 计算融资融券利息

### 3. `src/services/portfolio_service.py` — 服务层

**新增常量**：
```python
# [新增] 融资融券相关常量 | 2026-05-06
VALID_ACCOUNT_TYPES = {"cash", "margin"}
VALID_MARGIN_SIDES = {"margin_buy", "short_sell", "margin_repay", "short_cover"}
VALID_MARGIN_TYPES = {"margin", "securities"}
```

**新增方法**：
- `record_margin_trade()` - 记录融资融券交易
- `get_margin_details()` - 获取融资融券明细
- `get_margin_summary()` - 获取融资融券汇总
- `calculate_margin_interest()` - 计算融资融券利息
- `get_maintenance_ratio()` - 获取维持担保比例
- `close_margin_detail()` - 平仓融资融券

### 4. `api/v1/endpoints/portfolio.py` — API 端点

**新增端点**：
```
POST /margin/trades        - 录入融资融券交易
GET  /margin/details       - 获取融资融券明细
GET  /margin/summary       - 获取融资融券汇总
GET  /margin/interest      - 计算融资融券利息
GET  /margin/maintenance   - 获取维持担保比例
POST /margin/{detail_id}/close - 平仓融资融券
GET  /margin/risk          - 获取融资融券风险报告
```

### 5. `api/v1/schemas/portfolio.py` — Schema 定义

**新增 Schema**：
- `MarginTradeCreateRequest` - 融资融券交易创建请求
- `MarginDetailItem` - 融资融券明细
- `MarginDetailListResponse` - 融资融券明细列表
- `MarginSummary` - 融资融券汇总
- `MarginInterestItem` / `MarginInterestResponse` - 利息计算
- `MaintenanceRatioResponse` - 维持担保比例
- `MarginCloseRequest` - 平仓请求

**修改 Schema**：
- `PortfolioAccountCreateRequest` - 新增 `account_type`, `margin_interest_rate`, `securities_interest_rate`, `margin_ratio` 字段
- `PortfolioAccountItem` - 新增对应返回字段

### 6. `src/services/portfolio_risk_service.py` — 风险管理

**新增方法**：
- `get_margin_risk_report()` - 获取融资融券风险报告
- `_build_margin_alerts()` - 构建融资融券风险告警

**风险指标**：
- 维持担保比例监控
- 追保线（150%）和平仓线（130%）告警
- 利息成本提醒

### 7. `src/services/portfolio_import_service.py` — CSV 导入

**新增融资融券 CSV 解析器**：
- `huatai_margin` - 华泰融资融券
- `citic_margin` - 中信融资融券
- `cmb_margin` - 招商融资融券

**新增方法**：
- `parse_margin_csv()` - 解析融资融券 CSV
- `commit_margin_records()` - 提交融资融券记录
- `_normalize_margin_row()` - 标准化融资融券行
- `_normalize_margin_side()` - 标准化融资融券交易类型

### 8. `apps/dsa-web/src/types/portfolio.ts` — 前端类型

**新增类型**：
```typescript
// [新增] 融资融券相关类型 | 2026-05-06
export type MarginSide = 'margin_buy' | 'short_sell' | 'margin_repay' | 'short_cover';
export type MarginType = 'margin' | 'securities';

export interface MarginTradeCreateRequest { ... }
export interface MarginDetailItem { ... }
export interface MarginDetailListResponse { ... }
export interface MarginSummary { ... }
export interface MarginInterestItem { ... }
export interface MarginInterestResponse { ... }
export interface MaintenanceRatioResponse { ... }
export interface MarginCloseRequest { ... }
```

**修改类型**：
- `PortfolioAccountItem` - 新增 `accountType`, `marginInterestRate`, `securitiesInterestRate`, `marginRatio` 字段
- `PortfolioAccountCreateRequest` - 新增对应字段

### 9. `apps/dsa-web/src/api/portfolio.ts` — 前端 API 客户端

**新增方法**：
```typescript
// [新增] 融资融券 API | 2026-05-06
recordMarginTrade(payload: MarginTradeCreateRequest): Promise<PortfolioEventCreatedResponse>
getMarginDetails(params): Promise<MarginDetailListResponse>
getMarginSummary(accountId: number): Promise<MarginSummary>
calculateMarginInterest(params): Promise<MarginInterestResponse>
getMaintenanceRatio(accountId: number): Promise<MaintenanceRatioResponse>
closeMarginDetail(detailId: number, payload: MarginCloseRequest): Promise<{ closed: number }>
```

**修改方法**：
- `createAccount()` - 新增 `accountType`, `marginInterestRate`, `securitiesInterestRate`, `marginRatio` 参数

### 10. `apps/dsa-web/src/pages/PortfolioPage.tsx` — 前端页面

**新增功能**：
- 账户创建表单：新增"账户类型"选择（普通账户/融资融券账户）及融资融券参数输入
- 融资融券交易录入表单：支持融资买入、融券卖出、卖券还款、买券还券
- 融资融券概览说明卡片

**新增状态**：
```typescript
// [新增] 融资融券表单状态 | 2026-05-06
const [marginForm, setMarginForm] = useState({
  symbol: '',
  side: 'margin_buy',
  quantity: '',
  price: '',
  interestRate: '',
  fee: '',
  tax: '',
  note: '',
});
```

**新增处理函数**：
- `handleMarginTradeSubmit()` - 融资融券交易提交

---

## 修改四：券商 CSV 导入支持东吴证券

**修改时间**：2026-05-07

**修改目的**：为券商 CSV 导入功能添加东吴证券支持，包括普通交易和融资融券 CSV 格式

**涉及文件**：

### 1. `src/services/portfolio_import_service.py` — 解析器注册

**新增普通交易解析器**（`DEFAULT_PARSER_SPECS`）：
```diff
+    # [新增] 东吴证券 CSV 解析器 | 2026-05-07
+    CsvParserSpec(
+        broker="dongwu",
+        aliases=("soochow", "dwzq"),
+        display_name="东吴",
+        column_hints={
+            "trade_date": ("成交日期", "发生日期", "日期"),
+            "symbol": ("证券代码", "股票代码", "代码"),
+            "side": ("买卖标志", "买卖方向", "操作", "交易类别"),
+            "quantity": ("成交数量", "数量", "成交股数"),
+            "price": ("成交价格", "成交均价", "成交价", "价格"),
+            "trade_uid": ("成交编号", "委托编号", "合同编号"),
+        },
+    ),
```

**新增融资融券解析器**（`MARGIN_PARSER_SPECS`）：
```diff
+    # [新增] 东吴证券融资融券 CSV 解析器 | 2026-05-07
+    CsvParserSpec(
+        broker="dongwu_margin",
+        aliases=("soochow_margin", "dwzq_margin"),
+        display_name="东吴融资融券",
+        column_hints={
+            "trade_date": ("成交日期", "交易日期", "日期"),
+            "symbol": ("证券代码", "股票代码", "代码"),
+            "side": ("交易类别", "业务类型", "交易类型"),
+            "quantity": ("成交数量", "数量", "成交股数"),
+            "price": ("成交价格", "成交价", "价格"),
+            "interest_rate": ("利率", "年利率", "融资利率", "融券利率"),
+            "fee": ("手续费", "佣金", "交易费"),
+            "interest": ("利息", "融资利息", "融券利息"),
+        },
+    ),
```

### 2. `apps/dsa-web/src/pages/PortfolioPage.tsx` — 前端页面

**FALLBACK_BROKERS 新增东吴**：
```diff
  const FALLBACK_BROKERS: PortfolioImportBrokerItem[] = [
    { broker: 'huatai', aliases: [], displayName: '华泰' },
    { broker: 'citic', aliases: ['zhongxin'], displayName: '中信' },
    { broker: 'cmb', aliases: ['cmbchina', 'zhaoshang'], displayName: '招商' },
+   // [新增] 东吴证券 | 2026-05-07
+   { broker: 'dongwu', aliases: ['soochow', 'dwzq'], displayName: '东吴' },
  ];
```

**formatBrokerLabel 新增东吴标签**：
```diff
  if (value === 'huatai') return 'huatai（华泰）';
  if (value === 'citic') return 'citic（中信）';
  if (value === 'cmb') return 'cmb（招商）';
+ // [新增] 东吴证券标签 | 2026-05-07
+ if (value === 'dongwu') return 'dongwu（东吴）';
```

### 3. `api/v1/endpoints/portfolio.py` — API 端点

**更新 broker 参数描述**：
```diff
-    broker: str = Form(..., description="Broker id: huatai/citic/cmb"),
+    broker: str = Form(..., description="Broker id: huatai/citic/cmb/dongwu"),
```

---

## 修改五：融资利率输入精度修复

**修改时间**：2026-05-07

**修改目的**：修复账户创建表单中融资利率、融券利率、保证金比例输入框无法输入4位小数的问题（如 0.0520、0.0835）

**问题根因**：HTML `<input type="number">` 的 `step` 属性设置为 `"0.01"`，浏览器限制只能输入2位小数

**涉及文件**：

### 1. `apps/dsa-web/src/pages/PortfolioPage.tsx` — 前端页面

**修改输入框 step 属性**：
```diff
  {accountForm.accountType === 'margin' && (
    <>
+     {/* [修复] step 从 0.01 改为 0.0001，支持输入4位小数利率（如 0.0520） | 2026-05-07 */}
      <input
        className={PORTFOLIO_INPUT_CLASS}
        type="number"
-       step="0.01"
+       step="0.0001"
        min="0"
        max="1"
        placeholder="融资年利率（如 0.068 表示 6.8%）"
        ...
      />
      <input
        className={PORTFOLIO_INPUT_CLASS}
        type="number"
-       step="0.01"
+       step="0.0001"
        min="0"
        max="1"
        placeholder="融券年利率（如 0.08 表示 8%）"
        ...
      />
      <input
        className={PORTFOLIO_INPUT_CLASS}
        type="number"
-       step="0.01"
+       step="0.0001"
        min="0"
        max="1"
        placeholder="保证金比例（如 0.5 表示 50%）"
        ...
      />
```

---

## 修改六：融资融券交易录入方法调用修复

**修改时间**：2026-05-07

**修改目的**：修复融资买入提交时报错 `'PortfolioRepository' object has no attribute 'record_trade'` 和 `Unsupported trade side: margin_buy`

**问题根因**：
1. `portfolio_service.py` 的 `record_margin_trade()` 调用了不存在的 `self.repo.record_trade()`，仓库实际方法名为 `add_trade()`
2. 融资融券方向（如 `margin_buy`）直接传入交易表，但交易表只支持 `buy`/`sell`

**涉及文件**：

### 1. `src/services/portfolio_service.py` — 服务层

**修改方法调用、方向映射和返回值**：
```diff
+        # [修复] 融资融券方向映射为交易表标准方向 | 2026-05-07
+        trade_side = 'buy' if side_norm in ('margin_buy', 'short_cover') else 'sell'
-        trade = self.repo.record_trade(
+        trade = self.repo.add_trade(
             account_id=account_id,
+            trade_uid=None,
             symbol=symbol_norm,
             trade_date=date.today(),
-            side=side_norm,
+            side=trade_side,
             ...
         )
         margin_detail = self.repo.insert_margin_detail(
             account_id=account_id,
-            trade_id=trade['id'],
+            trade_id=trade.id,
             ...
         )
         return {
-            'trade': trade,
+            'trade': {'id': trade.id},
             'margin_detail': self._margin_detail_to_dict(margin_detail),
         }
```

**方向映射规则**：
- `margin_buy`（融资买入）→ `buy`
- `short_sell`（融券卖出）→ `sell`
- `margin_repay`（卖券还款）→ `sell`
- `short_cover`（买券还券）→ `buy`

---

## 修改汇总

| 序号 | 文件 | 修改类型 | 日期 |
|------|------|----------|------|
| 1 | `src/config.py:599-600` | 新增字段 | 2026-05-04 |
| 2 | `src/config.py:1320-1321` | 新增环境变量读取 | 2026-05-04 |
| 3 | `data_provider/tushare_fetcher.py:181-188` | 修改逻辑 | 2026-05-04 |
| 4 | `.env.example:25-26` | 新增配置模板 | 2026-05-04 |
| 5 | `.env:70-71` | 新增配置项 | 2026-05-04 |
| 6 | `src/storage.py` | 新增表和字段 | 2026-05-06 |
| 7 | `src/repositories/portfolio_repo.py` | 新增方法 | 2026-05-06 |
| 8 | `src/services/portfolio_service.py` | 新增方法 | 2026-05-06 |
| 9 | `api/v1/endpoints/portfolio.py` | 新增端点 | 2026-05-06 |
| 10 | `api/v1/schemas/portfolio.py` | 新增 Schema | 2026-05-06 |
| 11 | `src/services/portfolio_risk_service.py` | 新增方法 | 2026-05-06 |
| 12 | `src/services/portfolio_import_service.py` | 新增解析器和方法 | 2026-05-06 |
| 13 | `apps/dsa-web/src/types/portfolio.ts` | 新增类型 | 2026-05-06 |
| 14 | `apps/dsa-web/src/api/portfolio.ts` | 新增方法 | 2026-05-06 |
| 15 | `apps/dsa-web/src/pages/PortfolioPage.tsx` | 新增 UI 组件 | 2026-05-06 |
| 16 | `src/services/portfolio_import_service.py` | 新增东吴证券解析器 | 2026-05-07 |
| 17 | `apps/dsa-web/src/pages/PortfolioPage.tsx` | 新增东吴证券前端支持 | 2026-05-07 |
| 18 | `api/v1/endpoints/portfolio.py` | 更新 broker 参数描述 | 2026-05-07 |
| 19 | `apps/dsa-web/src/pages/PortfolioPage.tsx` | 修复利率输入精度 | 2026-05-07 |
| 20 | `src/services/portfolio_service.py` | 修复融资融券交易方法调用 | 2026-05-07 |

---

## 修改七：LLM 模型名称修复（.env）

**修改时间**：2026-05-08

**修改目的**：修复多策略分析报错 `deepseek-v4-pro[1m]` 模型名无效

**问题根因**：`.env` 中 `LLM_DEEPSEEK_MODELS` 和 `LITELLM_MODEL` 的值包含了终端转义字符 `[1m]`（ANSI 粗体标记），导致传给 DeepSeek API 的模型名为 `deepseek-v4-pro[1m]` 而非 `deepseek-v4-pro`

**涉及文件**：

### 1. `.env` — 环境变量（不纳入 git）

```diff
-LLM_DEEPSEEK_MODELS=deepseek-v4-pro[1m]
-LITELLM_MODEL=deepseek/deepseek-v4-pro[1m]
+LLM_DEEPSEEK_MODELS=deepseek-v4-pro
+LITELLM_MODEL=deepseek/deepseek-v4-pro
```

> `.env` 文件不纳入 git 跟踪，拉取上游更新时不会冲突。
> 其他修改文件需在 git pull 后检查是否有冲突。
