<script setup>
defineProps({ eyebrow: String, title: String, description: String })
</script>

<template>
  <header class="page-heading">
    <p>{{ eyebrow }}</p>
    <h1>{{ title }}</h1>
    <span>{{ description }}</span>
  </header>
</template>

<style scoped>
.page-heading { margin-bottom: 30px; }
.page-heading p { margin: 0 0 10px; color: var(--primary); font-size: 12px; font-weight: 800; letter-spacing: .14em; text-transform: uppercase; }
.page-heading h1 { margin: 0 0 12px; color: var(--text); font-size: clamp(28px, 4vw, 42px); letter-spacing: -.04em; }
.page-heading span { color: var(--muted); line-height: 1.7; }
</style>

