# 在线商城

基于 FastAPI、PostgreSQL、Redis 和 Vue 3 的全栈商城。买家可以浏览商品、加入购物车、结算、模拟付款并确认收货。发货员工在工作台登记承运商和物流单号。在线客服可以查询商品、本人订单和平台规则。

## 本地启动

将 `backend/.env.example` 复制为 `backend/.env`，设置随机的 `JWT_SECRET_KEY`。然后在仓库根目录运行：

```sh
docker compose --profile app up -d --build --wait
docker compose exec api python -m app.scripts.seed --catalog-only
```

商城地址为 `http://localhost:5173`，API 文档为 `http://localhost:8000/docs`。`--catalog-only` 为首次演示导入商品、分类和图片数据，已有商品时会跳过。浏览、型号与关键词搜索、结算和履约均可在未配置模型密钥时演示。

如需在空库中演示向量搜索和客服，先配置 `SILICONFLOW_API_KEY` 和 `DEEPSEEK_API_KEY`，再用 `python -m app.scripts.seed` 代替上面的 `--catalog-only` 命令。完整种子脚本会重置演示数据，请在空库中运行。

## 演示一笔订单

1. 注册两个本地账号，分别作为买家和发货员工。用数据库管理权限为已注册的员工账号开启发货权限，下面以 `demo_staff` 为例。

   ```sh
   docker compose exec postgres psql -U shopping -d shopping -c "UPDATE users SET can_ship_orders = TRUE WHERE username = 'demo_staff';"
   ```

2. 买家登录后浏览商品，加入购物车，填写地址，提交订单并模拟付款。
3. 员工重新登录，在「发货工作台」找到待发货订单，填写承运商和物流单号。
4. 买家刷新「我的订单」，查看物流单号并确认收货。订单进入「交易完成」。配置了模型的环境也可以从「在线客服」查询这笔订单。

付款为模拟操作，订单页显示员工登记的物流信息。

## 后端设计

- **结算**。在同一 PostgreSQL 事务里保存幂等键和订单、扣减库存、清理购物车。按商品 ID 顺序处理购物车条目和库存行。不同幂等键并发提交同一购物车条目时，只有一个请求能结算。
- **履约**。发货接口读取数据库里的员工权限。订单当前状态是 `UPDATE` 的条件之一，重复或并发发货只能成功一次。买家确认收货还必须满足订单归属。未付款订单由 APScheduler 扫描关闭，Redis 锁协调多个实例，订单状态和库存回补在数据库事务里更新。
- **检索**。商品目录由后端分页、分类和排序。搜索支持结构化型号、全文、模糊与可选的向量召回，通过 RRF 合并候选并优先展示完整型号命中。
- **客服**。Agent 使用商城查询服务获取实时商品和本人订单数据，通过 SSE 向页面返回带业务引用的回答。会话摘要和字符预算管理历史上下文，用户偏好由后端校验，回答按工具证据检查平台规则断言。

在配置好 PostgreSQL、Redis 和商品数据的独立测试环境中，进入 `backend` 运行 `python -m pytest tests/test_order_flow.py`，可复现库存竞争、重复请求、事务回滚和发货权限等场景。

[客服评测目录](backend/eval/README.md)包含用例集、上下文标定和历史回归记录。
