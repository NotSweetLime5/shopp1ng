<script setup>
import { RouterLink, RouterView, useRouter } from 'vue-router'
import { useAuth } from './store'

const auth = useAuth()
const router = useRouter()

function logout() {
  auth.logout()
  router.replace('/search')
}
</script>

<template>
  <header class="bar">
    <div class="brand">
      <span class="dot" />
      在线商城
    </div>
    <nav>
      <RouterLink to="/search">逛商城</RouterLink>
      <RouterLink to="/cart">购物车</RouterLink>
      <RouterLink to="/orders">我的订单</RouterLink>
      <RouterLink v-if="auth.user?.can_ship_orders" to="/fulfillment">发货工作台</RouterLink>
      <RouterLink to="/chat">在线客服</RouterLink>
    </nav>
    <div class="who">
      <template v-if="auth.logged">
        <span>{{ auth.user.nick_name || auth.user.username }}</span>
        <button class="ghost" @click="logout">退出</button>
      </template>
      <RouterLink v-else to="/login" class="login-link">登录 / 注册</RouterLink>
    </div>
  </header>

  <main class="page">
    <RouterView />
  </main>
</template>
