import router from '@/router'
import type { RouteLocationNormalizedLoaded } from 'vue-router'
import { getRawRoute } from '@/utils/routerHelper'
import { defineStore } from 'pinia'
import { store } from '../index'
import { findIndex } from '@/utils'
import { useAuthStoreWithOut } from './auth'

export interface TagsViewState {
  visitedViews: RouteLocationNormalizedLoaded[]
  cachedViews: Set<string>
  selectedTag?: RouteLocationNormalizedLoaded
  /** 页面状态数据映射，key 为 fullPath，value 为页面状态数据 */
  pageStates: Map<string, any>
}

export const useTagsViewStore = defineStore('tagsView', {
  state: (): TagsViewState => ({
    visitedViews: [],
    cachedViews: new Set(),
    selectedTag: undefined,
    pageStates: new Map()
  }),
  getters: {
    getVisitedViews(): RouteLocationNormalizedLoaded[] {
      return this.visitedViews
    },
    getCachedViews(): string[] {
      return Array.from(this.cachedViews)
    },
    getSelectedTag(): RouteLocationNormalizedLoaded | undefined {
      return this.selectedTag
    }
  },
  actions: {
    // 新增缓存和tag
    addView(view: RouteLocationNormalizedLoaded): void {
      this.addVisitedView(view)
      this.addCachedView()
    },
    // 新增tag
    addVisitedView(view: RouteLocationNormalizedLoaded) {
      if (this.visitedViews.some((v) => v.path === view.path)) return
      if (view.meta?.noTagsView) return
      this.visitedViews.push(
        Object.assign({}, view, {
          title: view.meta?.title || 'no-name'
        })
      )
      // 自动从 sessionStorage 恢复页面状态（页面刷新场景）
      this.restorePageStateFromStorage(view.fullPath)
    },
    // 新增缓存
    addCachedView() {
      const cacheMap: Set<string> = new Set()
      for (const v of this.visitedViews) {
        const item = getRawRoute(v)
        const needCache = !item?.meta?.noCache
        if (!needCache) {
          continue
        }
        const name = item.name as string
        cacheMap.add(name)
      }
      if (Array.from(this.cachedViews).sort().toString() === Array.from(cacheMap).sort().toString())
        return
      this.cachedViews = cacheMap
    },
    // 删除某个
    delView(view: RouteLocationNormalizedLoaded) {
      this.delVisitedView(view)
      this.addCachedView()
    },
    // 删除tag
    delVisitedView(view: RouteLocationNormalizedLoaded) {
      for (const [i, v] of this.visitedViews.entries()) {
        if (v.path === view.path) {
          this.visitedViews.splice(i, 1)
          // 自动清理对应的页面状态（内存）
          this.pageStates.delete(v.fullPath)
          // 同时清理 sessionStorage 中的状态
          try {
            const stateKey = `BASE_GRID_PAGE_STATE_${v.fullPath}`
            const importStateKey = `IMPORT_GRID_STATE_${v.fullPath}`
            sessionStorage.removeItem(stateKey)
            sessionStorage.removeItem(importStateKey)
          } catch (err) {
            console.error('清理 sessionStorage 状态失败:', err)
          }
          break
        }
      }
    },
    // 删除缓存
    delCachedView() {
      const route = router.currentRoute.value
      const index = findIndex<string>(this.getCachedViews, (v) => v === route.name)
      if (index > -1) {
        this.cachedViews.delete(this.getCachedViews[index])
      }
    },
    // 删除所有缓存和tag
    delAllViews() {
      this.delAllVisitedViews()
      this.addCachedView()
    },
    // 删除所有tag
    delAllVisitedViews() {
      const authStore = useAuthStoreWithOut()
      // 清理非固定标签的状态
      this.visitedViews.forEach((v) => {
        if (!v?.meta?.affix) {
          this.pageStates.delete(v.fullPath)
        }
      })
      this.visitedViews = authStore.getUser
        ? this.visitedViews.filter((tag) => tag?.meta?.affix)
        : []
    },
    // 删除其它
    delOthersViews(view: RouteLocationNormalizedLoaded) {
      this.delOthersVisitedViews(view)
      this.addCachedView()
    },
    // 删除其它tag
    delOthersVisitedViews(view: RouteLocationNormalizedLoaded) {
      // 清理被删除的标签的状态
      this.visitedViews.forEach((v) => {
        if (!v?.meta?.affix && v.path !== view.path) {
          this.pageStates.delete(v.fullPath)
        }
      })
      this.visitedViews = this.visitedViews.filter((v) => {
        return v?.meta?.affix || v.path === view.path
      })
    },
    // 删除左侧
    delLeftViews(view: RouteLocationNormalizedLoaded) {
      const index = findIndex<RouteLocationNormalizedLoaded>(
        this.visitedViews,
        (v) => v.path === view.path
      )
      if (index > -1) {
        // 清理被删除的标签的状态
        this.visitedViews.forEach((v, i) => {
          if (!v?.meta?.affix && v.path !== view.path && i <= index) {
            this.pageStates.delete(v.fullPath)
          }
        })
        this.visitedViews = this.visitedViews.filter((v, i) => {
          return v?.meta?.affix || v.path === view.path || i > index
        })
        this.addCachedView()
      }
    },
    // 删除右侧
    delRightViews(view: RouteLocationNormalizedLoaded) {
      const index = findIndex<RouteLocationNormalizedLoaded>(
        this.visitedViews,
        (v) => v.path === view.path
      )
      if (index > -1) {
        // 清理被删除的标签的状态
        this.visitedViews.forEach((v, i) => {
          if (!v?.meta?.affix && v.path !== view.path && i >= index) {
            this.pageStates.delete(v.fullPath)
          }
        })
        this.visitedViews = this.visitedViews.filter((v, i) => {
          return v?.meta?.affix || v.path === view.path || i < index
        })
        this.addCachedView()
      }
    },
    updateVisitedView(view: RouteLocationNormalizedLoaded) {
      for (let v of this.visitedViews) {
        if (v.path === view.path) {
          v = Object.assign(v, view)
          break
        }
      }
    },
    // 设置当前选中的tag
    setSelectedTag(tag: RouteLocationNormalizedLoaded) {
      this.selectedTag = tag
    },
    setTitle(title: string, path?: string) {
      for (const v of this.visitedViews) {
        if (v.path === (path ?? this.selectedTag?.path)) {
          v.meta.title = title
          break
        }
      }
    },
    /**
     * 保存页面状态
     * @param fullPath - 路由的完整路径（包含 query 参数）
     * @param state - 页面状态数据
     */
    setPageState(fullPath: string, state: any) {
      this.pageStates.set(fullPath, state)
    },
    /**
     * 获取页面状态
     * @param fullPath - 路由的完整路径（包含 query 参数）
     * @returns 页面状态数据，如果不存在则返回 null
     */
    getPageState(fullPath: string): any | null {
      return this.pageStates.get(fullPath) || null
    },
    /**
     * 清除页面状态
     * @param fullPath - 路由的完整路径（包含 query 参数）
     */
    clearPageState(fullPath: string) {
      this.pageStates.delete(fullPath)
    },
    /**
     * 从 sessionStorage 恢复页面状态（页面刷新场景）
     * 支持多种状态 key 前缀，自动检测并恢复
     * @param fullPath - 路由的完整路径（包含 query 参数）
     * @param stateKeyPrefixes - 状态 key 前缀数组，默认为 ['BASE_GRID_PAGE_STATE_', 'IMPORT_GRID_STATE_']
     */
    restorePageStateFromStorage(
      fullPath: string,
      stateKeyPrefixes: string[] = ['BASE_GRID_PAGE_STATE_', 'IMPORT_GRID_STATE_']
    ) {
      // 如果 pageStates 中已有，说明不是刷新场景，不需要恢复
      if (this.pageStates.has(fullPath)) return

      // 尝试从 sessionStorage 恢复（按优先级顺序尝试各个前缀）
      // 注意：只恢复第一个找到的状态，避免错误恢复其他组件的状态
      for (const prefix of stateKeyPrefixes) {
        try {
          const storageKey = `${prefix}${fullPath}`
          const storedState = sessionStorage.getItem(storageKey)
          if (storedState) {
            const state = JSON.parse(storedState)
            // 验证状态格式：BaseGrid 的状态应该包含 formDisplayParams 或 executedSearchParams
            // ImportGrid 的状态应该包含 dataList
            // 根据前缀判断应该是什么格式
            const isBaseGridPrefix = prefix === 'BASE_GRID_PAGE_STATE_'
            const isImportGridPrefix = prefix === 'IMPORT_GRID_STATE_'
            
            if (isBaseGridPrefix) {
              // BaseGrid 状态应该包含 formDisplayParams 或 executedSearchParams
              const isValid = state.formDisplayParams !== undefined || 
                             state.executedSearchParams !== undefined || 
                             state.currentPage !== undefined ||
                             state.pageSize !== undefined
              if (!isValid) {
                console.warn(`tagsViewStore: BaseGrid 状态格式不正确，跳过恢复`, { fullPath, prefix, state })
                continue
              }
            } else if (isImportGridPrefix) {
              // ImportGrid 状态应该包含 dataList
              const isValid = state.dataList !== undefined
              if (!isValid) {
                console.warn(`tagsViewStore: ImportGrid 状态格式不正确，跳过恢复`, { fullPath, prefix, state })
                continue
              }
            }
            
            this.pageStates.set(fullPath, state)
            console.log(`tagsViewStore: 从 sessionStorage 恢复页面状态`, { fullPath, prefix, storageKey })
            return
          }
        } catch (err) {
          console.error(`从 sessionStorage 恢复页面状态失败 (${prefix}):`, err)
        }
      }
    }
  },
  persist: false
})

export const useTagsViewStoreWithOut = () => {
  return useTagsViewStore(store)
}
