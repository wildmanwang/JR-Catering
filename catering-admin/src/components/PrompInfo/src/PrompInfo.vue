<script setup lang="ts">
import { computed, ref } from 'vue'
import { useAppStore } from '@/store/modules/app'
import { useI18n } from '@/hooks/web/useI18n'

type InfoType = 'info' | 'warn' | 'error'

interface InfoDisplay {
  type: InfoType
  message: string
}

const infoDisplay = ref<InfoDisplay | null>(null)

const appStore = useAppStore()
const { t } = useI18n()

const backgroundColor = computed(() => {
  return appStore.getIsDark ? '#000' : '#f5f7fa'
})

const displayText = computed(() => {
  if (infoDisplay.value?.message) {
    return infoDisplay.value.message
  }
  return t('common.ready')
})

const infoType = computed(() => {
  if (infoDisplay.value === null) {
    return 'ready' as const
  }
  return infoDisplay.value.type || null
})

const info = (msg: string) => {
  infoDisplay.value = { type: 'info', message: msg }
}

const warn = (msg: string) => {
  infoDisplay.value = { type: 'warn', message: msg }
}

const err = (msg: string) => {
  infoDisplay.value = { type: 'error', message: msg }
}

const ready = () => {
  infoDisplay.value = null
}

defineExpose({
  info,
  warn,
  err,
  ready
})
</script>

<template>
  <div
    :class="['promp-info', infoType ? `promp-info-${infoType}` : 'promp-info-empty']"
    :style="{ backgroundColor }"
  >
    {{ displayText }}
  </div>
</template>

<style scoped>
.promp-info {
  width: 100%;
  height: 32px;
  line-height: 32px;
  padding: 0 20px;
  display: flex;
  align-items: center;
  font-size: 14px;
  font-weight: 400;
  text-align: left;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  border-radius: 0;
  box-sizing: border-box;
}

.promp-info-empty {
  color: transparent;
}

.promp-info-ready {
  color: #6b7280;
}

.promp-info-info {
  color: #6b7280;
}

.promp-info-warn {
  color: #f59e0b;
}

.promp-info-error {
  color: #ef4444;
}
</style>

