<script setup>
import { ref } from 'vue'
import { ApiError, api } from '../api'

const queue = ref(null)
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const notice = ref('')
const editing = ref(null)
const carrier = ref('')
const trackingNo = ref('')

async function load(page = 1) {
  loading.value = true
  error.value = ''
  try {
    let result = await api.pendingShipments(page)
    const lastPage = Math.max(1, Math.ceil(result.total / result.size))
    if (page > lastPage) result = await api.pendingShipments(lastPage)
    queue.value = result
  } catch (e) {
    queue.value = null
    error.value = e instanceof ApiError ? e.message : '待发货订单加载失败'
  } finally {
    loading.value = false
  }
}

function edit(id) {
  editing.value = id
  carrier.value = ''
  trackingNo.value = ''
}

async function ship(order) {
  if (saving.value || !carrier.value.trim() || !trackingNo.value.trim()) return
  saving.value = true
  error.value = ''
  notice.value = ''
  try {
    await api.shipOrder(order.id, { carrier: carrier.value.trim(), tracking_no: trackingNo.value.trim() })
    notice.value = `订单 ${order.order_no} 已登记发货。`
    editing.value = null
    await load(queue.value?.page)
  } catch (e) {
    if (e instanceof ApiError && e.code === 409) {
      editing.value = null
      await load(queue.value?.page)
    }
    error.value = e instanceof ApiError ? e.message : '发货提交失败'
  } finally {
    saving.value = false
  }
}

load()
</script>

<template>
  <section class="card">
    <div class="row header">
      <h2>发货工作台</h2>
      <button class="ghost" :disabled="loading || saving" @click="load(queue?.page)">刷新</button>
    </div>
    <p class="muted">核对收件信息后登记承运商和物流单号。</p>
    <p v-if="notice" role="status">{{ notice }}</p>
    <p v-if="error" class="err" role="alert">{{ error }}</p>
    <p v-if="loading" class="muted">加载中…</p>
    <p v-else-if="queue && !queue.items.length" class="muted">暂无待发货订单。</p>
    <template v-else-if="queue">
      <article v-for="order in queue.items" :key="order.id" class="order">
        <div class="row header">
          <strong>订单 {{ order.order_no }}</strong>
          <button class="ghost" :disabled="saving" @click="edit(order.id)">登记发货</button>
        </div>
        <p class="muted">{{ order.receiver_name }} {{ order.receiver_phone }} · {{ order.receiver_address }}</p>
        <form v-if="editing === order.id" class="row" @submit.prevent="ship(order)">
          <label>承运商 <input v-model="carrier" required maxlength="60" :disabled="saving" /></label>
          <label>物流单号 <input v-model="trackingNo" required maxlength="64" :disabled="saving" /></label>
          <button class="primary" :disabled="saving">{{ saving ? '提交中…' : '确认发货' }}</button>
          <button type="button" class="ghost" :disabled="saving" @click="editing = null">取消</button>
        </form>
      </article>
      <div v-if="queue.total > queue.size" class="row pagination">
        <button class="ghost" :disabled="saving || queue.page <= 1" @click="load(queue.page - 1)">上一页</button>
        <span>第 {{ queue.page }} / {{ Math.ceil(queue.total / queue.size) }} 页</span>
        <button class="ghost" :disabled="saving || queue.page * queue.size >= queue.total" @click="load(queue.page + 1)">下一页</button>
      </div>
    </template>
  </section>
</template>

<style scoped>
h2 { margin: 0; }
.row { display: flex; flex-wrap: wrap; align-items: center; gap: 8px 12px; }
.header { justify-content: space-between; }
.order { border-top: 1px solid var(--line); padding: 12px 0; }
.order p { margin: 5px 0 8px; overflow-wrap: anywhere; }
.pagination { justify-content: center; }
input { width: 150px; }
</style>
