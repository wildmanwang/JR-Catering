import { hasRoute } from './router'
import router from './router'
import type { RouteRecordRaw } from 'vue-router'
import { useTitle } from '@/hooks/web/useTitle'
import { useNProgress } from '@/hooks/web/useNProgress'
import { usePermissionStoreWithOut } from '@/store/modules/permission'
import { usePageLoading } from '@/hooks/web/usePageLoading'
import { useAuthStoreWithOut } from '@/store/modules/auth'
import { getRoleMenusApi } from '@/api/login'

const { start, done } = useNProgress()

const { loadStart, loadDone } = usePageLoading()

const whiteList = ['/login', '/docs/privacy', '/docs/agreement']

router.beforeEach(async (to, from, next) => {
  start()
  loadStart()
  const permissionStore = usePermissionStoreWithOut()
  const authStore = useAuthStoreWithOut()

  if (authStore.getToken) {
    if (to.path === '/login') {
      next({ path: '/' })
    } else if (to.path === '/reset/password') {
      next()
    } else {
      if (!authStore.getIsUser) {
        await authStore.setUserInfo()
      }
      if (permissionStore.getIsAddRouters) {
        if (to.path === '/') {
          next({ path: '/dashboard/workplace', replace: true })
          return
        }
        if (!hasRoute(to.path)) {
          authStore.logout('认证已过期，请重新登录！')
        }
        next()
        return
      }

      const targetPath = to.path
      const redirectPath = from.query.redirect as string
      
      const res = await getRoleMenusApi()
      const routers = res.data || []
      await permissionStore.generateRoutes(routers).catch(() => {})
      permissionStore.getAddRouters.forEach((route) => {
        router.addRoute(route as RouteRecordRaw)
      })
      if (router.hasRoute('CatchAllBeforeLoad')) {
        router.removeRoute('CatchAllBeforeLoad')
      }
      permissionStore.setIsAddRouters(true)
      
      let finalPath = redirectPath ? decodeURIComponent(redirectPath) : targetPath
      if (finalPath === '/') {
        finalPath = '/dashboard/workplace'
      }
      
      if (hasRoute(finalPath)) {
        next({ path: finalPath, replace: true })
      } else {
        next({ path: '/dashboard/workplace', replace: true })
      }
    }
  } else {
    if (whiteList.indexOf(to.path) !== -1) {
      next()
    } else {
      next(`/login?redirect=${to.path}`)
    }
  }
})

router.afterEach((to) => {
  useTitle(to?.meta?.title as string)
  done()
  loadDone()
})
