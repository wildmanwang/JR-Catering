<script setup lang="ts">
import { ElSkeleton, ElCard, ElDivider, ElLink } from 'element-plus'
import { useI18n } from '@/hooks/web/useI18n'
import { ref, reactive, computed } from 'vue'
import { getGreeting, getCurrentDate, getDayOfWeek } from '@/utils'
import { Highlight } from '@/components/Highlight'
import avatar from '@/assets/imgs/avatar.jpg'
import { useAuthStore } from '@/store/modules/auth'
import { useRouter } from 'vue-router'
import { ButtonPre } from '@/components/ButtonPre'

defineOptions({
  name: 'DashboardWorkplace'
})

const authStore = useAuthStore()
const router = useRouter()

const loading = ref(true)

type ShortcutItem = {
  name: string
  path: string
}

const shortcuts = reactive<ShortcutItem[]>([
  {
    name: '用户管理',
    path: '/system/user'
  }
])

const handleShortcutClick = (item: ShortcutItem) => {
  router.push(item.path)
}

// 获取动态 - 已清空，不再获取数据
let dynamics = reactive<any[]>([])

const getAllApi = async () => {
  // 不再获取动态数据
  loading.value = false
}

getAllApi()

const { t } = useI18n()

const user = computed(() => authStore.getUser)
</script>

<template>
  <div class="bg-[var(--app-content-bg-color)] flex-grow workplace-page">
    <div class="workplace-header">
      <ElCard shadow="never" class="workplace-header-card">
        <ElSkeleton :loading="loading" animated>
          <div class="workplace-header-content">
            <div class="workplace-header-greeting">
              <img
                :src="user.avatar ? user.avatar : avatar"
                alt=""
                class="w-70px h-70px rounded-[50%] mr-20px"
              />
              <div>
                <div class="text-20px">
                  {{ getGreeting() }}，{{ user.name }}，{{ t('workplace.happyDay') }}
                </div>
                <div class="mt-10px text-14px text-gray-500">
                  {{ getCurrentDate() }}，{{ getDayOfWeek() }}
                </div>
              </div>
            </div>
            <div class="workplace-header-login">
              <div class="text-14px text-gray-400">最近登录时间</div>
              <span class="text-20px">{{ user.last_login?.split(' ')[0] }}</span>
            </div>
          </div>
        </ElSkeleton>
      </ElCard>
    </div>

    <div class="mx-20px mb-20px workplace-content">
      <div class="workplace-grid">
        <div class="workplace-dynamic">
          <ElCard shadow="never" class="dynamic-card">
            <template #header>
              <div class="flex justify-between">
                <span>{{ t('workplace.dynamic') }}</span>
                <ElLink type="primary" :underline="false">{{ t('workplace.more') }}</ElLink>
              </div>
            </template>
            <ElSkeleton :loading="loading" animated>
              <div v-if="dynamics.length > 0">
                <div v-for="(item, index) in dynamics" :key="`dynamics-${index}`">
                  <div class="flex items-center">
                    <img
                      src="@/assets/imgs/avatar.jpg"
                      alt=""
                      class="w-35px h-35px rounded-[50%] mr-20px"
                    />
                    <div>
                      <div class="text-14px">
                        <Highlight :keys="item.keys.map((v) => t(v))">
                          {{ t('workplace.pushCode') }}
                        </Highlight>
                      </div>
                      <div class="mt-15px text-12px text-gray-400">
                        {{ useTimeAgo(item.time) }}
                      </div>
                    </div>
                  </div>
                  <ElDivider />
                </div>
              </div>
              <div v-else class="dynamic-empty">暂无动态</div>
            </ElSkeleton>
          </ElCard>
        </div>
        <div class="workplace-shortcut">
          <ElCard shadow="never" class="shortcut-card">
            <template #header>
              <span>{{ t('workplace.shortcutOperation') }}</span>
            </template>
            <ElSkeleton :loading="loading" animated>
              <div class="shortcut-grid">
                <ElLink
                  v-for="item in shortcuts"
                  :key="item.name"
                  type="primary"
                  :underline="false"
                  class="shortcut-link"
                  @click="handleShortcutClick(item)"
                >
                  {{ item.name }}
                </ElLink>
              </div>
            </ElSkeleton>
          </ElCard>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.workplace-page {
  --workplace-gap: 20px;
  display: flex;
  flex-direction: column;
  height: 100%;
  max-height: 100%;
  overflow: hidden;
}

.workplace-header {
  flex-shrink: 0;
  margin: 0 0 20px 0;
}

.workplace-header-card {
  height: auto;
}

.workplace-header :deep(.el-card__body) {
  padding: 20px;
  min-height: 70px;
  display: flex;
  align-items: flex-end;
}

.workplace-header-content {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  width: 100%;
}

.workplace-header-greeting {
  display: flex;
  align-items: center;
  flex: 1;
  min-width: 0;
}

.workplace-header-login {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  flex-shrink: 0;
  text-align: right;
  margin-left: auto;
  margin-right: 20px;
}

.workplace-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.workplace-grid {
  display: flex;
  flex-wrap: wrap;
  gap: var(--workplace-gap);
  flex: 1;
  min-height: 0;
  align-items: stretch;
}

.workplace-dynamic {
  flex: 1 1 0;
  min-width: 280px;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.dynamic-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.dynamic-card :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: auto;
}

.dynamic-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.workplace-shortcut {
  flex: 0 0 320px;
  margin-left: auto;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.shortcut-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.shortcut-card :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.shortcut-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex: 1;
  justify-content: flex-start;
}

.shortcut-link {
  text-align: left;
  padding-left: 30%;
  font-size: 15px;
}

@media (max-width: 992px) {
  .workplace-grid {
    flex-direction: column;
  }

  .workplace-shortcut {
    margin-left: 0;
    flex: 1 1 auto;
  }

  .shortcut-link {
    padding-left: 0;
  }
}
</style>
