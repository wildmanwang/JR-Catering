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
  /** 页签关闭前检查函数映射，key 为 fullPath，value 为检查函数，返回 Promise<boolean>，true 表示允许关闭，false 表示阻止关闭 */
  beforeCloseHandlers: Map<string, () => Promise<boolean>>
}

const VISITED_VIEWS_STORAGE_KEY = 'TAGS_VIEW_VISITED_VIEWS'

export const useTagsViewStore = defineStore('tagsView', {
  state: (): TagsViewState => ({
    visitedViews: [],
    cachedViews: new Set(),
    selectedTag: undefined,
    pageStates: new Map(),
    beforeCloseHandlers: new Map()
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
    /**
     * 新增访问视图（同时添加标签和缓存）
     * @param view - 路由视图对象
     */
    addView(view: RouteLocationNormalizedLoaded): void {
      this.addVisitedView(view)
      this.addCachedView()
    },
    /**
     * 新增访问标签
     * @param view - 路由视图对象
     */
    addVisitedView(view: RouteLocationNormalizedLoaded) {
      if (this.visitedViews.some((v) => v.path === view.path)) return
      if (view.meta?.noTagsView) return
      
      // 如果是刷新后首次添加标签，尝试从 sessionStorage 恢复 visitedViews
      if (this.visitedViews.length === 0) {
        this.restoreVisitedViewsFromStorage()
      }
      
      // 检查是否已存在（可能在恢复时已添加）
      if (this.visitedViews.some((v) => v.path === view.path)) return
      
      this.visitedViews.push(
        Object.assign({}, view, {
          title: view.meta?.title || 'no-name'
        })
      )
      
      // 保存 visitedViews 到 sessionStorage
      this.saveVisitedViewsToStorage()
      
      // 自动从 sessionStorage 恢复页面状态（页面刷新场景）
      this.restorePageStateFromStorage(view.fullPath)
    },
    /**
     * 更新缓存视图列表
     * 根据当前访问的视图自动计算需要缓存的组件
     */
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
    /**
     * 删除访问视图（同时删除标签和更新缓存）
     * @param view - 路由视图对象
     */
    delView(view: RouteLocationNormalizedLoaded) {
      this.delVisitedView(view)
      this.addCachedView()
    },
    /**
     * 删除访问标签
     * @param view - 路由视图对象
     */
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
            // 静默处理清理失败的情况
          }
          // 保存 visitedViews 到 sessionStorage
          this.saveVisitedViewsToStorage()
          break
        }
      }
    },
    /**
     * 删除当前路由的缓存
     */
    delCachedView() {
      const route = router.currentRoute.value
      const index = findIndex<string>(this.getCachedViews, (v) => v === route.name)
      if (index > -1) {
        this.cachedViews.delete(this.getCachedViews[index])
      }
    },
    /**
     * 删除所有访问视图（保留固定标签）
     */
    delAllViews() {
      this.delAllVisitedViews()
      this.addCachedView()
    },
    /**
     * 删除所有访问标签（保留固定标签）
     */
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
      // 保存 visitedViews 到 sessionStorage
      this.saveVisitedViewsToStorage()
    },
    /**
     * 删除其他访问视图（保留当前视图和固定标签）
     * @param view - 要保留的路由视图对象
     */
    delOthersViews(view: RouteLocationNormalizedLoaded) {
      this.delOthersVisitedViews(view)
      this.addCachedView()
    },
    /**
     * 删除其他访问标签（保留当前标签和固定标签）
     * @param view - 要保留的路由视图对象
     */
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
      // 保存 visitedViews 到 sessionStorage
      this.saveVisitedViewsToStorage()
    },
    /**
     * 删除左侧访问视图（保留当前视图及右侧视图和固定标签）
     * @param view - 当前路由视图对象
     */
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
        // 保存 visitedViews 到 sessionStorage
        this.saveVisitedViewsToStorage()
      }
    },
    /**
     * 删除右侧访问视图（保留当前视图及左侧视图和固定标签）
     * @param view - 当前路由视图对象
     */
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
        // 保存 visitedViews 到 sessionStorage
        this.saveVisitedViewsToStorage()
      }
    },
    /**
     * 更新访问视图信息
     * @param view - 路由视图对象
     */
    updateVisitedView(view: RouteLocationNormalizedLoaded) {
      for (let v of this.visitedViews) {
        if (v.path === view.path) {
          v = Object.assign(v, view)
          // 保存 visitedViews 到 sessionStorage
          this.saveVisitedViewsToStorage()
          break
        }
      }
    },
    /**
     * 设置当前选中的标签
     * @param tag - 路由视图对象
     */
    setSelectedTag(tag: RouteLocationNormalizedLoaded) {
      this.selectedTag = tag
    },
    /**
     * 设置标签标题
     * @param title - 标题文本
     * @param path - 路由路径，如果不提供则使用当前选中的标签路径
     */
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
                // 状态格式不正确，跳过恢复
                continue
              }
            } else if (isImportGridPrefix) {
              // ImportGrid 状态应该包含 dataList
              const isValid = state.dataList !== undefined
              if (!isValid) {
                // 状态格式不正确，跳过恢复
                continue
              }
            }
            
            this.pageStates.set(fullPath, state)
            return
          }
        } catch (err) {
          // 静默处理恢复失败的情况，继续尝试下一个前缀
        }
      }
    },
    /**
     * 注册页签关闭前检查函数
     * @param fullPath - 路由的完整路径（包含 query 参数）
     * @param handler - 检查函数，返回 Promise<boolean>，true 表示允许关闭，false 表示阻止关闭
     */
    registerBeforeCloseHandler(fullPath: string, handler: () => Promise<boolean>) {
      this.beforeCloseHandlers.set(fullPath, handler)
    },
    /**
     * 注销页签关闭前检查函数
     * @param fullPath - 路由的完整路径（包含 query 参数）
     */
    unregisterBeforeCloseHandler(fullPath: string) {
      this.beforeCloseHandlers.delete(fullPath)
    },
    /**
     * 执行页签关闭前检查
     * @param fullPath - 路由的完整路径（包含 query 参数）
     * @returns Promise<boolean>，true 表示允许关闭，false 表示阻止关闭
     */
    async executeBeforeCloseHandler(fullPath: string): Promise<boolean> {
      const handler = this.beforeCloseHandlers.get(fullPath)
      if (handler) {
        return await handler()
      }
      // 如果没有注册检查函数，默认允许关闭
      return true
    },
    /**
     * 保存 visitedViews 到 sessionStorage
     */
    saveVisitedViewsToStorage() {
      try {
        // 只保存必要的字段，避免序列化问题
        const viewsToSave = this.visitedViews.map((v) => ({
          path: v.path,
          fullPath: v.fullPath,
          name: v.name,
          meta: v.meta,
          params: v.params,
          query: v.query,
          hash: v.hash,
          title: v.meta?.title || 'no-name'
        }))
        sessionStorage.setItem(VISITED_VIEWS_STORAGE_KEY, JSON.stringify(viewsToSave))
      } catch (err) {
        console.error('保存 visitedViews 到 sessionStorage 失败：', err)
      }
    },
    /**
     * 从 sessionStorage 恢复 visitedViews（页面刷新场景）
     */
    restoreVisitedViewsFromStorage() {
      try {
        const savedViews = sessionStorage.getItem(VISITED_VIEWS_STORAGE_KEY)
        if (savedViews) {
          const views = JSON.parse(savedViews)
          if (Array.isArray(views) && views.length > 0) {
            // 恢复 visitedViews（但不触发自动保存，避免循环）
            this.visitedViews = views as RouteLocationNormalizedLoaded[]
            // 恢复后更新缓存
            this.addCachedView()
          }
        }
      } catch (err) {
        console.error('从 sessionStorage 恢复 visitedViews 失败：', err)
      }
    }
  },
  persist: false
})

export const useTagsViewStoreWithOut = () => {
  return useTagsViewStore(store)
}
