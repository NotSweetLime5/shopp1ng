<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ApiError, api } from '../api'

const router = useRouter()
const q = ref('')
const loading = ref(false)
const error = ref('')
const result = ref(null)
const semantic = ref(false)
const categories = ref([])
const category = ref(null)
const sort = ref('default')
const catalog = ref(null)
const catalogLoading = ref(false)
const catalogError = ref('')
const visible = computed(() => result.value ?? catalog.value)

async function browse(page = 1) {
  catalogLoading.value = true
  catalogError.value = ''
  try {
    catalog.value = await api.goods({ page, size: 12, sort: sort.value, category_id: category.value })
  } catch (e) {
    catalogError.value = e instanceof ApiError ? e.message : '商品列表加载失败'
    catalog.value = null
  } finally {
    catalogLoading.value = false
  }
}

async function loadCategories() {
  try {
    categories.value = await api.categories()
  } catch {
    // 分类加载失败时仍可浏览全部商品和使用搜索。
  }
}

async function run() {
  const term = q.value.trim()
  if (!term || loading.value) return
  loading.value = true
  error.value = ''
  try {
    result.value = await api.search(term, { semantic: semantic.value ? 'true' : 'false', limit: 20 })
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : '请求失败'
    result.value = null
  } finally {
    loading.value = false
  }
}

function clearSearch() {
  q.value = ''
  result.value = null
  error.value = ''
}

browse()
loadCategories()
</script>

<template>
  <section class="card">
    <h2 style="margin: 0 0 4px">逛商城</h2>
    <p class="muted" style="margin: 0 0 16px">
      按分类浏览，或搜索商品名称和完整型号
    </p>

    <div class="row">
      <input
        v-model="q"
        aria-label="搜索商品"
        placeholder="例如 Mate60Pro、降噪耳机"
        style="flex: 1; min-width: min(240px, 100%)"
        @keyup.enter="run"
      />
      <button class="primary" :disabled="loading || !q.trim()" @click="run">
        {{ loading ? '搜索中…' : '搜索' }}
      </button>
      <button v-if="result || error" class="ghost" :disabled="loading" @click="clearSearch">清除搜索</button>
      <label class="switch">
        <input v-model="semantic" type="checkbox" />
        按需求搜索
      </label>
    </div>
    <p v-if="error" class="err">{{ error }}</p>
  </section>

  <section class="card" style="margin-top: 16px">
    <div v-if="!result" class="row browse-controls">
      <label>分类
        <select v-model="category" :disabled="catalogLoading" @change="browse()">
          <option :value="null">全部分类</option>
          <option v-for="item in categories" :key="item.id" :value="item.id">{{ item.name }}</option>
        </select>
      </label>
      <label>排序
        <select v-model="sort" :disabled="catalogLoading" @change="browse()">
          <option value="default">默认排序</option>
          <option value="newest">最新上架</option>
          <option value="price_asc">价格从低到高</option>
          <option value="price_desc">价格从高到低</option>
        </select>
      </label>
      <span v-if="catalog" class="muted">共 {{ catalog.total }} 件商品</span>
    </div>
    <p v-else class="muted">找到 {{ result.total }} 件商品</p>

    <p v-if="!result && catalogLoading" class="muted" role="status">商品加载中…</p>
    <div v-else-if="!result && catalogError" class="row" role="alert">
      <span class="err">{{ catalogError }}</span>
      <button class="ghost" @click="browse()">重试</button>
    </div>
    <p v-else-if="!visible?.items.length" class="muted">暂无符合条件的商品。</p>

    <ul v-else class="list">
      <li v-for="it in visible.items" :key="it.id">
        <RouterLink :to="`/goods/${it.id}`" class="thumblink">
          <img v-if="it.header_pic" :src="it.header_pic" :alt="it.goods_name" class="thumb" />
          <div v-else class="thumb">{{ it.goods_name.slice(0, 2) }}</div>
        </RouterLink>
        <div class="info">
          <div class="name">
            <RouterLink :to="`/goods/${it.id}`">{{ it.goods_name }}</RouterLink>
            <span v-if="!it.is_marketable" class="tag">已下架</span>
          </div>
          <div class="cap muted">{{ it.caption }}</div>
          <div v-if="it.model_name" class="cap muted">型号：{{ it.model_name }}</div>
          <span v-if="it.matched_by?.includes('model_exact')" class="tag">型号精确匹配</span>
        </div>
        <div class="right">
          <div class="price">¥{{ it.price }}</div>
          <div class="muted small">{{ it.stock > 0 ? '有货' : '缺货' }}</div>
          <button class="ghost" @click="router.push(`/goods/${it.id}`)">详情</button>
        </div>
      </li>
    </ul>
    <div v-if="!result && catalog && catalog.total > catalog.size" class="row pagination">
      <button class="ghost" :disabled="catalogLoading || catalog.page <= 1" @click="browse(catalog.page - 1)">上一页</button>
      <span>第 {{ catalog.page }} / {{ Math.ceil(catalog.total / catalog.size) }} 页</span>
      <button class="ghost" :disabled="catalogLoading || catalog.page * catalog.size >= catalog.total" @click="browse(catalog.page + 1)">下一页</button>
    </div>

  </section>
</template>

<style scoped>
.row {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}
.switch {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--muted);
  user-select: none;
}
.browse-controls { margin-bottom: 12px; }
.pagination { justify-content: center; margin-top: 12px; }
.list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.list li {
  display: flex;
  gap: 14px;
  align-items: center;
  padding: 14px 0;
  border-top: 1px solid var(--line);
}
.thumb {
  width: 46px;
  height: 46px;
  border-radius: 8px;
  background: linear-gradient(135deg, #dbeafe, #e0e7ff);
  color: #3730a3;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  object-fit: cover;
}
.info {
  flex: 1;
  min-width: 0;
}
.name {
  font-weight: 600;
}
.name a {
  color: inherit;
  text-decoration: none;
}
.name a:hover {
  color: var(--brand);
}
.thumblink {
  flex-shrink: 0;
}
.cap {
  font-size: 12px;
  margin: 2px 0 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.right {
  text-align: right;
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: flex-end;
}
.price {
  font-weight: 700;
  color: #b91c1c;
}
.small {
  font-size: 12px;
}
</style>
