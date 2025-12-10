<script lang="tsx">
import { ElBreadcrumb, ElBreadcrumbItem } from 'element-plus'
import { ref, watch, computed, unref, defineComponent, TransitionGroup } from 'vue'
import { useRouter } from 'vue-router'
import { usePermissionStore } from '@/store/modules/permission'
import { filterBreadcrumb } from './helper'
import { filter, treeToList } from '@/utils/tree'
import { pathResolve } from '@/utils/routerHelper'
import type { RouteLocationNormalizedLoaded } from 'vue-router'
import { useI18n } from '@/hooks/web/useI18n'
import { Icon } from '@/components/Icon'
import { useAppStore } from '@/store/modules/app'
import { useDesign } from '@/hooks/web/useDesign'

const { getPrefixCls } = useDesign()

const prefixCls = getPrefixCls('breadcrumb')

const appStore = useAppStore()

// 面包屑图标
const breadcrumbIcon = computed(() => appStore.getBreadcrumbIcon)

export default defineComponent({
  name: 'Breadcrumb',
  setup() {
    const { currentRoute } = useRouter()

    const { t } = useI18n()

    const levelList = ref<AppRouteRecordRaw[]>([])

    const permissionStore = usePermissionStore()

    const menuRouters = computed(() => {
      const routers = permissionStore.getRouters
      return filterBreadcrumb(routers)
    })

    /**
     * 创建不过滤 hidden 路由的完整路由列表（用于面包屑匹配）
     * 与 filterBreadcrumb 的区别：不过滤 hidden=true 的路由
     */
    const createAllRoutersForBreadcrumb = (
      routes: AppRouteRecordRaw[],
      parentPath = ''
    ): AppRouteRecordRaw[] => {
      const res: AppRouteRecordRaw[] = []

      for (const route of routes) {
        const meta = route?.meta
        // 只过滤 breadcrumb: false 的路由，不过滤 hidden 路由
        if (meta?.breadcrumb === false) {
          continue
        }

        const data: AppRouteRecordRaw =
          !meta?.alwaysShow && route.children?.length === 1
            ? { ...route.children[0], path: pathResolve(route.path, route.children[0].path) }
            : { ...route }

        data.path = pathResolve(parentPath, data.path)

        if (data.children) {
          data.children = createAllRoutersForBreadcrumb(data.children, data.path)
        }
        if (data) {
          res.push(data)
        }
      }
      return res
    }

    /**
     * 获取完整路由列表（不过滤 hidden 路由）
     * 用于查找不在菜单中但需要显示面包屑的路由
     */
    const allRouters = computed(() => {
      const routers = permissionStore.getRouters
      return createAllRoutersForBreadcrumb(routers)
    })

    const getBreadcrumb = () => {
      const currentPath = currentRoute.value.matched.slice(-1)[0].path
      
      // 先尝试从菜单路由中查找（优先显示菜单中的路由）
      let matchedRoutes = filter<AppRouteRecordRaw>(unref(menuRouters), (node: AppRouteRecordRaw) => {
        return node.path === currentPath
      })
      
      // 如果在菜单路由中找不到，从完整路由列表中查找（包括 hidden 路由）
      if (!matchedRoutes || matchedRoutes.length === 0) {
        matchedRoutes = filter<AppRouteRecordRaw>(unref(allRouters), (node: AppRouteRecordRaw) => {
          return node.path === currentPath
        })
      }
      
      levelList.value = matchedRoutes || []
    }

    const renderBreadcrumb = () => {
      const breadcrumbList = treeToList<AppRouteRecordRaw[]>(unref(levelList))
      return breadcrumbList.map((v) => {
        const disabled = !v.redirect || v.redirect === 'noredirect'
        const meta = v.meta
        return (
          <ElBreadcrumbItem to={{ path: disabled ? '' : v.path }} key={v.name}>
            {meta?.icon && breadcrumbIcon.value ? (
              <>
                <Icon icon={meta.icon} class="mr-[5px]"></Icon> {t(v?.meta?.title || '')}
              </>
            ) : (
              t(v?.meta?.title || '')
            )}
          </ElBreadcrumbItem>
        )
      })
    }

    watch(
      () => currentRoute.value,
      (route: RouteLocationNormalizedLoaded) => {
        if (route.path.startsWith('/redirect/')) {
          return
        }
        getBreadcrumb()
      },
      {
        immediate: true
      }
    )

    return () => (
      <ElBreadcrumb separator="/" class={`${prefixCls} flex items-center h-full ml-[10px]`}>
        <TransitionGroup appear enter-active-class="animate__animated animate__fadeInRight">
          {renderBreadcrumb()}
        </TransitionGroup>
      </ElBreadcrumb>
    )
  }
})
</script>

<style lang="less" scoped>
@prefix-cls: ~'@{elNamespace}-breadcrumb';

.@{prefix-cls} {
  :deep(&__item) {
    display: flex;
    .@{prefix-cls}__inner {
      display: flex;
      align-items: center;
      color: var(--top-header-text-color);

      &:hover {
        color: var(--el-color-primary);
      }
    }
  }

  :deep(&__item):not(:last-child) {
    .@{prefix-cls}__inner {
      color: var(--top-header-text-color);

      &:hover {
        color: var(--el-color-primary);
      }
    }
  }

  :deep(&__item):last-child {
    .@{prefix-cls}__inner {
      color: var(--el-text-color-placeholder);

      &:hover {
        color: var(--el-text-color-placeholder);
      }
    }
  }
}
</style>
